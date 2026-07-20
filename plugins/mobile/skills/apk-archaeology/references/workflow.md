# Workflow — visual map

Illustrative only. A hand-drawn-style diagram of the whole flow: **Foundation** (once
per APK, through the reach gate's `normal / degraded / no-go` verdict — boxed not
because it repeats but so the four extract steps stay adjacent and feed `data/` as one
edge instead of four converging ones) → `data/` as the shared factual base — the one
artifact read by both halves downstream → the **per-feature loop** (boxed because it
is the only part that repeats — dispatched per partition, drawn left-to-right as a
band) → the **output backbone** (flat: deterministic skeleton, then agent synthesis,
then renderers) → the **dynamic pass** (v2 — optional, gated, the dotted `if
authorized` branch). Named file artifacts hang off the step that
produces them, at the same visual weight as everything else — nothing here overrides
the prose in `SKILL.md`, `method.md`, or `cognitive-sequence.md`.

**Known gaps this diagram cannot resolve visually** — hold these in mind whenever
reading it; they are the places it is most likely to mislead if taken at face value:

- **Feature ≠ partition** — the subgraph is named "Per-feature loop" (the method's own
  name for the phase), but its re-dispatch edge says "per partition": that tension is
  the *open design gap* per `cognitive-sequence.md`, "Feature ≠ partition — `spec
  pendente`". The loop dispatches per **partition** (mechanical, package-prefix), not
  per migration **feature** — the feature→slice join is unsolved; don't read the loop
  as one iteration per feature.
- **Per-feature-loop deliverables are spec'd, not yet exercised.** OpenAPI, data
  dictionary, state machines, and TDD stubs have a recipe but no real-run mileage yet,
  unlike Foundation's extract scripts (persistence and harvest are explicitly "built,
  selftest-passing, corpus-validated" per `SKILL.md`; endpoints and graph share the
  same script+selftest discipline). The diagram draws all steps at the same weight —
  maturity is stated here, not encoded visually.
- **The output backbone is not purely mechanical.** Between `findings.json`'s
  deterministic skeleton and the renderers sits an agent-synthesis step — drawn as its
  own node — that fills `verdict`, `migration_shape`, `blind_spots`, `next_steps`,
  `caveats`, and the `bridge_*` metrics: `findings.schema.json` tags these fields
  `synthesized`/`mixed`, and `SKILL.md` warns never to present them as mechanically
  verified fact.
- **Intent/Dossier ordering varies by document.** This diagram sequences Intent →
  Dossier, matching `SKILL.md`'s numbered per-feature-loop steps (5 → 6). The
  client-report flowchart in
  `tools/apk-archaeology/references/modelo-relatorio.pt-BR.md` (§3 Metodologia,
  diagram subgraph "ETAPA 2") sequences Dossiê (`DOS`) → Triagem (`TRI`, where
  `intent` is decided) — the opposite order. Both are accurate to their own
  document; the variance is named here, not resolved — reconciling the two is a
  separate decision the operator has not made.
- **The four extract steps have different classify-scopes** the diagram does not
  differentiate: endpoints runs over `business-candidate ∪ unclassifiable`; graph and
  persistence over `business-candidate` only; harvest is not classify-filtered at all
  (`SKILL.md`, Foundation steps 3–6).
- **The reach gate's verdict is three-valued** — the node names `normal · degraded ·
  no-go`, but the edges still draw only the stop/proceed fork: a `degraded` run
  proceeds with bounded claims, it is not `normal` (`method.md`, "The reach gate").
- **The dynamic pass never yields a "native" verdict by itself.** `parse_logcat.py`
  emits SIGNALS, never a verdict — only the `uiautomator` dump (0 `WebView` nodes),
  read by a human, can support a "native" call; and the cross-check against the static
  bands is a human step by design, with no auto-reconcile (`method.md`, "Dynamic
  analysis (v2)"). Likewise the loop's `blind` route terminates where it is drawn — no
  synthesis pipeline runs for it, honesty instead of a contract
  (`cognitive-sequence.md`, per-feature loop step 1).

Self-critique is deliberately **not** a node in this diagram — it lives in the
per-contract honesty stamps (🟢/🟡/⬜) and the confidence ladder (`blind → observed →
cross-validated → business-ratified`) described in the deliverable recipes, not as a
step of its own.

```mermaid
---
config:
  look: handDrawn
  theme: base
  themeVariables:
    primaryColor: "#fefdfa"
    primaryBorderColor: "#2b2b2b"
    lineColor: "#4a453c"
    primaryTextColor: "#1a1a1a"
    clusterBkg: "#fefdfa"
    clusterBorder: "#8a8378"
    fontFamily: "Comic Sans MS, Chalkboard SE, Comic Neue, cursive"
---
flowchart TB

%% ---- Foundation — once per APK (boxed for locality: the extract fan stays
%%      adjacent and the box feeds data/ as ONE edge, not four converging ones) ----

APK(["APK + authorization"])
D["Decompile"]
STOP(["STOP the run"]):::stop

subgraph FOUND["Foundation — once per APK"]
  direction TB
  CL["Classify"]
  RG["Reach gate —<br/>normal · degraded · no-go"]
  EP["Extract endpoints"]
  GR["Extract graph"]
  PST["Extract persistence"]
  HV["Extract harvest"]
  SEAM["Name the seam —<br/>leader sequences epics"]
  CL --> RG
  RG --> EP
  RG --> GR
  RG --> PST
  RG --> HV
  GR --> SEAM
end

DATA["data/ — factual base"]

APK ==> D --> CL
RG -.->|no-go| STOP
FOUND ==> DATA

%% ---- Per-feature loop — the one repeating sub-process (internally LR so the
%%      loop reads as a wide band instead of stretching the parallel columns) ----

subgraph LOOP["Per-feature loop"]
  direction LR
  P["Partitioning"] --> RT["Route"]
  RT -->|"native / WebView"| WORK["OpenAPI · data dictionary · state machines"]
  RT -.->|blind| BLIND(["Mark the bounded blind spot"])
  WORK --> FEAT["features/slice/"]
  WORK --> INT["Intent —<br/>preserve · fix · redesign · remove"]
  INT --> DOS["Dossier —<br/>in-triage · ready-for-us"]
  DOS -->|"preserve / fix"| TDD["TDD stubs"]
  TDD --> FEAT
  DOS -.->|"per partition, concurrently"| P
end

DATA ==> P

%% ---- Output backbone — once per run (flat, no box) ----

EF["Emit the findings skeleton —<br/>deterministic, from data/"]
FJ["findings.json"]
AGSYN["Agent synthesis"]
RO["Render the overview"]
RC["Render the C4 diagram"]
OVF["OVERVIEW.md"]
C4F["analysis/architecture.c4.mmd"]

DATA ==> EF
EF --> FJ --> AGSYN
AGSYN --> RO --> OVF
AGSYN --> RC --> C4F

%% ---- Dynamic pass v2 — optional, gated (flat, no box) ----

CAP["Capture the dynamic session"]
LOG["logcat.txt"]
UID["uiautomator dump"]
PL["Parse the captured log"]
DJ["dynamic.json"]
CC["Human cross-check"]

RG -.->|"if authorized"| CAP
CAP --> LOG --> PL --> DJ --> CC
CAP --> UID --> CC

%% self-critique is distributed, not a node: honesty stamps (green/yellow/blank)
%% + the ladder blind -> observed -> cross-validated -> business-ratified

classDef stop fill:#f3e6e2,stroke:#9c4a3a,stroke-width:1.5px,color:#7a2f22;
```

> Rendering note: `look: handDrawn` needs Mermaid ≥ v10.5 and the YAML frontmatter
> config form above (not the older `%%{init: {...}}%%` pseudo-JSON, which silently
> drops the setting if any value has mixed quoting). Editors/extensions bundling an
> older Mermaid core will render this as a plain (non-sketchy) flowchart — the diagram
> is still correct, just not hand-drawn.
