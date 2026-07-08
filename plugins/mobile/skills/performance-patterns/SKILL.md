---
name: performance-patterns
description: Invoke to review or apply performance patterns in a Flutter/MobX app — Observer rebuilds, network calls (Dio), images, memory. Triggers — "this Observer is rebuilding too much", "this list is slow", "performance review of this screen".
---

# Performance Patterns

Performance patterns for the Flutter + MobX stack covering Observer rebuilds, Dio, images, memory, and RUM. Details in `REFERENCE.md` (same folder) — read the relevant sections before applying.

## Project Config

The examples assume MobX (`Observer`/`@computed`/`runInAction`) and Dio for networking. References to a "RUM tool" point to your project's config (Datadog, Firebase Performance, Sentry, etc.) — swap in the real name.

## MobX Rebuild Optimization

Read `REFERENCE.md` §MobX Rebuild Optimization: granular `Observer` splitting, `const` children inside `Observer`, `@computed` for derived values, batching with `runInAction`.

> MobX rules (rebuilding the whole `Observer`, pure `@computed`, reaction disposers) are codified in `mobile:mobx` `REFERENCE.md`.

## Widget Tree Optimization

Read `REFERENCE.md` §Widget Tree Optimization: `const` constructors, `ListView.builder`, `RepaintBoundary`, `AnimatedOpacity` vs `Opacity`, `IntrinsicHeight` caveats, `MediaQuery.sizeOf`.

## Network and Images

Read `REFERENCE.md` §Network Performance (Dio): `CancelToken` on dispose, `Future.wait` for parallel calls, result caching.

Read `REFERENCE.md` §Image Performance: always pass explicit dimensions to your project's image widget.

## Memory Management

Read `REFERENCE.md` §Memory Management: MobX reaction disposers, disposing Flutter controllers, clearing large state on navigation.

## Performance Checklist

Read `REFERENCE.md` §Performance Checklist for the full pre-review checklist.
