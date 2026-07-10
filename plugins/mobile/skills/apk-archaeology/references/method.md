# From Extraction to Backlog — Method Reference (provisional)

> **STATUS: provisional.** Validated on ONE public app (WordPress for Android 26.9,
> non-obfuscated) at roughly one-epic depth. Generalization to obfuscated or
> server-driven apps is NOT yet demonstrated — see "Not yet validated" below.
>
> The extraction pipeline itself (decompile → classify → endpoints → graph →
> dimension-A synthesis) lives in `../SKILL.md` and is **not restated here** — this
> reference covers the layer between the pipeline's consolidated output and an
> agile backlog draft. Keeping a single source for the pipeline is deliberate:
> a duplicated process description was already caught drifting from the real
> scripts once.

## What this produces

A **legacy-observed backlog draft**: epics → user stories → business rules →
acceptance criteria, every factual claim anchored at `file:line`, every judgment
call explicitly handed to a human. It inverts the blank page for the PO; it does
not replace the PO.

## The chain

```
APK (pipeline output — SKILL.md steps 1–6)
 → CT  technical component inventory (screens, flows, APIs, local storage, permissions)
 → RF  observed functional requirement ("the app allows X today")
 → US  user story (As a / I want / so that)
 → RN  business rules under each US (condition/trigger/result, tiered, anchored)
 → CA  acceptance criteria (Gherkin, @legacy-observed)
 → Epic → backlog draft
```

Each link keeps traceability: a CA references its RN; an RN anchors at `file:line`;
a US references its CTs and RF. The traceability matrix (template §7) is the
consolidated flat view — RN and CA live nested inside their US, not in separate
catalogs, so there is exactly one place where each rule is stated.

## The epistemic spine (non-negotiable)

Inherited from the pipeline's inviolable rules and exercised in the WordPress run:

- **Origin legend on every field**: 🟢 recovered from code (anchored `file:line`) ·
  🟡 observed/inferred (PO ratifies) · ⬜ out of RE reach (design/PO/team fills).
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
- **Recovered behavior may be a legacy bug** — ratification is the safeguard
  (the COBOL→Java lesson).
- **Observation step per 🟢 RN** — each anchored rule names one concrete way to
  *see it fire* on the running legacy app (a UI action, or a v2 logcat line).
  Verifying the observation is true comes *before*, and is separate from, the PO's
  keep/change/drop decision: ratifying a decision on top of an unverified
  observation is the failure the "login in a webview" over-claim exposed.

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

**The honest ceiling:** the method stops at the decision boundary — that stop is
what makes it reliable.

## Known degradation (identified, not yet systematized)

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
them. A full field-by-field degradation matrix stays deferred on purpose — it would
predict a regime not yet observed (zero obfuscated runs), and presenting it as
systematized knowledge is exactly the over-claim the anti-laundering clause forbids.

## Not yet validated — do not sell as done

- **Degradation map** field-by-field — deferred on purpose (see "Known
  degradation"): a per-field table would predict an unobserved regime. The two
  vectors stay in prose until a real obfuscated/server-driven run grounds them.
- **Coverage *metric* per epic** (a number: classes read vs. total) — deferred as
  false rigor: the denominator is the noisy business-node count this method itself
  flags (leaked libs, name collisions), and classes-read is not a proxy for
  rules-covered. The honest kernel — the ⬜ split "didn't look" vs. "confirmed
  absent" — is now in the origin legend, without a number.
- **A second run on an obfuscated/server-driven app** — the word "method" is
  earned there, not here.
- **Dynamic analysis (v2)** — the log-based *instrument* is specified in its own
  section below and exercised once on WordPress; the *method* is not yet
  validated on the hard axes (obfuscated / authenticated / real business
  webview). See "Dynamic analysis (v2) — log-based observation".

## Dynamic analysis (v2) — log-based observation

> **Status: spec + one instrument-validation exemplar** (see the WordPress
> example). This is NOT a validated method on the hard axes — read the
> anti-laundering clause before citing it.

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
Flutter logs in debug. **Behavior, not contract**: logcat without interception
shows what the app does and renders, never its wire payloads — the static pass
already recovers endpoints from code, so v2 must not reach for traffic (that way
lies a network-interception project this method deliberately excludes).

**Dynamic reach map** (mirror of the static reach map — what logcat can
cross-check, robust items first because they are framework-level and survive
release log-stripping):

- **Real boot→first-screen navigation sequence** (`ActivityManager` START lines)
  vs. the module graph's *directional guess* — runtime disambiguates what the
  graph only signals.
- **Native vs. embedded-WebView vs. Custom-Tab per reachable screen**
  (`chromium` / `cr_*` tags for in-process WebView; `ActivityManager` launching
  a Chrome/CustomTabs activity). Directly re-checks the documented "login is a
  webview" failure mode.
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

- **Report template** (pt-BR, client-facing): `modelo-relatorio.pt-BR.md` — also
  the source for the `.docx` deliverable.
- **Worked example** (pt-BR): `../examples/relatorio-wordpress.pt-BR.md` —
  WordPress 26.9, consolidates the first run.
- Runtime output language follows the client (pt-BR here); method internals stay
  in English (kit standard).

## Authorization and responsible use

Only on apps you own or are contractually authorized to analyze; respect store
terms, third-party licenses, IP law, and data-protection law (e.g. LGPD). Content
extracted from an unauthorized third party's APK never leaves the local
environment — publication governance in the design doc §8.
