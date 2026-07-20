# Cheap Static Harvest — recipe (Foundation, block #5)

> Recipe for `tools/apk-archaeology/scripts/extract_harvest.py`. Five independent, mechanically-cheap
> categories of facts that survive intact in the decompiled tree, harvested because
> they cost nothing beyond what decompile already did. Foundation-level: runs **once
> per APK**, never per-feature — the per-feature loop later synthesizes over a
> *slice* of this data, it does not re-extract it. Pure stdlib, deterministic (same
> input trees → same output). See `references/cognitive-sequence.md`, "Cheap static
> harvest (block #5)" for where this sits in the overall method.

## Input / how to run

```
python3 tools/apk-archaeology/scripts/extract_harvest.py <jadx_sources_dir> <apktool_dir> --out data/harvest.json
```

In the `<work_dir>` layout used by the rest of Foundation:

```
python3 tools/apk-archaeology/scripts/extract_harvest.py <work_dir>/decompile/jadx/sources <work_dir>/decompile/apktool --out <work_dir>/data/harvest.json
```

Both directory arguments are positional and required, in that order (jadx sources
tree first, apktool resource tree second). `--out` defaults to `data/harvest.json`;
pass `--out ""` to print to stdout instead of writing a file. Run it **once**,
after decompile, alongside the other Foundation extractors — not per feature.

## Output: `data/harvest.json`

Top-level shape is `{"summary": {...}, "build_config": [...], "network_security_config":
{...}, "di_modules": [...], "crash_keys": [...], "design_tokens": {...}}`. Every
entry that comes from a source file carries `file` + `line` — anchored fact (🟢),
never an unanchored guess. `summary` holds mechanical counts only (files scanned,
totals, secrets redacted) — no synthesis.

### 1. `build_config` — base URLs per env + a security action

One entry per `public static final` field found in any `BuildConfig.java` under the
jadx sources tree: `{file, line, field, type, value, secret_name_flag,
value_redacted}`.

**For the migration:** this is where the base URL per environment (dev/staging/
prod), compiled feature flags, and any hardcoded API key live. Feed the URLs
straight into the per-feature loop's OpenAPI/DTO work (base URLs per env, one per
Dio client config).

**The security action:** when `value_redacted` is `true`, that field held something
that looks like a real secret in the shipped binary — the action is not "note it",
it's **rotate it**. Two independent signals drive redaction, and both matter:
- the *value* looks like a secret (reused from `extract_endpoints.looks_like_secret`
  — one shared redaction rule, not a forked copy);
- the field *name* matches a secret-naming convention (`API_KEY`, `APP_KEY`,
  `SECRET`, `TOKEN`, `PASSWORD`, `CREDENTIAL`, `PRIVATE_KEY`, `ACCESS_KEY`,
  `CLIENT_SECRET`, ...), flagged in `secret_name_flag` independent of the value
  check.

  The name signal is not redundant with the value signal — verified against a real
  corpus, a hex-encoded app key in a field literally named `*_APPKEY` measured
  ~3.2 bits/char Shannon entropy, under the ≥4.0 threshold the value-only heuristic
  needs to fire. Without the name signal, that secret would have shipped in the
  clear in `harvest.json`. Check `summary.build_config_secret_names_flagged` versus
  `summary.build_config_secrets_redacted` — a nonzero gap between them is exactly
  the case the name signal exists to catch.

Non-string-literal fields (booleans, ints, array literals, enum/class refs) are
kept verbatim — nothing to leak there.

### 2. `network_security_config` — who the BFF must trust

Parsed from `res/xml/network_security_config.xml` (apktool tree):
`{found, file, base_cleartext_traffic_permitted, domain_configs: [{line,
cleartext_traffic_permitted, domains: [{domain, include_subdomains, line}],
pin_set: {expiration, pins: [{digest, value, line}]} | null}]}`. `found: false`
(with everything else empty) is an honest null — not every app ships this file.

**For the migration:** this is the trust boundary the target BFF/Dio client must
reproduce — which domains are trusted (and whether subdomains are included),
whether cleartext (plain HTTP) is allowed at the root or only for specific domains,
and any certificate pin-set. Getting this wrong in the Flutter target either breaks
connectivity to a legitimately pinned domain or silently widens the trust surface
the legacy app deliberately narrowed.

### 3. `di_modules` — the real architectural boundary, a 2nd viewpoint

One entry per `@Module`/`@Component` (Dagger/Hilt) declaration found anywhere in
the jadx sources tree: `{file, line, class, annotation, provides: [<method names>]}`.
A nested `@Module` inside its own `@Component` gets its own entry — the outer
`@Component`'s `provides` list does not swallow the nested module's bindings (this
is verified against a real Component-wraps-Module file in the script's selftest).

**For the migration:** DI module boundaries are drawn by the original team for a
reason — they are a second, independent viewpoint on where the app's real seams
are, next to the package-graph partitioning the per-feature loop already does. Use
`di_modules` to **validate** the Flutter target's module/package split: if a
proposed Flutter module cuts across what was one Dagger module in the legacy app,
that's worth a second look before committing to the split.

This is a boundary *signal*, not a full dependency graph — it does not resolve
`@Inject` constructor sites or trace the graph beyond `@Binds`/`@Provides` method
names.

### 4. `crash_keys` — what the team considers sensitive

One entry per `setCustomKey("literal_name", ...)` call site with a string-literal
first argument: `{file, line, key}`.

**For the migration:** the crash-reporting keys a team chooses to attach to every
crash report are a signal of which entities/fields they consider worth tracking at
failure time (user tier, account state, feature flags, ...) — useful context when
deciding what the Flutter target's own crash instrumentation should carry forward.

**Honest null, not a fabrication:** an app that only ever calls the batch form
(`setCustomKeys(map)`, plural) with a runtime-built map will yield an **empty**
`crash_keys` list — the key names are not string literals in the source, so they
are not statically visible, and the script does not attempt dataflow to recover
them. Report that as "no literal crash keys found — the app uses the batch form"
if it comes up, not as "no crash keys" (that would overclaim something this
heuristic can't see).

### 5. `design_tokens` — colors/dims → `ThemeData`

From `res/values/colors.xml` and `res/values/dimens.xml` (the **base** `values/`
directory only): `{colors: [{name, value, file, line}], dimens: [{name, value,
file, line}]}`.

**Token resolution — the one recoverable part of UI:** per the cognitive sequence,
native UI *layout* in the Flutter target is built fresh, not reverse-engineered —
the legacy screens are flow-reference only. Tokens are the exception: color and
dimension values map close to 1:1 onto a Flutter `ThemeData` (`ColorScheme` entries,
spacing constants), so they are worth recovering even though the layout around them
is not. "Fresh" applies to the layout, not to the tokens.

## Minimal example

A tiny, generic excerpt — one entry per category (values illustrative, not from any
real app):

```json
{
  "summary": {
    "build_config_files_scanned": 1,
    "build_config_fields_total": 1,
    "build_config_secrets_redacted": 1,
    "build_config_secret_names_flagged": 1,
    "network_security_config_found": true,
    "network_security_config_domain_configs_total": 1,
    "network_security_config_domains_total": 1,
    "network_security_config_pins_total": 0,
    "di_modules_total": 1,
    "di_bindings_total": 1,
    "crash_keys_total": 1,
    "design_tokens_colors_total": 1,
    "design_tokens_dimens_total": 1
  },
  "build_config": [
    {
      "file": "com/telecorp/app/BuildConfig.java",
      "line": 6,
      "field": "API_KEY",
      "type": "String",
      "value": "[REDACTED]",
      "secret_name_flag": true,
      "value_redacted": true
    }
  ],
  "network_security_config": {
    "found": true,
    "file": "res/xml/network_security_config.xml",
    "base_cleartext_traffic_permitted": false,
    "domain_configs": [
      {
        "line": 3,
        "cleartext_traffic_permitted": false,
        "domains": [
          {"domain": "api.telecorp.example", "include_subdomains": true, "line": 4}
        ],
        "pin_set": null
      }
    ]
  },
  "di_modules": [
    {
      "file": "com/telecorp/di/NetworkModule.java",
      "line": 9,
      "class": "NetworkModule",
      "annotation": "@Module",
      "provides": ["provideApiClient"]
    }
  ],
  "crash_keys": [
    {"file": "com/telecorp/crash/CrashReporter.java", "line": 12, "key": "user_tier"}
  ],
  "design_tokens": {
    "colors": [
      {"name": "brand_primary", "value": "#FF0000", "file": "res/values/colors.xml", "line": 3}
    ],
    "dimens": [
      {"name": "spacing_small", "value": "8.0dp", "file": "res/values/dimens.xml", "line": 3}
    ]
  }
}
```

## Consumers and value

- **Dev:** `build_config` base URLs feed the per-feature OpenAPI/DTO work directly
  (one env config per Dio client); `di_modules` validates the Flutter module split
  against the legacy one; `design_tokens` seeds `ThemeData` without redoing the
  legacy's visual design work from scratch.
- **Leader (security read):** `network_security_config` states who the BFF must
  trust and whether cleartext/pinning constraints travel to the target; a
  `build_config` entry with `value_redacted: true` is a rotation action item, not
  just a finding — a real secret shipped in a production binary is a live risk
  independent of the migration.

All five categories together cost one script run, once per APK — the value is
that none of this has to be re-derived by hand from a jadx tree, and every entry
is anchored at `file:line` so it can be checked against the source in seconds.

## Known limitations (by design, not chased)

Each is a documented, accepted scope boundary — consistent with the rest of this
script family (`classify_packages.py`, `extract_endpoints.py`): a named fragility,
not a bug to fix with more machinery.

- **`build_config`** assumes one `public static final` field per physical line
  (jadx's actual output shape, verified against ~30 real `BuildConfig.java`
  files). A field whose initializer legitimately spans multiple lines is silently
  skipped.
- **`network_security_config`** is line-anchored regex, not a full XML parser —
  it assumes apktool's default pretty-print (one tag per physical line). A
  hand-minified file with several elements packed on one line would under-anchor.
- **`di_modules`** is a best-effort boundary signal (declaration + binding-method
  names in a bounded lookahead window), not a full dependency graph — it does not
  resolve `@Inject` sites or trace bindings transitively.
- **`crash_keys`** only matches a string-literal first argument to
  `setCustomKey(...)`. A call site passing a variable, or the batch form
  `setCustomKeys(map)`, is invisible to this heuristic by design — see the honest
  null above.
- **`design_tokens`** only reads the base `res/values/colors.xml` and
  `res/values/dimens.xml` — not `values-night/`, `values-v31/`, locale variants,
  or `styles.xml`. Scanning every resource-qualifier variant is a documented
  non-goal of this pass, not an oversight.
