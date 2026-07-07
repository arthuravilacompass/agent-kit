#!/usr/bin/env python3
# desc: Censo de uso dos artefatos invocáveis (commands/skills) por janela de tempo.
"""census_usage.py — censo de uso dos artefatos invocáveis de um projeto Claude Code
(.claude/commands + .claude/skills): quantas vezes cada um foi realmente invocado, por
janela de tempo.

Correções sobre a v1 (census_claude_usage.py):

1. Baseline discount — a v1 contava toda ocorrência textual de "/nome" no transcript
   inteiro como proxy de invocação. Mas o nome de um artefato também aparece, todo
   turno, dentro dos blocos <system-reminder> que o harness reinjeta (a listagem de
   "available skills/commands" com nome + descrição) — e várias descrições citam o
   próprio comando com a barra (`/nome ...`). Isso infla a contagem de TODO artefato
   igualmente, mascarando os que ninguém de fato chama. Esta versão remove os spans
   <system-reminder>...</system-reminder> ANTES de contar — o que sobra é textualmente
   mais próximo de invocação real (um "/nome" digitado pelo usuário/assistant fora do
   reminder, ou um tool_use de Skill com input.skill == nome).

2. Janela real coberta — a v1 rotulava colunas "30d/60d/90d" sem checar se o projeto
   de fato tem esse histórico de transcripts. Um projeto com 10 dias de uso mostra
   "90d: 0" para tudo, o que lê como "zero uso" quando na verdade é "zero dados".
   Esta versão imprime o span real (mtime mais antigo → agora) e avisa quando uma
   janela pedida excede o histórico disponível.

Ainda uma limitação conhecida (herdada): é um proxy textual, não semântico — trate
ZERO na janela inteira como o sinal forte (não invocado), não pequenos deltas entre
artefatos (ruído de citação em prosa/exemplo ainda é possível mesmo após o discount).

Uso:
  python3 census_usage.py --workspace /path/to/project [--windows 30,60,90]
"""
import argparse
import os
import re
import time
from pathlib import Path

SYSTEM_REMINDER_RE = re.compile(r"<system-reminder>.*?</system-reminder>", re.DOTALL)


def artifacts(workspace: Path) -> list[str]:
    names = {f.stem for f in (workspace / ".claude" / "commands").glob("*.md")}
    skills_dir = workspace / ".claude" / "skills"
    if skills_dir.is_dir():
        names |= {d.name for d in skills_dir.iterdir() if d.is_dir()}
    return sorted(names)


def project_transcripts_dir(workspace: Path) -> Path:
    """Convenção de sanitização do Claude Code p/ diretório de projeto: path absoluto
    com "/" trocado por "-", sob ~/.claude/projects/."""
    key = str(workspace.resolve()).replace(os.sep, "-")
    return Path.home() / ".claude" / "projects" / key


def strip_auto_injected(text: str) -> str:
    """Baseline discount: remove spans <system-reminder>...</system-reminder> — conteúdo
    reinjetado pelo harness todo turno, não invocação real do usuário/agente."""
    return SYSTEM_REMINDER_RE.sub("", text)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--workspace", default=".", help="raiz do projeto contendo .claude/ (default: cwd)")
    ap.add_argument("--windows", default="30,60,90", help="janelas em dias, separadas por vírgula (default: 30,60,90)")
    args = ap.parse_args()

    workspace = Path(args.workspace).resolve()
    window_days = sorted(int(d) for d in args.windows.split(","))
    windows = {f"{d}d": d * 86400 for d in window_days}

    names = artifacts(workspace)
    if not names:
        print(f"nenhum command/skill encontrado em {workspace}/.claude/")
        return

    pats = {
        n: re.compile(r'(?:^|[\s">(`])/' + re.escape(n) + r"\b|\"skill\"\s*:\s*\"" + re.escape(n) + r"\"")
        for n in names
    }

    transcripts_dir = project_transcripts_dir(workspace)
    files = sorted(transcripts_dir.glob("*.jsonl")) if transcripts_dir.is_dir() else []
    now = time.time()
    counts = {n: dict.fromkeys(windows, 0) for n in names}

    oldest_mtime = None
    for f in files:
        mtime = f.stat().st_mtime
        oldest_mtime = mtime if oldest_mtime is None else min(oldest_mtime, mtime)
        age = now - mtime
        text = strip_auto_injected(f.read_text(errors="ignore"))
        for n in names:
            k = len(pats[n].findall(text))
            if not k:
                continue
            for w, span in windows.items():
                if age <= span:
                    counts[n][w] += k

    print("| artefato | " + " | ".join(windows) + " |")
    print("|---|" + "---|" * len(windows))
    last_window = f"{window_days[-1]}d"
    for n in sorted(names, key=lambda x: counts[x][last_window]):
        c = counts[n]
        print(f"| {n} | " + " | ".join(str(c[w]) for w in windows) + " |")

    if files and oldest_mtime is not None:
        coverage_days = (now - oldest_mtime) / 86400
        span_start = time.strftime("%Y-%m-%d", time.localtime(oldest_mtime))
        span_end = time.strftime("%Y-%m-%d", time.localtime(now))
        print(f"\n_{len(files)} transcripts · janela real coberta: {span_start} → {span_end} "
              f"(~{coverage_days:.0f}d de histórico) · gerado {time.strftime('%Y-%m-%d')}_")
        for w, span in windows.items():
            req_days = span / 86400
            if coverage_days < req_days:
                print(f"AVISO: janela '{w}' pedida ({req_days:.0f}d) excede o histórico real "
                      f"disponível (~{coverage_days:.0f}d) — contagem dessa coluna é parcial, "
                      "não 'zero uso confirmado'.")
    else:
        print(f"\n_0 transcripts encontrados em {transcripts_dir}_")


if __name__ == "__main__":
    main()
