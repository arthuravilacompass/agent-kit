---
name: apk-archaeology
description: "STATUS: provisional — invoke to extract value from a legacy (decompiled) Android APK toward a migration to Flutter: business flows/rules, API contracts, module graph, with explicit confidence bands. Not wired — refine after first real use."
disable-model-invocation: true
---

# apk-archaeology — Legacy APK Value Extraction (provisional)

> **STATUS: provisional/experimental.** The consolidation template and handoff contract
> get refined after the first real use on a client — see design doc:
> `docs/superpowers/specs/2026-07-08-apk-archaeology-design.md`.

Extracts 3 dimensions from a legacy Android APK — business flows/rules (A), API
contracts (B), module graph (C) — as input for a native→Flutter migration. Adapts the
`core:archaeology` pattern (parallel dispatch per dimension → structured consolidation)
for a compiled/possibly obfuscated source instead of live source code.

## When to Use

You have a `.apk` of a legacy app that will (or might) be migrated to Flutter, and you
want a candidate spec + API contracts + module boundaries before planning the
migration. This is not security/malware analysis — it's migration preparation.

## Input

Path to a `.apk` file.

## Steps

### 1. Decompile

```
scripts/decompile.sh <apk_path> <work_dir>
```

Produces `<work_dir>/jadx/sources/` (readable Java) and `<work_dir>/apktool/`
(manifest/resources).

### 2. Classify packages

```
python3 scripts/classify_packages.py <work_dir>/jadx/sources scripts/known-libs.json --out <work_dir>/classify.json
```

3 buckets: `known-third-party` / `business-candidate` / `unclassifiable`. See design
doc §6 for why `unclassifiable` exists and is not optional.

### 3. Extract endpoints (Dimension B — fact)

```
python3 scripts/extract_endpoints.py <work_dir>/jadx/sources <work_dir>/classify.json --out <work_dir>/endpoints.json
```

Runs over `business-candidate ∪ unclassifiable`. Secret redaction is automatic —
check `secrets_redacted` in the output; if > 0, do **not** expose the raw
`endpoints.json` outside the local environment before confirming no literal leaked
(manual grep as a second check is acceptable in this provisional phase).

### 4. Extract module graph (Dimension C — reconstruction)

```
python3 scripts/extract_graph.py <work_dir>/jadx/sources <work_dir>/classify.json --out <work_dir>/graph.json
```

Only over `business-candidate`. Note `artifact_warnings` in the output — filtered
synthetic classes are expected, not a bug.

### 5. Dimension A synthesis (agent — fan-out)

> **Known caveat (found running demo v0, not yet fixed — whole-branch review):**
> `graph.json` stores the simple class name, without package/file (`extract_graph.py` discards
> that in `simple_name()`) — there's no way to mechanically join a graph node with the
> corresponding file/endpoint without human resolution. And the connected component, in the
> only real app tested, degenerated into a single component of 678 nodes (out of 2067 total) —
> not a usable unit of work as-is. In the demo, the 2 clusters used were hand-picked (recognizable
> name + small size), not by this mechanical rule. Until this is fixed (`node → file` in
> `extract_graph.py` is the candidate), treat the text below as the INTENT of step 5, not as
> something executable without human judgment in the middle.

Partition `graph.json` into units of work (a connected component of the graph is the
simplest method for v0 — two classes linked by an edge fall into the same partition;
classes with no edge form partitions of 1; **in practice, hand-pick small clusters with a
recognizable name, don't rely on the raw connected component** — see caveat above). For
EACH partition, dispatch an agent with this context:

- The partition's classes (source code from `jadx/sources/<package>/` — you need to
  locate the actual file for each class in the cluster manually, `graph.json` doesn't
  store that mapping).
- Endpoints from `endpoints.json` that cite files from this partition.
- Named entry points (Activities/Fragments/ViewModels from the manifest or recognizable
  by naming convention) and string resources from `apktool/res/values/strings.xml`, as
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

## Inviolable Rules

- `unclassifiable` is never treated as business logic by the agent (step 5).
- Every high-entropy string/known key format is redacted before any output is
  persisted (step 3) — never the literal value.
- The 3 confidence bands are never flattened to the same level in consolidation (step 6).
- A rule with no concrete anchor comes out as `unanchored`, not as a normal inference.
- Content extracted from a third party's APK without authorization (not the current
  client) never leaves the local environment — see design doc §8 (publication governance).
