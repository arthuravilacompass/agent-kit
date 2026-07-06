---
name: performance-patterns
description: Invoque para revisar ou aplicar padrões de performance num app Flutter/MobX — rebuilds de Observer, chamadas de rede (Dio), imagens, memória. Gatilhos em pt-BR — "esse Observer está rebuildando demais", "essa lista tá lenta", "revisão de performance dessa tela".
---

# Performance Patterns

Padrões de performance para o stack Flutter + MobX cobrindo rebuilds de Observer, Dio, imagens, memória, e RUM. Detalhes em `REFERENCE.md` (mesma pasta) — leia as seções relevantes antes de aplicar.

## Config do projeto

Os exemplos assumem MobX (`Observer`/`@computed`/`runInAction`) e Dio para rede. Referências a "ferramenta de RUM" apontam pra config do seu projeto (Datadog, Firebase Performance, Sentry, etc.) — troque pelo nome real.

## MobX Rebuild Optimization

Leia `REFERENCE.md` §MobX Rebuild Optimization: split granular de `Observer`, filhos `const` dentro de `Observer`, `@computed` pra valores derivados, batching com `runInAction`.

> As regras de MobX (rebuild em `Observer` inteiro, `@computed` puro, disposers de reaction) estão codificadas em `mobile:mobx` `REFERENCE.md`.

## Widget Tree Optimization

Leia `REFERENCE.md` §Widget Tree Optimization: construtores `const`, `ListView.builder`, `RepaintBoundary`, `AnimatedOpacity` vs `Opacity`, ressalvas de `IntrinsicHeight`, `MediaQuery.sizeOf`.

## Network and Images

Leia `REFERENCE.md` §Network Performance (Dio): `CancelToken` no dispose, `Future.wait` para chamadas paralelas, cache de resultado.

Leia `REFERENCE.md` §Image Performance: sempre passar dimensões explícitas pro widget de imagem do seu projeto.

## Memory Management

Leia `REFERENCE.md` §Memory Management: disposers de reaction MobX, dispose de controllers Flutter, limpar estado grande na navegação.

## Performance Checklist

Leia `REFERENCE.md` §Performance Checklist para o checklist completo pré-review.
