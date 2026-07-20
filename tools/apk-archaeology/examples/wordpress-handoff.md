# apk-archaeology — v0 handoff artifact (WordPress)

> **⚠ Prior doctrine (v0 record).** This artifact proves the acceleration step under the old
> Dimension A/B/C framing (candidate US + DTO skeletons); it predates the deliverable-first
> restructure (Foundation + per-feature loop; deliverables — OpenAPI, data dictionary, state
> machines, TDD stubs — at the center). Kept as the empirical acceleration record, not current
> method — see `references/cognitive-sequence.md` and `references/deliverables/`.
>
> **Note (post-extraction):** `references/…` paths here point to the `apk-archaeology` skill (`plugins/mobile/skills/apk-archaeology/references/`); this example now lives under `tools/`, so they are cross-tree pointers, not local files.

> Downstream artifact consumable by `tech-breakdown`/`spec-refine`. Format **provisional**
> (design §5), pinned at first real client use. Companion to `newpipe-demo.md`: the demo
> proves *viability* (measured extraction fidelity on a clean OSS reference); **this artifact
> proves the *acceleration step*** — that Dimension A/B output actually feeds the
> Spec/Implementation/Testes stages of §11 — on a richer, WebView-hybrid app.
>
> **legacy-observed ≠ target-approved** — every story, criterion, and DTO below is a hypothesis
> about the *legacy* WordPress app, input for PO reconciliation, **never an acceptance criterion
> on its own**. A user story's **role** and **benefit** are INFERENCE (not in the bytecode); only
> the **capability** is anchored to `file:line` evidence, with a confidence tier.

## Why WordPress, why this partition

WordPress-Android (F1: a public app closer to a real client's shape than NewPipe was) is a
**native shell + multiple purpose-specific WebViews** — the same architecture as the private
telecom target the tool was built for. The partition below, `org/wordpress/android/ui/domains`,
is a **consumer self-service purchase flow** (search a domain → fill contact details → buy in a
WebView checkout → manage it) — the class of business rule NewPipe (a media player) structurally
could not exercise (design §10). It also surfaces the **WebView blind spot** (see the dedicated
section): the money-handling logic runs *inside* the WebView, invisible to static Java.

## Provenance

- **Input**: WordPress-Android (`org.wordpress.android`), GitHub tag **26.9**, `wpandroid-26.9.apk`
  · `sha256: 74bde810878b0c9de5ccaa7bf784e239ed776140ad52565e02ca48a6ae68c2a4` · GPLv2 (public source)
- **Tools**: jadx 1.5.5 · apktool (homebrew) · macOS (arm64) · 2026-07-08
- **Partition**: `org/wordpress/android/ui/domains` (derived mechanically by package prefix, not hand-picked — see SKILL.md step 5)
- **Dimension B context (honest counts)**: 292 URL literals extracted → ~184 after filtering
  XML-namespace/placeholder noise (`w3.org`, `xml.org`, `ccil.org`, `example.com`); 31 against the
  real REST host `public-api.wordpress.com`. This partition contributes **9 WebView-target URLs**;
  the **DTO material comes from the `fluxc` REST layer** (`public-api.wordpress.com`), cited per DTO.

---

## A — Candidate user stories (Dimension A) — partition `ui/domains`

### US-1 — Search for a purchasable domain
As a `site owner (role — inferred)`, I want to **search domain names and see ranked, purchasable
suggestions** (`capability — [tier: high]`), so that `I can find an available custom domain to buy
(benefit — inferred)`.

Anchored capability evidence: 250ms-debounced query (`ui/domains/DomainSuggestionsViewModel.java:172`);
results ordered highest-relevance-first (`:436`); free suggestions omitted from the non-WPCOM list
(`:389`); the select action is enabled only once a suggestion is chosen (`:229`).

```gherkin
@legacy-observed
Scenario: Debounced, relevance-ranked domain suggestions
  Given the domain search screen
  When the user types a query and 250ms elapse with no further input
  Then a suggestions fetch is dispatched          # DomainSuggestionsViewModel.java:172 — PO must ratify
  And the suggestions are shown highest-relevance first   # :436 — PO must ratify
  And free suggestions are omitted from the list   # :389 — PO must ratify
```

### US-2 — Provide registrant contact details
As a `domain buyer (role — inferred)`, I want the app to **require complete contact details before
it submits my registration** (`capability — [tier: high]`), so that `the registration is not
rejected downstream for missing data (benefit — inferred)`.

Anchored capability evidence: 9 contact fields (first/last name, email, country code, phone, country,
address line 1, city, postal code) are required non-empty and the first empty field receives focus
before submit (`ui/domains/DomainRegistrationDetailsFragment.java:613`).

```gherkin
@legacy-observed
Scenario: Contact form completeness gate
  Given the domain registrant contact form
  When any of the 9 required fields is empty and the user submits
  Then submission is blocked
  And the first empty field receives focus         # DomainRegistrationDetailsFragment.java:613 — PO must ratify
```

### US-3 — Complete the purchase in a WebView checkout
As a `domain buyer (role — inferred)`, I want to **complete payment in the checkout and have the
app recognize when it succeeded** (`capability — [tier: high for the native shell; the in-WebView
logic is NOT observable — see blind spot]`), so that `the app can finalize my domain after I pay
(benefit — inferred)`.

Anchored capability evidence: the purchase loads an authenticated `https://wordpress.com/checkout/`
WebView (`ui/domains/DomainRegistrationCheckoutWebViewActivity.java:259`); the app treats the purchase
as complete **only** when the visited path starts with `/checkout/thank-you/`
(`ui/domains/DomainRegistrationCheckoutWebViewClient.java:54`); in-WebView navigation is confined to an
allow-list of `wordpress.com` paths (`ui/domains/DomainRegistrationCheckoutWebViewNavigationDelegate.java:20`).

```gherkin
@legacy-observed
Scenario: Checkout completion detected by the thank-you URL
  Given the checkout WebView has loaded https://wordpress.com/checkout/…
  When the visited-history path starts with "/checkout/thank-you/"
  Then the registration flow is treated as complete   # DomainRegistrationCheckoutWebViewClient.java:54 — PO must ratify

# BLIND SPOT (not testable from the legacy native code): cart line items, payment entry,
# 3-D Secure, coupon/credit application, order confirmation are all server-rendered inside
# the WebView. The only signal the native app observes is the thank-you path above.
```

### US-4 — Be offered the right next action on the domains dashboard
As a `site owner (role — inferred)`, I want the dashboard to **offer me the single most relevant
domain/plan action for my site's state** (`capability — [tier: medium]`), so that `I'm guided to the
right purchase/claim step (benefit — inferred)`.

Anchored capability evidence: a strict priority ladder picks one CTA — domain credit available →
"claim your domain"; else site already has a custom (non-wpcom) domain → "add domain"; else site is
on a paid plan → "add domain"; else free plan → "purchase plan"
(`ui/domains/DomainsDashboardViewModel.java:266-288`). **Tier medium**, not high: the `credit available`
and `on free plan` predicates are delegated **outside this partition** (`PlanUtilsKt.isDomainCreditAvailable`,
`SiteUtils.onFreePlan`, `:242-243`) and were not observed — the branching is anchored, the predicate
bodies are not.

```gherkin
@legacy-observed
Scenario Outline: Dashboard CTA priority ladder
  Given a site where domain-credit=<credit>, has-custom-domain=<custom>, plan=<plan>
  When the domains dashboard is built
  Then the CTA shown is "<cta>"                    # DomainsDashboardViewModel.java:266 — PO must ratify

  Examples:
    | credit | custom | plan | cta            |
    | yes    | any    | any  | claim domain   |
    | no     | yes    | any  | add domain     |
    | no     | no     | paid | add domain     |
    | no     | no     | free | purchase plan  |
  # UNOBSERVED: the credit-available / free-plan predicates live outside this partition (:242-243).
```

---

## B — API contracts (Dimension B) → DTO skeletons

> Dart `Dto` + `Entity` + `mapper` per endpoint, for the Flutter repository layer (design §11
> Implementation). **legacy-observed ≠ target-approved — PO must ratify before any of this is a
> contract.** Fields and types are those *observed* in the decompiled Gson models; nullability
> follows the legacy annotation posture (see note). Endpoint↔DTO binding confidence is stated per DTO.

### `DomainAvailabilityDto` — from `GET .../domains/{domain}/is-available` (v1.3)
Source: `fluxc/network/rest/wpcom/site/SiteRestClient.java:1417` · model `.../DomainAvailabilityResponse.java:7`
· **binding: ANCHORED** (response `.class` literal passed at the request call site) · tier: high

```dart
// legacy-observed ≠ target-approved — PO must ratify before this is a contract
class DomainAvailabilityDto {
  final int? productId;         // product_id
  final String? productSlug;    // product_slug
  final String? domainName;     // domain_name
  final String? status;         // status  (availability state — enum unknown from bytecode)
  final String? mappable;       // mappable
  final String? cost;           // cost    (string, not a numeric type in the legacy model)
  final bool supportsPrivacy;   // supports_privacy
  const DomainAvailabilityDto({/* ... */});
}
class DomainAvailability { /* domain Entity — shape TBD by PO */ }
// mapper: DomainAvailabilityDto -> DomainAvailability (decide status enum + cost parsing on ratification)
```

### `DomainSuggestionDto` — from `GET .../domains/suggestions` (v1.1)
Source: `fluxc/network/rest/wpcom/site/SiteRestClient.java:1113` · model `.../DomainSuggestionResponse.java:6`
· **binding: inferred-by-proximity** (call-site/response-type in same method, no `.class` literal) · tier: medium

```dart
// legacy-observed ≠ target-approved — PO must ratify
class DomainSuggestionDto {
  final String cost;            // cost (string)
  final String domainName;      // domain_name
  final bool isFree;            // is_free
  final bool isPremium;         // is_premium
  final int productId;          // product_id
  final String productSlug;     // product_slug
  final double relevance;       // relevance (drives US-1 ranking)
  final bool supportsPrivacy;   // supports_privacy
  final String vendor;          // vendor
  const DomainSuggestionDto({/* ... */});
}
class DomainSuggestion { /* domain Entity — shape TBD by PO */ }
// mapper note: legacy uses RAW public fields (default Gson snake_case match), not @SerializedName —
// a missing server field is a harder failure here than in the annotated models below.
```

### `DomainPriceDto` — from `GET .../domains/{domain}/price` (v1.1)
Source: `fluxc/network/rest/wpcom/site/SiteRestClient.java:1520` · model `.../DomainPriceResponse.java:8`
· **binding: inferred-by-proximity** · tier: medium

```dart
// legacy-observed ≠ target-approved — PO must ratify
class DomainPriceDto {
  final bool isPremium;         // is_premium
  final int? productId;         // product_id
  final String? productSlug;    // product_slug
  final String? cost;           // cost (display string)
  final double? rawPrice;       // raw_price (numeric — prefer this over `cost` for math)
  final String? currencyCode;   // currency_code
  const DomainPriceDto({/* ... */});
}
class DomainPrice { /* domain Entity — money type + currency decided by PO */ }
// mapper: raw_price + currency_code -> Money; do NOT parse the display `cost` string for arithmetic.
```

> A 4th observed model, `AllDomainsDomain` (`.../AllDomainsDomain.java:14`, from `GET .../all-domains`
> v1.1, `@SerializedName`-annotated, ~13 fields), backs the domain-management list (US-4 territory) —
> available if the PO wants the management surface modeled too. Left as a pointer, not a stub (Epicurus).

---

## C — Module graph note (Dimension C)

The `ui/domains` partition was derived **mechanically** (package-prefix, SKILL.md step 5), not hand-picked.
Full-run graph: 17972 business nodes / 10006 edges (`graph.json` carries `node_files`, the join that makes
this partitioning possible — repoint move 1a). Caveat: `known-libs.json` under-recognized several bundled
libraries (uniffi/zendesk/sentry/jsoup…), which inflate the business-node count (documented fragility, design §6);
this artifact sources **only** from `org/wordpress/android/*`, so leaked libs never reach the stories/DTOs above.

## Dimension A blind spot — logic behind the WebView

The single most important limit this WebView-hybrid app exposes (absent from the NewPipe demo): **the
partition's core business logic — the actual purchase — is not in the decompiled Java at all.** The native
code builds a URL, hands it to a WebView, and watches the address bar for `/checkout/thank-you/`
(`DomainRegistrationCheckoutWebViewClient.java:54`) as its *only* signal. Cart contents, payment method
capture, 3-D Secure, coupon/credit redemption, and order confirmation are server-rendered React/JS inside
`wordpress.com/checkout/…` and are **invisible to static analysis of the APK**. For a real client migration,
this means: Dimension A recovers the **native shell, the launch URL, and the navigation/allow-list rules**,
but the money-path business rules must come from the web frontend / backend, not the APK. Naming this is the
point — the acceleration is real for the shell, and honestly bounded at the WebView seam.

## What this is NOT

- **legacy-observed ≠ target-approved.** Every story/criterion/DTO is what the app *does today*, not
  what it *should* do — the PO gate remains (design §11.1).
- Demonstrated on an **un-obfuscated** app; the real target is obfuscated (Telecorp appendix, `newpipe-demo.md`).
  This proves the acceleration step, **not** fidelity under obfuscation, and adds **no** ROI/time-saved number
  (design §13).
- The **WebView seam** (above) bounds Dimension A: the purchase logic is not in the APK.
- **US-4 is tier-medium**: its `credit-available` / `free-plan` predicates were not observed (out of partition).
- A few method bodies (`FetchAllDomainsUseCase.execute`, `TransactionsRestClient.createShoppingCart`) failed
  clean jadx decompilation and were read as raw bytecode dumps — lower fidelity, flagged where used.
- Inference in A can be wrong even at tier-high; the tier is a calibrated signal, not a guarantee.
