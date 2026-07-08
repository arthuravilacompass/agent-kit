# Command Playbook — Android Deeplink / App Link

Concrete commands. All require sandbox disabled (local network + adb + access to CoreSimulator/device).

## 1. Connect to the device wirelessly (adb wifi, Android 11+)

Wireless debugging has **two steps with different ports** (both change every session):

```bash
# Device: Developer options → Wireless debugging → enable
# "Pair with code" shows IP:PORT_A + a 6-digit code:
adb pair 192.168.1.11:41505 535891      # PORT_A (pairing) + code
# The main Wireless debugging screen shows ANOTHER IP:PORT_B (connect):
adb connect 192.168.1.11:34977          # PORT_B (connect) — DIFFERENT from the pairing one
adb devices                             # confirm
```
Mac and device on the same wifi network. With more than one device, target every command with `adb -s <IP:PORT_B> ...`.

## 2. Which command answers which question

| Question | Command |
|---|---|
| Android version / SDK | `adb -s $S shell getprop ro.build.version.release` / `.sdk` |
| App installed / version | `adb -s $S shell dumpsys package <pkg> \| grep -E "versionName\|versionCode"` |
| Domain **verified**? (gate 2) | `adb -s $S shell pm get-app-links <pkg>` → `verified` / `1024` |
| Full internal state (verification + selection) | `adb -s $S shell "dumpsys package <pkg> \| grep -A20 'Domain verification state'"` |
| Filters the OS **registered** | `adb -s $S shell "dumpsys package <pkg> \| grep -iE 'Scheme\|Authority'"` |
| **Does the intent-filter match?** (gate 3, DECISIVE) | `adb -s $S shell am start -a android.intent.action.VIEW -c android.intent.category.BROWSABLE -d "<url>" <pkg>` |
| Who the system picks (shell bias!) | `adb -s $S shell cmd package resolve-activity --brief -a android.intent.action.VIEW -c android.intent.category.BROWSABLE -d "<url>"` |
| The real decision on tap | `logcat` — see section 4 |

**Reading `am start`:** `START_INTENT_NOT_RESOLVED` / `unable to resolve` = the filter doesn't match. Opens `MainActivity` = matches. Always run a **control host** (without the suspected element) to isolate the variable.

## 3. Inspect the APK (static, no device)

```bash
BT="$HOME/Library/Android/sdk/build-tools/35.0.0"
"$BT/apksigner" verify --print-certs app.apk | grep -i "SHA-256"   # signing cert (compare with assetlinks)
"$BT/aapt" dump badging app.apk | grep "^package:"                 # package + versionCode
"$BT/aapt" dump xmltree app.apk AndroidManifest.xml | grep -iE "intent-filter|autoVerify|host|uri-relative|pathPrefix"
```

## 4. Capture the real tap decision (logcat)

```bash
adb -s $S logcat -c                                   # clear buffer
# tap the link on the device, THEN:
adb -s $S logcat -d -v time ActivityTaskManager:I '*:S' | grep -iE "START u0.*(VIEW|<your-domain>)"
```
Key signals:
- `cmp=<pkg>/...MainActivity` → App Link routed to the app ✅
- `cmp=com.android.chrome/...IntentDispatcher` → went to the browser
- `CustomTabsIntent#shouldAlwaysUseBrowserUI() = false` → the originating app opened in a **Custom Tab** (bypasses App Links — invalid as a matching test)
- `cmp=com.google.android.keep/...LinkResolverActivity` → Keep intercepted it with its own resolver (same issue)

## 5. Validate assetlinks / AASA per host (web side)

```bash
for h in www.example.com example.com link.example.com; do
  curl -sS -m 15 -o /dev/null -w "%{http_code} %{content_type} server=%header{server}\n" \
    "https://$h/.well-known/assetlinks.json"
done
```
- Compare the published `sha256_cert_fingerprints` with the APK's cert (section 3). They must match.
- Distinct hosts may have distinct backends (CDN, dedicated web server, unserviced apex). AASA/assetlinks served by one host does NOT automatically cover another. Check every host your app declares.

## 6. Force re-verification / manipulate selection (experiments)

```bash
adb -s $S shell pm verify-app-links --re-verify <pkg>
adb -s $S shell pm set-app-links-user-selection --user 0 --package <pkg> true <host>
```
⚠️ This changes the device's state — revert / warn if it's someone else's device.

## Recommended Diagnostic Order

1. `pm get-app-links` → is the domain verified? (if not, it's gate 2: assetlinks/cert/host)
2. `am start ... <pkg>` on the problem link + **control host** → isolates gate 3 (matching)
3. If matching fails → `aapt dump xmltree` + `git show` on the manifest → find the element (e.g. `uri-relative-filter-group`)
4. Cross-check by Android version (12 ok / 15 breaks = new matching feature)
5. Only then a real tap (from an app that delegates, not a Custom Tab) for end-to-end confirmation
