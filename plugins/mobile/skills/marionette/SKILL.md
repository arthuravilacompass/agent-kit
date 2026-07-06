---
name: marionette
description: Invoque para validar visualmente mudanças de UI Flutter no app rodando no simulador — lançar o app em debug pra checks dirigidos por agente, tirar screenshots, tocar/rolar/dirigir telas, hot-reload após edits. Gatilhos em pt-BR — "confirma essa tela no simulador", "valida essa mudança visualmente", "screenshot do app rodando".
---

# Marionette — Validação Visual Dirigida por Agente

## Config do projeto

Flavors, env files, e a convenção de qual backend cada um aponta são específicos de cada app — preencha a tabela em `references/SETUP.md` §Environments & flavors com a config real do seu projeto antes de usar este skill em produção. O mecanismo de driving (conectar, listar elementos, tocar, screenshot, hot-reload) é genérico e não muda entre projetos.

## Overview

Conecta a sessão ao app Flutter rodando em debug no simulador via marionette MCP (LeanCode): `take_screenshots`, `tap`, `scroll_to`, `enter_text`, `get_logs`, `hot_reload`. Execução **inline na sessão principal** — o loop editar → hot_reload → re-screenshot depende do contexto da conversa (não delegar a subagent: screenshots de subagent são invisíveis pro usuário).

## Passo 0 — Preflight

As tools `marionette__*` estão disponíveis nesta sessão?

- **Não** e o usuário quer validação dirigida por agente → leia [references/SETUP.md](references/SETUP.md), passe os comandos de setup ao usuário e **PARE** (registro de MCP exige restart da sessão).
- **Não** e é um check rápido → fallback: peça screenshot manual ao usuário.
- **Sim** → siga.

## Pré-requisitos — explícitos, nunca defaults silenciosos

| Input | Como resolver |
|---|---|
| Device id do simulador | `xcrun simctl list devices booted` — vazio? pergunte ou boot |
| Backend alvo | Config do projeto: qual variável/env file decide o backend (geralmente não é o `--flavor` sozinho). Confira o backend que o script de launch imprime a cada run. |
| Estado logado | Fluxos autenticados (onboarding, checkout, perfil) exigem usuário logado no app |
| Feature-flag/onboarding visível | Config do projeto: se o app usa remote config pra controlar visibilidade de onboarding/feature, confira a flag relevante antes de assumir que a tela vai aparecer |

## Workflow

1. **Launch**: `bash scripts/run.sh -d <device-id> [-f <flavor>] [-t 600]` (deste skill) — mata runs duplicados, sobe o app em background, imprime o URI `ws://` de connect. Flavor e env file: convenção do projeto (ver `references/SETUP.md`), override com `-e`.
2. **Connect**: `marionette__connect` com o URI impresso — **como próxima ação, sem trabalho no meio**: VM service ocioso desanexa.
3. **Drive**: `get_interactive_elements` → `tap` / `enter_text` / `scroll_to`. Match por `ValueKey` > texto (widget sem key? ver Gotchas).
4. **Validar**: `take_screenshots` (renderiza como imagem pro agente) → compare com o esperado (design de referência / spec / screenshot do usuário).
5. **Iterar**: edite o código → `marionette__hot_reload` → re-screenshot. `get_logs` para eventos de analytics.

## Gotchas

| Sintoma | Causa / Fix |
|---|---|
| Tools `marionette__*` não aparecem | MCP server só carrega no boot da sessão — restart; persiste? registro pode ter sido feito fora da raiz do projeto/workspace (ver `references/SETUP.md`) |
| VM service não anexa / "OS terminated debug connection for being inactive" | Simulador com estado acumulado — reboot **sem erase**: `xcrun simctl shutdown <id> && xcrun simctl bootstatus <id> -b` (erase apaga Keychain/login), depois **re-rode o run.sh** |
| URI file vazio após timeout | Veja `/tmp/marionette_run.log`; confirme que não há runs duplicados: `pgrep -f main_marionette` |
| Widget não encontrado pelas tools | Adicione `ValueKey('...')` no widget alvo e `hot_reload` |
| App caiu em backend errado | A variável de ambiente que decide o backend (config do projeto) ≠ esperado — troque o env file ou o valor, não o `--flavor` |

## Quando NÃO usar

- Comparação estática código × design de referência sem precisar do app rodando → use a ferramenta de comparação do seu setup, se houver.
- Review de código → skills de review (`mobile:code-review-mobile`).
