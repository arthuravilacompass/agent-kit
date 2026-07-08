#!/usr/bin/env python3
# desc: Usage census of invokable artifacts (commands/skills) by time window.
"""census_usage.py — usage census of a Claude Code project's invokable artifacts
(.claude/commands + .claude/skills): how many times each one was actually invoked, by
time window.

Fixes over v1 (census_claude_usage.py):

1. Baseline discount — v1 counted every textual occurrence of "/name" in the whole
   transcript as an invocation proxy. But an artifact's name also appears, every
   turn, inside the <system-reminder> blocks the harness reinjects (the "available
   skills/commands" listing with name + description) — and several descriptions cite
   the command itself with the slash (`/name ...`). This inflates the count for EVERY
   artifact equally, masking the ones nobody actually calls. This version strips the
   <system-reminder>...</system-reminder> spans BEFORE counting — what's left is
   textually closer to a real invocation (a "/name" typed by the user/assistant
   outside the reminder, or a Skill tool_use with input.skill == name).

2. Real span covered — v1 labeled columns "30d/60d/90d" without checking whether the
   project actually has that much transcript history. A project with 10 days of usage
   shows "90d: 0" for everything, which reads as "zero usage" when it's actually
   "zero data". This version prints the real span (oldest mtime → now) and warns when
   a requested window exceeds the available history.

Still a known (inherited) limitation: it's a textual proxy, not a semantic one — treat
ZERO across the whole window as the strong signal (not invoked), not small deltas
between artifacts (citation noise in prose/examples is still possible even after the
discount).

Usage:
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
    """Claude Code's sanitization convention for the project directory: absolute path
    with "/" swapped for "-", under ~/.claude/projects/."""
    key = str(workspace.resolve()).replace(os.sep, "-")
    return Path.home() / ".claude" / "projects" / key


def strip_auto_injected(text: str) -> str:
    """Baseline discount: strips <system-reminder>...</system-reminder> spans — content
    reinjected by the harness every turn, not a real user/agent invocation."""
    return SYSTEM_REMINDER_RE.sub("", text)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--workspace", default=".", help="project root containing .claude/ (default: cwd)")
    ap.add_argument("--windows", default="30,60,90", help="windows in days, comma-separated (default: 30,60,90)")
    args = ap.parse_args()

    workspace = Path(args.workspace).resolve()
    window_days = sorted(int(d) for d in args.windows.split(","))
    windows = {f"{d}d": d * 86400 for d in window_days}

    names = artifacts(workspace)
    if not names:
        print(f"no command/skill found in {workspace}/.claude/")
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

    print("| artifact | " + " | ".join(windows) + " |")
    print("|---|" + "---|" * len(windows))
    last_window = f"{window_days[-1]}d"
    for n in sorted(names, key=lambda x: counts[x][last_window]):
        c = counts[n]
        print(f"| {n} | " + " | ".join(str(c[w]) for w in windows) + " |")

    if files and oldest_mtime is not None:
        coverage_days = (now - oldest_mtime) / 86400
        span_start = time.strftime("%Y-%m-%d", time.localtime(oldest_mtime))
        span_end = time.strftime("%Y-%m-%d", time.localtime(now))
        print(f"\n_{len(files)} transcripts · real span covered: {span_start} → {span_end} "
              f"(~{coverage_days:.0f}d of history) · generated {time.strftime('%Y-%m-%d')}_")
        for w, span in windows.items():
            req_days = span / 86400
            if coverage_days < req_days:
                print(f"WARNING: requested window '{w}' ({req_days:.0f}d) exceeds the real "
                      f"available history (~{coverage_days:.0f}d) — this column's count is "
                      "partial, not 'confirmed zero usage'.")
    else:
        print(f"\n_0 transcripts found in {transcripts_dir}_")


if __name__ == "__main__":
    main()
