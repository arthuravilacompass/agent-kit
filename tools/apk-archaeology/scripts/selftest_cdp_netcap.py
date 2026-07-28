#!/usr/bin/env python3
"""selftest_cdp_netcap.py — exercises cdp_netcap.py's pure functions and its
hand-rolled WebSocket framing (the highest-risk, hand-written part of the
script) without a live CDP target.

Covers: WS frame masking/unmasking + fragmentation (ws_send/ws_recv over a
socketpair), console-arg joining, bridge-marker matching, contract parsing
(opt-in, with its truncated-message fallback), and — the load-bearing part —
that redaction actually removes a planted secret from every field it can
reach (headers, body, contract payload), not just some of them.
"""
import json
import os
import socket
import struct
import sys

sys.path.insert(0, os.path.dirname(__file__))
from cdp_netcap import (  # noqa: E402
    build_contract_re,
    contains_bridge_marker,
    join_console_args,
    parse_contract,
    redact_headers,
    redact_text,
    ws_recv,
    ws_send,
)

# High-entropy planted "secret" — must never survive any redaction path below.
LIVE_TOKEN = "aB3xZ9qWmK7pL2vN8sT4uY6rQ1wE5dF8"


def test_ws_roundtrip():
    a, b = socket.socketpair()
    a.settimeout(1.0)
    b.settimeout(1.0)

    # client -> server direction: ws_send MUST mask.
    obj = {"id": 1, "method": "Network.enable", "params": {}}
    ws_send(a, obj)
    raw = b.recv(65536)
    b0, b1 = raw[0], raw[1]
    assert b0 & 0x0F == 0x1, "expected a text frame opcode"
    assert b1 & 0x80, "client->server frames must be masked"
    ln = b1 & 0x7F
    mask = raw[2:6]
    payload = raw[6:6 + ln]
    unmasked = bytes(x ^ mask[i % 4] for i, x in enumerate(payload))
    assert json.loads(unmasked.decode()) == obj, unmasked

    # server -> client direction: ws_recv must decode an UNMASKED frame.
    payload2 = json.dumps({"method": "Network.requestWillBeSent"}).encode()
    frame = bytes([0x81, len(payload2)]) + payload2
    b.sendall(frame)
    buf = [b""]
    msg = ws_recv(a, buf)
    assert json.loads(msg) == {"method": "Network.requestWillBeSent"}, msg

    # fragmentation: two continuation frames must join into one message.
    part1, part2 = b"hello ", b"world"
    frame1 = bytes([0x01, len(part1)]) + part1  # fin=0, opcode=text
    frame2 = bytes([0x80, len(part2)]) + part2  # fin=1, opcode=continuation
    b.sendall(frame1 + frame2)
    buf2 = [b""]
    msg2 = ws_recv(a, buf2)
    assert msg2 == "hello world", msg2

    # 16-bit extended length (>=126) framing path.
    big = "x" * 200
    payload3 = json.dumps({"v": big}).encode()
    hdr = bytes([0x81, 126]) + struct.pack(">H", len(payload3))
    b.sendall(hdr + payload3)
    buf3 = [b""]
    msg3 = ws_recv(a, buf3)
    assert json.loads(msg3) == {"v": big}, len(msg3)

    a.close()
    b.close()


def test_join_console_args():
    args = [
        {"type": "string", "value": "hello"},
        {"type": "number", "value": 42},
        {"type": "object", "description": "Object", "preview": {}},
    ]
    text, saw_preview_only = join_console_args(args)
    assert "hello" in text and "42" in text and "Object" in text, text
    assert saw_preview_only is True, saw_preview_only

    text2, saw_preview_only2 = join_console_args([{"type": "string", "value": "plain"}])
    assert text2 == "plain", text2
    assert saw_preview_only2 is False, saw_preview_only2


def test_bridge_marker():
    assert contains_bridge_marker("native WebViewBridge: ping", ("bridge",))
    assert contains_bridge_marker("BRIDGE MESSAGE received", ("bridge",))
    assert not contains_bridge_marker("ordinary console log line", ("bridge",))
    assert not contains_bridge_marker(None, ("bridge",))
    assert not contains_bridge_marker("something", [])


def test_contract_parsing():
    marker = "[breadcrumb] api response:"
    contract_re = build_contract_re(marker)

    # well-formed line: marker + name + json payload.
    line = f"{marker} SomeAgent_someMethod {{\"a\": 1, \"token\": \"{LIVE_TOKEN}\"}}"
    entry = parse_contract(line, marker, contract_re, saw_preview_only=False)
    assert entry is not None
    assert entry["name"] == "SomeAgent_someMethod", entry
    assert entry["ok"] is True, entry
    assert entry["payload"]["a"] == 1, entry
    assert entry["payload"]["token"] == "[REDACTED]", entry
    assert LIVE_TOKEN not in json.dumps(entry), "LIVE TOKEN LEAKED IN CONTRACT OUTPUT"

    # marker present but no closing brace visible (truncated upstream) -> fallback path.
    truncated = f"{marker} SomeAgent_someMethod {{\"a\": 1"
    entry2 = parse_contract(truncated, marker, contract_re, saw_preview_only=True)
    assert entry2 is not None
    assert entry2["ok"] is False, entry2
    assert "note" in entry2, entry2

    # marker absent -> None (not structured).
    assert parse_contract("irrelevant line", marker, contract_re, False) is None
    # marker not configured (opt-in) -> None even if the line would otherwise match.
    assert parse_contract(line, None, None, False) is None


def test_redact_text():
    text = f'{{"ok": true, "token": "{LIVE_TOKEN}", "id": "1"}}'
    redacted = redact_text(text)
    assert LIVE_TOKEN not in redacted, "LIVE TOKEN LEAKED IN BODY TEXT"
    assert '"ok": true' in redacted, redacted
    assert '"id": "1"' in redacted, redacted  # low-entropy value kept verbatim
    assert redact_text("") == ""
    assert redact_text(None) is None


def test_redact_headers():
    headers = {
        "Authorization": f"Bearer {LIVE_TOKEN}",
        "Cookie": f"session={LIVE_TOKEN}",
        "X-Request-Id": "not-a-secret",
        "X-Custom": f"leaked={LIVE_TOKEN}",
    }
    out = redact_headers(headers)
    assert out["Authorization"] == "[REDACTED]", out
    assert out["Cookie"] == "[REDACTED]", out
    assert out["X-Request-Id"] == "not-a-secret", out
    assert LIVE_TOKEN not in json.dumps(out), "LIVE TOKEN LEAKED IN HEADERS OUTPUT"


def main():
    test_ws_roundtrip()
    test_join_console_args()
    test_bridge_marker()
    test_contract_parsing()
    test_redact_text()
    test_redact_headers()
    print(
        "OK: WS frame masking/unmasking + fragmentation, console-arg joining, "
        "bridge-marker matching, opt-in contract parsing (+ truncated-message "
        "fallback), and secret redaction across headers/body/contract payload — "
        "no live token leaked in any output"
    )


if __name__ == "__main__":
    main()
