#!/usr/bin/env bash
# desc: selftest for check-ceiling.sh's ratchet — asserts the gate fails when the tier exceeds the ratchet.
set -uo pipefail
cd "$(dirname "$0")/.." || exit 1
fails=0

# 1) Passes at the real ratchet value.
if ./scripts/check-ceiling.sh >/dev/null 2>&1; then
  echo "PASS: gate green at the committed ratchet"
else
  echo "FAIL: gate red at the committed ratchet — the ratchet is stale, bump it"
  fails=1
fi

# 2) Fails when the ratchet is below the measured size.
out=$(TIER_RATCHET=100 ./scripts/check-ceiling.sh 2>&1)
rc=$?
if [ "$rc" -ne 0 ] && printf '%s' "$out" | grep -q 'ratchet'; then
  echo "PASS: gate red when the tier exceeds the ratchet"
else
  echo "FAIL: gate stayed green with TIER_RATCHET=100 — the ratchet does not bite"
  fails=1
fi

# 3) The absolute ceiling still fires independently.
out=$(TIER_RATCHET=999999 CEILING_OVERRIDE=100 ./scripts/check-ceiling.sh 2>&1)
rc=$?
if [ "$rc" -ne 0 ] && printf '%s' "$out" | grep -q 'ceiling'; then
  echo "PASS: absolute ceiling still fires"
else
  echo "FAIL: absolute ceiling stopped firing"
  fails=1
fi

exit "$fails"
