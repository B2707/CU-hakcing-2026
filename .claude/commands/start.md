---
description: Take an issue — worktree + branch created, brief and team memory loaded
---
Run `./scripts/task start $ARGUMENTS`.

Then, from its output:
1. cd into the printed worktree path.
2. Read the TASK BRIEF carefully — it defines your approach, file scope,
   acceptance criteria, and tests. The brief is the contract.
3. Absorb TEAM GOTCHAS and INSTINCTS — they are hard-won; do not repeat them.
4. Confirm your plan in ONE short paragraph, then start.

Standing duties while you work (non-negotiable):
- Stay inside the brief's file scope. If you discover work outside it, run
  `/propose` — never fix silently, never create issues directly.
- If something costs you >10 minutes or would bite a teammate, run `/gotcha`
  before continuing.
- Tests first where the brief specifies them (the brief IS the test spec).
