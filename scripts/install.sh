#!/usr/bin/env bash
# desc: Thin wrapper around `claude plugin marketplace add` + `claude plugin install` for named profiles.
set -uo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
MARKETPLACE="agent-kit"

usage() {
  cat <<'EOF'
Usage: install.sh [minimal|mobile|team|full] [--dry-run]
       install.sh --tool <name> [--out DIR]

Profiles (default: minimal):
  minimal   core + council
  mobile    minimal + mobile
  team      minimal + team
  full      core + council + team + mobile

Options:
  --dry-run    print the commands that would run, without executing them
  --tool NAME  instead of installing plugins, emit agent-kit's portable epistemic
               tier for another AI tool (currently: copilot -> AGENTS.md)
  --out DIR    with --tool, write output into DIR (default: current directory)
  -h, --help   show this help
EOF
}

profile="minimal"
profile_seen=0
dry_run=0
tool=""
tool_seen=0
out_dir="."

while [ $# -gt 0 ]; do
  case "$1" in
    minimal|mobile|team|full)
      profile="$1"
      profile_seen=1
      ;;
    --dry-run)
      dry_run=1
      ;;
    --tool)
      shift
      tool="${1:-}"
      tool_seen=1
      ;;
    --out)
      shift
      out_dir="${1:-}"
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "ERROR: unrecognized argument '$1'" >&2
      usage >&2
      exit 1
      ;;
  esac
  shift
done

# --- port emitter dispatch (the seam a --tool flag redirects to) ------------
# --tool emits the portable epistemic tier for another AI tool and exits; it
# does not install plugins, so it runs before the `claude` CLI check below.
if [ "$tool_seen" -eq 1 ]; then
  if [ "$profile_seen" -eq 1 ]; then
    echo "ERROR: a profile ('$profile') can't be combined with --tool — they are different modes (install plugins vs. emit a portable tier)." >&2
    usage >&2
    exit 1
  fi
  emit_args=("$tool" --out "$out_dir")
  [ "$dry_run" -eq 1 ] && emit_args+=(--dry-run)
  exec bash "$REPO_ROOT/scripts/emit-port.sh" "${emit_args[@]}"
fi

if ! command -v claude >/dev/null 2>&1; then
  echo "ERROR: 'claude' CLI not found on PATH — install Claude Code first: https://docs.claude.com/claude-code" >&2
  exit 1
fi

# --- profile -> plugin list resolution --------------------------------------
# (The `--tool <name>` flag dispatches above, before the `claude` CLI check, to
# scripts/emit-port.sh. Plugin install is the default path below when no --tool
# is given.)
case "$profile" in
  minimal) plugins=(core council) ;;
  mobile)  plugins=(core council mobile) ;;
  team)    plugins=(core council team) ;;
  full)    plugins=(core council team mobile) ;;
esac

# --- apply step (the seam a --tool flag would redirect) ---------------------
run_cmd() {
  echo "+ $*"
  if [ "$dry_run" -eq 1 ]; then
    return 0
  fi
  "$@"
  local rc=$?
  if [ "$rc" -ne 0 ]; then
    echo "ERROR: command failed (exit $rc): $*" >&2
    exit "$rc"
  fi
}

echo "Profile: $profile (plugins: ${plugins[*]})"
echo "Repo root: $REPO_ROOT"
if [ "$dry_run" -eq 1 ]; then
  echo "-- dry run: no commands will execute --"
fi
echo

run_cmd claude plugin marketplace add "$REPO_ROOT"
for p in "${plugins[@]}"; do
  run_cmd claude plugin install "${p}@${MARKETPLACE}"
done

echo
if [ "$dry_run" -eq 1 ]; then
  echo "Dry run complete — no changes made."
  exit 0
fi

# marketplace add / plugin install both exit 0 and report "already installed"
# on a repeat run, so re-running this script is safe (idempotent).
echo "Done. Verify with: bash scripts/doctor.sh"
