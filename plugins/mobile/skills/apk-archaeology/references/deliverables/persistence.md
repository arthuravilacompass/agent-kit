# Persistence & Crypto Matrix — Data Dictionary Recipe (loop step 3)

**What this is.** The recipe for the per-feature loop's step 3, "Persistence & crypto
matrix" (`../cognitive-sequence.md`; `../../SKILL.md` loop step 3): turning a feature's
persistence slice into a data dictionary. Marked `spec pendente` in both of those files
until this recipe existed — this is that spec.

Unlike step 2 (OpenAPI), this deliverable has no per-route branch: `extract_persistence.py`
runs once, unconditionally, in Foundation — every feature draws a slice of the same
app-wide extraction, never a re-run.

## Input — Foundation runs the extractor once, per APK

```
python3 tools/apk-archaeology/scripts/extract_persistence.py <sources_dir> <classify.json> --out data/persistence.json
```

- `<sources_dir>` — decompiled Java sources (jadx output). Required.
- `<classify.json>` — optional positional argument. When given, scoping mirrors
  `extract_endpoints.py`: only `business-candidate` and `unclassifiable` packages are
  scanned, `known-third-party` is excluded. Without it, the whole `sources_dir` is
  scanned unscoped.
- `--out` — defaults to `data/persistence.json` if omitted.

This runs once in Foundation (step 5), same "extraction ran once" discipline as
`endpoints.json`. Loop step 3, per feature, then draws its **slice**: every finding whose
`file` falls under the partition's package prefix — the same join `openapi.md`'s Input
section uses for the endpoint slice. Never re-invoke the extractor per feature.

## Output — two layers

- **`data/persistence.json`** (Foundation, app-wide, raw facts). Shape:
  `{summary: {...}, findings: [...]}`.
  - `summary` (exact keys emitted by the script): `room_entities`, `room_daos`,
    `room_dao_methods`, `room_databases`, `shared_prefs_files`, `shared_prefs_keys`,
    `keystore_usages`, `encrypted_prefs_usages`, `sqlite_helpers`, `sqlite_table_ddls`,
    `total_findings`, `secrets_redacted`.
  - `findings[]`: `{type, class, file, line, detail}`. `type` is one of `room_entity`,
    `room_dao`, `room_dao_method`, `room_database`, `shared_prefs_file`,
    `shared_prefs_key`, `keystore_usage`, `encrypted_prefs_usage`, `sqlite_helper`,
    `sqlite_table_ddl`. Every string value inside `detail` (pref names, keys, table
    names, DDL, snippets) is already redaction-checked by the script — a literal that
    looked like a secret is replaced with `[REDACTED]`, counted in `secrets_redacted`,
    never emitted.
- **`features/<slice>/data-dictionary.json`** (loop step 3 proper, synthesis). The
  feature's slice of `persistence.json`, re-shaped into one row per store/table/key,
  with three columns added that do **not** exist in the raw extractor output —
  Flutter-target mapping, expiration, LGPD flag. Producing these three is the synthesis
  this recipe defines; the extractor only gives raw facts.

## Method — category → Flutter target mapping

| Script finding type(s) | What it captures | Flutter/Dart target | Notes |
|---|---|---|---|
| `room_entity`, `room_dao`, `room_dao_method`, `room_database` | Room ORM: entity table name + fields, DAO methods with the literal SQL behind `@Query`, DB version + entity list | `drift` (preferred — typed queries, migrations) or `sqflite` (thinner, if the team wants to keep raw SQL close to the legacy shape) | Entity fields map to drift table columns close to 1:1; a DAO's `@Query` SQL is often reusable close to verbatim. |
| `sqlite_helper`, `sqlite_table_ddl` | Hand-rolled `SQLiteOpenHelper` subclasses + `CREATE TABLE` DDL string literals | `sqflite` (or `drift`, if the team wants to modernize while porting) | The DDL is frequently copy-portable into `execute()`; the helper class name anchors which DB the DDL belongs to when a file has several. |
| `shared_prefs_file`, `shared_prefs_key` | Named `SharedPreferences` files + individual keys, each with an accessor telling you the value type (`getString`/`getInt`/`getBoolean`/`getLong`/`getFloat`/`getStringSet`, or `put*`/`contains`/`remove`) | `shared_preferences` | Android's per-file namespacing has no direct analog — `shared_preferences` is one flat store. Treat each `shared_prefs_file` as a **naming-prefix convention** in the dictionary (e.g. `telecorp_session_prefs.customer_id`), not a second Flutter store. |
| `keystore_usage`, `encrypted_prefs_usage` | Call-site of `KeyStore.getInstance(...)` / `EncryptedSharedPreferences.create(...)` | `flutter_secure_storage` | These are **usage sites, not key inventories** — see Honesty, below. The row in the dictionary often starts as "secure storage confirmed present here" with the actual protected key(s) still to be pinned down by reading around the call site. |

**Two columns the script never emits — added in synthesis, per store/row:**

1. **Expiration.** Read the source around the `file:line` anchor for a TTL constant, a
   cache-expiry check, a `System.currentTimeMillis()` comparison near the read/write. If
   one is visible, record it 🟢 (literal, anchored). If nothing like that is near the
   finding, record `not observed` ⬜ — never infer a TTL from convention or guesswork.
2. **LGPD flag.** `yes` / `no` / `unclear`, based on whether the key/table/field name (or
   its immediate neighbors in the same class) looks like personal data — document number,
   name, email, phone, address, biometric template, precise location, and the like. This
   is a **human judgment call over the finding, not an extracted fact** — mark its
   provenance as such (not 🟢 literal) so a reader doesn't mistake a flag for something
   the script asserted.

## Honesty caveat — a `room_* : 0` result is a fact, not a gap

The corpus this extractor was validated against (`telecorp`, the real target run to date)
has **zero Room usage at the source level** — its persistence surface is entirely
`SharedPreferences` + `KeyStore` + hand-rolled SQLite. This is a real, load-bearing
property of the extractor's validation history, not a limitation to route around:

- If a real run reports `room_entities: 0`, `room_daos: 0`, `room_dao_methods: 0`,
  `room_databases: 0`, **trust it** — that is the extractor describing this app
  truthfully. Do not go hunting for "hidden" Room usage the tool must have missed, and do
  not treat an all-zero Room summary as evidence the tool is broken.
- The flip side: the Room **positive**-extraction path (an app that actually uses
  `@Entity`/`@Dao`/`@Database`) has not yet been exercised against a real decompiled app —
  only against the script's own selftest fixture, a synthetic one. The first real
  `room_entities > 0` result deserves a quick spot-check of a couple of `file:line`
  anchors before it's trusted at the same level as a SharedPreferences/KeyStore finding,
  precisely because it hasn't been through that corpus trial yet.
- **The extractor does not false-positive on Retrofit's `@Query`** — a distinct library
  that happens to share the literal annotation name with Room's DAO method annotation.
  The discrimination is structural, not name-based: `room_dao_method` findings are only
  emitted for a `@Query`/`@Insert`/`@Update`/`@Delete` annotation whose position falls
  **inside the body span of a class already found `@Dao`-annotated** (`dao_spans` in the
  script). Retrofit's `@Query("page")` sits on a method parameter inside a Retrofit `@GET`
  interface, never inside a `@Dao`-annotated class body, so it is never counted here even
  though the token `Query` matches. This is worth stating to the reader explicitly — an
  annotation-name-only regex could plausibly conflate the two, and this script's scoping
  is what avoids it.

## Minimal worked example

Input — a 3-finding slice of `data/persistence.json` (generic `telecorp` domain,
redacted-clean, one SharedPreferences file + one key + one KeyStore usage; no Room, no
SQLite in this slice):

```json
{
  "summary": {
    "room_entities": 0,
    "room_daos": 0,
    "room_dao_methods": 0,
    "room_databases": 0,
    "shared_prefs_files": 1,
    "shared_prefs_keys": 1,
    "keystore_usages": 1,
    "encrypted_prefs_usages": 0,
    "sqlite_helpers": 0,
    "sqlite_table_ddls": 0,
    "total_findings": 3,
    "secrets_redacted": 0
  },
  "findings": [
    {
      "type": "shared_prefs_file",
      "class": "SessionManager",
      "file": "com/telecorp/session/SessionManager.java",
      "line": 22,
      "detail": {"name": "telecorp_session_prefs", "mode": "MODE_PRIVATE"}
    },
    {
      "type": "shared_prefs_key",
      "class": "SessionManager",
      "file": "com/telecorp/session/SessionManager.java",
      "line": 47,
      "detail": {"accessor": "getString", "key": "customer_document_number"}
    },
    {
      "type": "keystore_usage",
      "class": "CryptoHelper",
      "file": "com/telecorp/security/CryptoHelper.java",
      "line": 31,
      "detail": {
        "api": "KeyStore.getInstance",
        "snippet": "KeyStore ks = KeyStore.getInstance(\"AndroidKeyStore\");"
      }
    }
  ]
}
```

Resulting `features/session/data-dictionary.json` rows (rendered as a table for
readability):

| Store | Key / item | Native type | Flutter target | Expiration | LGPD | Origin |
|---|---|---|---|---|---|---|
| `telecorp_session_prefs` (SharedPreferences file) | `customer_document_number` | String | `shared_preferences` | not observed ⬜ | yes — document number is personal data | 🟢 `SessionManager.java:47` |
| `AndroidKeyStore` (KeyStore) | usage site only — no key alias captured by the extractor | n/a | `flutter_secure_storage` | not observed ⬜ | unclear — depends what the key protects, not visible at this call site | 🟢 `CryptoHelper.java:31` |

Note the second row's honesty: the script gave a confirmed **usage site**, not a key
inventory — the dictionary carries that gap forward instead of inventing a key name.

## Consumer — dev (storage + schema) and leader (security + LGPD)

- **Dev**: reads the Flutter-target column to pick the package per store
  (`drift`/`sqflite`/`shared_preferences`/`flutter_secure_storage`) and writes the actual
  schema/migration from the entity fields or DDL already recovered — the dictionary is
  the input to that write-up, not a substitute for it. Value: the dev stops re-deriving
  "what does this app persist and how" from a fresh source read; the matrix already did
  that pass once, app-wide.
- **Leader**: reads the secure-storage rows (KeyStore/EncryptedSharedPreferences) and the
  LGPD column for the security/compliance read — which stores need
  `flutter_secure_storage` non-negotiably, which fields are personal data and need a
  retention/consent story before the port ships. Value: this read happens once, over the
  dictionary, instead of the leader re-deriving it screen-by-screen during review.
