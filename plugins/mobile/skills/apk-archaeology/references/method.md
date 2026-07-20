# From Extraction to Backlog — Method Reference (provisional)

> **STATUS: provisional — refined once.** First validated on ONE public app (WordPress
> for Android 26.9, non-obfuscated) at ~one-epic depth; then **refined on a second, real
> client run**. That run did not graduate the method (n=1 real; the ≥2× recurrence bar of
> the design doc is not met) — it **measured the hard walls without crossing them**:
> obfuscation measured to a hard `no-go` on one build (`telecorp`, 96.9% unclassifiable,
> no graph/backlog), and on a non-obfuscated client build the reach limit showed up as
> *readable ≠ reachable* (backend contract assembled at runtime, outside the bytecode;
> the dynamic pass unobtained via an install failure). The frontier is now **evidenced,
> not just anticipated** — but not crossed. Generalization to a fully obfuscated /
> server-driven run pushed *through* to synthesis is still NOT demonstrated — see "Not
> yet validated" below.
>
> Foundation (decompile → classify/reach-gate → endpoints → graph → persistence →
> harvest) + the per-feature loop lives in `../SKILL.md` and is **not restated
> here** — this reference covers the layer between the pipeline's consolidated
> output and an agile backlog draft. Keeping a single source for the pipeline is
> deliberate: a duplicated process description was already caught drifting from
> the real scripts once.

## The cognitive sequence — start here

The decision sequence that governs this whole reference — *given a decompiled APK, what do you actually do with it?* — lives in **`cognitive-sequence.md`**. It is the method **above** the lab: the reach map, the epistemic spine, and the chain below are how the sequence's steps get carried out. Read it first.

## What this produces

A **legacy-observed backlog draft**: epics → user stories → business rules →
acceptance criteria, every factual claim anchored at `file:line`, every judgment
call explicitly handed to a human. It inverts the blank page for the PO; it does
not replace the PO.

## The chain

```
APK (Foundation + per-feature loop output — `../SKILL.md`)
 → CT  technical component inventory (screens, flows, APIs, local storage, permissions)
 → RF  observed functional requirement ("the app allows X today")
 → US  user story (As a / I want / so that)
 → RN  business rules under each US (condition/trigger/result, tiered, anchored)
 → CA  acceptance criteria (Gherkin, @legacy-observed)
 → Epic → backlog draft
```

Each link keeps traceability: a CA references its RN; an RN anchors at `file:line`;
a US references its CTs and RF. The traceability matrix (template §8) is the
consolidated flat view — RN and CA live nested inside their US, not in separate
catalogs, so there is exactly one place where each rule is stated.

Triage aggregates findings into per-feature **dossiers** (descriptive, decision-pending) before any US; and epics are structured by **risk/value dimension**, not screen order (see `cognitive-sequence.md`).

## The epistemic spine (non-negotiable)

Inherited from the pipeline's inviolable rules and exercised in the WordPress run:

- **Origin legend on every field**: 🟢 recovered from code (anchored `file:line`) ·
  🟡 observed/inferred (engineering inference, not read at a concrete anchor) ·
  ⬜ out of RE reach (design/PO/team fills). The origin tag records only *where the
  field came from statically* — a fact frozen when the finding is born. It is a
  different axis from whether the finding is *confirmed true* (`confidence`:
  observed → cross-validated → business-ratified) and from *what to do about it*
  (`intent`: keep/change/drop). A 🟡 does **not** mean "PO ratifies": ratification
  is a `confidence` move and keep/change/drop is an `intent` move — the origin tag
  stays frozen through both.
  A ⬜ states which kind: **didn't look** (the classes were not read) vs. **looked,
  confirmed absent** (read, and the behavior is not there) — "no evidence found" is
  never conflated with "evidence of no behavior".
- **`legacy-observed ≠ target-approved`** — everything extracted is what the app
  does *today*: input for the PO to keep/change/drop, never an approved requirement.
- **Anchor rule** — a rule that can't be tied to a concrete string, endpoint, or
  entry point is marked `unanchored`, not disguised as a low-confidence inference.
- **Tiers are never flattened** — fact (endpoints), reconstruction (graph),
  inference (rules) stay visually separate end to end.
- **Scenario coverage per US** — a table separating "covered", "analogous
  (observed in a sibling flow — confirm)", and "not observed" (⬜ → human
  decision). Absence of evidence is stated, never silently omitted.
- **Recovered behavior may be a legacy bug** — the safeguard is the human
  keep/change/drop decision (`intent`), not confidence in the fact: a recovered bug
  is *true* (high `confidence`) yet must still be caught and changed, never
  preserved by default (the COBOL→Java lesson).
- **Observation step per 🟢 RN** — each anchored rule names one concrete way to
  *see it fire* on the running legacy app (a UI action, or a v2 logcat line). This
  is the catalog's `observed → cross-validated` transition one layer down: the named
  observation **is** the pre-registered criterion, and executing it against the
  running app — a regime-independent source (dynamic / v2 / traffic) — is exactly
  what promotes the finding `observed → cross-validated`. (A ⬜ finding has no
  anchor, hence no observation step, and cannot be promoted this way.) Verifying the
  observation is true comes *before*, and is separate from, the PO's keep/change/drop
  decision: ratifying a decision on top of an unverified observation is the failure
  the "login in a webview" over-claim exposed.

## Reach map — what RE fills vs. what stays human

| Ticket field | Reach | RE delivers | Human completes |
|---|---|---|---|
| Title | 🟡 | name derived from the observed flow | PO names/prioritizes |
| Story (As/want/so that) | 🟢 capability · 🟡 persona+benefit | the anchored capability | persona and benefit are inference — PO confirms |
| Business context | ⬜ inverted | "the legacy does X — evidence `file:line`" | the *why*, goals, A/B intent |
| Business rules (RN) | 🟢 observable ones | validations, gates, constants | keep/change/drop; a rare rule may be missing |
| Acceptance criteria (BDD) | 🟢 `@legacy-observed` | observed-behavior scenarios | desired-behavior scenarios; unobserved error/edge cases |
| Copy / labels | 🟡 recoverable | current strings (`res/values/strings.xml`) | new/approved copy |
| Design / layout | ⬜ | nothing — the target app does not exist in the APK | target design |
| Contract / backend | 🟢 (the legacy's) | endpoints, DTO shapes, module graph | target architecture |
| Dependencies / sequence | 🟢 directional | graph coupling → migration-order signal | team confirms |
| DoR / DoD / estimate | ⬜ | — | 100% team |
| Blind spots | 🟢 delimits | marks what is NOT recoverable (webview/dynamic) | keep-web vs. nativize decision |

**The honest ceiling — two stops, only one kept.** Stop that stays: the method
never *takes* the product decision — legacy-observed ≠ target-approved, the
keep/change/drop call is the human's, and that refusal is what makes it reliable.
Stop that goes: the *artifact* no longer ends at the decision boundary. What used to
be a prose full-stop in the per-run report is now `intent` — a tracked state in the
living catalog (`needs-decision → preserve|fix|redesign|remove`). "Continuing inward" means
only this: the finding crosses the decision as a record whose state moves, while the
method still refuses to decide for the team.

## Known degradation — the two vectors the reach gate now measures

Two vectors, surfaced by blind review of the first run:

- **Obfuscation kills readability.** Anchors like `Authenticator.java:178` exist
  because WordPress ships unobfuscated. Under R8/ProGuard the anchor becomes
  `c/a.java:17` and the "verifiable" foundation degrades sharply. The pipeline
  acknowledges this (design doc §6); the field-by-field degradation is not yet
  mapped.
- **Dynamic behavior kills observability.** Remote config, A/B flags,
  server-driven UI, webview interiors, reflection, and native `.so` logic are
  invisible to static reading. This bit once in the WordPress run: "login in a
  webview" was over-claimed from a string occurrence and corrected to native
  OAuth2 only by manual re-read of the code.

Which fields each vector actually threatens (a sharpening, deliberately not a
per-field table): the **anchor-dependent** ones — RN, CA, contract/DTO names, the
module graph's labels — lose their `file:line` footing first; the already-⬜ fields
(business context, design, DoR/DoD) were never RE-reached, so neither vector moves
them. A full field-by-field degradation matrix stays deferred on purpose: `telecorp`
detected the obfuscation wall but the run **stopped at the gate** (below) — no run has
been *pushed through* obfuscation to synthesis, so per-field degradation is still an
unobserved regime, and presenting it as systematized knowledge is exactly the
over-claim the anti-laundering clause forbids.

## The reach gate — measure the wall, decide normal / degraded / no-go

The two vectors above are no longer only described: before the synthesis investment
downstream — the per-feature loop and the output backbone — a **reach gate** reads
them as signals and sets the run's reach status.
`origin` stays frozen — the gate does not rewrite where a finding came from; it bounds
what the run may *claim*. Its verdict is one of **`normal` / `degraded` / `no-go`**, a
statement about reach, never a `confidence` promotion.

What it measures, and the ground truth for each:

- **Obfuscation** — the `unclassifiable` ratio from `classify.json`, cheap and
  upstream. Ground truth (`telecorp`, an obfuscated build of the same white-label
  operator platform): **558/576 packages (96.9%) `unclassifiable`** — 9
  business-candidate against 558 walls — producing **no `graph.json`, no backlog**.
  The run hit the wall and stopped. This is the empirical ballast the `no-go` verdict
  rests on — the regime was *measured*, not anticipated; the gate is the mechanism
  that now catches it upstream.
- **Tamper / pinning** — anti-tamper or certificate-pinning that would block the
  dynamic second source. The gate measures the **presence of the signal** (a
  third-party anti-tamper SDK shipped as an obfuscated island; a tamper-detection
  activity; cert-pinning) and reports it as a reach **risk**. It does **not** assert
  the effect: no run has yet observed tamper defeating a dynamic pass — the one dynamic
  attempt on a readable build was blocked by a mundane install failure, not tamper.
  Measure the signal; never launder it into an observed wall.
- **Load-bearing logic outside static reach — readable ≠ reachable.** This is the
  gate's point even at zero obfuscation. Ground truth: a non-obfuscated build of the
  same platform was **>99% readable**, yet its reach was bounded — Dimension B
  (contracts) under-delivered because the real URLs are **assembled at runtime**
  against a vendor API domain (not literals in code), the app is heavy-WebView, and it
  ships a third-party anti-tamper SDK as an obfuscated island. Static readability did
  not buy full reach.

**Doctrine — under obfuscation, a degraded anchor is not an anchor.**
`Authenticator.java:178` carries verifiability; `c/a.java:17` does not. A degraded
anchor does **not** earn 🟢 — it is `unanchored` reach, not a low-confidence inference
dressed as a citation. A `no-go` or `degraded` dimension is reported as a bounded blind
spot (⬜, *dimensioned* — how much of the app it covers), never silently thinned.

**`.so` and backend the gate marks as bounded blind spots — WebView is different.**
Native `.so` and the server backend are load-bearing logic the static pass cannot
follow: mark ⬜, dimension the reach lost, do **not** invent a bespoke pipeline for them.
**WebView, when the target is to nativize, is not a blind gate but a *second RE target*** —
the same cognitive sequence re-points to the SPA + traffic (`cognitive-sequence.md`, "The
WebView branch"), gated by the same attestation wall. Measure the wall for all three; but
do not collapse WebView's re-pointing route into `.so`-style blindness.

**Named and deferred — the wall is detected here, not crossed.** Building this
*detector* is grounded (telecorp and the readable build above). Building the method to **cross** the wall is
not, and stays named-only so the deferral is on the record, not an implicit promise:

- **De-obfuscation** — recovering the app's own readable logic under obfuscated names
  (symbol recovery; synthesis under illegible names). Not demonstrated. This is
  **distinct from** LibScout / LibRadar library fingerprinting, which only
  re-identifies known third-party libraries under renamed packages — that shrinks the
  classify step's false-negatives, it does not restore business logic.
- **Unpinning / instrumentation** — Frida against anti-tamper SDKs of this class to
  reopen the dynamic second source. Not demonstrated (and not to be conflated with the
  mundane install failure that blocked the one dynamic attempt).
- **Offline-first branch** — a run with zero dynamic footing from the start. Zero real
  exemplars.
- **The field-by-field degradation map** — stays deferred exactly as "Not yet
  validated" states: the gate decides *per dimension* (coarse, grounded); a *per-field*
  table would predict a regime no run has pushed through.

## Three mechanisms, not one "hook"

The method's deterministic checks are **three distinct mechanisms** — do not collapse them into a single "hook":

- **The classify-gate** — a *script with a selftest* (`scripts/classify_packages.py`), run pre-fan-out at Foundation step 2. It buckets packages; its `unclassifiable` ratio is the obfuscation signal the reach gate reads. A deterministic pipeline step, not a tool-event hook.
- **The reach gate** — *pre-run doctrine* (this reference, "The reach gate"): reads the classify signal + tamper/reach and decides `normal / degraded / no-go`. A decision, not a script.
- **The anti-laundering guard** — a *catalog invariant* (the confidence-promotion rule): a 2nd source must be regime-independent; a static re-read cross-validates the transcription, not the reach. Enforced over the catalog, not at a pipeline step.

They differ in kind (script / doctrine / invariant) and in when they act (Foundation step 2 / pre-run / on promotion) — naming them apart keeps the "just add a hook" reflex from fusing them.

## The intent gate — deciding is not free

`intent` (`needs-decision → preserve | fix | redesign | remove`) is not a column to fill — it is a **gated transition** with three preconditions. It is a **new gate with a small seed**, not a promotion of the responsible-use disclaimer.

- **Mandate** — whoever moves `intent` must own that behavior. No named owner → the finding stays `needs-decision`. Undecided is an honest state, not a blank to fill for convenience.
- **Legal right** — if the behavior belongs to a **third-party licensed platform** (not the client's bespoke code), `preserve`/`fix` may not be the client's to make: reimplementing vendor behavior can breach the license. Intent for those findings is gated by the legal question, not only the product one.
- **Mandatory lock — personal-data / accessibility** — a finding that touches personal data / consent (privacy law) or accessibility does **not** go to `remove`: silently dropping a consent screen or an a11y capability is a decision with legal consequence, not a scope cut.

## Not yet validated — do not sell as done

- **Degradation map** field-by-field — deferred on purpose (see "Known degradation"
  and "The reach gate"): `telecorp` grounds the gate's *detection* of the obfuscation
  wall, but no run has been pushed *through* it to synthesis, so a per-field table would
  still predict an unobserved regime. Detection graduated; the per-field map did not.
- **Coverage *metric* per epic** (a number: classes read vs. total) — deferred as
  false rigor: the denominator is the noisy business-node count this method itself
  flags (leaked libs, name collisions), and classes-read is not a proxy for
  rules-covered. The honest kernel — the ⬜ split "didn't look" vs. "confirmed
  absent" — is now in the origin legend, without a number.
- **A second run on an obfuscated/server-driven app** — the word "method" is
  earned there, not here.
- **Dynamic analysis (v2)** — the log-based *instrument* is now built (scripts,
  unit-tested) and exercised once on WordPress; the *method* is not yet validated
  on the hard axes (obfuscated / authenticated / real business webview). See
  "Dynamic analysis (v2) — log-based observation".

## Dynamic analysis (v2) — log-based observation

> **Status: instrument BUILT + one instrument-validation exemplar.** The scripts
> exist (`scripts/capture_dynamic.sh` + `scripts/parse_logcat.py`, unit-tested on a
> synthetic framework-log fixture) and were exercised once on WordPress. This is
> still NOT a validated *method* on the hard axes — read the anti-laundering clause
> before citing it.

**Anti-laundering clause (load-bearing — stated first, on purpose).** Log-based
v2 on an unauthenticated, non-obfuscated app (WordPress) demonstrates the
log↔static cross-check *mechanism* and re-verifies the native-vs-webview failure
mode on reachable screens. It validates the **instrument**, not the method:
exercising the cross-check where ground truth is already known (login is native
OAuth2, self-corrected earlier by a static re-read) proves the instrument would
give a cheap independent second source — it does **not** claim v2 has conquered
the hard unknown cases. "v2 validated" is earned only on an obfuscated /
server-driven app with authenticated flows and a real business webview — the
*same frontier* as the static method's already-open "second run" item.

**Approach.** Boot the legacy APK on an emulator/device and capture `adb logcat`
while driving flows via `adb input` / `uiautomator` / manual — **not**
`marionette`, which drives Flutter targets through the Dart VM service and cannot
attach to a native legacy APK. Cross-check what the app *does* at runtime against
the static extract. Same log-watching discipline used to verify GA4 events /
Flutter logs in debug. **Behavior, not contract — on the native/static path.** logcat without interception
shows what the app does and renders, never its wire payloads; on the native path the
static pass already recovers endpoints from code, so v2 does not reach for traffic
there. **This exclusion is scoped to the native path, not the method as a whole:**
where the contract is *not* in the bytecode — the WebView second RE target, whose
backend is assembled at runtime — a Fetch-tap + proxy is the oracle, not an excluded
network-interception project (see `cognitive-sequence.md`, "The WebView branch"). The
rule is "the native path does not *need* traffic", not "the method never taps
traffic": for a WebView finding, captured traffic is exactly the regime-independent
2nd source that promotes it `observed → cross-validated`.

**The instrument (built, not yet run on the hard axes).** Two scripts, mirroring
the static pipeline's script+selftest convention:

- `scripts/capture_dynamic.sh` — path-scoped, fail-closed capture wrapper: clears
  the buffer, records `adb logcat -v threadtime` while you drive the app, and dumps
  the current-screen `uiautomator` view hierarchy. Committed as a runbook; real runs
  stay local (design doc §8). The `uiautomator` dump is the *only* source that can
  support a "native" call (0 `WebView` nodes) — logcat can't.
- `scripts/parse_logcat.py` — deterministic, pure-stdlib parser (unit-tested by
  `selftest_parse_logcat.py`). Structures the robust framework-level items
  (navigation sequence; WebView / Custom-Tab *signals*) and only *surfaces* the
  app-specific ones (remote-config / analytics candidate lines) for a human — it
  does not structure what would generalize from one app. A secret-looking token in a
  Custom Tab's `dat=` URL is redacted on output, reusing `extract_endpoints`' rule.

There is **no auto cross-check script** against the static extract, on purpose: the
static `graph.json` is an extends/implements reconstruction with no navigation edges,
so scoring "agreement" between a runtime `START` *sequence* (fact) and an inheritance
graph (reconstruction) would flatten the confidence tiers this method keeps separate.
The cross-check is a human step — "runtime disambiguates what the graph only signals".

**Dynamic reach map** (mirror of the static reach map — what logcat can
cross-check, robust items first because they are framework-level and survive
release log-stripping):

- **Real boot→first-screen navigation sequence** (`ActivityManager` START lines)
  vs. the module graph's *directional guess* — runtime disambiguates what the
  graph only signals.
- **WebView / Custom-Tab SIGNALS per reachable screen** (`chromium` / `cr_*`
  tags for in-process WebView; a `START` into a browser `customtabs` activity).
  `parse_logcat.py` emits these as *signals* and NEVER labels a screen "native":
  logcat cannot prove absence (stripped logs / surface outside the capture window),
  and calling that "native" would conflate "no evidence found" with "evidence of no
  behavior". A native call comes only from the `uiautomator` dump (0 `WebView`
  nodes), read by a human. Directly re-checks the documented "login is a webview"
  failure mode — which the exemplar refined to a third category (Custom Tab).
- **Boot-time remote-config / feature-flag fetch** present or absent
  (corroborates a "config-driven branch" inference).
- **App analytics event taxonomy per screen**, if logged (fragile — release
  builds may strip app `Log.*`; a null here is a finding, not a gap).

**Honest ceiling** (mirror of the static honest ceiling):

- logcat shows only what app + framework *choose to log*; release builds may
  strip app logs → nulls (report them).
- **WebView interiors stay invisible** — you observe that a webview was created
  and maybe its URL, never the business logic inside. The checkout blind spot
  survives v2.
- Authenticated / deep flows need a test account.
- **Obfuscation is orthogonal** — dynamic observation does not restore static
  readability; the two degradation vectors are independent.
- Server-side decisions are invisible unless the resolved value is logged.

**Sequencing.** The real v2 run merges with the open obfuscated/server-driven
second-app frontier, on the actual client app where authenticated flows and real
business webviews exist — never committed (design doc §8 provenance discipline).

**Provenance guardrail.** Every command path-scoped to the public app's work dir
and APK; never touch a client artifact; hand-grep any committed artifact for
client identifiers before it leaves local — a green provenance gate does not
cover client identity.

## Outputs

- **Report template** (pt-BR, client-facing): `modelo-relatorio.pt-BR.md` — the
  filled file **is** the deliverable, shipped as Markdown (no `.docx` conversion;
  the process diagram is inline Mermaid, rendered by the viewer). Delivers two
  client-side audiences: the PO (decision — §6) and the dev team (implementation
  inputs — §7).
- **Filling guide** (pt-BR, filler/maintainer-facing): `guia-preenchimento.pt-BR.md`
  — filling order, worked example, legend pedagogy, conventions. **Never shipped
  with the report** (deliver only the report `.md`).
- **Worked example** (pt-BR): `../examples/relatorio-wordpress.pt-BR.md` —
  WordPress 26.9, consolidates the first run.
- Runtime output language follows the client (pt-BR here); method internals stay
  in English (kit standard).

## Authorization and responsible use

Only on apps you own or are contractually authorized to analyze; respect store
terms, third-party licenses, IP law, and data-protection law (e.g. LGPD). Content
extracted from an unauthorized third party's APK never leaves the local
environment — publication governance in the design doc §8.
