---
name: council
description: Invoke to consult the kit's index for the Council of Postures — the 6 wired postures (4 in-thread skills, 2 isolated subagents), what each interrogates, when to wear it, the output format (callout), and when to escalate to blind mode (agent epistemic-council). The work lives in each posture; this is the map.
---

# Council of Epistemic Postures

Modes of reasoning you wear on purpose — not tasks. Each one's output is a move on the reasoning, not an artifact, in the **Council callout** (see §Output format below).

## Output format — the Council callout

Every Council intervention — a proactive suggestion ("the council steps in") OR the output of a worn posture — comes out in a **callout**: a bold header + a **code-fence**. The code-fence is the only markdown primitive that renders as a bordered box in the terminal/UI; frames like `★ Insight` (ASCII `─`) render ragged and are **retired** here.

**The council steps in:**
```
∴ <Posture> perceives: <one-line observation>.

  <specific evidence/context — indented, short lines>

  <label>: <the question the posture forces>
```

- Prefix `∴` + the posture's name spelled out (no emoji inside the fence — emoji stays in the surrounding text, if you want it).
- Posture with a Restate Gate (Bohr/Schrödinger/Epicurus/Sagan): the Restate Gate opens the fence (`Original:` / `Reformulation:` / `Divergence:`); the deliberation's map/list follows **outside** the fence (otherwise it becomes a monospace wall).

| Posture | Question | When to wear | Vessel |
|---|---|---|---|
| 🐱 Schrödinger | Which explanations still coexist? | ambiguous diagnosis | skill |
| ⚛️ Bohr | Is the dichotomy false? | decision stuck on "A or B" | skill |
| 🌿 Epicurus | What here is excess? | before calling it done (cuts elements) | skill |
| 🔭 Sagan | Does this matter? At what scale? | before investing effort (altitude) | skill |
| 🧲 Maxwell | How does this propagate? | before touching something coupled | subagent |
| 🐢 Zeno | Where does this break? | validating a solution | subagent |

Invocation: the 4 skills are worn by name in the thread (`/council:bohr`, `/council:sagan`, `/council:epicurus`, `/council:schrodinger`); Maxwell and Zeno are dispatched isolated (this plugin's `maxwell` and `zeno` agents). **Zeno needs the live premises pasted into the dispatch** (see `plugins/council/agents/zeno.md`). The name is identity; the situational trigger lives in each file's `description`.

**Scale of convening:** one posture per decision is the default. Wear a second only when the Restate Gate reveals two genuinely distinct question-types inside the same decision (e.g., an A-or-B that also hides a scope call) — never to reinforce the first posture's verdict. Escalation to blind mode keeps its own criteria (below); more postures is not more rigor — a convened posture that adds no new question-type is noise.

**Automatic layer (optional, reference architecture — not included in this kit):** a `type:"agent"` gatekeeper on Stop (registrable in project settings) can intercept consequential conclusions FROM THE ASSISTANT (a state claim, a diagnosis, "done/validated," a number that becomes a premise) and block closing until the claim is verified by `epistemic-council` (blind mode, executable mandate) and the response revised — marker `∴ council-verified`. In that architecture the user never sees the nudge; they see an already-verified response. Proactive-suggestion hooks only go in once they've proven real use — the promotion bar in `docs/GOVERNANCE.md`, applied to anything advisory.

**Inline devices (in-thread overlays):** the 4 inline skills (`/council:bohr` `/council:schrodinger` `/council:epicurus` `/council:sagan`) open with a **Restate Gate** (step 0, structured output) and close with an **opposition device** in the callout + an **escalation clause** to the isolated subagent `epistemic-council` (blind mode). The devices raise the cost of performing agreement, but they run in the same thread — the real separation only exists at escalation. Memory/recall: `/council:council-log`, `/council:council-recall`.

**Output anti-contamination (ritual):** before delivering a *context-seeding* artifact (handoff / spec / "next session's prompt" / PR description), run it through **blind review** (isolated subagent, without the thread) + a mechanical checklist (no pre-written expected values; neutral framing; points-to-the-source). Not mechanized — see `POSITIONING.md`.

Positioning (the why — what the Council is, what it does NOT promise, and where it hasn't proven it works yet): `POSITIONING.md`.
