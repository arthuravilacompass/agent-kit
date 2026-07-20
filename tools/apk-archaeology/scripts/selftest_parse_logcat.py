#!/usr/bin/env python3
"""selftest_parse_logcat.py — fixture from DOCUMENTED Android framework line shapes.

Deliberately NOT a verbatim copy of the one WordPress capture (§3.2 of the
worked example). The regexes are meant to hold across the version-stable AOSP
line shapes (`START u0 {...cmp=...}`, `Displayed pkg/act: +time`, `chromium`/
`cr_*` tags, a browser `customtabs` component). Fixturing the *convention*
rather than one app's exact strings is the mitigation for the fixture-overfit
risk flagged in parse_logcat.py's docstring (APOSTA). Package is a neutral
`com.example.legacyapp`.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from parse_logcat import parse  # noqa: E402

# `adb logcat -v threadtime` capture, documented framework line shapes.
FIXTURE = """\
06-15 10:23:45.100  1200  1200 I ActivityTaskManager: START u0 {act=android.intent.action.MAIN cat=[android.intent.category.LAUNCHER] flg=0x10000000 cmp=com.example.legacyapp/.LaunchActivity} from uid 0
06-15 10:23:45.320  1200  1200 I ActivityTaskManager: START u0 {cmp=com.example.legacyapp/.MainActivity} from uid 10123
06-15 10:23:45.900  1200  1200 I ActivityTaskManager: START u0 {cmp=com.example.legacyapp/.ui.LoginActivity} from uid 10123
06-15 10:23:46.000  1200  1220 D RemoteConfigStore: fetch remote-field-config ok (60 flags)
06-15 10:23:46.010  1200  1220 D FeatureFlagsStore: fetch feature-flags resolved: web_login=true
06-15 10:23:46.500  1200  1220 D AnalyticsTracker: track event screen_view screen=login
06-15 10:23:47.000  1200  1200 V SomeNoise: irrelevant line that should be ignored
this is not a threadtime line at all and must be skipped
06-15 10:23:53.631  1200  1200 I ActivityTaskManager: Displayed com.example.legacyapp/.ui.LoginActivity: +7s731ms
06-15 10:24:10.050  1200  1200 I ActivityTaskManager: START u0 {act=android.intent.action.VIEW dat=https://auth.example.com/oauth2/authorize?client_id=abc cmp=com.android.chrome/org.chromium.chrome.browser.customtabs.CustomTabActivity} from uid 10123
06-15 10:24:11.200  1400  1450 I cr_media: request audio focus
06-15 10:24:11.210  1400  1450 I chromium: [INFO:CONSOLE(1)] page loaded
06-15 10:24:20.000  1200  1200 I ActivityTaskManager: START u0 {act=android.intent.action.VIEW dat=https://auth.example.com/magic?token=aB3xZ9qWmK7pL2vN8sT4uY6rQ1wE5dF8 cmp=com.android.chrome/org.chromium.chrome.browser.customtabs.CustomTabActivity} from uid 10123
"""

# high-entropy token embedded in the last custom-tab dat= URL — must be redacted
LIVE_TOKEN = "aB3xZ9qWmK7pL2vN8sT4uY6rQ1wE5dF8"


def main():
    r = parse(FIXTURE)

    # --- item 1: navigation sequence disambiguated from START lines ---
    seq = r["navigation"]["sequence"]
    assert seq[:3] == [
        "com.example.legacyapp/.LaunchActivity",
        "com.example.legacyapp/.MainActivity",
        "com.example.legacyapp/.ui.LoginActivity",
    ], seq
    # the launcher START carries act + from_uid, anchored to its line
    launch = r["navigation"]["starts"][0]
    assert launch["cmp"] == "com.example.legacyapp/.LaunchActivity", launch
    assert launch["act"] == "android.intent.action.MAIN", launch
    assert launch["from_uid"] == "0", launch
    assert launch["line"] == 1, launch

    # Displayed captured with timing, anchored
    disp = r["navigation"]["displayed"]
    assert len(disp) == 1, disp
    assert disp[0]["component"] == "com.example.legacyapp/.ui.LoginActivity", disp
    assert disp[0]["timing"] == "7s731ms", disp
    assert disp[0]["line"] == 9, disp

    # --- item 2: render-surface SIGNALS ---
    ct = r["render_surface"]["custom_tab_signals"]
    assert len(ct) == 2, ct
    assert all("customtabs" in c["cmp"].lower() for c in ct), ct
    # low-entropy client_id kept verbatim (not a secret)
    assert any(
        c["url"] == "https://auth.example.com/oauth2/authorize?client_id=abc" for c in ct
    ), ct
    # high-entropy token redacted, URL structure preserved
    redacted = next(c for c in ct if "magic" in c["url"])
    assert LIVE_TOKEN not in redacted["url"], redacted
    assert redacted["url"] == "https://auth.example.com/magic?token=[REDACTED]", redacted
    assert LIVE_TOKEN not in json.dumps(r), "LIVE TOKEN LEAKED IN OUTPUT"

    wv = {w["tag"] for w in r["render_surface"]["webview_signals"]}
    assert wv == {"cr_media", "chromium"}, wv

    # --- CRITICAL: the parser must NEVER emit a "native" verdict ---
    # A native call requires the uiautomator hierarchy (human), not logcat.
    # Structural guarantee: render_surface classifies nothing as native.
    assert set(r["render_surface"].keys()) == {
        "custom_tab_signals",
        "webview_signals",
        "note",
    }, r["render_surface"].keys()
    signal_values = json.dumps(
        {"c": ct, "w": r["render_surface"]["webview_signals"]}
    ).lower()
    assert "native" not in signal_values, "parser emitted a 'native' label in a signal"

    # --- items 3/4: candidate-line surfacing (non-empty here; a null = finding) ---
    rc = r["candidate_lines"]["remote_config"]
    an = r["candidate_lines"]["analytics"]
    assert any("RemoteConfigStore" == c["tag"] for c in rc), rc
    assert any("FeatureFlagsStore" == c["tag"] for c in rc), rc
    assert any("AnalyticsTracker" == c["tag"] for c in an), an

    # --- noise + non-threadtime lines skipped, not parsed ---
    # 12 well-formed threadtime lines; the "this is not a threadtime..." line is skipped.
    assert r["lines_total"] == 13, r["lines_total"]
    assert r["lines_parsed"] == 12, r["lines_parsed"]
    assert r["format_assumed"] == "adb logcat -v threadtime"

    print("OK: nav sequence, custom-tab + webview signals, secret redacted, "
          "candidate surfacing, NO 'native' verdict, noise skipped")


if __name__ == "__main__":
    main()
