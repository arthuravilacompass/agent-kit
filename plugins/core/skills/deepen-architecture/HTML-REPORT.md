# deepen-architecture — HTML report format

The review renders as a single self-contained HTML file in the OS temp directory. Tailwind and Mermaid come from CDNs. Mermaid handles graph-shaped diagrams reliably; hand-built divs and inline SVG handle the editorial visuals (mass diagrams, cross-sections). Mix the two — leaning on Mermaid for everything looks generic.

Adapted from the `improve-codebase-architecture` skill (Matt Pocock, `mattpocock/skills`, MIT). Glossary references point at `core:codebase-design`, this kit's own vocabulary skill.

## Scaffold

```html
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <title>Architecture review — {{repo name}}</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script type="module">
      import mermaid from "https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.esm.min.mjs";
      mermaid.initialize({ startOnLoad: true, theme: "neutral", securityLevel: "loose" });
    </script>
    <style>
      /* small custom layer for what Tailwind doesn't cover cleanly:
         dashed seam lines, hand-drawn-feeling arrow heads, etc. */
      .seam { stroke-dasharray: 4 4; }
      .leak { stroke: #dc2626; }
      .deep { background: linear-gradient(135deg, #0f172a, #1e293b); }
    </style>
  </head>
  <body class="bg-stone-50 text-slate-900 font-sans">
    <main class="max-w-5xl mx-auto px-6 py-12 space-y-12">
      <header>...</header>
      <section id="candidates" class="space-y-10">...</section>
      <section id="top-recommendation">...</section>
    </main>
  </body>
</html>
```

Both CDNs are load-time network dependencies. On a machine that can't reach them the report degrades to unstyled HTML with raw Mermaid source — say so when you hand over the path if the environment is known to be offline.

## Header

Repo name, date, and a compact legend: solid box = module, dashed line = seam, red arrow = leakage, thick dark box = deep module. No introduction paragraph — straight into the candidates.

## Candidate card

The diagrams carry the weight. Prose is sparse, plain, and uses `core:codebase-design`'s glossary terms without ceremony.

Each candidate is one `<article>`:

- **Title** — short, names the deepening (e.g. "Collapse the Order intake pipeline").
- **Badge row** — recommendation strength (`Strong` = emerald, `Worth exploring` = amber, `Speculative` = slate), plus a tag for the dependency category (`in-process`, `local-substitutable`, `ports & adapters`, `mock` — `core:codebase-design`'s `DEEPENING.md`).
- **Files** — monospaced list with `file:line` citations, `font-mono text-sm`.
- **Before / After diagram** — the centrepiece. Two columns, side by side.
- **Problem** — one sentence. What hurts.
- **Solution** — one sentence. What changes.
- **Wins** — bullets, ≤6 words each. "Tests hit one interface", "Pricing logic stops leaking", "Delete 4 shallow wrappers".
- **ADR callout** (if applicable) — one line in an amber-tinted box.

No paragraphs of explanation. If the diagram needs a paragraph to be understood, redraw the diagram.

## Diagram patterns

Pick what fits the candidate. Mix them — every diagram looking the same defeats the point.

### Mermaid graph (the workhorse for dependencies / call flow)

Use a `flowchart` or `graph` when the point is "X calls Y calls Z, and look at the mess". Wrap it in a Tailwind card so it doesn't feel parachuted in. Use `classDef` to color leakage edges red and the deep module dark. Sequence diagrams work well for "before: 6 round-trips; after: 1".

```html
<div class="rounded-lg border border-slate-200 bg-white p-4">
  <pre class="mermaid">
    flowchart LR
      A[OrderHandler] --> B[OrderValidator]
      B --> C[OrderRepo]
      C -.leak.-> D[PricingClient]
      classDef leak stroke:#dc2626,stroke-width:2px;
      class C,D leak
  </pre>
</div>
```

### Hand-built boxes-and-arrows (when Mermaid's layout fights you)

Modules as `<div>`s with borders and labels; arrows as inline SVG `<line>`/`<path>` positioned absolutely over a relative container. Reach for this when the "after" should read as one thick-bordered deep module with greyed-out internals — Mermaid won't render that with the right weight.

### Cross-section (layered shallowness)

Stack horizontal bands (`h-12 border-l-4`) for the layers a call passes through. Before: 6 thin layers each doing nothing. After: 1 thick band labelled with the consolidated responsibility.

### Mass diagram ("interface as wide as implementation")

Two rectangles per module — interface surface area, implementation. Before: the interface rectangle nearly as tall as the implementation (shallow). After: short interface, tall implementation (deep).

### Call-graph collapse

Before: a tree of calls as nested boxes. After: the same tree collapsed into one box, the now-internal calls faded inside it.

## Style guidance

- Lean editorial, not corporate dashboard. Generous whitespace. Serif headings (`font-serif`) work well with stone/slate.
- Color sparingly: one accent (emerald or indigo), red for leakage, amber for warnings.
- Keep diagrams ~320px tall so before/after sits side by side without scrolling.
- `text-xs uppercase tracking-wider` for module labels inside diagrams — schematic, not UI.
- The only scripts are the Tailwind CDN and the Mermaid ESM import. Otherwise static: no app code, no interactivity beyond Mermaid's own rendering.

## Top recommendation section

One larger card. Candidate name, one sentence on why, anchor link to its card. That's it.

## Tone

Plain English, concise — architectural nouns and verbs straight from `core:codebase-design`. Concision is not an excuse to drift.

**Use exactly:** module, interface, implementation, depth, deep, shallow, seam, adapter, leverage, locality.

**Never substitute:** component, service, unit (for module) · API, signature (for interface) · boundary (for seam) · layer, wrapper (for module, when you mean module).

No hedging, no throat-clearing, no "it's worth noting that…". If a sentence could be a bullet, make it a bullet. If a bullet could be cut, cut it. If a term isn't in the glossary, reach for one that is before inventing a new one.
