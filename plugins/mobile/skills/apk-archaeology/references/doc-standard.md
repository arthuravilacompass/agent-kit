# Doc Standard — apk-archaeology documentation discipline

## § What this is

This standard governs every apk-archaeology doc a human reads. It makes the pipeline
become prose with discipline along three axes — structure/content · data source ·
rendering — for two audiences: engineer and business stakeholder. The north is
epistemic, not stylistic: reverse engineering recovers **lost requirements** (design
recovery, Chikofsky & Cross 1990), not the old architecture. Legacy behavior describes
what the system does, not why — legacy behavior ≠ intent ≠ spec of the new system
(Martraire).

## §Genres

The standard defines **3 genres**:

- **G1 target-view** — `analysis/*.md`, engineer reader.
- **G2 baseline** — `analysis/baseline.md`, engineer/architect onboarding onto the
  system.
- **G3 report** — `report/*`, PO + client dev (see §report).

`analysis/` also hosts three genres this standard names but does **not** define the
skeleton of, because they belong to other bodies:

- **VERDICT** — the OVERVIEW/framing family: viability, verdict, next stage (e.g.
  `feasibility.md`); also covers portability/decision verdict tables, not only
  single-verdict docs.
- **LEDGER** — uses the kit's `ledger-format` (e.g. `decisions.md`).
- **PROOF** — a constructive demonstration (e.g. a port pilot showing a seam ports 1:1
  to the target stack). Its worth is the demonstration itself, so it is not forced into
  the G1 fact/inference/gap skeleton.

Recommendation and verdict never invade the 3 genres this standard defines — they live
in VERDICT, LEDGER, PROOF, or `report/`.

## §Header

Every doc, every genre, opens with three mandatory facts:

1. **Reader** — who this doc is for.
2. **Use** — what the reader does with it.
3. **Data source** — declared as a Symphony-style mapping rule (e.g. "derived from
   `data/endpoints.json` + grep over `decompile/jadx/`").

The header is the inspectable trail from claim to artifact. No doc skips it.

**Heading language (retrofit).** In a retrofit, section headings and header labels take
the document's own language — a pt-BR view uses `§Observado`/`§Leitura`/`§Aberto` and
`Leitor·Uso·Fonte`; an English view uses `§Observed`/`§Reading`/`§Open` and
`Reader·Use·Source`. Same skeleton, either language.

## §G1 — target-view

Skeleton, in order:

1. **Header** — reader · use · data source · view scope.
2. **`§Observed`** — facts. Each claim carries a typed anchor: `file:line` (static) or
   `capture:<id>` (dynamic — logcat, HAR, beta screen). No anchor, no entry — the claim
   is not `§Observed`.
3. **`§Reading`** — analyst inferences. Each one anchored to the `§Observed` fact that
   supports it.
4. **`§Open`** — named gaps, information-request style. Never filled in silently.

**Annotated-catalog sub-pattern.** A dense classification catalog whose rows fuse an
observed fact with an inline reading (e.g. a partition/feature ranking table) may keep
its table under `§Observed` with an explicit caveat that the reading-column is
inference — splitting the table across sections would destroy its use as a menu.

Recommendation does not live in G1 — to-be lives outside `analysis/` (see §Transversal).

**Marker↔section map.** 🟢 (fact-anchored) → `§Observed`; 🟡 (analyst inference) →
`§Reading`; ⬜ (out of static reach) → `§Open`. In G1 prose the section carries this
distinction — the marker is not repeated in the text. The anchor itself is the 🟢
signal. Markers 🟢🟡⬜ survive only where no section can carry the distinction:
diagrams (C4) and `findings.json`.

## §G2 — baseline

Skeleton, in order:

1. **Context-as-fact** — black box + external actors/systems, C4 Context level. 🟢
   only: observable fact, never a decision.
2. **Known/open inventory** — the aggregate (manual in v1) of every view's `§Open`.
   Regenerated from current state each run, never patched.
3. **View index** — a guided tour: recommended reading order by reader goal.

OVERVIEW does not duplicate the baseline — it keeps viability + manifest and points
here.

## §report

The `report/` genre is already governed by shipped state (mobile 0.9.0):

- **Recon report** — `tools/apk-archaeology/references/modelo-relatorio.pt-BR.md`. The
  filled file *is* the deliverable, with the internal PO/§6 and dev/§7 split.
- **Scope proposal** — freeform, no template.

This standard adds only the epistemic discipline on top of those artifacts, and does
not redefine or duplicate either one:

- **BLUF executive summary** — "report in miniature," proportional, jargon-free.
- **Findings translate faithfully** — the translation preserves the source G1's
  fact/reading separation; it does not editorialize.
- **Fact/opinion split by genre**, not by annotation inside a doc: recon report is
  observation; scope proposal is opinion/proposal. The proposal is free engineering/PO
  judgment — it is not obliged to trace input claim-by-claim; the fact→recommendation
  separation is preserved structurally (the proposal is a distinct, labeled genre), not
  by an in-doc trail.

## §Transversal

- **Fact about someone else's decision.** A discovered structural boundary (a DI/Dagger/
  Hilt module boundary, say) is the original team's decision, observed in the artifact —
  legitimate as C4 Container/Component in the as-is, with its origin marked on the
  diagram. Context level is fact; Container/Component is fact-about-a-decision. A *new*
  decision belongs only in the to-be.
- **New view only with a named reader** (Views & Beyond). Keep docs small and focused —
  no "map of the whole world."
- **Gap → `§Open`.** Never silent inference.
- **To-be/recommendation lives outside `analysis/`** — in the scope proposal and the
  backlog.
- **Retrofit relocates, never deletes.** Folding an existing doc into its genre moves
  out-of-genre content to its home, it does not drop it: to-be/recommendation →
  proposal + backlog; a verdict → VERDICT; a decision → LEDGER; run-specific
  method/tooling → the run's method notes or `data/` artifacts. A view is not the
  graveyard of what doesn't fit — the run keeps the knowledge, sorted by genre.
- **Lifecycle: overwrite (L8).** A doc reflects current state only. When later evidence
  moves an item between sections, it overwrites what was there — the epistemic history
  lives in git, not in an inline "corrected" note or a per-doc changelog section.
