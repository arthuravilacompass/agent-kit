#!/usr/bin/env bash
# desc: v2 dynamic capture — adb logcat (threadtime) + uiautomator dump of a booted legacy APK
#       (references/method.md, "Dynamic analysis (v2)"). Behavior, not contract: logcat only,
#       NEVER traffic interception. Runbook + wrapper. Feeds parse_logcat.py.
#
# WHY THIS PAIRS logcat WITH uiautomator:
#   - logcat -v threadtime  → what the app DID (nav START/Displayed, webview/custom-tab
#     SIGNALS, boot-time config/analytics candidate lines). parse_logcat.py reads this.
#   - uiautomator dump      → the view hierarchy of the CURRENT screen. This is the ONLY
#     source that can support a "native" call (0 WebView nodes). logcat cannot prove a
#     surface is native (absence != native — see parse_logcat.py). A HUMAN reads the dump;
#     no script turns it into a verdict.
#
# PROVENANCE / AUTHORIZATION (fail-closed, load-bearing — read before running):
#   - Only on an app you own or are contractually authorized to analyze. Respect store
#     terms, third-party licenses, IP law, and data-protection law (e.g. LGPD).
#   - Everything is path-scoped to <work_dir>. NEVER point <work_dir> at a client tree or
#     mix a client capture with a public one.
#   - The raw capture is UNREDACTED by nature (it is the ground truth). Before ANY artifact
#     derived from it leaves the local environment, hand-grep it for client identifiers —
#     a green provenance gate checks the repo, not this capture. parse_logcat.py redacts
#     secret-looking tokens from its OUTPUT, but logcat.txt itself is not sanitized.
#   - This script is committed as a runbook. Real runs happen on the operator's machine
#     against the real app, and are NEVER committed (design doc §8).
set -uo pipefail

if [[ $# -lt 1 ]]; then
  echo "usage: capture_dynamic.sh <work_dir> [<package>] [<duration_sec>]" >&2
  echo "  <work_dir>     path-scoped output dir (logcat.txt, uihierarchy-*.xml)" >&2
  echo "  <package>      optional app id, only used to label output" >&2
  echo "  <duration_sec> optional fixed capture window; omit for interactive (Enter to stop)" >&2
  echo "" >&2
  echo "  Requires env APK_ARCH_AUTHORIZED=1 (explicit authorization acknowledgement)." >&2
  exit 1
fi

WORK_DIR="$1"
PACKAGE="${2:-}"
DURATION="${3:-}"

# --- fail-closed authorization gate ---
if [[ "${APK_ARCH_AUTHORIZED:-}" != "1" ]]; then
  echo "REFUSED: set APK_ARCH_AUTHORIZED=1 only if you own or are contractually" >&2
  echo "authorized to analyze this app. Captures stay local; hand-grep before any" >&2
  echo "derived artifact leaves the machine (see header)." >&2
  exit 2
fi

if ! command -v adb >/dev/null 2>&1; then
  echo "ERROR: adb not found on PATH." >&2
  echo "Install: brew install --cask android-platform-tools" >&2
  exit 1
fi

# Exactly one device/emulator attached — avoid capturing the wrong target.
DEVICES=$(adb devices | awk 'NR>1 && $2=="device" {print $1}')
DEV_COUNT=$(printf '%s\n' "$DEVICES" | grep -c . || true)
if [[ "$DEV_COUNT" -ne 1 ]]; then
  echo "ERROR: expected exactly 1 attached device/emulator, found $DEV_COUNT." >&2
  echo "Attach one (emulator preferred for a public app) and retry:" >&2
  adb devices >&2
  exit 1
fi

mkdir -p "$WORK_DIR"
LOGCAT="$WORK_DIR/logcat.txt"

[[ -n "$PACKAGE" ]] && echo "[i] labeling capture for package: $PACKAGE" >&2

echo "[1/2] clearing logcat buffer and starting capture (-v threadtime)..." >&2
adb logcat -c || true
adb logcat -v threadtime > "$LOGCAT" &
LOGCAT_PID=$!

# Stop the background capture cleanly on any exit path.
cleanup() { kill "$LOGCAT_PID" 2>/dev/null || true; wait "$LOGCAT_PID" 2>/dev/null || true; }
trap cleanup EXIT INT TERM

if [[ -n "$DURATION" ]]; then
  echo "    capturing for ${DURATION}s — drive the app now (adb input / uiautomator / manual)." >&2
  sleep "$DURATION"
else
  echo "    drive the app now (boot, then walk each reachable screen)." >&2
  echo "    press Enter to stop capture..." >&2
  read -r _
fi

cleanup
trap - EXIT INT TERM

# --- current-screen view hierarchy (the native-vs-webview ground truth for a human) ---
echo "[2/2] dumping current-screen view hierarchy (uiautomator)..." >&2
TS_LABEL="last"  # no wall-clock in a committed script; operator can rename per screen
if adb shell uiautomator dump /sdcard/ui-dump.xml >/dev/null 2>&1; then
  adb pull /sdcard/ui-dump.xml "$WORK_DIR/uihierarchy-${TS_LABEL}.xml" >/dev/null 2>&1 \
    && echo "    saved $WORK_DIR/uihierarchy-${TS_LABEL}.xml (grep for '<node class=\"android.webkit.WebView\"' — 0 nodes supports a native call)" >&2 \
    || echo "    WARN: uiautomator dump produced no pullable file (some screens block dump)" >&2
else
  echo "    WARN: uiautomator dump failed on this screen (secure/anti-capture flag?) — a null here is a finding, not a gap" >&2
fi

LINES=$(wc -l < "$LOGCAT" | tr -d ' ')
echo "OK: captured $LINES logcat lines to $LOGCAT" >&2
echo "Next: python3 parse_logcat.py $LOGCAT --out $WORK_DIR/dynamic.json" >&2
echo "Then: cross-check dynamic.json against the static extract BY HAND (method.md — the" >&2
echo "cross-check is a human step; there is no auto-reconciliation script by design)." >&2
