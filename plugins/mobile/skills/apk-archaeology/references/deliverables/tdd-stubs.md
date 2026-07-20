# TDD Stubs — the anti-regression shield (loop step 7)

**What this is.** The recipe for the per-feature loop's last deliverable
(`cognitive-sequence.md`, loop step 7): turning the *decided* rule topology into
`_test.dart` skeletons — `group`/`test` scaffolding with descriptive names and
arrange/act/assert structure, **no implementation body**. The stub is the DoD: a
migrated feature is done when a dev has filled these in and they pass. This recipe
does not write the implementation — that stays the dev's job, on purpose (see
"Honesty," below).

## Input — the decided topology only, never the raw one

The source is loop step 4's output (`state-machines.mmd` + truth tables) **after**
it has passed through step 5, intent (`cognitive-sequence.md`, loop steps 4-5). Only
rules whose `intent` landed on `preserve` or `fix` are in scope:

- **`preserve`** — the legacy transition is correct and stays; the stub locks it in.
- **`fix`** — the legacy transition is being corrected; the stub encodes the
  **corrected** expected value, not the legacy one (the anchor still names what the
  legacy build did — see "Honesty" — but the assertion is the new behavior).
- **`redesign` / `remove`** — **no stub, by construction.** There is nothing to
  regression-guard: `redesign` means new intent *and* new implementation (nothing
  legacy to lock in), `remove` means the behavior is gone. Do not generate a stub
  "just in case" — an unused stub for a removed rule is a false anchor, not caution.
- **`needs-decision`** — not yet gated; no stub either. A rule stuck at
  `needs-decision` has no named owner or no ratified intent, so there is nothing
  decided to shield yet (`method.md`, "The intent gate").

A rule topology that hasn't reached step 5 is not this recipe's input — running it
early would generate stubs for rules that might still be removed or redesigned out
from under them.

## Output — one file per feature slice

```
features/<slice>/<rule>_test.dart
```

One file per feature slice (not per app, not per screen — the same slice unit the
whole per-feature loop uses). Inside it, one `group` per rule cluster (a state
machine's related transitions) and one `test` per transition. A cluster with a
single transition can skip the `group` wrapper; a cluster with several (loading /
success / failure / retry) should keep them grouped so the file reads as one rule,
not a flat list of unrelated assertions.

## Method — one test per transition, ⬜ gets skipped, not guessed

1. **Each business rule → one `test`, or a `group` per rule cluster.** The state
   machine's transitions (step 4) are the enumeration: every edge in
   `state-machines.mmd` (or every row in the accompanying truth table) is one
   expected behavior, hence one test case. Don't invent test cases beyond the
   transitions actually recovered — the shield covers what was observed, not what
   might exist.
2. **The test name states the observable behavior**, not the mechanism —
   `'disabled when required fields are empty'`, not `'calls isFormValid'`. A dev
   reading only the test names should be able to reconstruct the rule topology
   without opening the diagram.
3. **Arrange/act/assert scaffolding, no implementation body.** `build`/`act`/
   `expect` (or `arrange`/`act`/`assert` comments in plain `flutter_test`) are
   present as structure — parameter slots, comments marking what goes where — but
   the actual bloc, event, and expected-state values are left for the dev to wire
   up. The stub proves the test *exists* and names the *shape* of the check; it
   does not do the check.
4. **Mark `@Skip`/TODO where the expected value is ⬜.** Some transitions carry an
   anchor for the *event* (something calls it) but not for the *expected result* —
   a debounce interval read in Kotlin but never confirmed at runtime, a fallback
   whose trigger condition is inferred, not observed (see `rxjava-to-bloc.md`'s
   `.debounce(...)` row: an event transformer, not a state, and not always
   confirmed). For those, keep the test (naming the behavior the human still owes
   a decision on) but skip it — `skip: 'needs-decision: <what's missing, anchor>'`
   on the `test`/`group`, or a file-level `@Skip('...')` if the whole cluster is
   blocked — so CI doesn't fail on a value nobody has ratified yet. A skipped stub
   is a flagged blind spot, not a passing test and not a missing one.
5. **Anchor every stub to its source.** A leading comment citing the legacy
   `file:line` the rule came from and the `intent` that authorized the stub
   (`preserve`/`fix`) keeps the regression net traceable back to the finding that
   produced it — the same anchor discipline the rest of the loop uses, extended to
   the test file.

## Worked example — `SubmitEnabled`

A generic rule: *the submit button is disabled until the form validates.* Two
transitions recovered from the legacy state machine (`INVALID → VALID`,
`VALID → INVALID`), intent `preserve` on both; a third, debounce timing on the
validation trigger, intent `preserve` but its value is ⬜ (read in the legacy
Kotlin, never confirmed at runtime).

```dart
// features/checkout/submit_enabled_test.dart
//
// Rule: submit is disabled until every required field validates.
// Origin: 🟢 CheckoutViewModel.kt:88 (legacy `canSubmit()` gate)
// Intent: preserve (see feature dossier — owner: <PO name>, <date>)

import 'package:bloc_test/bloc_test.dart';
import 'package:flutter_test/flutter_test.dart';

// import '.../checkout_bloc.dart';

void main() {
  group('SubmitEnabled', () {
    blocTest<CheckoutBloc, CheckoutState>(
      'disabled when a required field is empty',
      build: () => /* TODO: dev — construct CheckoutBloc with its real deps */
          throw UnimplementedError(),
      act: (bloc) => /* TODO: dev — emit the event that clears/empties a field */
          throw UnimplementedError(),
      expect: () => [
        // TODO: dev — assert state.canSubmit == false
      ],
    );

    blocTest<CheckoutBloc, CheckoutState>(
      'enabled once every required field validates',
      build: () => throw UnimplementedError(), // TODO: dev
      act: (bloc) => throw UnimplementedError(), // TODO: dev — fill all fields
      expect: () => [
        // TODO: dev — assert state.canSubmit == true
      ],
    );

    // Origin: 🟡 CheckoutViewModel.kt:94, `.debounce(300, TimeUnit.MILLISECONDS)`
    // — event transformer read in the legacy source, never confirmed at runtime.
    // Expected debounce interval: ⬜ out of static reach.
    blocTest<CheckoutBloc, CheckoutState>(
      'debounces rapid field edits before re-validating',
      build: () => throw UnimplementedError(), // TODO: dev
      act: (bloc) => throw UnimplementedError(), // TODO: dev
      expect: () => [], // TODO: dev — fill in once the interval is ratified
      skip: 'needs-decision: debounce interval unconfirmed at runtime, '
          'CheckoutViewModel.kt:94 — see feature dossier',
    );
  });
}
```

No `CheckoutBloc`/`CheckoutState` import is resolved and every body throws or is
empty on purpose — this file should not compile-and-pass as-is. It is a checklist
with names, not working code; the dev's job is to make it real.

## Consumer — dev fills it, hooks/CI gate on it

- **Dev**: writes the implementation against the stub, filling `build`/`act`/
  `expect` (or the arrange/act/assert bodies) until the named behaviors actually
  hold. The stub is the spec the implementation is written *to*.
- **Hooks/CI**: the stubs, once filled, are the regression gate — a migrated
  feature is not "done" by vibes, it's done when its `_test.dart` file passes (and
  a skipped test stays visibly skipped, not silently green). Value: this is the
  Definition of Done made executable, not a checklist that lives in a ticket
  someone can mark complete without running anything.

## Honesty — a regression net, not an approval

The stub encodes **legacy-observed** behavior — what the old app actually does,
per its `preserve`/`fix` intent — not a design review's blessing. A rule marked
`preserve` may still be a legacy bug the team chose to keep for now (compatibility,
low priority, whatever the intent gate's named owner decided); the stub locks that
behavior in exactly as decided, bug and all. Passing this test suite means "we did
not regress relative to the decided topology," never "this behavior was checked
for correctness here." That check already happened, upstream, at the intent gate
(`cognitive-sequence.md`, loop step 5) — this deliverable is downstream of that
decision, not a second opinion on it.
