# Worker brief — input format

Every worker dispatch is one Agent-tool call (`subagent_type: general-purpose` or a fitting custom agent, Worker tier — default `model: sonnet` per the current personal binding, overridable; concrete model never baked here, see `core:methodology` §Topology) carrying this brief. It is the INPUT side of the dispatch; the OUTPUT side is `core:methodology` §Dispatch contract — referenced here, not restated.

**Context-isolation caveat** (`../SKILL.md` step 4): a kit Agent-tool worker already starts with what `core:methodology` §Dispatch contract gives every subagent — unlike the reference this is adapted from, that includes the CLAUDE.md/memory hierarchy, not a truly empty slate. Write every brief as if it were empty anyway: inputs pasted inline and complete, never "see the conversation above," "the file we discussed," or any other pointer into inherited context the worker cannot be trusted to resolve the same way the orchestrator would.

## Template

```
You are a worker completing ONE subtask of a larger project. This brief is
everything you get for this subtask. No follow-ups are possible.

SUBTASK: <one-line goal>
INPUTS: <everything needed, inline and complete>
ACCEPTANCE CRITERIA (the result fails if any fail):
1. <criterion>
2. <criterion>
3. <criterion>
OUTPUT FORMAT: <exact structure, length, style>

Rules: do only the subtask, no scope expansion, no editorializing. If an input
is missing or contradictory, write INPUT GAP plus one line naming it at the
top, then proceed with what you have. Return only the deliverable, no preamble.
```

When filling in OUTPUT FORMAT for a real dispatch, shape it to what Verify and
Synthesize (`../SKILL.md` steps 5–6) need — the output contract itself (verdict,
evidence, `file:line` refs, STOP on a pending decision) is `core:methodology`
§Dispatch contract, not restated here.

## Redispatch rule

When a result comes back FIX (`../SKILL.md` step 5), send a new brief that quotes the failed criterion and names the specific failure. Never reply to the prior dispatch — every dispatch is fresh, addressed as if to a worker with no memory of the earlier attempt.
