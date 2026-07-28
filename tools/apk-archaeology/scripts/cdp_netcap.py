#!/usr/bin/env python3
# desc: captures WebView network + bridge/console traffic over CDP for a debuggable WebView (method.md "Dynamic analysis (v2)")
"""cdp_netcap.py — Chrome DevTools Protocol (CDP) capture instrument
(references/method.md, "Dynamic analysis (v2)" § "A third capture surface").

WHY THIS EXISTS, next to `capture_dynamic.sh` + `parse_logcat.py`. Those two
cover the native/logcat transport, and logcat truncates each line at ~4000
chars — a real content contract can run to tens of KB and arrives cut mid-object.
When the WebView is debuggable (a QA build, or
`setWebContentsDebuggingEnabled(true)`), attaching to its DevTools socket gives
the web-side console/log traffic **untruncated**, plus the page's own
`Network` requests. Pick the surface by transport: logcat for native
transport-client frames, this script for web-side channels and oversized
payloads. Minimal stdlib CDP client — no proxy or MITM certificate needed.

WHAT IT DOES. Connects to a forwarded WebView DevTools socket, attaches to one
page target, enables Network + Page + Runtime + Log, reloads, and in a single
run collects:
  - network requests (method, url, resourceType, status, mime, headers), and
  - console/log lines matching a bridge marker (a WebView<->native JS bridge
    logging its messages — genuinely common convention, still app-specific in
    exact wording, see `--bridge-marker` below), and
  - (opt-in only, see `--contract-marker`) structured `<name> {json}` breadcrumb
    entries some apps log after each API call.
After the capture window, it fetches full response bodies for completed JSON/
text responses via `Network.getResponseBody`.

Emits one JSON object: `{"requests": [...], "bridge": [...], "contracts": [...]}`.
No third-party deps.

SECRETS. Every field that can carry a live token — request/response headers,
response bodies, contract payloads, request URLs — is redacted before it
reaches the output, reusing `extract_endpoints.looks_like_secret` (the same
heuristic `parse_logcat.redact_url` applies to URLs) so the static and both
dynamic instruments share ONE redaction rule. Sensitive header names
(`Authorization`, `Cookie`, `Set-Cookie`, ...) are redacted whole; every other
header/body is token-redacted. Redaction happens once, up front — there is no
unredacted copy of a captured field anywhere in the output.

APP-SPECIFIC SURFACES ARE OPT-IN, NOT DEFAULTED. `parse_logcat.py`'s own
doctrine (see its docstring) is that a field extractor keyed to one app's exact
logging convention doesn't get structured by default — it's surfaced only when
the operator names the marker. `--contract-marker` has NO default for exactly
that reason: the breadcrumb text prefixing a `<agent>_<method> {json}` line is
one app's own convention, not a general Android/WebView pattern. `--bridge-marker`
defaults to the single generic term "bridge" (case-insensitive) — a naming
convention common enough across WebView<->native bridges (JSBridge,
WebViewBridge, nativeBridge, ...) that it earns a default the way
`parse_logcat`'s `remote.?config|feature.?flag` keyword set does; pass more
markers to widen it for a specific app.

AUTHORIZATION. Same fail-closed gate as `capture_dynamic.sh`: requires
`APK_ARCH_AUTHORIZED=1`. This is a live capture against a running app's network
traffic, not an offline parser — same discipline as the logcat capture wrapper,
and the same reminder applies: the raw capture is unredacted only in memory
during the run; hand-grep any derived artifact for client identifiers before it
leaves the local environment (a green provenance gate checks the repo, not a
capture).

Getting <ws_debugger_url>: forward the WebView's DevTools socket, e.g.
`adb forward tcp:9222 localabstract:webview_devtools_remote_<pid>`
(`adb shell cat /proc/net/unix | grep webview_devtools` lists the live socket
names), then `curl http://localhost:9222/json` lists targets — copy one page
target's `webSocketDebuggerUrl`.

Usage:
  APK_ARCH_AUTHORIZED=1 python3 cdp_netcap.py <ws_debugger_url> \\
      [--capture-seconds N] [--bridge-marker M ...] [--contract-marker TEXT] [--out <path>]
"""
import argparse
import base64
import json
import os
import re
import socket
import struct
import sys
import time
from urllib.parse import urlparse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from extract_endpoints import looks_like_secret  # noqa: E402  (shared redaction rule)
from parse_logcat import redact_url  # noqa: E402  (shared URL redaction rule)

# Generic default — a common WebView<->native bridge naming convention, not
# tied to any one app. Widen with repeated --bridge-marker for a specific app.
DEFAULT_BRIDGE_MARKERS = ("bridge",)

# Header names redacted WHOLE regardless of content (never token-scanned —
# an auth token can be low-entropy-looking, e.g. a short opaque session id).
SENSITIVE_HEADER_NAMES = {
    "authorization", "cookie", "set-cookie", "proxy-authorization",
    "x-api-key", "x-auth-token",
}

# Mime types eligible for body fetching.
BODY_FETCH_MIMES = ("application/json", "text/json", "text/plain")
BODY_FETCH_STATUSES = range(200, 300)

# Broader delimiter set than parse_logcat.redact_url's (URL-only) one — JSON
# bodies and console text need punctuation/whitespace as token boundaries too.
TEXT_DELIMS = re.compile(r'([\s"\'{}\[\](),:;<>])')


def redact_text(text):
    """Token-wise secret redaction over arbitrary text (JSON bodies, console
    lines), reusing extract_endpoints.looks_like_secret — the same heuristic
    parse_logcat.redact_url applies to URLs, generalized to a wider delimiter
    set so JSON punctuation also isolates tokens."""
    if not text:
        return text
    parts = TEXT_DELIMS.split(text)
    out = []
    for part in parts:
        if not part or TEXT_DELIMS.fullmatch(part):
            out.append(part)
        elif looks_like_secret(part):
            out.append("[REDACTED]")
        else:
            out.append(part)
    return "".join(out)


def redact_headers(headers):
    """Redact a headers dict: sensitive header names redacted whole, every
    other value token-redacted. Applied once, up front — no raw copy of a
    captured header survives elsewhere in the output."""
    out = {}
    for k, v in (headers or {}).items():
        if k.lower() in SENSITIVE_HEADER_NAMES:
            out[k] = "[REDACTED]"
        elif isinstance(v, str):
            out[k] = redact_text(v)
        else:
            out[k] = v
    return out


def contains_bridge_marker(text, markers):
    """True if any marker (case-insensitive substring) is present in text."""
    if not text:
        return False
    low = text.lower()
    return any(mk.lower() in low for mk in markers)


def join_console_args(args):
    """Join every console arg's value/description into one untruncated
    string. Returns (joined_text, saw_object_without_value) where the second
    flag signals an arg that only exposed a preview/description (i.e. a live
    object CDP didn't stringify for us), so callers can note the payload may
    be incomplete."""
    parts = []
    saw_preview_only = False
    for a in args:
        v = a.get("value")
        if v is None:
            if a.get("type") == "object" and ("preview" in a or "objectId" in a):
                saw_preview_only = True
            v = a.get("description")
        if v is not None:
            parts.append(v if isinstance(v, str) else json.dumps(v, ensure_ascii=False))
    return " ".join(parts), saw_preview_only


def build_contract_re(marker):
    """Build the '<marker> <name> {json}' regex for one operator-supplied
    marker string. group(1) = name token, group(2) = the (possibly huge) JSON
    payload, captured greedily to the end so nested braces are included."""
    return re.compile(
        re.escape(marker) + r"\s*([\w.]+)\s*(\{.*\})\s*$",
        re.DOTALL,
    )


def parse_contract(text, marker, contract_re, saw_preview_only):
    """Extract one structured contract entry from a console/log line carrying
    `marker`, or None when the marker isn't present (or isn't configured —
    opt-in by design, see the module docstring). The payload is redacted
    before it is parsed as JSON, so a secret embedded in the payload never
    reaches the output even inside `payload_parsed`."""
    if not marker or not text or marker not in text:
        return None
    m = contract_re.search(text)
    if m:
        name = m.group(1)
        payload_str = m.group(2)
    else:
        # Marker present but regex didn't match (e.g. no closing brace visible
        # -> genuinely truncated upstream, or the payload only arrived as an
        # object preview). Keep everything after the marker as raw text rather
        # than dropping it.
        idx = text.index(marker) + len(marker)
        rest = text[idx:].strip()
        sp = rest.split(None, 1)
        name = sp[0] if sp else "UNKNOWN"
        payload_str = sp[1] if len(sp) > 1 else rest
    payload_str = redact_text(payload_str)
    try:
        parsed = json.loads(payload_str)
        ok = True
    except Exception:
        parsed = payload_str
        ok = False
    entry = {
        "name": name,
        "ok": ok,
        "bytes": len(payload_str.encode("utf-8", "replace")),
        "payload": parsed,
    }
    if saw_preview_only:
        entry["note"] = (
            "one or more console args only exposed preview/description (no "
            "full value); payload may be incomplete"
        )
    return entry


def ws_connect(ws_url):
    u = urlparse(ws_url)
    host, port = u.hostname, u.port or 80
    path = u.path
    key = base64.b64encode(os.urandom(16)).decode()
    req = (
        f"GET {path} HTTP/1.1\r\n"
        f"Host: {host}:{port}\r\n"
        "Upgrade: websocket\r\nConnection: Upgrade\r\n"
        f"Sec-WebSocket-Key: {key}\r\nSec-WebSocket-Version: 13\r\n\r\n"
    )
    s = socket.create_connection((host, port))
    s.sendall(req.encode())
    # read handshake response headers
    buf = b""
    while b"\r\n\r\n" not in buf:
        buf += s.recv(4096)
    assert b"101" in buf.split(b"\r\n")[0], f"handshake failed: {buf[:120]}"
    s.settimeout(1.0)
    return s


def ws_send(s, obj):
    payload = json.dumps(obj).encode()
    hdr = bytearray([0x81])  # FIN + text
    n = len(payload)
    mask = os.urandom(4)
    if n < 126:
        hdr.append(0x80 | n)
    elif n < 65536:
        hdr.append(0x80 | 126)
        hdr += struct.pack(">H", n)
    else:
        hdr.append(0x80 | 127)
        hdr += struct.pack(">Q", n)
    hdr += mask
    masked = bytes(b ^ mask[i % 4] for i, b in enumerate(payload))
    s.sendall(bytes(hdr) + masked)


def _recv_exact(s, n, buf):
    while len(buf[0]) < n:
        try:
            chunk = s.recv(65536)
        except socket.timeout:
            return False
        if not chunk:
            return False
        buf[0] += chunk
    return True


def ws_recv(s, buf):
    """Return one full text message (handles fragmentation), or None on timeout."""
    frames = []
    while True:
        if not _recv_exact(s, 2, buf):
            return None
        b0, b1 = buf[0][0], buf[0][1]
        fin = b0 & 0x80
        ln = b1 & 0x7f
        off = 2
        if ln == 126:
            if not _recv_exact(s, 4, buf):
                return None
            ln = struct.unpack(">H", buf[0][2:4])[0]
            off = 4
        elif ln == 127:
            if not _recv_exact(s, 10, buf):
                return None
            ln = struct.unpack(">Q", buf[0][2:10])[0]
            off = 10
        if not _recv_exact(s, off + ln, buf):
            return None
        payload = buf[0][off:off + ln]
        buf[0] = buf[0][off + ln:]
        opcode = b0 & 0x0f
        if opcode == 0x8:  # close
            return None
        frames.append(payload)
        if fin:
            return b"".join(frames).decode("utf-8", "replace")


def capture(ws_url, capture_seconds, bridge_markers, contract_marker):
    contract_re = build_contract_re(contract_marker) if contract_marker else None
    s = ws_connect(ws_url)
    buf = [b""]
    mid = 0

    def cmd(method, params=None):
        nonlocal mid
        mid += 1
        ws_send(s, {"id": mid, "method": method, "params": params or {}})

    cmd("Network.enable")
    cmd("Page.enable")
    cmd("Runtime.enable")
    cmd("Log.enable")
    cmd("Page.reload", {"ignoreCache": True})

    reqs = {}  # requestId -> dict
    order = []
    loading_finished = set()  # requestIds whose loading completed (body available)
    bridge = []
    contracts = []

    def keep_bridge(source, level, text):
        if contains_bridge_marker(text, bridge_markers):
            bridge.append({"source": source, "level": level, "text": redact_text(text)[:2000]})

    def keep_contract(text, saw_preview_only):
        entry = parse_contract(text, contract_marker, contract_re, saw_preview_only)
        if entry is not None:
            contracts.append(entry)

    deadline = time.time() + capture_seconds
    while time.time() < deadline:
        msg = ws_recv(s, buf)
        if msg is None:
            continue
        try:
            m = json.loads(msg)
        except Exception:
            continue
        method = m.get("method")
        p = m.get("params", {})
        if method == "Network.requestWillBeSent":
            r = p.get("request", {})
            rid = p.get("requestId")
            if rid not in reqs:
                order.append(rid)
            reqs[rid] = {
                "method": r.get("method"),
                "url": redact_url(r.get("url") or ""),
                "type": p.get("type"),
                "status": None,
                "mime": None,
                "headers": redact_headers(r.get("headers", {})),
            }
        elif method == "Network.responseReceived":
            rid = p.get("requestId")
            resp = p.get("response", {})
            if rid in reqs:
                reqs[rid]["status"] = resp.get("status")
                reqs[rid]["mime"] = resp.get("mimeType")
        elif method == "Network.loadingFinished":
            # mark request as complete so body is available for fetching
            loading_finished.add(p.get("requestId"))
        elif method == "Runtime.consoleAPICalled":
            text, saw_preview_only = join_console_args(p.get("args", []))
            keep_bridge("consoleAPICalled", p.get("type"), text)
            keep_contract(text, saw_preview_only)
        elif method == "Log.entryAdded":
            entry = p.get("entry", {})
            text = entry.get("text")
            keep_bridge("Log.entryAdded", entry.get("level"), text)
            keep_contract(text, False)
    s.close()

    # ---- body-fetch phase -------------------------------------------------
    # Re-connect to the same target and fetch response bodies for completed
    # JSON/text responses. Bodies are best-effort: if reconnect or any single
    # fetch fails, the rest of the output is unaffected. Redacted BEFORE
    # body_parsed is derived from it, so no raw copy survives either field.
    body_eligible = [
        rid for rid in order
        if rid in loading_finished
        and reqs[rid].get("status") in BODY_FETCH_STATUSES
        and any(m in (reqs[rid].get("mime") or "") for m in BODY_FETCH_MIMES)
    ]
    if body_eligible:
        try:
            s2 = ws_connect(ws_url)
            buf2 = [b""]
            body_request_ids = {}  # cmd_id -> requestId
            for rid in body_eligible:
                mid += 1
                ws_send(s2, {"id": mid, "method": "Network.getResponseBody",
                             "params": {"requestId": rid}})
                body_request_ids[mid] = rid
            body_deadline = time.time() + 5.0
            while body_request_ids and time.time() < body_deadline:
                msg = ws_recv(s2, buf2)
                if msg is None:
                    continue
                try:
                    bm = json.loads(msg)
                except Exception:
                    continue
                cmd_id = bm.get("id")
                if cmd_id in body_request_ids:
                    rid = body_request_ids.pop(cmd_id)
                    result = bm.get("result", {})
                    raw = result.get("body", "")
                    if result.get("base64Encoded"):
                        raw = base64.b64decode(raw).decode("utf-8", "replace")
                    redacted = redact_text(raw)
                    reqs[rid]["body"] = redacted
                    try:
                        reqs[rid]["body_parsed"] = json.loads(redacted)
                    except Exception:
                        pass
            s2.close()
        except Exception as exc:
            for rid in body_eligible:
                if "body" not in reqs[rid]:
                    reqs[rid]["body_fetch_error"] = str(exc)
    # -------------------------------------------------------------------------

    return {"requests": [reqs[rid] for rid in order], "bridge": bridge, "contracts": contracts}


def main():
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("ws_debugger_url", help="CDP page target ws:// URL (see docstring for how to get one)")
    ap.add_argument("--capture-seconds", type=float, default=8.0,
                     help="capture window in seconds (default: 8.0)")
    ap.add_argument("--bridge-marker", action="append", default=None,
                     help="case-insensitive substring marking a console/log line as bridge "
                          "traffic; repeatable. Default: %s" % (list(DEFAULT_BRIDGE_MARKERS),))
    ap.add_argument("--contract-marker", default=None,
                     help="opt-in: exact marker string prefixing a structured '<name> {json}' "
                          "breadcrumb in console/log output. No default (app-specific convention).")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    if os.environ.get("APK_ARCH_AUTHORIZED") != "1":
        print("REFUSED: set APK_ARCH_AUTHORIZED=1 only if you own or are contractually", file=sys.stderr)
        print("authorized to analyze this app. Captures stay local; hand-grep any derived", file=sys.stderr)
        print("artifact for client identifiers before it leaves the machine (capture_dynamic.sh's", file=sys.stderr)
        print("discipline applies here too).", file=sys.stderr)
        sys.exit(2)

    bridge_markers = args.bridge_marker if args.bridge_marker else list(DEFAULT_BRIDGE_MARKERS)
    result = capture(args.ws_debugger_url, args.capture_seconds, bridge_markers, args.contract_marker)
    output = json.dumps(result, ensure_ascii=False, indent=2)

    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(output + "\n")
    else:
        print(output)


if __name__ == "__main__":
    main()
