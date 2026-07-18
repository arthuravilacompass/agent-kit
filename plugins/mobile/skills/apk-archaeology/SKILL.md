---
name: apk-archaeology
description: "STATUS: provisional — invoke to extract value from a legacy (decompiled) Android APK toward a migration to Flutter: business flows/rules, API contracts, module graph, with explicit confidence bands. Not wired — refine after first real use."
disable-model-invocation: true
---

# apk-archaeology — Legacy APK Value Extraction (provisional)

> **STATUS: provisional/experimental.** The consolidation template and handoff contract
> get refined after the first real use on a client — see design doc:
> `docs/superpowers/specs/2026-07-08-apk-archaeology-design.md`.

> **From extraction to backlog.** The report method — the CT→RF→US→RN→CA chain,
> the reach map, the confidence tiers, and the log-based v2 (dynamic) instrument
> (`scripts/capture_dynamic.sh` + `scripts/parse_logcat.py`, step 8) — lives
> in `references/method.md`. The client-facing report template (pt-BR) is
> `references/modelo-relatorio.pt-BR.md` (the filled file **is** the deliverable,
> shipped as Markdown — inline Mermaid diagram, no `.docx` conversion); how to fill
> it (filling order, worked example, conventions — filler/maintainer-facing, never
> shipped with the report) is `references/guia-preenchimento.pt-BR.md`; a worked
> example (WordPress) is
> `examples/relatorio-wordpress.pt-BR.md`.

Extracts 3 dimensions from a legacy Android APK — business flows/rules (A), API
contracts (B), module graph (C) — as input for a native→Flutter migration. Adapts the
`core:archaeology` pattern (parallel dispatch per dimension → structured consolidation)
for a compiled/possibly obfuscated source instead of live source code.

## When to Use

You have a `.apk` of a legacy app that will (or might) be migrated to Flutter, and you
want a candidate spec + API contracts + module boundaries before planning the
migration. This is not security/malware analysis — it's migration preparation.

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
├── data/                  (classify.json, classify.v1.json, endpoints.json, graph.json, partitions.json)
├── report/                (on-demand — generated only when a client-facing report is requested; NEW, never a relocation)
└── decompile/             (jadx/, apktool/ — gitignored + regenerable cache, see step 1)
```

`data/` holds every raw JSON artifact steps 2-4 produce; `analysis/` and
`backlog.md` are where the agent's synthesis (steps 5-7) lands; `decompile/`
is disposable — re-running step 1 regenerates it from the same APK.

## Steps

### 1. Decompile

```
scripts/decompile.sh <apk_path> <work_dir>
```

Produces `<work_dir>/decompile/jadx/sources/` (readable Java) and
`<work_dir>/decompile/apktool/` (manifest/resources) — see Run layout above.
`decompile/` is a gitignored, regenerable cache: the script writes a
`.gitignore` (`*`) into it on every run, so it never needs a manual exclusion
elsewhere. The script also creates `<work_dir>/data/` up front so steps 2-4
below always have somewhere to write.

### 2. Classify packages

```
python3 scripts/classify_packages.py <work_dir>/decompile/jadx/sources scripts/known-libs.json --out <work_dir>/data/classify.json
```

3 buckets: `known-third-party` / `business-candidate` / `unclassifiable`. See design
doc §6 for why `unclassifiable` exists and is not optional.

### 3. Extract endpoints (Dimension B — fact)

```
python3 scripts/extract_endpoints.py <work_dir>/decompile/jadx/sources <work_dir>/data/classify.json --out <work_dir>/data/endpoints.json
```

Runs over `business-candidate ∪ unclassifiable`. Secret redaction is automatic —
check `secrets_redacted` in the output; if > 0, do **not** expose the raw
`endpoints.json` outside the local environment before confirming no literal leaked
(manual grep as a second check is acceptable in this provisional phase).

### 4. Extract module graph (Dimension C — reconstruction)

```
python3 scripts/extract_graph.py <work_dir>/decompile/jadx/sources <work_dir>/data/classify.json --out <work_dir>/data/graph.json
```

Only over `business-candidate`. Note `artifact_warnings` in the output — filtered
synthetic classes are expected, not a bug.

### 5. Dimension A synthesis (agent — fan-out)

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

Instruct the agent: synthesize business flows/rules observable in this partition. Every
rule cited at `file:line`. **Anchor rule**: if you can't tie a rule to a concrete
string, endpoint, or entry point, mark it as `unanchored` — don't disguise it as a normal
low-confidence inference. Never treat classes from the `unclassifiable` package as
business logic.

### 6. Consolidate

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

### 7. Emit findings + render (mechanized output backbone)

```
python3 scripts/emit_findings.py <work_dir> --out <work_dir>/findings.json
```

Deterministic skeleton: counts and structure computed mechanically from
`data/*.json` (endpoint/graph/partition metrics, a manifest of the data files
actually consumed, run id/date read off the `<work_dir>` folder name). Every
synthesized field (`verdict`, `migration_shape`, `blind_spots`, `next_steps`,
`caveats`, the narrative) is left `null`/empty for the agent to fill next,
informed by steps 5-6. `references/findings.schema.json`'s `x-source` tag on
each field marks deterministic vs. synthesized vs. mixed — don't hand-edit a
field tagged deterministic, and don't ship a synthesized field still null.

Then render the deterministic slice:

```
python3 scripts/render_overview.py <work_dir>/findings.json references/overview.template.md --out <work_dir>/OVERVIEW.md
python3 scripts/render_c4.py <work_dir>/findings.json references/c4.template.mmd --out <work_dir>/analysis/architecture.c4.mmd
```

Both renderers fail loud (non-zero exit) if a deterministic placeholder is
still null in `findings.json` — that means step 7's skeleton wasn't fully
populated, not a bug in the renderer. The `AGENT:START`/`AGENT:END` blocks in
the templates (the BLUF in `overview.template.md`, the annotations in
`c4.template.mmd`) are copied through byte-for-byte — hand/agent-authored
prose, never re-rendered.

**State honestly**: only this deterministic slice is drift-proof, guarded by
`selftest_render_overview.py` / `selftest_render_c4.py`. The verdict,
migration shape, blind spots, and the C4 topology itself are
agent-synthesized judgment, not derived — carry the same tiered-confidence
discipline as step 5's business-rule inferences, never present them as
mechanically verified fact.

### 8. Dynamic pass (v2 — optional, provisional)

A runtime second source that cross-checks the static bands. Only with a
device/emulator **and** authorization (scope so far: non-obfuscated by decision):

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

- `unclassifiable` is never treated as business logic by the agent (step 5).
- Every high-entropy string/known key format is redacted before any output is
  persisted (step 3) — never the literal value.
- The 3 confidence bands are never flattened to the same level in consolidation (step 6).
- A rule with no concrete anchor comes out as `unanchored`, not as a normal inference.
- Content extracted from a third party's APK without authorization (not the current
  client) never leaves the local environment — see design doc §8 (publication governance).
