# The Cognitive Sequence — the method above the lab

> **What this is.** The reusable answer to one question: *given a decompiled APK, what do you actually do with it?* It sits **above** the lab's mechanical pipeline (`../SKILL.md`) and the report method (`method.md`): those are *how* you extract and consolidate; this is the **decision sequence** that governs them. It applies to any target, not one app.
>
> The sequence runs in **two tempos**, not a flat list: **Foundation** runs once per APK — the app-level substrate every feature draws on; the **per-feature loop** runs once per feature, *synthesizing over that feature's slice* of the Foundation data, never re-extracting.
>
> It is still the seam of two half-answers, but the seam moved. It used to split between step ranges (front vs. back); now it is a single hinge **inside** the loop, at the **intent** step. Everything up to and including state machines — Foundation, route, contract, persistence, state machines — is **description** (what the app *is*). Intent is where description turns into **prescription** (what *becomes* a requirement); dossier and the anti-regression shield are prescription's continuation. Neither half alone answers the question.

## The frame that governs everything

An APK is **evidence to interrogate toward a decision, not code to read**. RE is **capture of topology + behavior** (assembling data + requirements), not syntax translation (Java→Dart). The **unit of the method** is a feature's migration task plus the leader↔dev support around it. **Deliverables are at the center**; the epistemic doctrine (origin/confidence/intent/reach) is a **stamp on each deliverable, not a station**. The output is not translated code — it is a **decidable backlog**, where every finding carries `origin`, `confidence`, and an `intent`. **Legacy behavior ≠ approved requirement.** RE runs **alongside** implementation, feature by feature — it does not "finish" before the first widget.

## Foundation — runs once per APK

**Decompile + classify, then the reach-gate verdict.** Before anything else: is the target bespoke, or a reskinned white-label platform? Obfuscation level, build type, third-party SDK islands, the legal question of reverse-engineering a *licensed* platform — the package structure answers before any rule does. *(A one-file skin over a vendor platform makes "port the skin" empty — one question can remap the whole project.)* Decompile and classify run first and produce the `unclassifiable` ratio; **the reach gate is a verdict over that output, not a literal step ahead of extraction** — it fires as soon as classify lands, before the synthesis investment downstream. It reads obfuscation (the `unclassifiable` ratio), tamper/pinning signal, and load-bearing logic outside static reach, and returns **normal / degraded / no-go**. A `no-go` stops the run before the loop ever starts (`telecorp`, 96.9% unclassifiable, is the ballast). This measurement is app-level, taken once — the per-feature routing below (loop step 1) is a separate, per-feature question.

**Map the perimeter, find the module graph and the seam.** The manifest gives the skeleton, but the native-screen inventory can **lie** about where the product actually lives — the money flows may not be native screens at all, but WebView. *(The real move is finding where the product is, not counting screens.)* Out of the graph comes the **true migration unit**: not "N screens," but the thing that, if you don't reproduce it, kills everything downstream — the critical path. *(A multi-capability JS bridge whose absence kills the WebView tabs: the unit was the seam, not the screens.)* The seam is load-bearing for everything that follows: it is what "Structuring the backlog by risk, not by screen" (below) sequences epics around, and what the WebView branch (below) re-points to when the product lives behind a WebView. **Consumer:** the leader, who sequences epics by risk from it, and dev.

**Map the transport layer, not just the screen surface.** The seam above answers *native vs. web*; it does **not** answer *how config and content actually arrive at runtime*. A modern white-label app can be **server-driven** over its own transport — a persistent WebSocket / JSON-RPC channel that pushes the **shell itself** (tabs, bottom-navbar, navigation modes, login config) and streams per-screen content — a substrate that is neither a native screen, nor the JS bridge, nor WebView HTML. *(On one real run, a `wss://…/<transport>` JSON-RPC client — a dozen-plus classes present in the decompile — drove the entire tab bar and the login handshake, yet the static triage never surfaced it: it is not a screen to inventory, nor an endpoint literal to grep, nor the bridge.)* Two moves the method now forces. **(1) Transport as a first-class Foundation target, with server-driven shell config as its own extraction category** — tabs/nav/login pushed from the server are knowledge to extract, distinct from screen and from data contract; the port must *render* that config, not hardcode it. **(2) Confront the static map with a dynamic boot-trace as a completeness check** — because a whole transport subsystem can sit in the bytecode *unsurfaced* by static triage, the dynamic pass is not only a WebView-contract oracle (below); it is a **completeness audit of the static perimeter itself**: what connects and speaks on boot points straight back at the classes the triage under-weighted. Session attachment for such a transport is a place to look, not assume: it may be an in-band handshake (a first authenticated call carrying the token as a field) rather than a header on the connection — read it, don't guess it.

**Cheap static harvest (block #5)** — extraction script built (`extract_harvest.py`, selftest-passing, corpus-validated); synthesis recipe: `references/deliverables/harvest.md`. Facts that survive intact in the bytecode, cheap because they cost nothing beyond what decompile already did, roughly ordered by extraction cost:
- **BuildConfig** — base URL per env, API keys, compiled feature flags (a real secret found here is a security action: rotate it).
- **network-security-config.xml** — trusted domains / cleartext / pinning: who the BFF trusts.
- **DI modules** (Dagger/Hilt) — the real architectural boundary, a second viewpoint on the module split.
- **Crash-reporting `setCustomKey`** — context logged on every crash points at the entities the team considers sensitive.
- **Performance baseline** — cold start / frame / memory: the non-regression contract for the port.
- **`res/values` → design tokens.** Colors, dims, styles map to `ThemeData`. **Token resolution:** native UI *layout* is built fresh — the legacy is flow-reference only (see "Structuring the backlog," below) — but the *tokens* themselves ARE recoverable. "Fresh" applies to the layout, not to the tokens.
- **WorkManager + push/FCM** — background sync and push deep-links surface paths manual navigation never reveals.
- **Remote-config keys + assumed fallbacks** — partial: static gives the keys and the default branch, not the value actually served.
- **Dead vs. live (`re-deadcode`)** — dead code, a feature behind an off-flag, and a staging endpoint left in the beta are three distinct targets, not one.
- **`criticidade` / severity** on a finding (e.g., "touches billing") — today implicit in the risk epics below, not yet an axis in the findings schema.
- (Outside the APK: store history and reviews — a roadmap proxy and what users actually notice.)

**Anchor everything.** `file:line`, or an explicit "out of reach." This is the discipline that separates fact from anchored hallucination — it does not stop at Foundation. Every deliverable the loop produces below carries the same rule as its own stamp (OpenAPI's 🟢 literal / ⬜ runtime; Mermaid's 🟢/🟡/⬜): unanchored is a labeled state, never a guess dressed as a citation.

## Per-feature loop — runs once per feature

**Feature ≠ partition — `spec pendente`.** A partition is package-prefix and mechanical (a real app yields ~1000+); a *migration feature* usually crosses several partitions, and the motivating case — a money flow living entirely in a WebView — has a near-empty native partition and an empty endpoint slice. The feature→slice join is not solved; name it as an open design gap, don't silently equate the two. This is also why the loop carries a **per-route variant**: native routes synthesize over the endpoint/graph slice Foundation already extracted; a WebView route synthesizes from a Fetch-tap against the Flutter host used as harness (the WebView branch, below) — **not** a Foundation slice at all.

Each of the seven steps below is a **synthesis over that feature's slice of Foundation's data**, not a re-extraction — the extraction ran once, in Foundation.

1. **Route** → native | WebView | blind. Per-feature, not app-level: the gate's obfuscation measure above was taken once for the whole app; this is a separate call for each feature (money flows route to WebView even when the native line for the same app is clean). `blind` means this feature has no static reach at all — mark the bounded blind spot, don't invent a bespoke pipeline for it.
2. **Network contract → OpenAPI/Swagger v3 `.yaml`** — spec'd (recipe exists), not yet exercised on a real run. Native: from the Retrofit/OkHttp calls in the slice. WebView: from the Fetch-tap (see the WebView branch). Static gives the SHAPE; dynamic gives VALUES and the ERROR contract — what the method cannot see here is a **bounded blind spot**, marked, never filled by assumption. Stamped 🟢 literal / ⬜ runtime. **Consumer:** dev, via `openapi_generator` → DTOs (Freezed) + a Dio client.
3. **Persistence & crypto matrix → data dictionary** — spec'd (recipe exists), not yet exercised on a real run. Room `@Entity`/`@Dao`, SharedPreferences, KeyStore, mapped to relational/NoSQL/secure_storage + expiration + an LGPD flag. **Consumer:** dev, and the leader for the security read.
4. **State machines + rule topology → Mermaid `stateDiagram-v2` + truth tables** — spec'd (recipe exists), not yet exercised on a real run. States, transitions, and the micro-details that make users say "the new one got worse" (debounce/timeout/retry/cache-fallback). This is also where the rule gets recovered from where it actually *lives* — native: ViewModel/Presenter/UseCase; WebView: the SPA + backend, outside the bytecode (see the WebView branch). **Consumer:** dev (BLoC/Riverpod), and the PO.
5. **Intent → `needs-decision → preserve | fix | redesign | remove`.** The description→prescription hinge: everything through state machines above described what the app *is*; intent is the first step that decides what it *should* be. A **product** decision, not a technical one, and it needs a named owner — without one, the finding stays `needs-decision`, an honest state, not a blank left for convenience. It comes **before** the shield: there is no anti-regression test for a rule you are about to remove or redesign. (`redesign` = the team diverges from legacy *on purpose*, new intent and new implementation; distinct from `fix`, which keeps the intent and changes the implementation, and from `remove`, which drops it.) A finding only reaches this gate once its `confidence` has climbed the trajectory `observed → cross-validated → business-ratified` — confidence is a trajectory, not an origin stamp, and a finding still stuck at `observed`/`blind` is not yet ready for the decision.
6. **Feature dossier → decided backlog.** Findings aggregate per feature into a dossier — screens + contracts + rules + telemetry in one record, `status: in-triage | ready-for-us`. The US is born only from a `ready-for-us` dossier, never 1:1 from the raw catalog (one dossier usually becomes 3–5 independently testable stories; a single giant US means triage is incomplete). The dossier is descriptive-aggregated (what exists, decision pending); the US is prescriptive (what should exist). **Consumer:** dev and PO, in triage.
7. **Anti-regression shield → TDD stubs (`_test.dart`)** — spec'd (recipe exists), not yet exercised on a real run. Group/test skeletons of the *decided* rule topology, no implementation — the DoD. Only for rules that were kept or fixed; a rule marked `remove`/`redesign` gets no stub, by construction of step 5. **Consumer:** dev, and hooks/CI.

**Re-running the loop.** RE and implementation share the same loop, feature by feature: re-extract on the new build, diff lightly, and re-decide — because the target moves. This is iterative, not a merge-keyed persistent-catalog state machine: there is no cross-run dedup or cross-partition reconciliation living in the method. The diff stays lightweight on purpose.

## The WebView branch — a second RE target, gated

When a flow lives behind a WebView **and the target is to nativize** (not re-host), RE does not stop at `blind`. The **same sequence re-points** to the WebView, with a different artifact and toolset (not decompiled DEX) — this feeds the loop's contract and state-machine steps above from a different source than the Foundation slice:

- **UI** — reconstruct from the running SPA (screenshots/DOM) + the vendor **design system**, if one is partially shipped in the APK (a known/documented DS yields recoverable tokens/components, not from scratch).
- **Client logic** — the SPA is JS, readable in devtools even minified (source maps if present): validations, state machines, formatting.
- **Backend contract** — tap the network handler (Fetch) + a proxy. The seam ports, so you host the SPA in the **Flutter host you are already building** and observe what it calls — the host becomes the **extraction harness**, without depending on the tamper-protected APK for the client side.
- `confidence` still applies: the WebView rule is born `blind` (static APK can't see it), rises to `observed` (read the JS), `cross-validated` (captured the traffic), `business-ratified` (PO).

**Gated by the same walls (honest ceiling of this branch):**

1. Backend traffic hits the **same wall** — hosting the SPA outside the attested APK gives the client side (JS, which bridge-calls, the shape), but the **real backend responses** may be refused by the same identity/tamper attestation as the go/no-go gate. Not a separate easy win — gated by the same gate.
2. The **vendor spec** matters more, then: for a licensed platform, obtaining the vendor's SPA source / API docs beats reversing minified JS *and* bypasses the wall.
3. **Moving target** — the SPA is updated by the vendor; extraction must be live (re-capture per release), which is exactly why the loop re-runs (above) rather than treating any one capture as final.

> **Caveat (do not launder).** This branch imports the two walls into the JS layer: it assumes the SPA runs outside the attested APK (the backend, tied to the original identity, may refuse it — the same wall) and that minified JS is readable (without a source map it is as opaque as obfuscated bytecode). The branch is a real second RE target, not a free reach.

## Structuring the backlog by risk, not by screen

Migrating screen-by-screen fails; value (ROI) comes from **mitigating the biggest risk first**. Two orderings govern this, and they are **not the same axis**:

- **Cost-of-extraction** — what to harvest first: BuildConfig + contracts → telemetry → design tokens → dynamic → outside-APK. This governs the Foundation harvest order, above.
- **Risk-of-delivery** — what to ship first: Foundation & Contracts → Auth & Session → high-friction revenue domains → UI/design system. This governs the backlog's epic order, below.

Epics organize by the risk/value dimension, not screen order:

- **Foundation & Contracts (core)** — DTOs, interceptors, local crypto, tokens. Unblocks all parallel development — the team stops guessing what the API expects (this is the loop's contract step, before UI).
- **Auth & Session** — refresh token, biometrics, session timeout. Mitigates the security risk.
- **High-friction domains** — revenue-critical complex rules (financial calculation, eligibility, gating). Protects revenue (keeps the migration from shipping a billing bug).
- **UI/UX design system** — native UI *layout* is **not** reverse-engineered: it is built fresh, the legacy is flow-reference only. Its *tokens* are the one recoverable part (see the block-#5 harvest, above) — "fresh" applies to layout, not tokens. Exception: a **WebView/SPA** UI, being the product itself, *is* reconstructed (the second RE target, above).

Biggest-risk-first is Foundation's seam (the true migration unit = the critical path) applied to delivery order.

## Provenance of this sequence

This is the seam of two half-answers, now run as two tempos instead of two step ranges: Foundation (once per APK) and the per-feature loop, with the description→prescription hinge folded to a single step — intent — inside the loop. The reusable method is their seam; the mechanical pipeline (`../SKILL.md`) and the report method (`method.md`) are this sequence turned into structure.
