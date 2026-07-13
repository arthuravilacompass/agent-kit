#!/usr/bin/env bash
# desc: UserPromptSubmit — advisory: deterministic pattern-match detects posture/checkpoint opportunities in the prompt (done-claim → grill-me pre-done, direction lock-in → grill-me pre-plan, A-or-B → bohr, live hypotheses → schrodinger, validate-solution → zeno, coupled change → maxwell, worth-it → sagan, past-discussion memory → council-recall) and injects a one-line suggestion; max one per prompt, once per signal per session.
#
# Closes the Council's on-demand gap: postures only helped when the operator
# remembered to invoke them. Design follows the proactive-support literature
# (CHI 2025 "Assistance or Disruption?") and the ecosystem's skill-activation
# hook pattern: user initiative wins (a prompt that is already a slash command
# or names a posture is skipped), silence is the default (conservative
# patterns, max ONE suggestion per prompt, once per signal per session), and
# the injection is purely advisory — it never blocks the prompt.
#
# Failure modes, documented: (1) the prompt field name has drifted across
# Claude Code versions — the hook reads `prompt` then `user_input`; both
# absent -> silent; (2) regex false positive -> hedged by advisory posture +
# the once-per-session marker; (3) marker-dir write failure never blocks the
# suggestion itself (mirrors codegen-staleness); (4) absent `session_id`
# collapses the once-per-session marker to once-ever (same caveat family as
# codegen-staleness); (5) a prompt that mentions a posture name incidentally
# (e.g. "vi um documentário sobre carl sagan") is fully silenced by the
# skip-guard — accepted tradeoff, the hook always fails toward silence; (6)
# SIGNALS suggestions reference live skills by name — renaming/demoting a
# posture requires updating this table (the kit's demote-pairing discipline
# is the guard; no automated drift detector by design).

set -uo pipefail

if ! command -v python3 &>/dev/null; then
    exit 0
fi

INPUT_JSON=$(cat)
export INPUT_JSON

# Lossless anchor union derived branch-by-branch from SIGNALS (adversarial
# review 2026-07-13): every alternation branch of every signal pattern below
# contains at least one of these mandatory ASCII-safe literals. A false
# positive here just falls through to python, which decides exactly; NEVER
# add a SIGNALS branch without an ASCII-safe anchor here. Measured saving:
# ~50-70ms interpreter spawn per non-matching prompt (UserPromptSubmit fires
# on every turn). 2026-07-13 (proplasma/anamnesis anchors): "go" and "isso"
# are common substrings (algo/logo/category; any pt prompt saying "isso") —
# the union is measurably leakier now; python still decides exactly, the
# saving only applies to prompts missing every literal.
if ! LC_ALL=C grep -qiE 'pronto|commitar|comitar|finalizar|fechar|entregar|done|ready|commit|ship|merge|finalize|qual|which|escolher|choose|devo|should|usar|pode|might|could|sei|sure|duas|hip|two|mais|valida|validate|resolve|cobre|funciona|does|solve|cover|handle|refatorar|mexer|mudar|alterar|refactor|change|touch|impacto|propagate|vale|compensa|worth|devemos|invest|vamos|seguir|go|isso|didn|haven|talked' <<< "$INPUT_JSON"; then
    exit 0
fi

MARKER_DIR="${CLAUDE_PLUGIN_DATA:-${TMPDIR:-/tmp}/agent-kit-council}/posture-signal"
export MARKER_DIR

python3 << 'PYEOF'
import hashlib, json, os, re, sys, unicodedata

try:
    data = json.loads(os.environ.get("INPUT_JSON", "{}"))
except Exception:
    sys.exit(0)


def main(data):
    prompt = data.get("prompt") or data.get("user_input") or ""
    if not isinstance(prompt, str):
        sys.exit(0)

    # NFC normalization + whitespace collapse (two confirmed silent-false-negative
    # bugs): NFD (decomposed) input makes every accented char-class (n[aã]o,
    # [ée], [cç]) silently never match — NFC emits, NFD is dead silent; and the
    # SIGNALS patterns' `.`-based proximity spans don't cross newlines, so a
    # multi-line pasted prompt silently never matches — collapsing whitespace to
    # single spaces fixes it without needing re.DOTALL.
    low = re.sub(r"\s+", " ", unicodedata.normalize("NFC", prompt).lower()).strip()
    if not low:
        sys.exit(0)

    # User initiative wins: an explicit command, or a prompt that already names a
    # posture/checkpoint, means the operator is ahead of the signal — stay silent.
    if low.startswith("/"):
        sys.exit(0)
    if re.search(r"(council:|council-recall|grill-me|\b(bohr|schr[oö]dinger|epicurus|sagan|maxwell|zeno)\b)", low):
        sys.exit(0)

    # (signal, pattern, suggestion) — priority order, first match wins. Proximity
    # bounds ({0,40}/{0,50}/{0,60}) are deliberately bounded so unrelated clauses
    # don't bridge into a false match; the exact values are tested-not-sacred.
    SIGNALS = [
        ("predone",
         r"(t[aá] pronto|est[aá] pronto|podemos +(commitar|comitar|finalizar|fechar|entregar)|pronto +pra? +(commit|entrega|merge)|(posso|devo) +(commitar|comitar)|is +(it|this) +(done|ready)|ready +to +(commit|ship|merge)|can +we +(commit|ship|merge|finalize)|call +it +done)",
         "this reads like a definition-of-done moment — consider `/core:grill-me pre-done` before calling it done."),
        # proplasma/anamnesis (2026-07-13): mined from a neighbor trigger
        # taxonomy; both point at EXISTING kit mechanisms (grill-me pre-plan
        # checkpoint, council-recall) — no new posture. proplasma sits above
        # bohr: when lock-in language and an A-or-B co-occur, the pre-plan
        # consult subsumes the dichotomy probe (the reverse doesn't hold);
        # accepted loss: it also outranks schrodinger/zeno on co-occurrence.
        # \b on every opening token is load-bearing: pt imperfect tense
        # ("está[vamos com a] abordagem", "em[bora seguir com]") and EN
        # compounds ("tab[lets go with]") otherwise match inside words. EN
        # "commit to" is allowlisted to direction nouns so git phrasing
        # ("commit to main/this branch") stays silent.
        # 2026-07-13 (blind review, post-ship): the open `vamos +de +<any
        # noun>` branch was removed — blind review demonstrated it's an
        # open word class (blocklisting idioms is whack-a-mole: "carro",
        # "pizza", "metrô", "férias"...) and that a multi-token X escapes
        # the ou-guard ("vamos de arquitetura limpa ou clean MVC?" fired on
        # an open question). Accepted, documented conservative false
        # negative: "vamos de MobX então" no longer fires — see the pinned
        # case in hook-cases.jsonl.
        ("proplasma",
         r"(\b(vamos|bora) +seguir +com|\bvamos +com +(ess[ae]\b|a +op[cç][aã]o|a +abordagem|o +plano|a +ideia)|\bvamos +ness[ae] +(abordagem|op[cç][aã]o|dire[cç][aã]o|linha|caminho|rota)|\b(let['’]?s|we['’]?ll) +(go +with|commit +to +((the|this|that|an?) +)?(approach|plan|direction|option|idea|design|architecture|strategy|stack)\b))",
         "a direction is being locked in — consider `/core:grill-me pre-plan` before committing to it."),
        ("bohr",
         r"(qual +d(os|as) +d(oi|ua)s|which +of +the +two|escolher +entre|choose +between|(devo|should +(i|we)) +(usar|use|go +with|ir +de) +\S.{0,40}\b(ou|or)\b)",
         "this reads like an A-or-B choice — `/council:bohr` tests whether the dichotomy is real before you pick a side."),
        ("schrodinger",
         r"(pode +ser +\S.{0,50}\bou\b|(might|could) +be +\S.{0,50}\bor\b|n[aã]o +sei +se +[ée]|not +sure +(if|whether)|duas +hip[oó]teses|two +hypotheses|mais +de +uma +(causa|explica[cç][aã]o))",
         "more than one hypothesis looks alive — `/council:schrodinger` keeps them open until an observation discriminates."),
        ("zeno",
         r"(validar? +(essa|esta|a) +(solu[cç][aã]o|abordagem)|validate +(this|the) +(solution|approach|fix)|ser[aá] +que +(isso +)?(resolve|cobre)|does +(this|it) +(actually +|really +)?(solve|cover|handle)|essa +solu[cç][aã]o +(resolve|funciona))",
         "a proposed solution is being validated — the `council:zeno` agent pushes its invariants to the limits (zero, one, infinity, fail-midway) to find where it breaks."),
        ("maxwell",
         r"((refatorar|mexer +em|mudar|alterar|refactor|change|touch) +.{0,60}(acoplad|coupled|usado +em +(todo|v[aá]rios)|used +(everywhere|in +many)|toda +a +base|across +the +(codebase|app))|impacto +dessa +mudan[cç]a|how +does +this +change +propagate)",
         "this touches something coupled — the `council:maxwell` agent maps how the change propagates before you touch it."),
        ("sagan",
         r"(vale +a +pena|compensa +(fazer|construir|investir)|worth +(the +effort|building|investing|doing)|devemos +investir|should +we +invest)",
         "an effort-worthiness question — `/council:sagan` calibrates whether it matters, at what scale, and whether it survives time."),
        # anamnesis last: recall is orthogonal support — when it co-fires with
        # a substantive signal the posture is more useful now, and
        # council-recall is documented as invoked *together with* the posture.
        # Every pt branch requires isso/disso (also its ASCII anchor);
        # 3rd-person singular verbs require an explicit "a gente" subject so
        # reported third-party decisions ("o backend já decidiu isso") stay
        # silent; bare EN simple past requires before/earlier so "we talked
        # about this morning" stays silent.
        ("anamnesis",
         r"(\bj[aá] +(n[aã]o +)?(discutimos|decidimos|falamos|conversamos|vimos) +(sobre +)?(isso|disso)|\ba +gente +j[aá] +(n[aã]o +)?(discutiu|decidiu|falou|conversou) +(sobre +)?(isso|disso)|\bisso +j[aá] +(n[aã]o +)?foi +(discutido|decidido|falado|conversado)|\bdidn['’]?t +we +(already +)?(discuss|decide|talk +about|go +over|cover)|\bhaven['’]?t +we +(already +)?(discussed|decided|talked +about|covered|settled|been +over)|\bwe['’]ve +(already +)?talked +about +this|\bwe +(already +)?talked +about +this +(before|earlier)\b)",
         "you're reaching for a past discussion — `/council:council-recall` queries the episodic memory for cases that rhyme."),
    ]

    session_id = str(data.get("session_id", ""))
    marker_dir = os.environ.get("MARKER_DIR", "")

    for name, pattern, suggestion in SIGNALS:
        if not re.search(pattern, low):
            continue
        # Once per signal per session (same rationale as codegen-staleness: without
        # session_id the contract would become once-per-machine-ever). A marker hit
        # here means only THIS signal is spent — continue, don't exit, so a
        # lower-priority signal still available can fire on the same prompt.
        marker = os.path.join(marker_dir, hashlib.sha1((session_id + "|" + name).encode()).hexdigest())
        if marker_dir and os.path.exists(marker):
            continue
        if marker_dir:
            try:
                os.makedirs(marker_dir, exist_ok=True)
                open(marker, "w").close()
            except Exception:
                pass  # marker failure never blocks the suggestion itself
        print(json.dumps({
            "hookSpecificOutput": {
                "hookEventName": "UserPromptSubmit",
                "additionalContext": (
                    "[posture-signal] " + suggestion +
                    " (Deterministic pattern-match on the prompt; advisory - ignore freely."
                    " Fires once per signal per session.)"
                ),
            }
        }))
        sys.exit(0)  # max ONE suggestion per prompt


# Broad exception guard: an uncaught traceback after this point would exit 1
# with stderr noise on every prompt — this hook must fail toward silence.
# SystemExit subclasses BaseException (not Exception), so every sys.exit(0)
# inside main() propagates untouched; only genuinely unexpected errors land here.
try:
    main(data)
except Exception:
    sys.exit(0)

sys.exit(0)
PYEOF

exit $?
