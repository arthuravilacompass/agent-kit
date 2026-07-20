---
name: apk-archaeology
description: "STATUS: provisional (refined once, not graduated) — invoke to extract value from a legacy (decompiled) Android APK toward a migration to Flutter: a Foundation pass (contracts, module graph + the seam, cheap static harvest) then a per-feature loop producing concrete migration deliverables (OpenAPI, data dictionary, state machines, TDD stubs), each stamped with origin/confidence/intent/reach. Refined after a second real client run that measured the hard walls (obfuscation, dynamic) without crossing them; n=1, not yet graduated."
disable-model-invocation: true
---

# apk-archaeology — Legacy APK Value Extraction (provisional)

> **STATUS: provisional/experimental — refined once.** The consolidation template and
> handoff contract were refined after real client use — a second run that **measured the
> hard walls (obfuscation, dynamic reach) without crossing them**. Not graduated (n=1
> real; the ≥2× bar is not met).

> **This skill conducts; the tool executes.** Every script, selftest, and output
> template lives in `tools/apk-archaeology/` (repo-root, not inside this plugin) — a
> standalone tool by the criterion in `docs/GOVERNANCE.md`, "Skill vs. standalone
> tool." This SKILL.md is the thin conductor: when to use, what phase does what, and
> how to invoke the tool. **Run every command below from the repo root**
> (`cd ~/dev/agent-kit`) — all paths are repo-root-relative.

> **Prerequisites.** `jadx`, `apktool`, `adb` on `PATH` (checked via `command -v`; the
> scripts fail loud with an install hint if missing — never vendored). Scripts are
> pure Python 3 stdlib, no `requirements.txt`, no venv.

> **The cognitive sequence (start here).** The decision sequence *above* this pipeline —
> *given a decompiled APK, what do you actually do with it?* — lives in
> `references/cognitive-sequence.md`. The Steps below run in the same two tempos as that
> reference — **Foundation** (once per APK), then the **per-feature loop** (once per
> feature) — followed by the output backbone and the optional dynamic pass; that
> reference is the decision method they serve.

> **Visual workflow map.** A hand-drawn-style diagram of the whole flow — Foundation →
> `data/` → per-feature loop → output backbone → dynamic pass, with named artifacts
> hanging off each step — lives in `references/workflow.md`. Illustrative only: if it
> ever drifts from the Steps below, this prose wins.

> **From extraction to backlog.** The report method — the CT→RF→US→RN→CA chain, the
> reach map, the confidence tiers, and the log-based v2 (dynamic) instrument
> (`tools/apk-archaeology/scripts/capture_dynamic.sh` +
> `tools/apk-archaeology/scripts/parse_logcat.py`, the Dynamic pass below) — lives in
> `references/method.md`. The client-facing report template (pt-BR) is
> `tools/apk-archaeology/references/modelo-relatorio.pt-BR.md` (the filled file **is**
> the deliverable, shipped as Markdown — inline Mermaid diagram, no `.docx`
> conversion); how to fill it (filling order, worked example, conventions —
> filler/maintainer-facing, never shipped with the report) is
> `tools/apk-archaeology/references/guia-preenchimento.pt-BR.md`; a worked example
> (WordPress) is `tools/apk-archaeology/examples/relatorio-wordpress.pt-BR.md`.

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

`data/` holds every raw JSON artifact **Foundation** produces; `features/<slice>/`
holds what the **per-feature loop** synthesizes over each feature's slice of that
data; `analysis/` and `backlog.md` are where the **output backbone**'s synthesis
lands; `decompile/` is disposable — re-running Foundation step 1 regenerates it from
the same APK.

## Steps

### Foundation (runs once per APK)

The app-level substrate every feature draws on; the per-feature loop synthesizes over
slices of this data, never re-extracting. The rationale for each step (why the reach
gate, why the seam, the full harvest list) lives in `references/cognitive-sequence.md`,
"Foundation" — below is just the invocation sequence.

1. **Decompile.**

   ```
   tools/apk-archaeology/scripts/decompile.sh <apk_path> <work_dir>
   ```

   Produces `<work_dir>/decompile/{jadx,apktool}/` (gitignored, regenerable cache —
   the script writes its own `.gitignore`) and creates `<work_dir>/data/` up front.

2. **Classify packages → the reach-gate verdict.**

   ```
   python3 tools/apk-archaeology/scripts/classify_packages.py <work_dir>/decompile/jadx/sources tools/apk-archaeology/scripts/known-libs.json --out <work_dir>/data/classify.json
   ```

   3 buckets: `known-third-party` / `business-candidate` / `unclassifiable`. The
   `unclassifiable` ratio feeds the **reach gate** — `normal` / `degraded` / `no-go`,
   fired as soon as classify lands, before the synthesis investment downstream
   (`references/method.md`, "The reach gate"). A high ratio bounds or stops the run
   before the per-feature loop ever opens.

3. **Extract endpoints (fact).**

   ```
   python3 tools/apk-archaeology/scripts/extract_endpoints.py <work_dir>/decompile/jadx/sources <work_dir>/data/classify.json --out <work_dir>/data/endpoints.json
   ```

   Runs over `business-candidate ∪ unclassifiable`. Secret redaction is automatic —
   check `secrets_redacted` in the output; if > 0, do not expose the raw
   `endpoints.json` outside the local environment before confirming no literal leaked.

4. **Extract module graph (reconstruction) → the seam.**

   ```
   python3 tools/apk-archaeology/scripts/extract_graph.py <work_dir>/decompile/jadx/sources <work_dir>/data/classify.json --out <work_dir>/data/graph.json
   ```

   Only over `business-candidate`. Filtered synthetic classes surface as
   `artifact_warnings` in the output — expected, not a bug. Naming **the seam** — the
   critical migration unit the leader sequences epics around — is app-level judgment
   over this graph, not a script output (`references/cognitive-sequence.md`, "Map the
   perimeter").

5. **Extract persistence** (built, selftest-passing, corpus-validated).

   ```
   python3 tools/apk-archaeology/scripts/extract_persistence.py <work_dir>/decompile/jadx/sources <work_dir>/data/classify.json --out <work_dir>/data/persistence.json
   ```

   Room `@Entity`/`@Dao`, `SharedPreferences`, `KeyStore` from `business-candidate`.
   Feeds the per-feature loop's data dictionary (`references/deliverables/persistence.md`).

6. **Cheap static harvest** (built, selftest-passing, corpus-validated).

   ```
   python3 tools/apk-archaeology/scripts/extract_harvest.py <work_dir>/decompile/jadx/sources <work_dir>/decompile/apktool --out <work_dir>/data/harvest.json
   ```

   BuildConfig, network-security-config, DI modules, crash keys, design tokens — full
   list and rationale: `references/cognitive-sequence.md`, "Cheap static harvest
   (block #5)"; recipe: `references/deliverables/harvest.md`.

### Per-feature loop (runs once per feature)

Synthesis over a **slice** of Foundation's data, never re-extraction. Feature ≠
partition is an open design gap (`references/cognitive-sequence.md`, "Feature ≠
partition — `spec pendente`") — the per-route variant below (native vs. WebView) is
how the loop routes around it.

**Partitioning (mechanical — do not hand-pick, do not use the raw connected
component; it degenerates into one giant blob on every real app tested).** Take each
`business-candidate` root from `data/classify.json`, descend the package path a fixed
depth below it (root + ~3 segments works in practice — WordPress `org/wordpress` at
depth 5 → ~1121 named partitions instead of one 9600-node blob), and join classes to
files via `data/graph.json["node_files"]`. Known limitation: a few packages stay large
after this split (e.g. `fluxc/store` ~834); descending one more level tames them — a
dedicated `partition_work.py` is deferred.

For EACH partition, dispatch an agent with: the partition's classes and files
(resolved via `node_files`), endpoints from `data/endpoints.json` under its package
prefix, and named entry points + string resources as anchors
(`decompile/apktool/res/values/strings.xml`). **Anchor rule**: a finding that can't be
tied to a concrete string, endpoint, or entry point is marked `unanchored`, never
disguised as a normal low-confidence inference. Never treat `unclassifiable` classes
as business logic.

Seven deliverables per partition, every finding cited at `file:line` (full recipes in
`references/deliverables/`):

1. **Route** → `native` | `WebView` | `blind` — a per-feature call, not app-level
   (money flows route to WebView even when the native line for the same app is
   clean); native synthesizes over the endpoint/graph slice, WebView from a Fetch-tap
   against the Flutter host used as harness (`references/cognitive-sequence.md`, "The
   WebView branch").
2. **OpenAPI v3 `.yaml`** — spec'd, not yet exercised on a real run — recipe:
   `references/deliverables/openapi.md`. **Consumer:** dev, via `openapi_generator` →
   DTOs (Freezed) + a Dio client.
3. **Data dictionary** — spec'd, not yet exercised on a real run — recipe:
   `references/deliverables/persistence.md`. **Consumer:** dev, and the leader for
   the security read.
4. **State machines + truth tables → Mermaid `stateDiagram-v2`** — spec'd, not yet
   exercised on a real run — recipe: `references/deliverables/state-machines.md`.
   **Consumer:** dev (BLoC/Riverpod), and the PO.
5. **Intent** → `needs-decision` → `preserve | fix | redesign | remove` — a product
   decision, needs a named owner; comes **before** the shield (step 7) — there is no
   anti-regression test for a rule about to be removed or redesigned.
6. **Feature dossier → decided backlog.** `status: in-triage | ready-for-us`; the US
   is born only from a `ready-for-us` dossier, never 1:1 from the raw catalog.
   **Consumer:** dev and PO, in triage.
7. **Anti-regression shield → TDD stubs (`_test.dart`)** — spec'd, not yet exercised
   on a real run — recipe: `references/deliverables/tdd-stubs.md`. Only for rules
   kept or fixed; a rule marked `remove`/`redesign` gets no stub, by construction of
   step 5. **Consumer:** dev, and hooks/CI.

### Output backbone (mechanized)

One synthesis, 3 bands ALWAYS visually separated, never flattened — Provenance /
B-API-Contracts (fact) / C-Module-Graph (reconstruction) / A-Flows-and-Rules (tiered
inference) / What This Is NOT (full consolidation template: `references/method.md`).

```
python3 tools/apk-archaeology/scripts/emit_findings.py <work_dir> --out <work_dir>/findings.json
python3 tools/apk-archaeology/scripts/render_overview.py <work_dir>/findings.json tools/apk-archaeology/references/overview.template.md --out <work_dir>/OVERVIEW.md
python3 tools/apk-archaeology/scripts/render_c4.py <work_dir>/findings.json tools/apk-archaeology/references/c4.template.mmd --out <work_dir>/analysis/architecture.c4.mmd
```

`emit_findings.py` computes the deterministic skeleton from `data/*.json` — counts and
structure it genuinely derives — and leaves every synthesized field (`verdict`,
`migration_shape`, `blind_spots`, `next_steps`, `caveats`, the narrative) `null`/empty
for the agent to fill next. `references/findings.schema.json`'s `x-source` tag on each
field marks deterministic vs. synthesized vs. mixed — don't hand-edit a field tagged
deterministic, don't ship a synthesized field still null. Both renderers fail loud
(non-zero exit) if a deterministic placeholder is still null — that means the
emit-findings step's skeleton wasn't fully populated, not a bug in the renderer. The
`AGENT:START`/`AGENT:END` blocks in the templates are copied through byte-for-byte,
never re-rendered.

**State honestly**: only this deterministic slice is drift-proof, guarded by
`selftest_render_overview.py` / `selftest_render_c4.py`. The verdict, migration
shape, blind spots, and the C4 topology itself are agent-synthesized judgment, not
derived — carry the same tiered-confidence discipline as the per-feature loop's
business-rule inferences, never present them as mechanically verified fact.

### Dynamic pass (v2 — optional, provisional)

A runtime second source that cross-checks the static bands. Only with a
device/emulator **and** authorization, and only on targets the **reach gate** did not
mark `no-go` (`references/method.md`, "The reach gate"):

```
APK_ARCH_AUTHORIZED=1 tools/apk-archaeology/scripts/capture_dynamic.sh <work_dir> <package>
python3 tools/apk-archaeology/scripts/parse_logcat.py <work_dir>/logcat.txt --out <work_dir>/dynamic.json
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
  client) never leaves the local environment.
