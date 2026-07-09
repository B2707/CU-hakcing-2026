#!/usr/bin/env bash
# drill.sh — scripted tripwire fires (D4 deterministic drill, audit C2).
# Dispatches every tripwire through the REAL Discord alert path with a
# [DRILL] prefix — SERIALLY. tripwires.yml serializes all runs on a shared
# concurrency group (`group: tripwires`), so parallel dispatch makes GitHub
# auto-cancel every queued run except the newest (observed: 3/8 success,
# 5 cancelled). Each wire therefore waits for its run to complete before
# the next fires. The binary checkpoint is human: #ops must show exactly
# 3 [DRILL][P0] lines (red-main, panic, demo-freeze) and #feed exactly 5
# [DRILL][P1] lines (stuck-pr, stale-claim, collision, deadlock, budget).
# Anything else = wiring broken; fix before the D5 team drill.
#
# Usage: scripts/drill.sh <owner/repo>
set -euo pipefail

REPO="${1:?usage: drill.sh <owner/repo>}"
WIRES=(red-main stuck-pr stale-claim panic collision deadlock budget demo-freeze)
REGISTER_TIMEOUT_S=45   # per wire: dispatch -> run visible in the API
RUN_TIMEOUT_S=180       # per wire: run visible -> completed

latest_run_id() {
  gh run list --repo "$REPO" --workflow tripwires.yml \
    --event workflow_dispatch --limit 1 \
    --json databaseId --jq '.[0].databaseId // 0'
}

echo "==> dispatching ${#WIRES[@]} drill fires on $REPO (serial — see header)"
pass=0
results=()
for wire in "${WIRES[@]}"; do
  before=$(latest_run_id)
  gh workflow run tripwires.yml --repo "$REPO" -f simulate="$wire"
  echo "    fired: $wire"

  # wait for the new run to register
  run_id=""
  deadline=$((SECONDS + REGISTER_TIMEOUT_S))
  while [ "$SECONDS" -lt "$deadline" ]; do
    sleep 3
    cur=$(latest_run_id)
    if [ "$cur" != "$before" ] && [ "$cur" != "0" ]; then run_id="$cur"; break; fi
  done
  if [ -z "$run_id" ]; then
    results+=("$wire: NO RUN REGISTERED")
    continue
  fi

  # wait for that run to complete
  conclusion=""
  deadline=$((SECONDS + RUN_TIMEOUT_S))
  while [ "$SECONDS" -lt "$deadline" ]; do
    line=$(gh run view "$run_id" --repo "$REPO" --json status,conclusion \
      --jq '.status + " " + (.conclusion // "")')
    if [ "${line%% *}" = "completed" ]; then conclusion="${line#* }"; break; fi
    sleep 5
  done
  [ "$conclusion" = "success" ] && pass=$((pass + 1))
  results+=("$wire: ${conclusion:-timeout} (run $run_id)")
done

echo "==> results"
printf '    %s\n' "${results[@]}"

if [ "$pass" -ne "${#WIRES[@]}" ]; then
  echo "FAIL: $pass/${#WIRES[@]} drill runs succeeded — inspect: gh run list --workflow tripwires.yml --repo $REPO" >&2
  exit 1
fi

echo "==> PASS: ${#WIRES[@]}/${#WIRES[@]} drill runs green"
echo
echo "BINARY CHECKPOINT (a human answers yes/no):"
echo "  1. #ops shows exactly 3 [DRILL][P0] lines (red-main, panic, demo-freeze)?"
echo "  2. #feed shows exactly 5 [DRILL][P1] lines (stuck-pr, stale-claim, collision, deadlock, budget)?"
echo "If either answer is no: webhook secrets are missing/mis-wired — see docs/RUNBOOKS.md."
