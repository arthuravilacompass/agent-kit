---
name: apk-archaeology
description: "STATUS: provisional (refined once, not graduated) — invoke to extract value from a legacy (decompiled) Android APK toward a migration to Flutter: a Foundation pass (contracts, module graph + the seam, cheap static harvest) then a per-feature loop producing concrete migration deliverables (OpenAPI, data dictionary, state machines, TDD stubs), each stamped with origin/confidence/intent/reach. Refined after a second real client run that measured the hard walls (obfuscation, dynamic) without crossing them; n=1, not yet graduated."
disable-model-invocation: true
---

# apk-archaeology — Legacy APK Value Extraction (provisional)

> **STATUS: provisional/experimental — refined once.** The consolidation template and
> handoff contract were refined after real client use — a second run that **measured the
> hard walls (obfuscation, dynamic reach) without crossing them**. Not graduated (n=1
> real; the ≥2× bar is not met). See design docs:
> `docs/superpowers/specs/2026-07-08-apk-archaeology-design.md` (graduation bar) and
> `docs/superpowers/specs/2026-07-17-apk-archaeology-output-architecture-design.md` (output architecture).

> **The cognitive sequence (start here).** The decision sequence *above* this pipeline —
> *given a decompiled APK, what do you actually do with it?* — lives in
> `references/cognitive-sequence.md`. The Steps below run in the same two tempos as that
> reference — **Foundation** (once per APK), then the **per-feature loop** (once per
> feature) — followed by the output backbone and the optional dynamic pass; that
> reference is the decision method they serve.

> **From extraction to backlog.** The report method — the CT→RF→US→RN→CA chain,
> the reach map, the confidence tiers, and the log-based v2 (dynamic) instrument
> (`scripts/capture_dynamic.sh` + `scripts/parse_logcat.py`, the Dynamic pass below) —
> lives in `references/method.md`. The client-facing report template (pt-BR) is
> `references/modelo-relatorio.pt-BR.md` (the filled file **is** the deliverable,
> shipped as Markdown — inline Mermaid diagram, no `.docx` conversion); how to fill
> it (filling order, worked example, conventions — filler/maintainer-facing, never
> shipped with the report) is `references/guia-preenchimento.pt-BR.md`; a worked
> example (WordPress) is
> `examples/relatorio-wordpress.pt-BR.md`.

Runs in two tempos: **Foundation** (once per APK — contracts, module graph, the seam)
then a **per-feature loop** that synthesizes over each feature's slice of that data.
The output is concrete migration deliverables a dev writes Dart against — OpenAPI
contracts, a data dictionary, state machines, TDD stubs — not a finding dump. The
three confidence bands (fact / reconstruction / inference) are how the consolidation
keeps evidence separate, not the skill's output shape. Adapts the `core:archaeology`
pattern (parallel dispatch, now per feature-slice → structured consolidation) for a
compiled/possibly obfuscated source instead of live source code.

## When to Use

You have a `.apk` of a legacy app that will (or might) be migrated to Flutter, and you
want the concrete deliverables that accelerate that migration — API contracts, module
topology, business rules and state machines, anti-regression test stubs — each stamped
with origin/confidence/intent/reach for honesty, before planning the migration. This is
not security/malware analysis — it's migration preparation.

The same recovery serves adjacent cases when up-to-date documentation is gone:
resuming maintenance with a team that didn't build the app; auditing behavior before
an authorized integration; or reconstructing a lost backlog. All of them produce the
same deliverable — a traceable, evidence-anchored draft backlog, never approved specs.

## Input

Path to a `.apk` file.

## Run layout

Every step below targets one `<work_dir>` tree, laid out like this:

```
<work_dir>/
├── OVERVIEW.md            (rendered: deterministic slice by render_overview.py + agent BLUF)
├── findings.json          (emit_findings.py skeleton + agent synthesis; contract: references/findings.schema.json)
├── backlog.md             (the value — agent-authored)
├── analysis/              (feasibility.md, flows.md, architecture.md, bridge-pilot.md, architecture.c4.mmd, decisions.md)
├── data/                  (Foundation output: classify.json, classify.v1.json, endpoints.json, graph.json,
│                            partitions.json, persistence.json, harvest.json)
├── features/<slice>/      (per-feature loop output, spec'd, not yet exercised on a real run:
│                            openapi.yaml, data-dictionary.json, state-machines.mmd, <rule>_test.dart)
├── report/                (on-demand — generated only when a client-facing report is requested; NEW, never a relocation)
└── decompile/             (jadx/, apktool/ — gitignored + regenerable cache, see Foundation step 1)
```

`data/` holds every raw JSON artifact **Foundation** produces (classify, endpoints,
graph, persistence, harvest); `features/<slice>/` holds what the **per-feature loop**
synthesizes over each feature's slice of that data; `analysis/` and `backlog.md` are
where the **output backbone**'s synthesis (consolidate + emit_findings/render) lands;
`decompile/` is disposable — re-running Foundation step 1 regenerates it from the same
APK.

## Steps

### Foundation (runs once per APK)

The app-level substrate every feature draws on. Runs once; the per-feature loop below
synthesizes over slices of this data, never re-extracting.

#### 1. Decompile

```
scripts/decompile.sh <apk_path> <work_dir>
```

Produces `<work_dir>/decompile/jadx/sources/` (readable Java) and
`<work_dir>/decompile/apktool/` (manifest/resources) — see Run layout above.
`decompile/` is a gitignored, regenerable cache: the script writes a
`.gitignore` (`*`) into it on every run, so it never needs a manual exclusion
elsewhere. The script also creates `<work_dir>/data/` up front so Foundation
steps 2-6 below always have somewhere to write.

#### 2. Classify packages → the reach-gate verdict

```
python3 scripts/classify_packages.py <work_dir>/decompile/jadx/sources scripts/known-libs.json --out <work_dir>/data/classify.json
```

3 buckets: `known-third-party` / `business-candidate` / `unclassifiable`. See design
doc §6 for why `unclassifiable` exists and is not optional. The `unclassifiable` ratio
is also the input to the **reach gate**: a verdict over this step's output —
**normal / degraded / no-go** — that fires as soon as classify lands, before the
synthesis investment downstream (`references/method.md`, "The reach gate"; the reach
gate is a verdict over classify's output, not a literal step ahead of extraction). The
ballast case came back 96.9% `unclassifiable` with no graph/backlog — the `no-go`
regime the gate exists to catch. A high ratio bounds or stops the run before the
per-feature loop ever opens; it is not just a bucket.

#### 3. Extract endpoints (Dimension B — fact)

```
python3 scripts/extract_endpoints.py <work_dir>/decompile/jadx/sources <work_dir>/data/classify.json --out <work_dir>/data/endpoints.json
```

Runs over `business-candidate ∪ unclassifiable`. Secret redaction is automatic —
check `secrets_redacted` in the output; if > 0, do **not** expose the raw
`endpoints.json` outside the local environment before confirming no literal leaked
(manual grep as a second check is acceptable in this provisional phase).

#### 4. Extract module graph (Dimension C — reconstruction) → the seam

```
python3 scripts/extract_graph.py <work_dir>/decompile/jadx/sources <work_dir>/data/classify.json --out <work_dir>/data/graph.json
```

Only over `business-candidate`. Note `artifact_warnings` in the output — filtered
synthetic classes are expected, not a bug.

Out of this graph comes **the seam**: not "N screens" but the critical migration
unit — the thing that, if not reproduced, kills everything downstream (e.g. a
multi-capability JS bridge whose absence breaks every WebView tab it feeds). Naming
the seam is app-level judgment over the graph, not a script output; it is what the
leader sequences epics by risk around (`references/cognitive-sequence.md`, "Map the
perimeter, find the module graph and the seam").

#### 5. Extract persistence (built — selftest-passing; corpus-validated on extraction)

```
python3 scripts/extract_persistence.py <work_dir>/decompile/jadx/sources <work_dir>/data/classify.json --out <work_dir>/data/persistence.json
```

**Built** (selftest-passing; corpus-validated on extraction — SharedPreferences/KeyStore/SQLite;
Room positive path selftest-only; not yet wired into emit_findings/render). Recovers Room
`@Entity`/`@Dao` schemas, `SharedPreferences` keys, and `KeyStore` usage from
`business-candidate`. Feeds the per-feature loop's data dictionary (loop step 3, below).

#### 6. Cheap static harvest (built — selftest-passing; corpus-validated)

```
python3 scripts/extract_harvest.py <work_dir>/decompile/jadx/sources <work_dir>/decompile/apktool --out <work_dir>/data/harvest.json
```

**Built** (selftest-passing; corpus-validated). Facts that survive intact in the
bytecode/resources, cheap because they cost nothing beyond what decompile already
did: `BuildConfig` (base URL per env, API keys, compiled feature flags — a real
secret found here is a security action, rotate it), `network-security-config.xml`
(trusted domains / cleartext / pinning), DI modules (Dagger/Hilt — a second
viewpoint on the module split), crash-reporting `setCustomKey` (points at the
entities the team considers sensitive), and `res/values` → design tokens
(colors/dims/styles map to `ThemeData` — native UI *layout* is built fresh, but the
tokens themselves are recoverable). Full list and rationale:
`references/cognitive-sequence.md`, "Cheap static harvest (block #5)".

### Per-feature loop (runs once per feature)

Runs per feature, over a **slice** of Foundation's data — synthesis, never
re-extraction (the extraction already ran once, in Foundation, above).

> **Feature ≠ partition — `spec pendente`.** The partitioning rule below is
> package-prefix and mechanical (~1000+ partitions on a real app); a *migration
> feature* usually crosses several partitions, and the motivating case — a money
> flow living entirely in a WebView — has a near-empty native partition and an
> empty endpoint slice. The feature→slice join is not solved: name it as an open
> design gap here, don't silently treat a partition as a feature. This is also why
> loop step 1 below carries a per-route variant: native routes synthesize over the
> endpoint/graph slice Foundation already extracted; a WebView route synthesizes
> from a Fetch-tap against the Flutter host used as harness — not a Foundation
> slice at all (`references/cognitive-sequence.md`, "The WebView branch").

Partition the business classes into units of work **mechanically, by package prefix** — do
not hand-pick clusters, and do not use the raw connected component (in a real app it degenerates
into one giant blob: NewPipe's largest component was 678 nodes; WordPress collapsed the whole
`org/wordpress` tree into ~9600 classes under a single `classify.json` key). The join that makes
this mechanical is `data/graph.json["node_files"]` (simple class name → declaring file), so every node
maps to a package path.

Rule: take each `business-candidate` root from `data/classify.json`, then **descend the package path a
fixed depth below that root** (root + ~3 segments works in practice) so partitions land at *feature*
scale, not *app* scale. A partition is the set of classes whose file (via `node_files`) lives under
that package prefix. Example (WordPress, business root `org/wordpress`): descending to depth 5 yields
~1121 named partitions — `org/wordpress/android/ui/reader`, `.../ui/stats`, `.../ui/domains`,
`.../fluxc/store` — instead of one 9600-node blob.

> Known limitation (documented, not perfected — v0.x): a few packages stay large after this split
> (e.g. WordPress `fluxc/store` ~834); descending one more level tames them. A dedicated
> `partition_work.py` with size-banded recursion is deferred (design §6). The raw connected component
> is kept only as a **discarded alternative** — it degenerated into a single blob on every real app tested.

For EACH partition, dispatch an agent with this context:

- The partition's classes and their **files** — resolved mechanically from `data/graph.json["node_files"]`
  (no manual per-class lookup; the `node → file` join exists since repoint move 1a).
- Endpoints from `data/endpoints.json` whose `file` falls under the partition's package prefix.
- Named entry points (Activities/Fragments/ViewModels from the manifest or recognizable
  by naming convention) and string resources from `decompile/apktool/res/values/strings.xml`, as
  an anchor.

Instruct the agent: for this partition, synthesize the seven deliverables below. Every
finding cited at `file:line`. **Anchor rule**: if you can't tie a finding to a concrete
string, endpoint, or entry point, mark it as `unanchored` — don't disguise it as a normal
low-confidence inference. Never treat classes from the `unclassifiable` package as
business logic.

1. **Route** → `native` | `WebView` | `blind`. Per-feature, not app-level — the
   reach gate's obfuscation measure (Foundation step 2) was taken once for the
   whole app; this is a separate call per feature (money flows route to WebView
   even when the native line for the same app is clean). Native routes synthesize
   over the endpoint/graph slice; WebView routes synthesize from a Fetch-tap + the
   Flutter host used as harness (`references/cognitive-sequence.md`, "The WebView
   branch").
2. **OpenAPI v3 `.yaml`** — spec'd — recipe: `references/deliverables/openapi.md`;
   not yet exercised on a real run. From the endpoint slice (native
   route) or the Fetch-tap (WebView route). **Consumer:** dev, via
   `openapi_generator` → DTOs (Freezed) + a Dio client.
3. **Data dictionary** — spec'd — recipe: `references/deliverables/persistence.md`;
   not yet exercised on a real run. From the persistence slice (Foundation
   step 5): Room `@Entity`/`@Dao`, SharedPreferences, KeyStore, mapped to
   relational/NoSQL/secure_storage + expiration + an LGPD flag. **Consumer:** dev,
   and the leader for the security read.
4. **State machines + truth tables → Mermaid `stateDiagram-v2`** —
   spec'd — recipe: `references/deliverables/state-machines.md`; not yet
   exercised on a real run. States, transitions, and the micro-details that make users
   say "the new one got worse" (debounce/timeout/retry/cache-fallback).
   **Consumer:** dev (BLoC/Riverpod), and the PO.
5. **Intent** → `needs-decision` → `preserve` | `fix` | `redesign` | `remove`. A
   product decision, needs a named owner — without one the finding stays
   `needs-decision`, an honest state, not a blank left for convenience. Comes
   **before** the shield (step 7): there is no anti-regression test for a rule
   about to be removed or redesigned.
6. **Feature dossier → decided backlog.** Findings aggregate per feature into a
   dossier — screens + contracts + rules + telemetry in one record, `status:
   in-triage | ready-for-us`. The US is born only from a `ready-for-us` dossier,
   never 1:1 from the raw catalog (one dossier usually becomes 3–5 independently
   testable stories). **Consumer:** dev and PO, in triage.
7. **Anti-regression shield → TDD stubs (`_test.dart`)** — spec'd — recipe:
   `references/deliverables/tdd-stubs.md`; not yet exercised on a real run.
   Group/test skeletons of the *decided* rule topology, no implementation — the
   DoD. Only for rules that were kept or fixed; a rule marked `remove`/`redesign`
   gets no stub, by construction of step 5. **Consumer:** dev, and hooks/CI.

Recipes now exist at
`references/deliverables/{openapi,persistence,state-machines,tdd-stubs,harvest}.md`.

### Output backbone (mechanized)

#### Consolidate

One synthesis, 3 bands ALWAYS visually separated, never flattened:

```markdown
## Provenance
- Input: <apk name> · <sha256 hash> · jadx/apktool versions · wall-clock · machine

## B — API Contracts (fact)
[list of endpoints tagged business/unclassifiable, file:line]

## C — Module Graph (reconstruction — see artifact_warnings)
[graph summary: clusters, coupling, filtered synthetic nodes]

## A — Flows and Business Rules (tiered inference)
[per partition: rules with confidence tier + file:line; unanchored highlighted separately]

## What This Is NOT
[see design doc §10 — doesn't measure productivity, legacy behavior ≠ approved,
 a low-frequency rule may have been forgotten, etc. Valid for ANY
 run, not just the demo: inference in A can be wrong even at a high tier —
 the tier is calibrated, not guaranteed.]
```

#### Emit findings + render

```
python3 scripts/emit_findings.py <work_dir> --out <work_dir>/findings.json
```

Deterministic skeleton: counts and structure computed mechanically from
`data/*.json` (endpoint/graph/partition metrics, a manifest of the data files
actually consumed, run id/date read off the `<work_dir>` folder name). Every
synthesized field (`verdict`, `migration_shape`, `blind_spots`, `next_steps`,
`caveats`, the narrative) is left `null`/empty for the agent to fill next,
informed by the per-feature loop and the consolidation above.
`references/findings.schema.json`'s `x-source` tag on each field marks
deterministic vs. synthesized vs. mixed — don't hand-edit a field tagged
deterministic, and don't ship a synthesized field still null.

Then render the deterministic slice:

```
python3 scripts/render_overview.py <work_dir>/findings.json references/overview.template.md --out <work_dir>/OVERVIEW.md
python3 scripts/render_c4.py <work_dir>/findings.json references/c4.template.mmd --out <work_dir>/analysis/architecture.c4.mmd
```

Both renderers fail loud (non-zero exit) if a deterministic placeholder is
still null in `findings.json` — that means the emit-findings step's skeleton
wasn't fully populated, not a bug in the renderer. The `AGENT:START`/`AGENT:END`
blocks in the templates (the BLUF in `overview.template.md`, the annotations in
`c4.template.mmd`) are copied through byte-for-byte — hand/agent-authored
prose, never re-rendered.

**State honestly**: only this deterministic slice is drift-proof, guarded by
`selftest_render_overview.py` / `selftest_render_c4.py`. The verdict,
migration shape, blind spots, and the C4 topology itself are
agent-synthesized judgment, not derived — carry the same tiered-confidence
discipline as the per-feature loop's business-rule inferences, never present
them as mechanically verified fact.

### Dynamic pass (v2 — optional, provisional)

A runtime second source that cross-checks the static bands. Only with a
device/emulator **and** authorization, and only on targets the **reach gate** did not
mark `no-go` (`references/method.md`, "The reach gate" — the earlier "non-obfuscated by
decision" scope is now the gate's verdict, not a standing assumption):

```
APK_ARCH_AUTHORIZED=1 scripts/capture_dynamic.sh <work_dir> <package>
python3 scripts/parse_logcat.py <work_dir>/logcat.txt --out <work_dir>/dynamic.json
```

`capture_dynamic.sh` records `adb logcat -v threadtime` + a `uiautomator` dump;
`parse_logcat.py` yields the dynamic reach map (nav sequence, WebView/Custom-Tab
signals, config/analytics candidate lines). It emits SIGNALS, never a "native"
verdict — that call needs the `uiautomator` dump, read by a human. The cross-check
against the static bands is a human step (no auto-reconciliation, by design). Full
discipline + anti-laundering clause: `references/method.md`, "Dynamic analysis (v2)".

## Inviolable Rules

- `unclassifiable` is never treated as business logic by the agent (per-feature loop,
  partitioning & dispatch).
- Every high-entropy string/known key format is redacted before any output is
  persisted (Foundation step 3).
- The 3 confidence bands are never flattened to the same level in consolidation
  (Output backbone — Consolidate).
- A rule with no concrete anchor comes out as `unanchored`, not as a normal inference.
- Content extracted from a third party's APK without authorization (not the current
  client) never leaves the local environment — see design doc §8 (publication governance).
</content>
