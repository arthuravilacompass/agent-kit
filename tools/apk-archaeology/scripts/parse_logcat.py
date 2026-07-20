#!/usr/bin/env python3
# desc: parses a captured logcat into the v2 dynamic reach-map (method.md "Dynamic analysis (v2)")
"""parse_logcat.py — v2 dynamic instrument (references/method.md, "Dynamic analysis (v2)").

Turns a captured `adb logcat` text into the *dynamic reach map* the method
specifies: what the running app DID, cross-checkable by a human against the
static extract. It is the runtime mirror of the static `extract_*.py` scripts —
deterministic, pure stdlib, every observation anchored to the capture's line
number (the file:line mirror; here file = the logcat capture, line = its 1-based
line).

WHAT THIS DOES — and, on purpose, what it does NOT.

- Structured, robust (framework-level — survives release log-stripping):
    1. `navigation` — the boot→screen sequence from `ActivityTaskManager` /
       `ActivityManager` `START` lines and `Displayed` lines. Runtime
       disambiguates what the static module graph only signals directionally.
    2. `render_surface` — SIGNALS only: `custom_tab_signals` (a START into a
       browser `customtabs` component) and `webview_signals` (`chromium` / `cr_*`
       tags = in-process WebView). It NEVER emits "native". Logcat cannot prove a
       screen is native: absence of a webview/custom-tab signal means native OR
       stripped logs OR the surface was outside the capture window. Calling that
       "native" would conflate "no evidence found" with "evidence of no behavior"
       (method.md origin-legend rule). The one thing that DOES support a native
       call — a `uiautomator` view-hierarchy dump with 0 WebView nodes — is
       captured by `capture_dynamic.sh` and read by a human, not parsed here.

- Candidate-line surfacing only (app-specific — NOT generalizable, do not sell
  as structured extraction):
    3. `remote_config` / 4. `analytics` — lines whose tag/message match a small
       keyword set. These ride app-specific tags (e.g. one app's
       `RemoteConfigStore`/`FeatureFlagsStore`), so structuring them would
       generalize a field-extractor from one app — the over-claim the method's
       anti-laundering clause forbids. A null here is a FINDING (release builds
       strip app `Log.*`), never a silent gap. The parser hands a human candidate
       lines to read, it does not decide.

NO auto cross-check against the static extract. The static `graph.json` is an
extends/implements reconstruction (see extract_graph.py) with no navigation
edges; scoring "agreement" between a runtime START *sequence* (fact) and an
inheritance graph (reconstruction) would flatten the confidence tiers the method
keeps separate end to end. The cross-check is a HUMAN step, by design.

APOSTA (untested assumption, stated because it is one): the framework line
shapes parsed here (`START u0 {...cmp=...}`, `Displayed pkg/act: +time`,
`chromium`/`cr_*` tags) are treated as version-stable Android convention. They
are documented and stable across the AOSP versions seen, but this is validated
against ONE capture format only (`-v threadtime`) — a different Android version
or a non-threadtime capture may shift them. `capture_dynamic.sh` pins the format
to `-v threadtime` to close half of this gap.

SECRETS: the one structured value that can carry a live token is a Custom Tab's
`dat=` URL (an OAuth authorize / magic-link the app navigated to, logged by the
framework). It is redacted before it reaches the output, reusing
`extract_endpoints.looks_like_secret` so the static and dynamic instruments share
ONE redaction rule (the method doc itself warns against duplicated logic). The
raw capture on disk is unredacted by nature — the provenance guardrail in
`capture_dynamic.sh` (path-scope + hand-grep before anything leaves local)
covers the capture file and the free-form candidate lines.

Pure stdlib. Deterministic.

Usage:
  python3 parse_logcat.py <logcat_txt> [--out <path>]

Input format: `adb logcat -v threadtime` (what capture_dynamic.sh produces):
  MM-DD HH:MM:SS.mmm  PID  TID L TAG: message
"""
import argparse
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from extract_endpoints import looks_like_secret  # noqa: E402  (shared redaction rule)

# threadtime line: "06-15 10:23:45.123  1234  1235 I ActivityTaskManager: START ..."
THREADTIME_RE = re.compile(
    r"^\d\d-\d\d\s+\d\d:\d\d:\d\d\.\d+\s+\d+\s+\d+\s+[VDIWEFS]\s+(?P<tag>.+?):\s?(?P<msg>.*)$"
)

# START intent block fields (order-independent inside the { } braces).
START_RE = re.compile(r"\bSTART\b.*?\{(?P<intent>[^}]*)\}")
ACT_RE = re.compile(r"\bact=(?P<act>[^\s}]+)")
DAT_RE = re.compile(r"\bdat=(?P<dat>[^\s}]+)")
CMP_RE = re.compile(r"\bcmp=(?P<cmp>[^\s}]+)")
FROM_UID_RE = re.compile(r"\bfrom uid (?P<uid>\d+)")

# "Displayed org.wordpress.android/.ui.accounts.LoginActivity: +7s731ms"
DISPLAYED_RE = re.compile(r"^Displayed\s+(?P<component>\S+?):\s+\+(?P<timing>\S+)")

# In-process WebView renders under chromium; tags are "chromium" or "cr_*".
WEBVIEW_TAG_RE = re.compile(r"^(chromium|cr_.+)$")

# A START whose component is a browser CustomTabs activity = Custom Tab (a 3rd
# category: not native form, not embedded WebView — a web page in a Custom Tab).
CUSTOMTABS_RE = re.compile(r"customtabs", re.IGNORECASE)
URL_RE = re.compile(r"^https?://", re.IGNORECASE)

# Candidate-surfacing keyword sets (heuristic — human reads the result).
REMOTE_CONFIG_RE = re.compile(r"remote.?config|feature.?flag|remote-field|feature-flags", re.IGNORECASE)
ANALYTICS_RE = re.compile(r"analytics|firebaseanalytics|ga4|track.?event", re.IGNORECASE)

RENDER_NOTE = (
    "SIGNALS only. Absence of a webview/custom-tab signal is NOT 'native' — "
    "logcat cannot prove absence (stripped logs / outside capture window). A "
    "native call needs the uiautomator view hierarchy (0 WebView nodes), read "
    "by a human, not this parser."
)
CANDIDATE_NOTE = (
    "App-specific candidate lines for a human to interpret, NOT structured "
    "extraction. An empty list is a FINDING (release builds may strip app "
    "Log.*), not a silent gap."
)

URL_DELIMS = re.compile(r"([/?&=:@])")


def redact_url(url):
    """Redact secret-looking tokens from a URL, token-wise on delimiters.

    Shares the secret heuristic with extract_endpoints (KEY_PATTERNS + entropy),
    so a token in a Custom Tab's dat= URL never reaches the persisted output.
    """
    parts = URL_DELIMS.split(url)
    out = []
    for part in parts:
        if URL_DELIMS.fullmatch(part):
            out.append(part)
        elif part and looks_like_secret(part):
            out.append("[REDACTED]")
        else:
            out.append(part)
    return "".join(out)


def parse(text):
    navigation = {"starts": [], "displayed": [], "sequence": []}
    render_surface = {"custom_tab_signals": [], "webview_signals": [], "note": RENDER_NOTE}
    candidate_lines = {"remote_config": [], "analytics": [], "note": CANDIDATE_NOTE}

    lines = text.splitlines()
    lines_parsed = 0

    for lineno, raw in enumerate(lines, start=1):
        m = THREADTIME_RE.match(raw)
        if not m:
            continue
        lines_parsed += 1
        tag = m.group("tag").strip()
        msg = m.group("msg")

        # --- item 1/2: navigation + custom-tab signal (from START intent) ---
        start_m = START_RE.search(msg)
        if start_m:
            intent = start_m.group("intent")
            act = ACT_RE.search(intent)
            dat = DAT_RE.search(intent)
            cmp_ = CMP_RE.search(intent)
            uid = FROM_UID_RE.search(msg)
            act_v = act.group("act") if act else None
            dat_v = dat.group("dat") if dat else None
            cmp_v = cmp_.group("cmp") if cmp_ else None
            # A dat= URL can carry a live token (OAuth/magic-link) — redact ONCE,
            # up front, so no raw copy survives in starts[] or the signal below.
            dat_is_url = bool(dat_v and URL_RE.match(dat_v))
            dat_out = redact_url(dat_v) if dat_is_url else dat_v
            navigation["starts"].append(
                {
                    "line": lineno,
                    "act": act_v,
                    "cmp": cmp_v,
                    "dat": dat_out,
                    "from_uid": uid.group("uid") if uid else None,
                }
            )
            if cmp_v:
                navigation["sequence"].append(cmp_v)
                if CUSTOMTABS_RE.search(cmp_v):
                    render_surface["custom_tab_signals"].append(
                        {
                            "line": lineno,
                            "cmp": cmp_v,
                            "url": dat_out if dat_is_url else None,
                        }
                    )

        # --- item 1: Displayed ---
        disp_m = DISPLAYED_RE.match(msg)
        if disp_m:
            navigation["displayed"].append(
                {
                    "line": lineno,
                    "component": disp_m.group("component"),
                    "timing": disp_m.group("timing"),
                }
            )

        # --- item 2: embedded-WebView signal (by tag) ---
        if WEBVIEW_TAG_RE.match(tag):
            render_surface["webview_signals"].append({"line": lineno, "tag": tag})

        # --- items 3/4: candidate-line surfacing ---
        haystack = tag + " " + msg
        if REMOTE_CONFIG_RE.search(haystack):
            candidate_lines["remote_config"].append({"line": lineno, "tag": tag, "message": msg})
        if ANALYTICS_RE.search(haystack):
            candidate_lines["analytics"].append({"line": lineno, "tag": tag, "message": msg})

    return {
        "format_assumed": "adb logcat -v threadtime",
        "lines_total": len(lines),
        "lines_parsed": lines_parsed,
        "navigation": navigation,
        "render_surface": render_surface,
        "candidate_lines": candidate_lines,
    }


def main():
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("logcat_txt")
    parser.add_argument("--out", default=None)
    args = parser.parse_args()

    with open(args.logcat_txt, encoding="utf-8", errors="replace") as f:
        text = f.read()

    result = parse(text)
    output = json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False)

    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(output + "\n")
    else:
        print(output)


if __name__ == "__main__":
    main()
