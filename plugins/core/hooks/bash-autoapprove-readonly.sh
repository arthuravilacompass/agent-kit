#!/usr/bin/env bash
# PreToolUse(Bash) — fallback auto-approve para comandos read-only.
#
# v2 (compound-aware): decompõe comandos compostos em vez de recusar todo metacaractere.
# Aprova SOMENTE se TODO segmento (e todo comando dentro de $()/crase) for read-only.
# Invariante de segurança: qualquer ambiguidade (aspas desbalanceadas, comando
# desconhecido, redirect pra arquivo, substituição aninhada, `&` background) -> DEFERE.
# Parse-failure = defer, NUNCA approve.
#
# NUNCA bloqueia (nunca exit 2 / deny) — só emite `allow` ou defere (`{}`).
# Limites conhecidos (deferem -> caem no prompt normal):
#   - redirect pra ARQUIVO (`> f`, `>> f`, `2> f`): pode escrever. Só fd-dup (`2>&1`)
#     e `/dev/null` são aprovados.
#   - `sed`/`awk`/`xargs`/`find`/`mkdir`/`cp`/`mv`/`rm`/`tee`: escrevem ou executam.
#   - `for`/`while`/`if` (palavras-chave de shell como 1º token) -> desconhecido -> defere.
#   - substituição de comando ANINHADA ($() dentro de $()) -> defere.
# O mecanismo primário de redução de prompt continua sendo o sandbox; este hook só
# ajuda quando o sandbox está inativo ou o comando cai fora dele.

INPUT_JSON=$(cat)
export INPUT_JSON

python3 <<'PY'
import json, os, shlex, sys

def defer():
    print("{}")
    sys.exit(0)

def allow(reason):
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "allow",
            "permissionDecisionReason": reason,
        }
    }))
    sys.exit(0)

try:
    data = json.loads(os.environ.get("INPUT_JSON", "{}"))
    cmd = (data.get("tool_input", {}) or {}).get("command", "")
except Exception:
    defer()

if not cmd or not cmd.strip():
    defer()

# `cd` é seguro (muda diretório, não escreve). `:`/`true` são no-ops.
READ_ONLY = {
    "cd", ":", "true",
    "ls", "cat", "head", "tail", "wc", "echo", "grep", "egrep", "fgrep", "rg",
    "which", "file", "stat", "diff", "uniq", "cut", "tr", "nl", "basename",
    "dirname", "realpath", "tree", "pwd", "printf", "column", "comm", "sort",
}
# Deliberadamente FORA: find, xargs, sed, awk, mkdir, cp, mv, rm, tee, dd (escrevem/executam).

GIT_RO = {
    "status", "log", "diff", "show", "blame", "ls-files", "ls-tree", "grep",
    "rev-parse", "merge-base", "describe", "reflog", "for-each-ref", "cat-file",
    "shortlog", "fetch", "rev-list", "name-rev", "verify-pack", "count-objects",
}


def cmd_readonly(tokens):
    """tokens = um único segmento já tokenizado (sem operadores). True se read-only."""
    if not tokens:
        return True  # só atribuições de env restaram; substituições validadas à parte
    cmd0, rest = tokens[0], tokens[1:]

    if cmd0 in READ_ONLY:
        if cmd0 == "sort":  # `-o`/`--output` escreve arquivo
            for a in rest:
                if a in ("-o", "--output") or a.startswith("--output="):
                    return False
        return True

    if cmd0 == "git":
        g = list(rest)
        while g and g[0].startswith("-"):
            if g[0] == "-C" and len(g) >= 2:  # só `-C <path>`; `-c`/outras -> recusa
                g = g[2:]
                continue
            return False
        if not g:
            return False
        sub, args = g[0], g[1:]
        if sub == "config":
            return bool(args and args[0] in ("--get", "--get-all", "--list", "-l"))
        if sub == "branch":
            return not any(a in ("-d", "-D", "-m", "-M", "--delete", "--move") for a in args)
        if sub == "tag":
            return not any(a in ("-d", "--delete", "-f", "--force") for a in args)
        if sub == "remote":
            return not (args and args[0] in ("add", "remove", "rm", "set-url", "rename", "prune", "set-head"))
        return sub in GIT_RO

    if cmd0 == "flutter":
        if rest[:1] in (["analyze"], ["test"], ["doctor"]):
            return True
        return rest[:2] in (["pub", "get"], ["pub", "deps"])

    if cmd0 == "dart":
        if rest[:1] in (["analyze"], ["test"]):
            return True
        if rest[:2] in (["pub", "get"], ["pub", "deps"]):
            return True
        if rest[:1] == ["format"]:
            return "--output=none" in rest or ("-o" in rest and "none" in rest)
        return False

    return False


def strip_env_assignments(tokens):
    i = 0
    while i < len(tokens):
        t = tokens[i]
        if "=" in t and not t.startswith("-") and t.split("=", 1)[0].isidentifier():
            i += 1
            continue
        break
    return tokens[i:]


def extract_substitutions(s):
    """Remove $(...) e `...`, devolve (texto_sem_subst, [inners]). None se aninhado/desbalanceado."""
    subs, out, i, n = [], [], 0, len(s)
    while i < n:
        c = s[i]
        if c == "`":
            j = s.find("`", i + 1)
            if j == -1:
                return None, None
            subs.append(s[i + 1:j])
            out.append("__SUBST__")  # sem espaços: preserva `VAR=$(...)` como 1 token
            i = j + 1
            continue
        if c == "$" and i + 1 < n and s[i + 1] == "(":
            depth, j = 1, i + 2
            while j < n and depth:
                if s[j] == "(":
                    depth += 1
                elif s[j] == ")":
                    depth -= 1
                j += 1
            if depth:
                return None, None
            inner = s[i + 2:j - 1]
            if "$(" in inner or "`" in inner:
                return None, None  # aninhado -> complexo demais -> defere
            subs.append(inner)
            out.append("__SUBST__")  # sem espaços: preserva `VAR=$(...)` como 1 token
            i = j
            continue
        out.append(c)
        i += 1
    return "".join(out), subs


SEP_OPS = {"|", "||", "&&", ";", "|&"}


def command_is_readonly(text, _depth=0):
    if _depth > 2:
        return False
    # Newlines separam statements; shlex(whitespace_split) os engole. Normaliza pra `;`
    # ANTES de tokenizar, senão `echo hi\nrm -rf x` viraria UM segmento cujo cmd0 (echo)
    # parece read-only -> aprovaria o `rm`. Dentro de aspas, o `;` fica literal (seguro).
    text = text.replace("\r\n", "\n").replace("\r", "\n").replace("\n", ";")
    stripped, subs = extract_substitutions(text)
    if stripped is None:
        return False
    for sub in subs:  # toda substituição precisa ser read-only
        if not command_is_readonly(sub, _depth + 1):
            return False

    # Tokeniza respeitando aspas; operadores (| & ; < >) viram tokens próprios.
    try:
        lex = shlex.shlex(stripped, posix=True, punctuation_chars=True)
        lex.whitespace_split = True
        tokens = list(lex)
    except ValueError:
        return False  # aspas desbalanceadas etc.

    segments, cur, i = [], [], 0
    while i < len(tokens):
        t = tokens[i]
        if t in SEP_OPS:
            segments.append(cur)
            cur = []
            i += 1
            continue
        if t == "&":  # background -> não verificável -> defere
            return False
        # Operador de redirect/grouping é um token feito SÓ de pontuação (<>&()).
        # NÃO use substring (`">" in t`): um arg como "a -> b" contém `>` e não é redirect.
        if t and all(c in "<>&()" for c in t):
            if "(" in t or ")" in t:  # subshell / process substitution -> não verificável
                return False
            if cur and cur[-1].isdigit():  # fd prefixo (ex.: o `2` de `2>&1`)
                cur.pop()
            nxt = tokens[i + 1] if i + 1 < len(tokens) else None
            if t in (">&", "<&"):  # duplicação de fd: alvo é número ou `-`
                if nxt is not None and (nxt.isdigit() or nxt == "-"):
                    i += 2
                    continue
                return False
            # demais redirects (`>`,`>>`,`<`,`&>`,...): só /dev/null é seguro
            if nxt == "/dev/null":
                i += 2
                continue
            return False
        cur.append(t)
        i += 1
    segments.append(cur)

    for seg in segments:
        seg = strip_env_assignments(seg)
        if not cmd_readonly(seg):
            return False
    return True


try:
    ok = command_is_readonly(cmd)
except Exception:
    defer()  # qualquer erro de parse -> defere (fail-safe, nunca aprova por engano)
if ok:
    allow("compound read-only command (every segment + substitution verified)")
defer()
PY
