# agent-kit

*Português · [English](README.md) — o arquivo em inglês é a fonte de verdade.*

> **agent-kit é um kit de disciplina epistêmica para trabalho Flutter/Dart com Claude Code — verificadores determinísticos para o que o harness não checa, mais as posturas de raciocínio para usá-los bem.**

**Como ler o mapa.** A banda de cima é entrada — três jeitos: frase solta, comando `/ce-*`, ou sempre ativo (sem invocação). O trilho embaixo é condução: `superpowers` é dono de Discover, `compound-engineering` ("CE") é dono de Plan até Ship — os dois plugins externos, instalados à parte. Este repo (`/core:*`, `/team:*`) é o piso sempre ativo sob qualquer condutor.

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="assets/routing-diagram-dark.svg">
  <img alt="agent-kit routing map: how you enter (loose phrase, /ce-*, always-on) and who conducts each stage" src="assets/routing-diagram-light.svg">
</picture>

*O gate depois de Ship é `/core:review-local`; a captura depois é `/ce-compound` e `core:learn`. `/core:tech-breakdown` (beco sem saída, pontilhado) nunca entra na CE sozinho — a saída dele é copiada e colada em `/ce-plan`.*

Só os hooks são garantia: disparam sozinhos. Toda skill, gate e postura roda porque você invocou. Lifecycle, regra de promoção, teto sempre-ativo, publicação e os gates: **[docs/OPERATIONS.md](docs/OPERATIONS.md)**.

## O que vem junto

Quatro plugins instaláveis por um marketplace local: `mobile` (carro-chefe, toolkit Flutter/Dart), `core` (mecanismo determinístico — sempre necessário), `council` (lentes de raciocínio para decisões caras de reverter, recomendado com `core`), `team` (cerimônias ágeis, refinement e comunicação com squad). Detalhe de cada um, requisitos e o que falta se você pular um: tabela completa em **[README.md](README.md#whats-included)**.

**A stack que `mobile` assume:** MobX + `get_it`/`injectable` (scaffolding também assume `dartz`). Em Bloc/Riverpod o check de DI simplesmente não dispara — sem falso positivo, mas sem cobertura também.

Catálogo completo de toda skill, agente, hook e script: navegue `plugins/*/skills`, `plugins/*/agents`, `plugins/*/hooks`. Severidade de cada dependência (o que quebra se faltar): tabela de requisitos em **[README.md](README.md#requirements)**.

## Instalação

Os comandos de clone e instalação vivem no [README.md](README.md#1-clone-once) — copie de lá; esta página não duplica comandos.

Verifique com `~/dev/agent-kit/scripts/doctor.sh` — checa CLI, marketplace, plugins e os gates do próprio kit, e imprime o comando exato pra corrigir o que faltar.

Comandos nativos passo a passo, emissão de `AGENTS.md` para outras ferramentas de IA (Copilot, Cursor), e desinstalação: **[docs/INSTALL.md](docs/INSTALL.md)**.

## Qual ferramenta, quando

A convenção de fronteira: frase solta → `superpowers`; slash command → CE — a sintaxe elege, não o reconhecimento de padrão. A tabela completa, indexada por situação (ideia vaga, ticket, código quebrado, decisão cara de desfazer, review, e mais), vive na fonte de verdade: **[README.md](README.md#which-tool-when)**.

---

[docs/OPERATIONS.md](docs/OPERATIONS.md) · [docs/INSTALL.md](docs/INSTALL.md) · [CHANGELOG.md](CHANGELOG.md)
