# OVERVIEW — apk-archaeology run {{ run.id }}

**Target:** `{{ run.package }}` v{{ run.version }} · sha256 `{{ run.sha256 }}`
**Run:** {{ run.mode }} · tooling: {{ run.tooling }}

---

## BLUF

<!-- AGENT:START bluf -->
Write the Q1-Q4 narrative here (agent-synthesized, per design §3 -- NOT
script-filled; the render layer only fills the deterministic slice below):

1. Is a native -> Flutter port viable? (verdict.feasibility / .one_line / .confidence)
2. What is this app, really? (what_it_is.nature / .build_signal / .obfuscated_island.note)
3. What is the shape of the migration -- where does the cost live? (migration_shape.* -- the four buckets: port_native, stays_webview, bridge_to_reimplement, infra_platform)
4. What can the team now decide, and what is still unknown? (blind_spots, next_steps, caveats)
<!-- AGENT:END bluf -->

---

## Metrics

- Bridge capabilities: {{ metrics.bridge_capabilities.value }} across {{ metrics.bridge_capabilities.domains }} domains
- Partitions: {{ metrics.partitions.total }} total ({{ metrics.partitions.feature }} feature / {{ metrics.partitions.infra }} infra)
- Endpoints: {{ metrics.endpoints.total }}
- Graph: {{ metrics.graph.nodes }} nodes / {{ metrics.graph.edges }} edges ({{ metrics.graph.kind }}), largest component {{ metrics.graph.largest_component }}
- Bridge-pilot handlers: {{ metrics.bridge_pilot_handlers.value }}

---

## Manifest

| Path | Role | Status |
|------|------|--------|
{{# manifest }}| `{{ key }}` | {{ role }} | {{ status }} |
{{/ manifest }}
