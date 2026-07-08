#!/usr/bin/env bash
# Day-0 Stage 5 (docs/DAY0.md, 0:50 "Scope + stack"): stamp the chosen stack
# into the repo. Full version lands at D4; this stub validates inputs and
# reports what auto-activates once stack files exist.
set -euo pipefail
cd "$(dirname "$0")/.."

if [[ ! -f stack.md ]]; then
  echo "stack-stamp: stack.md not found." >&2
  echo "Write the chosen stack to stack.md first (Day-0 Stage 5), then rerun." >&2
  exit 1
fi

echo "stack-stamp: stack.md contents:"
sed 's/^/  | /' stack.md
echo
echo "Already wired (scripts/hooks/post-write-check.js — activates on its own):"
echo "  - TypeScript: tsc --noEmit runs on every .ts/.tsx edit once tsconfig.json exists"
echo "  - ESLint:     runs on every JS/TS edit once an eslint config exists"
echo
echo "TODO (D4): distill stack-specific rules into .claude/rules/, seed project"
echo "skills for the chosen framework, and dry-run the hook checks against a"
echo "deliberate violation in a dummy file."
