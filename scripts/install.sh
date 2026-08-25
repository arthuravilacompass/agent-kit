#!/usr/bin/env bash
# desc: Thin wrapper around `claude plugin marketplace add` + `claude plugin install` for named profiles.
set -uo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
MARKETPLACE="agent-kit"

usage() {
  cat <<'EOF'
Usage: install.sh [minimal|mobile|team|full] [--dry-run]

Profiles (default: minimal):
  minimal   core + council
  mobile    minimal + mobile
  team      minimal + team
  full      core + council + team + mobile

Options:
  --dry-run    print the commands that would run, without executing them
  -h, --help   show this help
EOF
}

profile="minimal"
dry_run=0

while [ $# -gt 0 ]; do
  case "$1" in
    minimal|mobile|team|full)
      profile="$1"
      ;;
    --dry-run)
      dry_run=1
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

if ! command -v claude >/dev/null 2>&1; then
  echo "ERROR: 'claude' CLI not found on PATH — install Claude Code first: https://docs.claude.com/claude-code" >&2
  exit 1
fi

# --- profile -> plugin list resolution --------------------------------------
case "$profile" in
  minimal) plugins=(core council) ;;
  mobile)  plugins=(core council mobile) ;;
  team)    plugins=(core council team) ;;
  full)    plugins=(core council team mobile) ;;
esac

# --- apply step --------------------------------------------------------------
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
