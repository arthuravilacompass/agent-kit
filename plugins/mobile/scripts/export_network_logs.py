#!/usr/bin/env python3
# desc: Exports HTTP network logs from the Dart VM Service to JSON.
"""
Flutter Network Logs Exporter

Connects to the Dart VM Service Protocol via WebSocket, fetches HTTP profile
data filtered by a time range, and saves structured JSON to ~/Downloads/.

Usage:
    python3 export_network_logs.py <url> <start-time> <end-time> [--output PATH]

    <url>         VM Service WS URL (ws://...) or DevTools browser URL (http://...)
                  or "auto" to detect from running Flutter processes
    <start-time>  HH:MM:SS or HH:MM:SS.mmm (local time, today)
    <end-time>    HH:MM:SS or HH:MM:SS.mmm (local time, today)
    --output      Override output path (default: ~/Downloads/flutter_network_logs_<timestamp>.json)

Examples:
    python3 export_network_logs.py auto 11:11:30 11:12:10
    python3 export_network_logs.py "ws://127.0.0.1:64673/hash=/ws" 11:11:30 11:12:10

Dependency:
    pip3 install websocket-client
"""

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Union
from urllib.parse import parse_qs, unquote, urlparse

try:
    import websocket
except ImportError:
    print("Missing dependency: websocket-client")
    print("Install with: pip3 install websocket-client")
    sys.exit(1)


# ── URL Parsing ──────────────────────────────────────────────────────────────


def detect_vm_service_url() -> Optional[str]:
    """Auto-detect VM Service URL from running Flutter/Dart processes."""
    try:
        result = subprocess.run(
            ["ps", "aux"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        for line in result.stdout.splitlines():
            match = re.search(r"--vm-service-uri=(http://[^\s]+)", line)
            if match:
                return match.group(1)
    except Exception:
        pass
    return None


def resolve_to_dds_url(http_url: str) -> str:
    """
    Follow HTTP redirects from a raw VM Service URL to find the DDS WebSocket URL.
    The raw VM service redirects to the DevTools page which embeds the DDS ws:// URI.
    """
    import urllib.request

    try:
        resp = urllib.request.urlopen(http_url, timeout=5)
        final_url = resp.url
        # The redirect lands on the DevTools page: http://127.0.0.1:9100/?uri=ws%3A%2F%2F...
        if "uri=" in final_url:
            parsed = urlparse(final_url)
            params = parse_qs(parsed.query)
            if "uri" in params:
                return unquote(params["uri"][0])
    except Exception:
        pass

    # Fallback: direct conversion (older Dart SDK without DDS)
    url = http_url
    if url.startswith("http://"):
        url = "ws://" + url[len("http://"):]
    if not url.endswith("/ws"):
        url = url.rstrip("/") + "/ws"
    return url


def parse_vm_service_url(url: str) -> str:
    """Convert any URL form to a ws://... DDS WebSocket URL."""
    if url == "auto":
        detected = detect_vm_service_url()
        if not detected:
            print("Error: No running Flutter debug session found.")
            print("Start your app in debug mode or provide the URL manually.")
            sys.exit(1)
        print(f"Auto-detected raw VM Service: {detected}")
        url = detected

    # Raw VM Service http:// URL → follow redirect to get DDS ws:// URL
    if url.startswith("http://") and "uri=" not in url:
        ws_url = resolve_to_dds_url(url)
        print(f"Resolved DDS WebSocket URL: {ws_url}")
        return ws_url

    # DevTools browser URL → extract uri param directly
    if url.startswith("http") and "uri=" in url:
        parsed = urlparse(url)
        params = parse_qs(parsed.query)
        if "uri" in params:
            url = unquote(params["uri"][0])

    # Already ws:// → ensure /ws suffix
    if url.startswith("ws://") or url.startswith("wss://"):
        if not url.endswith("/ws"):
            url = url.rstrip("/") + "/ws"
        return url

    # Convert http:// to ws:// as last resort
    if url.startswith("http://"):
        url = "ws://" + url[len("http://"):]
    elif url.startswith("https://"):
        url = "wss://" + url[len("https://"):]
    if not url.endswith("/ws"):
        url = url.rstrip("/") + "/ws"

    return url


# ── Time Parsing ─────────────────────────────────────────────────────────────


def parse_time(time_str: str) -> datetime:
    """Parse HH:MM:SS or HH:MM:SS.mmm into a datetime for today."""
    formats = ["%H:%M:%S.%f", "%H:%M:%S"]
    for fmt in formats:
        try:
            t = datetime.strptime(time_str, fmt).time()
            return datetime.combine(date.today(), t)
        except ValueError:
            continue
    print(f"Error: Invalid time format '{time_str}'. Use HH:MM:SS or HH:MM:SS.mmm")
    sys.exit(1)


def to_epoch_us(dt: datetime) -> int:
    """Convert a local datetime to epoch microseconds."""
    return int(dt.timestamp() * 1_000_000)


def from_epoch_us(us: int) -> str:
    """Convert epoch microseconds to ISO 8601 local time string."""
    return datetime.fromtimestamp(us / 1_000_000).isoformat(timespec="milliseconds")


# ── VM Service Client ────────────────────────────────────────────────────────


class VMServiceClient:
    def __init__(self, ws_url: str):
        self._ws_url = ws_url
        self._ws = None
        self._id = 0

    def connect(self):
        print(f"Connecting to {self._ws_url} ...")
        try:
            self._ws = websocket.create_connection(self._ws_url, timeout=60)
        except Exception as e:
            print(f"Error: Cannot connect to VM Service at {self._ws_url}")
            print(f"  {e}")
            print("Is the Flutter app still running in debug mode?")
            sys.exit(1)
        print("Connected.")

    def close(self):
        if self._ws:
            self._ws.close()

    def _call(self, method: str, params: Optional[Dict] = None) -> Dict:
        self._id += 1
        request = {
            "jsonrpc": "2.0",
            "id": self._id,
            "method": method,
            "params": params or {},
        }
        self._ws.send(json.dumps(request))

        # Read responses until we get the one matching our ID
        while True:
            raw = self._ws.recv()
            msg = json.loads(raw)
            if msg.get("id") == self._id:
                if "error" in msg:
                    raise RuntimeError(
                        f"VM Service error on '{method}': {msg['error']}"
                    )
                return msg.get("result", {})

    def get_main_isolate_id(self) -> str:
        """Find the isolate that has HTTP profiling enabled."""
        vm = self._call("getVM")
        isolates = vm.get("isolates", [])

        for iso_ref in isolates:
            iso_id = iso_ref["id"]
            try:
                iso = self._call("getIsolate", {"isolateId": iso_id})
                extensions = iso.get("extensionRPCs", [])
                if "ext.dart.io.getHttpProfile" in extensions:
                    print(f"Found HTTP profiling on isolate: {iso_ref.get('name', iso_id)}")
                    return iso_id
            except RuntimeError:
                continue

        print("Error: No isolate with HTTP profiling found.")
        print("Ensure the app is running in debug mode and has made network requests.")
        sys.exit(1)

    def get_http_profile(self, isolate_id: str, since_us: Optional[int] = None) -> list:
        params: Dict = {"isolateId": isolate_id}
        if since_us is not None:
            params["since"] = since_us
        result = self._call("ext.dart.io.getHttpProfile", params)
        return result.get("requests", [])

    def get_http_profile_request(self, isolate_id: str, request_id: int) -> dict:
        return self._call(
            "ext.dart.io.getHttpProfileRequest",
            {"isolateId": isolate_id, "id": request_id},
        )


# ── Filtering & Formatting ──────────────────────────────────────────────────


def filter_by_time(requests: list, start_us: int, end_us: int) -> list:
    filtered = [
        r
        for r in requests
        if r.get("startTime", 0) >= start_us
        and r.get("startTime", 0) <= end_us
    ]
    return sorted(filtered, key=lambda r: r.get("startTime", 0))


def decode_body(body_data) -> Optional[str]:
    """Attempt to decode a response/request body from the VM service format."""
    if body_data is None:
        return None
    if isinstance(body_data, str):
        return body_data
    if isinstance(body_data, list):
        try:
            return bytes(body_data).decode("utf-8", errors="replace")
        except Exception:
            return str(body_data)
    return str(body_data)


def format_headers(headers_list) -> dict:
    """Convert VM service headers format to a simple dict."""
    if not headers_list:
        return {}
    result = {}
    if isinstance(headers_list, dict):
        return headers_list
    if isinstance(headers_list, list):
        for h in headers_list:
            if isinstance(h, dict):
                name = h.get("name", "")
                value = h.get("value", "")
                result[name] = value
    return result


def build_request_entry(detail: dict) -> dict:
    """Build a structured dict from a full request detail."""
    start_us = detail.get("startTime", 0)
    end_us = detail.get("endTime", start_us)
    duration_ms = (end_us - start_us) / 1000 if end_us > start_us else 0

    req = detail.get("request", {})
    resp = detail.get("response", {})

    req_headers = format_headers(req.get("headers"))
    resp_headers = format_headers(resp.get("headers"))

    req_body = decode_body(detail.get("requestBody"))
    resp_body = decode_body(detail.get("responseBody"))

    # Try to parse JSON bodies for readability
    for label, body in [("request", req_body), ("response", resp_body)]:
        if body and isinstance(body, str):
            try:
                parsed = json.loads(body)
                if label == "request":
                    req_body = parsed
                else:
                    resp_body = parsed
            except (json.JSONDecodeError, ValueError):
                pass

    content_type = resp_headers.get("content-type", resp_headers.get("Content-Type", ""))

    return {
        "method": detail.get("method", req.get("method", "?")),
        "url": detail.get("uri", req.get("uri", "?")),
        "status_code": resp.get("statusCode"),
        "start_time": from_epoch_us(start_us) if start_us else None,
        "end_time": from_epoch_us(end_us) if end_us else None,
        "duration_ms": round(duration_ms, 1),
        "content_type": content_type,
        "request_headers": req_headers,
        "response_headers": resp_headers,
        "request_body": req_body,
        "response_body": resp_body,
        "error": detail.get("error"),
    }


def build_export(
    details: list, start_str: str, end_str: str, ws_url: str
) -> dict:
    entries = [build_request_entry(d) for d in details]
    return {
        "export_info": {
            "tool": "flutter-network-logs-exporter",
            "exported_at": datetime.now().isoformat(timespec="seconds"),
            "filter_start": start_str,
            "filter_end": end_str,
            "total_requests": len(entries),
            "vm_service_url": ws_url,
        },
        "requests": entries,
    }


# ── Main ─────────────────────────────────────────────────────────────────────


def main():
    parser = argparse.ArgumentParser(
        description="Export Flutter HTTP network logs from Dart VM Service"
    )
    parser.add_argument(
        "url",
        help='VM Service URL, DevTools browser URL, or "auto" to detect',
    )
    parser.add_argument("start_time", help="Start time (HH:MM:SS or HH:MM:SS.mmm)")
    parser.add_argument("end_time", help="End time (HH:MM:SS or HH:MM:SS.mmm)")
    parser.add_argument("--output", "-o", help="Output file path (default: ~/Downloads/...)")
    args = parser.parse_args()

    # Parse inputs
    ws_url = parse_vm_service_url(args.url)
    start_dt = parse_time(args.start_time)
    end_dt = parse_time(args.end_time)
    start_us = to_epoch_us(start_dt)
    end_us = to_epoch_us(end_dt)

    print(f"Time range: {args.start_time} → {args.end_time}")

    # Connect
    client = VMServiceClient(ws_url)
    client.connect()

    try:
        # Find isolate
        isolate_id = client.get_main_isolate_id()

        # Get profile — pass start_us as `since` to avoid fetching the full backlog
        requests = client.get_http_profile(isolate_id, since_us=start_us)
        print(f"Total HTTP requests in profile: {len(requests)}")

        # Filter
        filtered = filter_by_time(requests, start_us, end_us)
        print(f"Requests in time range: {len(filtered)}")

        if not filtered:
            print("No requests found in the specified time range.")
            return

        # Fetch details
        details = []
        for i, req in enumerate(filtered, 1):
            req_id = req.get("id")
            method = req.get("method", "?")
            uri = req.get("uri", "?")
            short_uri = uri[:80] + "..." if len(uri) > 80 else uri
            print(f"  [{i}/{len(filtered)}] {method} {short_uri}", file=sys.stderr)
            try:
                detail = client.get_http_profile_request(isolate_id, req_id)
                details.append(detail)
            except RuntimeError as e:
                print(f"    Warning: Could not fetch details: {e}", file=sys.stderr)

        # Build export
        export_data = build_export(details, args.start_time, args.end_time, ws_url)

        # Save
        if args.output:
            output_path = Path(args.output).expanduser()
        else:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = Path.home() / "Downloads" / f"flutter_network_logs_{timestamp}.json"

        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)

        size_kb = output_path.stat().st_size / 1024
        print(f"\nExported {len(details)} requests ({size_kb:.1f} KB)")
        print(f"Saved → {output_path}")

    finally:
        client.close()


if __name__ == "__main__":
    main()
