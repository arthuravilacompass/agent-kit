---
name: bug-report
description: Investigate a bug and produce a report with verified citations — deterministic gate (validate_citations --gate) + semantic verifier in a fresh context. Use when investigating/reporting a bug where asserting code behavior without reading the source is the risk.
disable-model-invocation: true
---

# /bug-report -- Bug Report with Verified Citations

Investigates a bug and **only finalizes** the report with findings whose `file:line` citation (1) overlaps code actually read in this session **and** (2) is semantically supported by the code. This is the path with a **hard gate** — because a bug report with a fabricated citation (e.g., a route that doesn't exist in the code, invented by the model) is a known failure mode in LLM-generated reports without this gate.

**Dependency:** this skill assumes the existence of the verified-citation mechanism — a read-ledger that logs every `Read`/`Grep` in the session + a `validate_citations.py --gate` script that rejects a `tool-output` finding citing code that wasn't read. In this kit the mechanism is already wired into the same plugin (`plugins/core/scripts/validate_citations.py`, fed by `plugins/core/hooks/read-ledger.sh`) — the commands below use `${CLAUDE_PLUGIN_ROOT}` and resolve without adjustment. If porting this skill alone elsewhere without that mechanism, it needs it before it works.

## Usage

```
/core:bug-report <bug description / ticket>
```

## Steps

1. **Scope** — symptom, repro steps, suspected area. Apply the project's bugfix-principles questions (contract violated? absent≠empty? state lifecycle? implicit invariant?), if the project has that rule.

2. **Investigate** — Read/Grep the relevant code. **Every Read populates the session's read-ledger**. Do not conclude about behavior without reading the source.

3. **Structured findings** — assemble JSON:
   ```json
   [{ "claim": "...", "epistemicSource": "tool-output",
      "evidence": { "file": "...", "lineStart": N, "lineEnd": M, "quote": "..." } }]
   ```
   `epistemicSource`: `tool-output` (claim about code read) · `inference` · `absence` · `external`. Only `tool-output` is gated.

4. **Deterministic (hard) gate** —
   ```
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/validate_citations.py" --session <current-session-id> --gate --findings <file>
   ```
   Pass explicit `--session` (concurrent sessions). **Exit 2** = there's a `tool-output` finding citing unread code (location fabrication) → **do NOT finalize**; go back to step 2, actually read the code or fix the finding. Only proceed on exit 0.

5. **Semantic verifier (fresh context)** — catches what the deterministic gate doesn't: a claim that cites **real** code but **misreads** it. Dispatch a subagent in a clean context, with this prompt, passing the findings that survived step 4:

   > You are a skeptical citation verifier. For EACH claim below, in a fresh context: (1) Read the EXACT range `file:lineStart-lineEnd`; read a few surrounding lines if needed. (2) Judge whether the code actually read **supports** the claim — `supported=true` only if the code implies what the claim asserts; `false` if it contradicts, doesn't mention, only partially supports (overreach), or the range is empty. (3) Skeptical default: when in doubt, `false`. Do NOT trust the provided `quote` — re-read the file. Scope: only a support verdict; do not review style or suggest a fix. Output per claim: `{ "claim", "file", "supported": bool, "confidence": "high|medium|low", "reason": "<citing what the code actually does>" }`.

   Findings with `supported=false` → "⚠️ Citation does not support the claim" section, **not** asserted as root cause.

6. **Report** — only findings `verified` (step 4) **and** `supported` (step 5):
   ```
   ## Bug: <title>
   **Symptom**: <...>  ·  **Repro**: <...>
   **Root cause**: <claim> — `<file>:<lineStart>-<lineEnd>`
   **Evidence**: <quote from the actual code>
   **Proposed fix**: <at the source, not the consequence>
   ### ⚠️ Citation does not support (<count>)   — findings refuted by one of the gates
   ```

## Important

- **Hard gate here** (≠ a looser review that just annotates) — the cost of a false bug report justifies blocking.
- **Fix at the source, never the consequence**; state that survives has a named lifecycle.
- Do not post to an external system (tracker/board) without explicit request.
