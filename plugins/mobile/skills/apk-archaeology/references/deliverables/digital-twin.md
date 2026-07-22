# Current-State Digital Twin — Visual Synthesis Recipe (Foundation output, optional visual synthesis)

**What this is.** Not a per-feature loop step — an optional, once-per-APK visual
synthesis assembled *after* Foundation has already produced `data/*.json`
(`../../SKILL.md`, "Foundation"). Where the per-feature loop's recipes
(`persistence.md`, `openapi.md`, `state-machines.md`, `tdd-stubs.md`) each turn one
feature's slice into a dev-facing artifact, the Digital Twin turns the **whole app's**
Foundation output into one self-contained visual a migration committee or architect
can read without opening a single `data/*.json` file directly. It sits on top of
Foundation, never gates it — no other deliverable depends on the Twin existing, and it
can be skipped entirely on a run where nobody needs the picture.

## Input — Foundation's outputs, assembled, never re-extracted

The Twin draws on Foundation data already sitting in `data/`, plus three narrower
extractions run alongside it:

- `data/partitions.json` — the partition list (per-feature loop's mechanical split,
  `../../SKILL.md`, "Partitioning").
- `data/graph.json` — the inheritance graph the partitions were cut from.
- `data/coupling.json` — cross-partition coupling, via `compute_coupling.py
  <graph.json> <partitions.json> --out data/coupling.json`.
- `data/layers.json` — per-partition logical-layer composition (presentation / domain
  / data / platform), via `extract_layers.py <sources_dir> <partitions.json> --out
  data/layers.json`.
- `data/permissions.json` — the manifest's declared permissions, via
  `extract_permissions.py <apktool_dir> --out data/permissions.json`.
- `data/persistence.json` and `data/harvest.json` — already-built Foundation
  extractors (`persistence.md`, `harvest.md`), re-read here for the security annex,
  not re-run.
- `findings.json`'s `migration_shape` buckets (`../../SKILL.md`, "Output backbone") —
  the four-way classification (`port_native`, `stays_webview`,
  `bridge_to_reimplement`, `infra_platform`) that colors the Twin's territories.

**Status, honestly.** All three extractors this recipe depends on beyond Foundation's
existing set — `compute_coupling.py`, `extract_layers.py`, `extract_permissions.py` —
are promoted into `tools/apk-archaeology/scripts/` proper, each following this
family's standard `<positional args> --out <path>` CLI convention with its own
selftest (`../../SKILL.md` steps 7-9 tag all three `(built, selftest-passing,
corpus-validated)`). "Corpus-validated" here means each was run once against a real
production APK outside this repo (not named or checked in here) and its output
reviewed by hand — one validated run, not a large or diverse corpus; a differently-
shaped manifest or source tree could still expose a gap that single run didn't.

**The self-containment constraint is deliberate, not a stopgap.** The Twin (and every
annex) is a single HTML file: inline CSS, inline JS, zero external `fetch`, zero
`<script src="...">`, zero `<link href="http...">`. That buys three things a
build-stepped alternative would not — it opens directly via `file://` with no server,
it has no CORS surface to fight, and it survives being copied to one file and emailed
without a bundler. Anything that evolves this artifact must preserve that property;
reaching for a CDN script or a fetch to a local dev server the moment a chart library
would be convenient is the single easiest way to quietly break it.

## Output — two layers: mechanical extraction vs. visual synthesis

- **Mechanical extraction layer** (Foundation-adjacent, raw facts):
  `data/coupling.json`, `data/layers.json`, `data/permissions.json` — same discipline
  as every other `data/*.json`, deterministic given the same input tree, no judgment
  calls baked in.
- **Visual synthesis layer** (this recipe's actual deliverable):
  - `analysis/digital-twin.html` — the Twin itself. Territories colored by
    `migration_shape` bucket, one box per partition, and a small hand-placed set of
    **seam** edges — deliberately *not* auto-derived from the full coupling graph.
    Only the architecturally deliberate seams get drawn (the JS↔native bridge, the
    auth handoff, the transport layer, the backend) — painting every edge
    `coupling.json` reports would bury the two or three seams that matter under noise
    from ordinary intra-app coupling.
  - Optional companion **annex** files, same self-containment constraint, split out
    because their content is too dense for the main body: `digital-twin-annex-
    coupling.html` (a coupling matrix/heatmap off `coupling.json`),
    `digital-twin-annex-permissions.html` (a permissions/privacy matrix,
    `permissions.json` cross-referenced against a **capability catalog**), and
    `digital-twin-annex-security.html` (a security/persistence summary curated from
    `persistence.json` + `harvest.json` + the same catalog) — all under `analysis/`.

  The capability catalog itself does not ship as a file in this kit yet — it is a
  small hand-maintained reference (not a script) mapping each dangerous-tier Android
  permission string, and each `known-libs.json` vendor entry, to a plain-English
  capability and a rough risk tier. Until one is checked in, treat the cross-reference
  as the synthesizer's own inline judgment, sourced in the annex, not a shared table.
  The security annex especially is **curation, not extraction** — say so on the page
  itself, the same way a synthesized `findings.json` field is never presented at the
  same confidence as a deterministic one.

## Rendering to a static image (a command that works, not a committed tool)

The Twin's edge geometry is computed **live**, via `getBoundingClientRect()` against
real on-screen layout, on resize and once fonts finish loading (Method, phase 4). So it
can only be captured by an actual browser rendering the page — a headless-CLI
screenshot flag does not do this: `chrome --headless --screenshot --window-size=W,H`
only captures the fixed viewport you gave it, not the full scrollable page height, so a
tall diagram comes back cropped. Documented gotcha, not a flaky one-off.

What worked this session: a small Node script driving a **system-installed**
Chrome/Chromium via `puppeteer-core` (not the bundled Chromium `puppeteer` normally
downloads), navigating to the local `file://` path, waiting for `document.fonts.ready`
so the artifact's own resize/font-load listener settles, then `page.screenshot({
fullPage: true, ... })` at a fixed `deviceScaleFactor` for reproducible pixel width:

```js
// Run once with `node -e '<paste this>'`, or as a throwaway .js file — this is
// NOT part of this repo's tooling. Requires `npm install puppeteer-core` and a
// system Chrome/Chromium install; both are one-off, local-only dependencies.
const puppeteer = require('puppeteer-core');
(async () => {
  const browser = await puppeteer.launch({
    executablePath: '/path/to/system/chrome', // e.g. Chrome.app's binary on macOS
    headless: 'new',
  });
  const page = await browser.newPage();
  await page.setViewport({ width: 1600, height: 1200, deviceScaleFactor: 2 });
  await page.goto('file:///absolute/path/to/analysis/digital-twin.html');
  await page.evaluate(() => document.fonts.ready);
  await page.screenshot({ path: 'digital-twin.png', fullPage: true });
  await browser.close();
})();
```

This introduces a Node+Chrome runtime dependency for whoever wants a screenshot —
deliberately **not** added as tracked kit tooling. It mirrors `render_c4.py`'s own
choice to stop at diagram-*source* generation and leave image rendering manual: this
tool family is pure-stdlib text/template generation with zero precedent for shelling
out to a browser, and this recipe follows that same honest-scope discipline.

## Method — four phases, in order

The single highest-value thing to preserve from this recipe: a hard sequencing rule,
not a suggestion. Skipping ahead (polishing layout before the data is frozen, hand-
tuning edge routing before the skeleton is approved) is the single most common way
this kind of artifact burns hours re-doing work the next phase was going to invalidate
anyway.

| Phase | Goal | What gets frozen | Anti-pattern this phase exists to block |
|---|---|---|---|
| 1. Content | Fix what the diagram *claims* | Every headline claim, honestly split by evidence quality | Shipping one blanket confidence claim over unevenly-evidenced areas |
| 2. Data/derivation | Turn every new dimension into reviewable data | A plain-text draft-verdict list, corrected by a human | Painting a judgment call onto a box before it's been checked |
| 3. Skeleton/structure | Decide position/size once | The sizing formula, the anchor element, the grouping | Hand-tuning layout against a skeleton that's still going to move |
| 4. Polish/finish | One pass of ink and routing | Edge paths, labels, badges, confidence-driven visual weight | Starting polish before phase 3 is actually frozen |

1. **Content phase.** Fix what the diagram claims before touching how it looks.
   - A confidence/viability claim in a header or seal must be honest and split by
     axis when evidence quality genuinely differs by area — "high confidence in
     structure, low confidence in one specific unverified surface," never one blanket
     claim smeared over uneven evidence.
   - The highest-risk, highest-decision-value surface gets promoted to a headline
     callout, with the decision left explicitly **open** if it genuinely is — never
     pre-select an option the data doesn't support.
   - A caveat that changes how a headline claim should be *read* — "the interface
     looks clean, but there's a second channel outside the documented contract" — is
     elevated to sit visibly alongside that claim, not buried as a footnote.
   - Fix raw coordinate/geometry bugs (usually a simple off-by-one-axis error, e.g.
     subtracting a horizontal offset from a vertical coordinate), and make edge
     recomputation **resize- and font-load-aware**, not compute-once-on-load — edges
     computed once at load silently drift the moment a web font swaps in or the
     window resizes.

2. **Data/derivation phase.** Before touching layout, derive every *new* analytical
   dimension (coupling degree, layer composition, portability verdicts, permissions)
   as data — scripts plus a plain reviewable list — **not** as rendered ink yet:
   - Any judgment call ("how hard is this module to port") is drafted as an explicit,
     clearly-marked **inference** in a plain-text list, for a human to correct
     *before* it is ever painted onto a box. Correcting a table row is cheap;
     correcting a rendered, styled node after the fact is expensive enough to tempt
     skipping the correction instead.
   - If a node is a **merge** of two or more underlying units that could carry
     *different* judgment calls (two sub-modules fused into one box, one easy and one
     hard to port), the fused box's badge must never silently pick just one
     constituent's value — either split the box, or make the disagreement explicit
     (a combined badge, a footnote). This is the single most costly mistake in this
     method (Honesty caveat, below): a merged node reading uniformly easy while
     quietly containing a hard, high-risk sub-component.

3. **Skeleton/structure phase.** Freeze structure *before* polishing it. Any decision
   that changes a box's position or size — a sizing formula ("box size reflects code
   volume *and* coupling, not just line/class count"), a visual signature element
   anchoring the reading order (a lineage/derivation scale down one side of the page),
   semantic grouping and spacing — is decided and rendered first, then treated as
   frozen. **Do not hand-tune edge routing or per-node micro-layout against a skeleton
   that is still going to move** — that work is wasted the moment the skeleton
   changes, and redoing it against the frozen skeleton later costs the same either
   way, so do it once, last. If a sizing/encoding formula is genuinely ambiguous —
   does box size mean *effort*, or *code volume* with effort as a separate channel? —
   that is a real decision fork worth surfacing explicitly, not picking silently: box
   size is usually the single most salient encoding on the whole page.

4. **Polish/finish phase.** One pass, after the skeleton is frozen: edge routing
   (orthogonal/jogged, never crossing an unrelated box or its text), label placement
   (visibly on or near its own edge, never floating free of the path it names, never
   overlapping an unrelated box), the per-node ink from phase 2's data (small,
   consistent-corner badges, not scattered), and a confidence-driven visual weight —
   modulating a box's saturation/contrast by how well-evidenced its content is. This
   last one is cheap and strong: it makes an epistemic-honesty system perceptible at a
   glance instead of requiring the reader to decode a legend on every box — but if a
   large fraction of the diagram is genuinely low-confidence, tune the effect so it
   stays legible rather than washing the whole page to near-blank. Typography,
   iconography, and narrative callouts land here too. If the artifact needs to survive
   a projector/slide context, that is a **separate, hand-authored static section**,
   not a CSS media-query transform of the dense version — a diagram whose edges are
   computed from live on-screen geometry will not repaginate correctly under
   print/reflow.

## Honesty caveat — a merged node's badge is not a safe average

- **A merged/fused visual node computing its badge from only one of its constituent
  parts is a systemic risk class, not a one-off bug.** Anywhere nodes get merged for
  visual economy, audit specifically for constituents with *differing* judgment
  calls — don't just spot-check a few boxes and call the pass done. A box that fuses
  an easy sub-module with a hard one, and shows only the easy verdict, is worse than
  showing no verdict at all: it actively misleads the reader scanning for risk.
- **A box-sizing/encoding decision is usually the single most legible, most
  decision-shaping element on the page.** Treat a change to what it *means* — effort
  vs. code volume vs. some blend — as a decision worth confirming explicitly, not an
  implementation detail buried in a commit nobody reads before the diagram ships.
- **"All is well" from a review pass that reused the build pass's own context and
  assumptions proves less than a review done blind.** A review that gets only the
  finished artifact plus the intended reader's role — no build rationale, no "here's
  what I was going for" — is a materially stronger check than the build-time reasoning
  marking its own homework. In this method's own validating run, the fused-node badge
  problem above was caught **only** by a review done this blind way — the build-time
  reasoning that produced the bug did not catch it, because it reasoned from the same
  assumptions that created the bug.

## Minimal worked example

A small, fully fictional app — `com.example.retailapp` — with four partitions from
`data/partitions.json` (fields trimmed to what matters here):

```json
[
  {"prefix": "com/example/retailapp/catalog", "kind": "feature", "class_count": 40},
  {"prefix": "com/example/retailapp/checkout", "kind": "feature", "class_count": 22},
  {"prefix": "com/example/retailapp/loyalty", "kind": "feature", "class_count": 18},
  {"prefix": "com/example/retailapp/infra", "kind": "infra", "class_count": 9}
]
```

`loyalty` is actually two sub-packages fused into one partition by the mechanical
depth-cut (`../../SKILL.md`, "Partitioning"): `loyalty/points` (a simple counter, easy
to port) and `loyalty/tierengine` (an undocumented rules engine deciding tier upgrades,
hard to port). Nothing in `partitions.json` marks this split — it only shows up once
someone reads the source tree.

A tiny `coupling.json` slice (invented counts):

```json
{
  "pairs": [
    {"a": "com/example/retailapp/checkout", "b": "com/example/retailapp/loyalty", "count": 4},
    {"a": "com/example/retailapp/catalog", "b": "com/example/retailapp/checkout", "count": 2}
  ],
  "degree": {
    "com/example/retailapp/checkout": 6,
    "com/example/retailapp/loyalty": 4,
    "com/example/retailapp/catalog": 2,
    "com/example/retailapp/infra": 0
  },
  "isolated_features": ["com/example/retailapp/infra"]
}
```

Phase 2's draft-verdict list — plain text, reviewed **before** anything is painted:

| Partition | Draft verdict | Evidence |
|---|---|---|
| `catalog` | easy | clean repository/datasource split, low coupling (degree 2) |
| `checkout` | hard | WebView payment step, highest coupling in the app (degree 6) |
| `loyalty/points` | easy | simple counter, no legacy quirks found |
| `loyalty/tierengine` | hard | 12-rule legacy tier engine, several undocumented edge cases |
| `infra` | n/a | `infra_platform` bucket, not a port target |

Read this table *before* the skeleton phase and the merge problem is visible for
free: `loyalty/points` and `loyalty/tierengine` both live under the single
`com/example/retailapp/loyalty` partition, so the skeleton phase is about to fuse them
into one box. A badge naively computed from "the loyalty partition's verdict" would
have to pick one of `easy`/`hard` — silently wrong either way. The fix decided here,
before any box is drawn: split `loyalty` into two boxes in the Twin (one per
sub-package), each with its own single-constituent badge, rather than shipping one
box with a badge that can only be half-true.

## Consumer

- **A future agent/session evolving or regenerating the Twin** — for a new APK, or a
  new pass on the same one. What this recipe saves them: re-deriving the four-phase
  ordering from scratch (and the hours lost polishing a skeleton that later moves),
  the render approach (so nobody has to rediscover the headless-screenshot gotcha
  independently), and the merge-badge gotcha (so a fused box doesn't ship a
  one-sided verdict the way it did the first time this method was run for real).
- **The migration committee / architect** reading the *finished* artifact. What it
  helps decide: scope triage — what's genuinely portable native code, what's
  infra/platform noise that doesn't need bespoke migration attention, and where the
  two or three real architectural seams sit. What it deliberately does **not**
  resolve: any open business/product decision that depends on evidence this method's
  reach hasn't reached yet — an authenticated-only surface nobody has walked past
  login, for instance, stays an open callout on the page, not a guess dressed up as a
  verdict. The Twin triages where to look next; it does not pretend to have looked
  everywhere already.
