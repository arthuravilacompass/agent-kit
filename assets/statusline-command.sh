#!/usr/bin/env bash
# Claude Code status line — Vedovelli style
#
# MANUAL INSTALL (this is an asset, not a plugin component — Claude Code does not
# load it automatically). To wire it:
#   1. Copy this file somewhere stable, e.g. ~/.claude/statusline-command.sh
#   2. chmod +x it.
#   3. Add to your settings.json (project or user level):
#        "statusLine": { "type": "command", "command": "bash ~/.claude/statusline-command.sh" }
#   Requires `jq` on PATH.

input=$(cat)

# ── Extract fields ──────────────────────────────────────────────────────────────
cwd=$(echo "$input"          | jq -r '.workspace.current_dir // .cwd // empty')
model_name=$(echo "$input"   | jq -r '.model.display_name // empty')
ctx_size=$(echo "$input"     | jq -r '.context_window.context_window_size // empty')
used_pct=$(echo "$input"     | jq -r '.context_window.used_percentage // empty')
daily_pct=$(echo "$input"    | jq -r '.rate_limits.five_hour.used_percentage // empty')
weekly_pct=$(echo "$input"   | jq -r '.rate_limits.seven_day.used_percentage // empty')
daily_reset=$(echo "$input"  | jq -r '.rate_limits.five_hour.resets_at // empty')
weekly_reset=$(echo "$input" | jq -r '.rate_limits.seven_day.resets_at // empty')

# ── Git branch ──────────────────────────────────────────────────────────────────
branch=""
if [ -n "$cwd" ] && git -C "$cwd" rev-parse --git-dir > /dev/null 2>&1; then
  branch=$(git -C "$cwd" -c core.hooksPath=/dev/null symbolic-ref --short HEAD 2>/dev/null \
           || git -C "$cwd" rev-parse --short HEAD 2>/dev/null)
fi

# ── Colors ──────────────────────────────────────────────────────────────────────
DIM="\033[2m"
BLUE="\033[38;2;82;182;215m"    # #52B6D7 cyan
YELLOW="\033[38;2;201;196;91m"  # #C9C45B yellow-green
GREEN="\033[38;2;72;201;108m"   # #48C96C green
RED="\033[31m"
R="\033[0m"

# ── Helpers ─────────────────────────────────────────────────────────────────────
fmt_tokens() {
  local n="$1"
  [ -z "$n" ] || [ "$n" = "null" ] && return
  if awk "BEGIN{exit !($n >= 1000000)}"; then
    awk "BEGIN{printf \"%.1fm\", $n/1000000}"
  else
    awk "BEGIN{printf \"%.1fk\", $n/1000}"
  fi
}

# Daily (5h) thresholds — stricter: <10% green, <=50% yellow, else red
daily_color() {
  local pct="$1"
  if awk "BEGIN{exit !($pct < 10)}"; then
    printf "%b" "$GREEN"
  elif awk "BEGIN{exit !($pct <= 50)}"; then
    printf "%b" "$YELLOW"
  else
    printf "%b" "$RED"
  fi
}

# Weekly (7d) thresholds — relaxed: <50% green, <=75% yellow, else red
weekly_color() {
  local pct="$1"
  if awk "BEGIN{exit !($pct < 50)}"; then
    printf "%b" "$GREEN"
  elif awk "BEGIN{exit !($pct <= 75)}"; then
    printf "%b" "$YELLOW"
  else
    printf "%b" "$RED"
  fi
}

color_dots() {
  local pct="$1" col="$2"
  [ -z "$pct" ] || [ "$pct" = "null" ] && return
  local filled=$(awk "BEGIN{n=int($pct/10+0.5); if(n>10)n=10; if(n<0)n=0; print n}")
  local empty=$((10 - filled))
  local dots="${col}" i=0
  while [ $i -lt $filled ]; do dots="${dots}●"; i=$((i+1)); done
  dots="${dots}${DIM}"
  i=0
  while [ $i -lt $empty ]; do dots="${dots}○"; i=$((i+1)); done
  dots="${dots}${R}"
  printf "%b" "$dots"
}

fmt_time() {
  local ts="$1"
  [ -z "$ts" ] || [ "$ts" = "null" ] && return
  date -r "$ts" "+%I:%M %p" 2>/dev/null | sed 's/^0//; s/ AM$/am/; s/ PM$/pm/'
}

fmt_day_time() {
  local ts="$1"
  [ -z "$ts" ] || [ "$ts" = "null" ] && return
  date -r "$ts" "+%a, %I:%M %p" 2>/dev/null | sed 's/, 0/, /; s/ AM$/am/; s/ PM$/pm/'
}

time_remaining() {
  local ts="$1"
  [ -z "$ts" ] || [ "$ts" = "null" ] && return
  local now diff h m
  now=$(date +%s)
  diff=$((ts - now))
  [ "$diff" -le 0 ] && echo "now" && return
  h=$((diff / 3600))
  m=$(( (diff % 3600) / 60 ))
  [ "$h" -gt 0 ] && echo "${h}h${m}m" || echo "${m}m"
}

# ── Line 1: Model + context window ─────────────────────────────────────────────
line1=""
if [ -n "$model_name" ] && [ "$model_name" != "null" ]; then
  ctx_fmt=$(fmt_tokens "$ctx_size")
  line1="${BLUE}${model_name}"
  [ -n "$ctx_fmt" ] && line1="${line1} (${ctx_fmt} context)"
  line1="${line1}${R}"

  if [ -n "$used_pct" ] && [ "$used_pct" != "null" ] && [ -n "$ctx_size" ] && [ "$ctx_size" != "null" ]; then
    used_tokens=$(awk "BEGIN{printf \"%d\", $ctx_size * $used_pct / 100}")
    free_tokens=$(awk "BEGIN{printf \"%d\", $ctx_size * (100 - $used_pct) / 100}")
    used_fmt=$(fmt_tokens "$used_tokens")
    free_fmt=$(fmt_tokens "$free_tokens")
    free_pct=$(awk "BEGIN{printf \"%.0f\", 100 - $used_pct}")
    pct_int=$(awk "BEGIN{printf \"%.0f\", $used_pct}")
    line1="${line1} ${DIM}|${R} ${YELLOW}${used_fmt} / ${ctx_fmt} (${pct_int}% used)${R}"
    line1="${line1} ${DIM}|${R} ${GREEN}${free_fmt} ${free_pct}% free${R}"
  fi
fi

# ── Line 2: Usage bars + git branch ────────────────────────────────────────────
line2=""
if [ -n "$daily_pct" ] && [ "$daily_pct" != "null" ]; then
  pct_int=$(awk "BEGIN{printf \"%.0f\", $daily_pct}")
  dcol=$(daily_color "$daily_pct")
  line2="${dcol}current:${R} $(color_dots "$daily_pct" "$dcol") ${dcol}${pct_int}%${R}"
fi
if [ -n "$weekly_pct" ] && [ "$weekly_pct" != "null" ]; then
  pct_int=$(awk "BEGIN{printf \"%.0f\", $weekly_pct}")
  wcol=$(weekly_color "$weekly_pct")
  [ -n "$line2" ] && line2="${line2} ${DIM}|${R} "
  line2="${line2}${wcol}weekly:${R} $(color_dots "$weekly_pct" "$wcol") ${wcol}${pct_int}%${R}"
fi
if [ -n "$branch" ]; then
  [ -n "$line2" ] && line2="${line2} ${DIM}|${R} "
  line2="${line2}${GREEN}${branch}${R}"
fi

# ── Line 3: Reset times ─────────────────────────────────────────────────────────
line3=""
if [ -n "$daily_reset" ] && [ "$daily_reset" != "null" ]; then
  remaining=$(time_remaining "$daily_reset")
  line3="${DIM}resets $(fmt_time "$daily_reset") (${remaining})${R}"
fi
if [ -n "$weekly_reset" ] && [ "$weekly_reset" != "null" ]; then
  [ -n "$line3" ] && line3="${line3} ${DIM}|${R} "
  line3="${line3}${DIM}resets $(fmt_day_time "$weekly_reset")${R}"
fi

# ── Output ──────────────────────────────────────────────────────────────────────
[ -n "$line1" ] && printf "%b\n" "$line1"
[ -n "$line2" ] && printf "%b\n" "$line2"
[ -n "$line3" ] && printf "%b\n" "$line3"
