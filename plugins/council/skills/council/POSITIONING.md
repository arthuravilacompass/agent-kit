# Council of Epistemic Postures — Positioning

## Before anything: the status of what follows

What follows is a **strong hypothesis**, not a result. It rests on HCI literature about overreliance (established in other contexts, extrapolated to this one) and on an internal trial with **N=1 per posture**. The claims about *mechanism* — that the Council forces a mode of reasoning, that the names route distinct procedures — are declared bets, not measured facts. Read the rest with that in mind. A manifesto about epistemic calibration that presented itself as proof would be the first thing to fail its own test.

## The thing it is

The Council is designed to operate as a **cognitive forcing function**. The idea, plainly: a fluent, fast, agreeable AI makes it easy to accept the first plausible answer and reinforce the framing you already brought. The Council exists to create the conditions for a second look at the points where accepting cheaply turns out expensive — *conditions*, not a guarantee: invoking a posture can itself be an automatic act. The deliberation isn't in calling the name; it's in the procedure the name triggers.

The formulation that drives it: among everything the AI hands you, it **is the only element whose declared purpose is to resist your own framing.** Everything else an assistant produces — code, review, breakdown — is, by construction, in service of moving you forward. The Council is in service of making you stop and look again. That asymmetry is the product. (A human reviewer, a failing test, a linter also resist your framing — which is why the claim is restricted to the AI-side and to *primary purpose*: none of those other pieces exists for this.)

It isn't a spec, isn't a task, isn't a pipeline. It's six **modes of reasoning** worn on purpose. Each one's output is **a move on your reasoning** — a reframe, a hypothesis kept alive, a propagation point you hadn't seen — never one more artifact.

## Why not "more perspectives"

Almost every toolkit of this kind sells the same thing: *better decisions through diversity of perspectives.* The Council refuses that on purpose. It sells **preservation of your judgment** — and is explicit that it does not directly increase the rate of correct decisions. What it tries to reduce is the rate of *non-deliberated* decisions; whether that improves the outcome depends on the quality of your judgment, which it preserves but does not replace.

The target problem isn't lack of information. It's an overreliance pattern documented in HCI: in the presence of a fluent system, the operator tends to trust quickly and interrogate less, and trust in the system grows without decision quality keeping pace. More trust in the AI is **not** monotonically good. (The literature measured this mostly in automation with a short feedback loop; transferring the effect to software decisions with the Council as the implementation is a plausible extrapolation, not an applied fact. And the slide-to-quick-answer is just one of the mechanisms — *automation bias* and skill atrophy are adjacent and aren't resolved the same way; they're outside this claim.)

## The nuance that cannot be erased

This is where most systems lie to themselves.

**Anti-sycophancy does not come from naming the posture.** The same Claude, in the same thread where it had been agreeing, is capable of *performing* skepticism — wearing "Zeno," sounding adversarial, and still bending everything toward the *lean* you showed. Calling the posture does not produce the property.

The property comes from **structural separation**: isolated context, adversarial prompt, anonymized review — the reasoning happens without seeing which way you were leaning.

- This was **demonstrated in the trial (N=1) in the two isolated subagents, Maxwell and Zeno** — in the structural domain. They run outside the thread, receive only the problem, and found things the thread wouldn't have asked for: Maxwell, a consumer reading the coordinator directly (breadth); Zeno, a one-frame window with inconsistent state (time), with no overlap with the default pass. N=1 shows that the separation produced *different* coverage — it doesn't prove it produces *correct* coverage in general, and the advantage may shrink on decisions that depend on the thread's semantic context (naming, product), where isolation becomes a disadvantage. The separation reduces the thread's context bias, not the base model's training-distribution bias.
- In the four inline overlays (Schrödinger, Bohr, Epicurus, Sagan) **there is no structural separation** — only disposition. **V1 materialized the in-thread devices**: a *Restate Gate* (step 0, YES/NO divergence) and the mandatory *steelman* of the opposite side in the callout. They raise the cost of performing agreement — but they run in the same thread that saw the *lean*, so they remain **disposition, not guarantee**. The real structural separation didn't come from a built-in "anonymized review" (cut in V1); it came from the **escalation clause** to the isolated subagent `epistemic-council` (blind mode). Without escalating, the overlay is a good disposition; the adversarial property is only structural outside the thread.

A manifesto about anti-sycophancy that pretended its overlays were already adversarial would itself be sycophantic. V1 honors that: the overlays gained devices that raise the cost, but only the isolated escalation claims the property. A project of origin went as far as designing a phased validation flow (mechanical + retrospective-with-stakes + isolated A/B) that refuses to hand out an accuracy score — if you're going to reproduce that design, design it again in the new project's context rather than inherit the old record.

## The bet on identity

The name — Bohr, Maxwell, Zeno — **is not cosmetic: it is the Council's assumed position.** But here is the honest order. The embodiment at *inference-time* (the model "wearing" Bohr right now) is a **declared extrapolation** from what's observed at *training-time* — plausible, not verified by ablation. *If* it holds, each name routes to a distinct interrogation and procedure (persona vectors select *how* the problem is attacked), and that separates the Council from the dominant "role = task" pattern, where the persona is decoration over the same prompt. The rival hypothesis hasn't been ruled out: the effect might come from training associations with the characters, not from the procedure — in which case the property is specific to the model used, not transferable. Swapping "Schrödinger" for "Superposition Posture" and comparing the output is the test that hasn't run yet.

What is **FACT** and what is **BET**:

- **Demonstrated (N=1):** structural separation produces differentiated coverage *to the extent of the separation itself* — in the subagents, in the structural domain.
- **Grounded in literature (extrapolated):** forcing functions reduce overreliance in System-1; transferring that to this workflow is a plausible bet, not measured here.
- **Fact (problem, not solution):** trust calibration in AI is a real problem. That *this* design recalibrates that trust is the bet.
- **BET (not measured):** that wearing the postures preserves *epistemic sovereignty* — your capacity to keep asking good questions — and that there's a second-order effect where you *internalize* the postures and interrogate better without the tooling. Plausible by analogy with the metacognition and cognitive-scaffolding literature; no direct measurement in this context. It will not be presented as more than a bet.

## Authority, trigger, client

**Authority: advisory only.** I offer, I don't decide. Never blocks, never demands, never holds up your commit. Preserving your judgment and then hijacking it would contradict the thesis itself.

**Trigger:** decisions with **high cost of reversal**, **pre-commit** — shared API contract, persisted-state change, a hard-to-undo merge. And, equally, when the reversal cost is **uncertain or underestimated** — because then System-2 hasn't been activated yet and the forcing function has more work to do. **Silence** on mechanical work for an already-clear decision: a forcing function that always fires becomes noise and teaches itself to be ignored.

**Client:** solo, opt-in. Written first for your own use. Shareable with the squad later — only by explicit opt-in, never imposed on the flow of someone who didn't ask for it.

## Anti-contamination of AI output (ritual)

The Council keeps the **dev's decisions**, not the **AI's outputs**. But the AI's output silently biases the next step when it travels into a context that has no way to check it — a **handoff, session summary, "next session's prompt," spec handed to an implementer, PR description**. There, the AI's framing becomes the next executor's premise without review. It's the gap that *defines* the gap: the Council doesn't catch it, the user does.

**Ritual (not mechanized — disposition, measure before gating):** before delivering an artifact of that *context-seeding* class, run it through **blind review** — an isolated subagent (`epistemic-council` / an exploration equivalent) that receives only the verification instruction, **without the thread or the framing**. Self-check in the same thread = disposition, not guarantee (the same failure as the inline overlays).

**Mechanical checklist** (verifiable without semantic reading): (1) no pre-written expected values; (2) neutral framing; (3) points-to-the-source instead of re-narrating conclusions.

Why a ritual and not a hook: it's the Council's most honest and verifiable *dev-side* gain ("the AI stops silently biasing the next step"), but mechanizing detection of the *context-seeding* class without semantic reading is uncertain — deferred until the ritual proves it pays off. Practiced by hand in a project of origin (blind-subagent validation; clean). Detail and the open decision live in that project of origin's internal notes, not included here.

## Post-audit update (findings from a prior validation)

An adversarial validation cycle (multi-agent workflow) + an audit of the mechanism on disk, run in a project of origin, shifted the framing like this:

- **AI-side vs. dev-side (the central finding).** The System-2 friction that V1 manufactures is executed **almost entirely on the AI's side**, which deliberates and hands over the finished result. The gain that actually accrues to the **developer** today is a *more lucid output to consume*, not a *more lucid developer*. "Differentiated coverage" and "interrupting System-1" are solid **AI-side** gains — not the dev's epistemic sovereignty. Separating the two explicitly is the pitch correction.
- **It isn't "multiplicative."** The combined gain is a **conditional interaction** whose sign depends on [decision criticality] × [friction calibration] × [real engagement] — it can be zero or negative (poorly-calibrated friction degrades throughput; one of the effects hypothesized in the reference literature wasn't supported). Nothing holds it up as an always-positive product.
- **2nd order = permanent debt** (previously: "unmeasured bet"). Internalization is **structurally impossible to emerge** in the short horizon without (1) active practice, (2) structured fading, (3) outcome feedback, (4) multi-week density — and silence-on-the-mechanical vs. density-of-practice are incompatible without a **separate practice mode** that V1 doesn't have. Logged as permanent debt, not a roadmap property.
- **Confirmed on disk (in a project of origin):** the 3 blind subagents did in fact exist (real anti-sycophancy separation, but opt-in/rare). A local episodic corpus was seeded with real cases from the trial — it stopped being theater as *recall* (returns analogues and displays outcome). But the **automatic outcome producer was still absent by choice**: recall doesn't rank by outcome, so there's no automatic calibration loop — wiring that into merge was deferred (measure-later).

---

The trial measured six postures; five paid off the cost. Epicurus ended up under-measured — it might have been an accident of the target problem (an already-lean design; re-test on a bloated one), it might be a structural limitation of the posture (cutting the excess may require a value model that only Sagan supplies). Both hypotheses remain open. N=1 per posture gives direction, not license. The Council is a strong hypothesis about how to keep a human lucid next to a persuasive AI — and it's honest enough to say where it hasn't proven it works yet.
