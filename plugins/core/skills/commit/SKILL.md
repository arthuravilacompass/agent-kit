---
name: commit
description: Invoque para rodar validação pré-commit (lint + testes) e criar um commit convencional a partir do diff staged — nunca commita sem aprovação explícita do usuário.
disable-model-invocation: true
---

# commit — Commit Padronizado

Valida o diff staged (lint, depois testes) e gera uma mensagem de commit convencional a partir dele. Só executa `git commit` depois de aprovação explícita do usuário.

## Config do projeto

Este skill assume que o projeto consumidor define:
- **Comando de lint/static analysis** (ex.: `flutter analyze`, `eslint .`, `ruff check`).
- **Comando de testes** (ex.: `flutter test`, `npm test`, `pytest`).

Sem essas configs, pule as steps 2/3 e avise o usuário que a validação automática não pôde rodar.

## Passos

1. **Verificar arquivos staged**

   Rode `git diff --cached --stat` para ver o que está staged.

   Se nada estiver staged, rode `git diff --stat` para mostrar as mudanças não staged e pergunte ao usuário: "Nothing is staged. Which files would you like to stage?"

2. **Rodar lint**

   Rode o comando de lint/static-analysis do projeto (config acima).

   Se o lint falhar, reporte todos os erros e **PARE**. Não prossiga para o commit.

3. **Rodar testes**

   Rode o comando de testes do projeto (config acima).

   Se os testes falharem, reporte as falhas e **PARE**. Não prossiga para o commit.

4. **Analisar o diff staged**

   Rode `git diff --cached` para entender o que está mudando.

5. **Gerar a mensagem de commit**

   Crie uma mensagem seguindo este formato:
   ```
   <type>: <description>

   <optional body>
   ```

   Regras:
   - Type: `feat`, `fix`, `refactor`, `docs`, `test`, `chore`, `perf` ou `ci`
   - Description: inglês, modo imperativo, sem ponto final, máximo 72 caracteres
   - Body: opcional, adicione quando o título sozinho não for autoexplicativo
   - Sem emojis

6. **Apresentar para aprovação**

   Mostre ao usuário:
   - Resumo dos arquivos staged
   - Mensagem de commit proposta
   - Pergunte: "Proceed with this commit? Reply with: yes, edit [new message], or abort"

7. **Executar o commit somente após aprovação explícita**

   Só rode `git commit -m "..."` depois que o usuário confirmar com "yes".

   Se o usuário disser "edit", use a nova mensagem dele.
   Se o usuário disser "abort", pare.

## Regras invioláveis

Nunca pule lint ou testes. Nunca commite com `--no-verify`.
