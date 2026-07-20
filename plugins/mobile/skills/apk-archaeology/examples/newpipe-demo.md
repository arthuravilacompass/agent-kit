# apk-archaeology — Demo v0 (NewPipe)

> **⚠ Prior doctrine (v0 record).** This demo measures extraction fidelity under the old
> 3-dimension (A/B/C) framing; it predates the deliverable-first restructure (Foundation +
> per-feature loop, concrete deliverables at the center). Kept as the empirical fidelity
> record of that run, not as current method — see `references/cognitive-sequence.md`.

> Provisional skill. See `docs/superpowers/specs/2026-07-08-apk-archaeology-design.md`
> for design decisions and limits. This document is the public example (spec §8) —
> OSS app, GPLv3, real source alongside the output.

## Provenance

- **Input**: NewPipe v0.28.8 (`org.schabi.newpipe`) — public APK, [github.com/TeamNewPipe/NewPipe](https://github.com/TeamNewPipe/NewPipe)
  `sha256: d9fb2540b3a2a0b059c73a296f0cda1c06738426d013c626dbf088aea66629b3`
- **Tools**: jadx 1.5.5 · apktool 3.0.2
- **Comparison source (non-circular, spec §9)**: two real clones, not the pipeline's own output —
  `TeamNewPipe/NewPipe` @ v0.28.8 (app) + `TeamNewPipe/NewPipeExtractor` @ v0.26.3 (the actual business
  logic lives in a separate repository, referenced via a Gradle dependency — found during the
  grading process itself, see §Lessons below)
- **Date**: 2026-07-08 · macOS (arm64)

## B — API Contracts (fact)

- **213 endpoints extracted** (business-candidate ∪ unclassifiable, known-third-party excluded; the same
  URL can appear at several file:line locations, e.g. a base-URL constant referenced across several
  classes — **125 unique URLs** after dedup, which is the basis of the scorecard below) ·
  **324 high-entropy literals redacted** (none appear in the output; the vast majority are isolated
  hashes/IDs with no URL context, not a secret embedded in an endpoint — only 2 of the 213 endpoints have
  an embedded `[REDACTED]`)

### Fidelity Scorecard (non-circular grading, spec §9)

| Correction step | real_count | true_positive | false_positive | false_negative | recall | Reproducible with `grade_fidelity.py` as-is? |
|---|---|---|---|---|---|---|
| Naive (app-only, with `test/`) | 96 | 30 | 95 | 66 | 0.31 | Yes |
| + `app/src/main` only (excludes test) | 51 | 29 | 96 | 22 | 0.57 | Yes (pointing the script at the right dir) |
| + includes `NewPipeExtractor` (correct version, production only) | 138 | 82 | 43 | 56 | **0.59** | **Yes — this is the number the shipped tool actually produces** |
| + excludes Javadoc comment from the answer key (contamination in the grader ITSELF) | 99 | 82 | 43 | 17 | 0.83 | **NO — manual step, not encoded in the script** |

**Number reproducible by the shipped tool: 0.59.** `grade_fidelity.py` doesn't distinguish a string
literal from a Javadoc comment (`URL_RE` matches `"https://..."` inside `<a href="...">` just like
any code literal) — this is a limitation of the comparison METHOD, documented but **not
fixed in the script in this run** (a v2 candidate if the pattern recurs in real use). The 0.83 is a
manual correction of that number, made in this session: I classified the 56 false negatives line by
line (regex `^\s*(\*|//)` at the start of the line where the URL appears) and found that **39 of the 56
only exist inside a comment/Javadoc, never compiled** — leaving 17 genuine false negatives.
This is auditable (the method is described here, the full list of the 39 excluded URLs is in
`~/dev/apk-archaeology-lab/demo-run/newpipe/` as a session artifact, outside the repo), but it is **not
what someone gets running the pipeline as it stands today** — reporting both numbers,
not just the prettier one, is the point.

**43 false positives, categorized** (none confirmed as a pure hallucination):
- ~6 are from `org.jsoup` (a real third-party lib, not registered in `known-libs.json` → falls into
  `business-candidate` for not being recognized — a fragility already documented in spec §6, now with
  a concrete instance and a real library name).
- Most of the rest (SoundCloud/Bandcamp/YouTube "API paths") are **real** endpoints, built in
  source code via string concatenation (`BASE_URL + path + "?param="`), which the compiler/R8
  fuses into a single constant in the bytecode — jadx decompiles it back as 1 literal, but the answer key
  (which reads the source `.java`, where they're still separate fragments) never sees this fused
  form as a single string. Not exhaustively verified item by item; the pattern is consistent with the checked cases.

## C — Module Graph (reconstruction)

- **2067 nodes, 1450 edges, 232 synthetic classes filtered** (`artifact_warnings`) — high filtering
  volume, expected for a real app with Compose/generated lambdas from R8.
- Cluster used as the unit of work for Dimension A: connected component (922 total components,
  largest with 678 nodes — dominated by library classes crossing the few `business-candidate` ones
  that bridge them; the 2 clusters used in the synthesis below were chosen for being small and named).

## A — Flows and Business Rules (tiered inference)

Two partitions synthesized — "Streaming Services" (4 classes: `StreamingService`, `YoutubeService`,
`BandcampService`, `PeertubeService`) and "Settings Fragments" (14 `*SettingsFragment` classes).
43 total claims, most `high`, 3 correctly marked `unanchored` (anchor rule, spec §5[5]
— none dressed up as a normal inference).

### Calibration (verified against the real source, sample of 4 `high` claims)

| Claim | Verdict | Evidence |
|---|---|---|
| YouTube declares only 1 active UI language (`en-GB`), 109 hardcoded countries | ✅ **true, exact** | The other ~74 languages are **commented out in the source** (`/* ... */`) — never compiled. Country count matches 109/109. The agent inferred this correctly from the bytecode alone, without seeing the comment. |
| SoundCloud limits to 9 countries (`AU,CA,DE,FR,GB,IE,NL,NZ,US`) | ✅ **true, exact** | List matches character-for-character with `SoundcloudService.java`. |
| A YouTube playlist with id `RD*` routes to the Mix extractor | ✅ **true, imprecise citation** | Behavior confirmed (`playlistId.startsWith("RD")`), but in the source it lives in `YoutubeParsingHelper.java`, not `YoutubeService.java` as the agent cited — decompilation merges/organizes differently than the source (a finding, not a speculative conclusion). |
| YouTube subscription import only accepts `INPUT_STREAM` | ✅ **true** | Concept confirmed in `SubscriptionExtractor.java`/`YoutubeSubscriptionExtractor.java`. |

**4/4 sampled verified, 4 true** (2 exact, 1 with a file-citation imprecision, 1 confirmed without
checking the exact line) — small sample, not an exhaustive audit of the 43 claims.
Reported as-is: no false claim found in the sample, but the sample is small and doesn't prove a zero
error rate for the whole set.

## What This Is NOT

- Doesn't measure productivity — no baseline, no real migration done.
- **Recovered legacy behavior ≠ approved desired behavior.** Every claim in A is an observation
  of what the app DOES today, not a decision about what it SHOULD do — the PO gate remains (see
  §11.1 of the design doc: legacy behavior may be a legacy bug, not a rule to preserve).
- Fidelity measured against a clean reference (NewPipe, unobfuscated) — not against obfuscated
  code (see the Telecorp appendix below, aggregate statistics only).
- Dimension A demonstrated against a reference poor in **business** rules (NewPipe is a media
  player — the rules found are routing/localization/UI, not pricing/entitlement/checkout/anti-fraud).
  Recovery of real business rules remains projected, not measured. → The **acceleration step**
  (candidate US + Gherkin AC + DTO skeleton feeding Spec/Impl/Tests) is demonstrated on a richer,
  WebView-hybrid app in the companion `wordpress-handoff.md` — real self-service purchase rules,
  though still un-obfuscated and unmeasured, and bounded at the WebView seam.
- Inference in A can be wrong even at a high tier — the tier is calibrated (4/4 sample here), not
  guaranteed for the whole set.
- A low-frequency business rule may have been missed — the candidate spec is input for human
  reconciliation, not a substitute for it.
- **The B scorecard's final value (0.83) is already a correction over 3 methodological errors in
  the grading process itself** (incomplete repo scope, wrong dependency version, answer key
  contaminated by comments) — see Lessons below. This isn't "the tool got it wrong 3 times", it's
  the evaluation process that needed 3 corrections before the number was honest.

## Appendix — Telecorp Smoke Test (real commercial app, pseudonym — spec §8)

- **96.9% of top-level packages fell into `unclassifiable`** (558 of 576) — real, heavy
  obfuscation, empirically confirming the name-fingerprint fragility documented in spec §6.
- **847 potential secrets redacted** — no literal value in this document or anywhere
  outside `~/dev/apk-archaeology-lab/` (spec §8). Post-hoc technical verification found no
  residual literal inside the persisted output's `url` field (check restricted to the sensitive
  field, not the whole JSON — a first, broader grep hit a false positive in the `file` field, which
  is a class path, not a secret).
- 15 endpoints tagged `business`, 38 `unclassifiable` — most of the real business content falls
  outside the "trusted" bucket, as expected under heavy obfuscation (spec §6).
- **Extracted content** (real endpoints, real domains) — NOT included. Internal, spec §8.

## Lessons From the Grading Process Itself (a finding of this demo, not of the design)

The biggest lesson from this run wasn't about the pipeline — it was about how to
grade fidelity correctly:

1. **Wrong repo initially.** NewPipe's business logic lives in a SEPARATE repository
   (`NewPipeExtractor`), referenced via `implementation(libs.newpipe.extractor)` in Gradle — not
   in the app's clone. 19 of the 21 claims in the "Streaming Services" partition cite files that only
   exist in that second repo.
2. **Wrong version of the second repo.** Cloning it without pinning a tag grabs the current default
   branch, not the version actually packaged in the tested APK (`v0.26.3`, found in `libs.versions.toml`) —
   the wrong pipeline gave 656 answer-key URLs; the correct one, 138 (production) / 656 with tests included.
3. **Answer key contaminated by comments.** `grade_fidelity.py`'s regex (`"(https?://...)"`) doesn't
   distinguish a string literal from a Javadoc comment (`<a href="https://...">`) — both have quotes. 39 of the
   56 "real" false negatives were, in fact, documentation links never compiled. This is a
   limitation of the grading METHOD (naive textual comparison), symmetric to the `test/`
   contamination already described above — recorded here, not fixed in `grade_fidelity.py` in this
   run (an ad-hoc fix to the clone's scope was enough for this demo; fixing the grader's regex is a
   v2 candidate if the pattern recurs in real use).
