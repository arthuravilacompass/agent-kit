---
name: ga4-validate
description: Invoke to validate GA4 tracking (screen × event, before × after a change) on a Flutter app in the simulator — drives the app, captures the real event with params, and builds the CT table with a visual report. Triggers — "validate the GA4 events for this screen", "confirm the tracking before and after this change".
---

# GA4 Validate — GA4 Tracking Validation (screen × event, before × after)

Reusable script to validate GA4 events for components of a Flutter app running in the simulator/emulator: drives the app, captures the **real** event with params, screenshots, matches screen × event, and builds the record (CT table + visual report). Serves both new GA4 tickets and regression checks (before × after comparison).

Reuses the `mobile:export-logs` skill's transport plumbing and the `mobile:marionette` skill to drive the app.

## Project Config

Fill in before use: which events/screens are in scope, whether the project has any tracking layer beyond the direct call to the analytics SDK (e.g. a custom middleware that only fires under certain conditions), and the target file names for temporary instrumentation (§Method A). The capture mechanism (3 approaches below) is universal Firebase/GA4 + Dart VM service — it doesn't change between projects.

## When to Use

- A tracking ticket that needs **screen × event** evidence (e.g. `view_promotion`/`select_promotion`/`view_item_list`/`select_content`, or your project's event names).
- **GA4 regression check:** capture a baseline ("before"), apply the change, re-capture identically ("after"), compare CT by CT.

## What It Produces

1. Per component/CT: the **real captured event** (name + params) + a **screenshot** of the screen.
2. A **CT table** (expected × captured × verdict).
3. (Optional) **Visual report** — start from this skill's `ga4-report-template.html` shell and fill in the sections. Publish via your setup's artifact tool, if any.

## Prerequisites (explicit, never a silent default)

| Input | How to resolve it |
|---|---|
| Device | `xcrun simctl list devices booted` (iOS) / `adb devices` (Android) |
| Backend | the environment variable that decides the backend (not `--flavor` alone) — see the `mobile:marionette` skill |
| Build with the full tracking layer | if the project has additional tracking beyond the direct SDK (middleware, decorator), confirm the build under test includes that layer — a build without it gives a false negative |
| Extra layer only fires under a condition | if your extra tracking layer has a precondition (e.g. only fires with an authenticated session, or only in a given environment), confirm the condition is satisfied before concluding "doesn't fire" |
| Logged in / state | authenticated flows require login; the target component needs to render on the tested screen |

## Capture Methods — 3 layers measuring DIFFERENT things (not "one is better")

Each layer observes a distinct point in the flow — choose based on the question you need to answer:

- **A. `vm_service` reader — *wire-truth*** (what actually goes out, post param-sanitization). Agent-readable.
- **B. DebugView — *Firebase receipt*** (what Firebase received). Manual spot-check in prod; web console, the agent doesn't read/screenshot it.
- **C. Decorator/interceptor on the analytics interface — *boundary*** (what the app **called**, before any sanitization) — only exists if the project has that seam. Measures the boundary, not the wire: reconstructed params, may not see additional tracking (middleware) that runs after the analytics call, and may false-flag names that sanitization normalizes (e.g. a hyphen becoming an underscore). Complements A/B, doesn't replace them.

| Situation | Method |
|---|---|
| **environment with no debug stream bound** (DebugView needs a prod-like stream) | **A. Reader** |
| **Reproducible record** (CTs, before×after, the agent needs to read/screenshot) | **A. Reader** |
| **Project's additional tracking layer (middleware)** | zero-touch if the `mobile:export-logs` skill already covers the HTTP call · or **A** instrumenting the send point · or a proxy (Charles/Proxyman). DebugView does **not** show middleware outside the analytics SDK. |
| **prod + quick manual spot-check** | **B. DebugView** |
| **broad zero-touch coverage** (if the project already has the decorator) | **C. Decorator** |

### A. `vm_service` Reader (agent-readable)

**Central gotcha:** `dart:developer.log()` **does NOT land in the OS log** (`simctl log stream` / equivalent); and analytics helpers usually only log on `catch` (silent on success). So capture works by **instrumenting** + reading the VM service's `Logging` stream.

1. **Instrument (temporary — REVERT at the end):** add `log('[GA4] …')` right **after** each successful analytics call, by **anchor** (not by line — lines drift), in your project's target files (project config: where the analytics layer logs today). Log the event name + the param keys relevant to your CT.
   - If the project blocks `print`/`debugPrint` in production code (lint hook, project config), use `log()` — it passes that kind of gate.
2. **Capture:** read the VM service's `Logging` stream and filter for the instrumented lines (e.g. `[GA4]`).

```dart
// Recipe: connect to the VM service and listen to the Logging stream.
// Usage: dart run <this-file>.dart <ws-uri>   (ws-uri comes from the app log: "Dart VM service is listening on")
import 'package:vm_service/vm_service.dart';
import 'package:vm_service/vm_service_io.dart';

Future<void> main(List<String> args) async {
  final service = await vmServiceConnectUri(args.first);
  await service.streamListen(EventStreams.kLogging);
  service.onLoggingEvent.listen((e) {
    final msg = e.logRecord?.message?.valueAsString;
    if (msg != null && msg.contains('[GA4]')) print(msg);
  });
  print('GA4 reader listening on ${args.first} — drive the app; Ctrl+C to stop');
}
```

3. **Revert:** `git checkout` on the instrumented files. **Confirm the repo is clean** (`git status --short lib/`) before wrapping up.

### B. DebugView (zero-touch — manual spot-check in prod)

- **iOS sim:** `xcrun simctl launch booted <bundle> -FIRDebugEnabled YES`.
- **Android:** `adb shell setprop debug.firebase.analytics.app <package>`.
- Requires a bound stream (prod); it's a web console — the agent doesn't read/screenshot it programmatically. Good for a manual check, bad for a reproducible record.

## Flow

1. **Preflight** — is the `mobile:marionette` skill available? Device booted? Build with the full tracking layer (if applicable)? Environment = the expected one?
2. **Prepare capture** — method A (instrument) or B (DebugView).
3. **Launch + connect** — `mobile:marionette` skill (`scripts/run.sh` → `marionette__connect`). Grab the ws URI from the app log.
4. **Drive + screenshot** — `get_interactive_elements` → `tap`/`scroll_to`. Screenshot to disk when marionette only returns inline (`xcrun simctl io booted screenshot <path>.png` or the Android equivalent). Marionette coords are **logical**, not pixels.
5. **Capture + match** — the reader prints the event; **match screen × event** and confirm the **origin** (the location/screen param = the screen under test — kills false positives from another screen).
6. **Record** — fill in the CT table (expected × captured × verdict). Mark `EMPIRICAL` (seen live) / `code` (verified in fan-out, not exercised) / `doesn't fire` (by design).
7. **(Optional) Report** — start from the `ga4-report-template.html` shell and fill in the sections.
8. **Revert** — undo the instrumentation; confirm the repos are clean.

## Regression — before × after

- The **baseline run** is the "before" (keep the CT-TABLE + screenshots).
- After the change, **re-run IDENTICALLY** (same method, device, build) → "after".
- **Compare CT by CT.** Success = the target CTs changed as expected. Update the "after" column and swap illustrative panels for real payloads.

## Platforms

| Platform | Status | Adaptation |
|---|---|---|
| **iOS Simulator / macOS / reader** | this script's canonical path (proven in a real run) | — |
| **Android** | reader = **the same** (it's Dart VM, platform-agnostic); DebugView via `adb setprop`; screenshot via `adb exec-out screencap -p`; ws URI from `flutter run`/logcat | validate the first time |
| **Windows** | **Android only** — iOS sim does NOT run on Windows; `simctl` doesn't exist (use `adb`) | validate the first time |

> Honesty: validate each platform adaptation the first time it's used — don't assume the mechanism generalizes without checking.

## Gotchas

- **Zero events from the extra tracking layer** → build without that layer, or its precondition wasn't met. Confirm both before reporting "doesn't fire".
- **Param naming can diverge between the middleware layer and plain GA4** (singular vs. plural, or slightly different names for the same concept) — check against your project's expectation before flagging as a bug.
- **Per-component impression** usually has a threshold (e.g. ≥50% visible for 1s) and re-fires when returning to the screen — not a bug if it fires again.
- **Instrumentation not reverted** = risk of leaking a log into a commit. Always `git checkout` + verify.

## References

- Driving the app: `mobile:marionette` skill
- VM service transport (reuse): `mobile:export-logs` skill
- Report shell: `ga4-report-template.html` (this skill)
