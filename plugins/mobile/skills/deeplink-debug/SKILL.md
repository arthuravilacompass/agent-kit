---
name: deeplink-debug
description: Invoke when a deeplink/App Link opens in the browser instead of the app, fails to route, opens the wrong screen, or you need to validate deeplink behavior on a device. Symptoms — "opens in the browser", "doesn't open the app", the link is verified but still opens in the browser, works on one Android/iOS version but not another.
---

# Deeplink / App Link Debugging (Android)

## Project Config

Swap the hosts/domains in the examples below for your app's. The mechanism (the three gates, the `adb`/`am`/`logcat` commands, assetlinks/AASA validation) is generic Android/iOS and doesn't change between projects.

## Overview

An App Link opening in the browser has **three independent gates**, and the fastest way to lose hours is letting a true-but-tangential signal (`verified`) close the case too early.

**Central principle: `verified` ≠ `matches`.** Domain verification (assetlinks) and intent-filter matching are *separate* Android steps. A domain can be `verified` while the intent-filter matches no path — the app is approved for the domain but doesn't declare a rule that captures the URL.

## The Three Gates (check in this order)

1. **OS routing (originating app):** the app that receives the tap decides how to open the link. **Custom Tab bypasses App Links entirely** — WhatsApp, Google Keep, Google Messages open links in an embedded Chrome tab and never consult the resolver. A "browser" result coming from these apps proves nothing.
2. **Verification (assetlinks):** does the domain belong to the app? → `pm get-app-links` (`verified` / `1024`). Answers *only* gate 2.
3. **Matching (intent-filter):** does the URL match a rule the app declared? → the decisive test below.

## Diagnostic Method

Test the gates directly instead of tapping in apps (which are biased). The decisive test is **matching**, forcing the package:

```
adb shell am start -a android.intent.action.VIEW -c android.intent.category.BROWSABLE -d "<url>" <pkg>
```
- `START_INTENT_NOT_RESOLVED` → the filter matches nothing (matching bug).
- opens the app → matching OK.

**Always run a control:** the same command on a host whose intent-filter differs by the single element you suspect (e.g. a host without the new `<uri-relative-filter-group>`). Failing case + passing control with one different variable = proven cause.

Cross-check with **version distribution**: "works on Android 12/iOS, breaks on 15+" points to a matching feature that only exists on newer Android (e.g. `uri-relative-filter-group`, API 35+).

## Instrument Bias (don't treat as evidence)

| Instrument | Why it lies |
|---|---|
| Tap from WhatsApp / Keep / Messages | Custom Tab — bypasses App Links by design |
| `am start` without pkg / `cmd package resolve-activity` | shell context — always resolves to the browser, ignores App Link verification |
| `pm get-app-links: verified` | answers verification, NOT matching |

## Full Command Playbook

See [references/PLAYBOOK.md](references/PLAYBOOK.md) — adb wifi pairing, full "which command answers which question" table, logcat capture (`ActivityTaskManager` START + `CustomTabsIntent`), APK inspection (`apksigner`/`aapt`), and per-host assetlinks validation.

## Common Mistakes

- Concluding "it's not the app, it's the test method" from `verified` + browser. That's the real trap — verify matching with `am start pkg=` before blaming the channel.
- Stacking failed taps (all Custom Tab) as if they were bug evidence. Repeated bias ≠ confirmation.
- Comparing the current manifest against the *last commit that worked* instead of the *version that actually worked* — the real diff is sometimes against an older baseline than the comparison assumes.
