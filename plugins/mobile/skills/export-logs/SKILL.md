---
name: export-logs
description: Invoke to export HTTP network logs from a running Flutter debug session, filtered by time range, as structured JSON. Triggers — "export the network logs for this time range", "get the HTTP requests between HH:MM:SS and HH:MM:SS", "capture the network traffic from this test".
---

# Export Logs — Export Flutter Network Logs by Time Range

Exports HTTP network logs from a running Flutter debug session, filtered by a time range, as structured JSON.

## Script

This plugin's `scripts/export_network_logs.py` script connects to the Dart VM Service Protocol via WebSocket and fetches the HTTP profile filtered by time — standard Flutter/Dart mechanics, doesn't change between projects.

```
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/export_network_logs.py" <url> <start-time> <end-time> [--output PATH]
```
- `<url>`: VM service WS URL, DevTools URL, or `auto` (detects from running Flutter processes via `--vm-service-uri`).
- `<start-time>` / `<end-time>`: `HH:MM:SS` or `HH:MM:SS.mmm` (local time, today).
- `--output`: output path (default: user's downloads folder, timestamped).

## Usage

```
/export-logs <start-time> <end-time>
```

Times use the `HH:MM:SS` or `HH:MM:SS.mmm` format (local time, today).

**Example:**
```
/export-logs 11:11:30 11:12:10
```

## Steps

### 1. Parse arguments

Extract `<start-time>` and `<end-time>` from the arguments.

If either is missing or doesn't match `HH:MM:SS` / `HH:MM:SS.mmm`, ask the user:
> "Please provide start and end time in HH:MM:SS format. Example: /export-logs 11:11:30 11:12:10"

### 2. Check the websocket-client dependency

Run:
```bash
python3 -c "import websocket"
```

If it fails, install:
```bash
pip3 install websocket-client
```

Then check the import again.

### 3. Run the export script

Use `auto` as the URL — the script detects the running Flutter session from the process arguments (`--vm-service-uri`):

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/export_network_logs.py" auto "<start-time>" "<end-time>"
```

Capture stdout and stderr. The script prints progress to stderr (fetching each request).

### 4. Handle errors

- **"No running Flutter debug session found"** → ask the user to paste the Chrome DevTools URL, and re-run with that URL instead of `auto`:
  ```bash
  python3 "${CLAUDE_PLUGIN_ROOT}/scripts/export_network_logs.py" "<devtools-url>" "<start-time>" "<end-time>"
  ```

- **"No requests found in the specified time range"** → the range might be wrong. Show the user the total request count from the output and suggest widening the range.

- **Connection refused** → the app isn't running anymore. Ask the user to relaunch it.

### 5. Report results

Show the user:
- Number of requests exported
- Full path of the output JSON file
- A brief table of the captured requests: method, URL, status code, duration

## Important

- Times are interpreted as local time, today. Ranges crossing midnight are not supported.
- `auto` URL detection reads `--vm-service-uri` from the running `dart` process's arguments.
- The app must be running in debug mode (any debug flavor/launch).
- Never run the script without time arguments.
- The output JSON can be opened in any editor or HAR viewer (Proxyman, Insomnia).
