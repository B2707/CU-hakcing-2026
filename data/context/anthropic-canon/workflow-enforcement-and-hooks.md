# Workflow Enforcement & Hooks

Domain 1 (27%), enforcement cluster. When compliance must be guaranteed, use
code-level mechanisms — hooks, prerequisite guards, state machines — not prompt
instructions. This is the principle the team harness is built on (fact-gate,
bash-guard, tripwires), so it is the highest-signal audit area for this repo.

## Prompts are probabilistic; hooks are deterministic

- Prompt instructions have a non-zero failure rate: the course cites production agents skipping critical steps in roughly 10-15% of interactions even when the prompt says to do them (https://www.anthropiccertifications.com/learn/agentic-architecture/workflow-enforcement).
- Decision rule: when deterministic compliance matters (identity verification before a financial op, ordering, business/compliance gates, financial thresholds), enforce it in code, not prose (https://www.anthropiccertifications.com/learn/agentic-architecture/workflow-enforcement).
- Soft preferences and style guidance, where occasional deviation is tolerable, are fine to leave as prompt instructions (https://www.anthropiccertifications.com/learn/agentic-architecture/agent-sdk-hooks).
- A prompt is a sign, code is a lock: no amount of prompt-polishing turns a probability into a guarantee, because the model is probabilistic by nature. Stakes decide the mechanism — financial/security/compliance → code; low-stakes formatting/tone → prompt is fine (https://www.anthropiccertifications.com/courses/claude-certified-architect-foundations/workflow-enforcement-and-handoff).
- A prerequisite gate works because the model only *proposes* actions while your code controls execution — block the downstream tool until the prerequisite completed this session; no prompt can bypass it (https://www.anthropiccertifications.com/courses/claude-certified-architect-foundations/workflow-enforcement-and-handoff).
- Wrong-layer trap: a routing classifier changes which tools are AVAILABLE for a request — it never controls the ORDER tools are called in, so it cannot fix a sequencing problem ("verify before refund"). Stronger prompts and more few-shot examples only make compliance more likely, not certain (https://www.anthropiccertifications.com/courses/claude-certified-architect-foundations/workflow-enforcement-and-handoff).

## The enforcement ladder (weakest → strongest)

1. Prompt only — suggests ordering (unreliable).
2. Prompt + examples — demonstrates ordering (better).
3. Programmatic guards — block unauthorized calls (deterministic).
4. State machine — full workflow engine (most robust).
   (https://www.anthropiccertifications.com/learn/agentic-architecture/workflow-enforcement)

- Programmatic prerequisite guard sketch: a `can_call_tool(tool, session_state)` check that blocks e.g. `process_refund`/`lookup_order` until `session_state.customer_verified` is true (https://www.anthropiccertifications.com/learn/agentic-architecture/workflow-enforcement).

## Hooks: what they are and the two kinds

- Hooks are code-level interception points in the agentic loop that give 100% (deterministic) enforcement, unlike probabilistic prompt instructions (https://www.anthropiccertifications.com/learn/agentic-architecture/agent-sdk-hooks).
- **PostToolUse hooks** transform tool *results* before the model sees them: normalize inconsistent formats (Unix timestamps vs ISO 8601 vs numeric status codes) into a uniform shape, enrich with computed fields, or strip sensitive data (https://www.anthropiccertifications.com/learn/agentic-architecture/agent-sdk-hooks).
- **Outgoing tool-call interception hooks** gate actions before they execute: enforce business/compliance rules (block refunds over a threshold and route to human escalation), apply policy gates, and log every call for audit (https://www.anthropiccertifications.com/learn/agentic-architecture/agent-sdk-hooks).
- Hooks work on both custom and third-party MCP tools without editing their source (https://www.anthropiccertifications.com/learn/agentic-architecture/agent-sdk-hooks).

## Hook timing, exit codes, and the wider taxonomy

- Timing decides capability: **PreToolUse fires BEFORE execution and is the only hook that can block or redirect an action**; PostToolUse fires after — it can reshape/log the result but can never block (the action already ran; "the refund already went out"). Blocking logic placed in a PostToolUse hook is a bug (https://www.anthropiccertifications.com/courses/claude-certified-architect-foundations/agent-sdk-hooks).
- Exit-code contract: exit 0 = allow; **exit 2 = block (pre-hooks only)**; exit 1 or any other code = non-blocking error, treated as allow. A hook may alternatively exit 0 and print a JSON decision (`permissionDecision: "deny"` + reason) — use exit codes OR JSON, never both (https://www.anthropiccertifications.com/courses/claude-certified-architect-foundations/agent-sdk-hooks).
- Hooks are **fail-open**: a crashing hook or unexpected exit code is treated as allow, so a buggy hook can't lock Claude out of tools — which means every blocking gate must be tested to prove it actually blocks (https://www.anthropiccertifications.com/courses/claude-code-101/gotchas-around-hooks).
- Hook I/O mechanics: the script receives the tool call as JSON on stdin (`tool_name`, `tool_input`); stderr goes back to Claude as feedback while stdout is ignored — so debug-log to a file, never stdout/stderr. The matcher takes pipe-separated tool names; tools name their path field inconsistently, so check `file_path`, `path`, and `pattern` (https://www.anthropiccertifications.com/courses/claude-code-101/defining-hooks).
- Operational gotchas: hook config/script changes are ignored until Claude Code restarts; keep hooks fast (<500ms, no network calls in pre-hooks) or every tool call feels sluggish; wrap stdin JSON parsing in try/catch (https://www.anthropiccertifications.com/courses/claude-code-101/gotchas-around-hooks).
- The taxonomy is wider than Pre/PostToolUse: subagent events (SubagentStart, SubagentStop), turn events (UserPromptSubmit, Stop — both can block), session events (SessionStart, SessionEnd — cannot block), and compaction events (PreCompact, PostCompact). Hooks can be scoped to one subagent (fire only while it's active), and a Stop hook attached to a subagent automatically becomes SubagentStop (https://www.anthropiccertifications.com/courses/claude-certified-architect-foundations/agent-sdk-hooks).
- Hooks are one of the four config surfaces, distinguished by *when* they run: they fire automatically on a lifecycle event (e.g., PostToolUse) and are executed by the harness, not chosen by Claude — so anything that must run automatically on every tool use belongs in a hook, never a skill or a CLAUDE.md line (https://www.anthropiccertifications.com/learn/claude-code-workflows/custom-skills-commands).

## Structured handoff when escalating to a human

- When escalating mid-process, compile a self-contained handoff summary — customer ID + verification status, root-cause analysis, requested action/amount, recommended resolution — because the human agent usually cannot see the full conversation transcript (https://www.anthropiccertifications.com/learn/agentic-architecture/workflow-enforcement).
- Escalate to a human on: explicit customer request for a human (honor immediately, before investigating), genuine policy gaps/ambiguity (not merely "complex" cases), and inability to make meaningful progress. Sentiment and self-reported confidence are unreliable complexity proxies (https://www.anthropiccertifications.com/learn/context-management).

## Applying this to a hook-driven team harness

- Any rule stated as "NEVER do X" or "always do Y before Z" that must hold on every seat is a candidate for a hook or CI gate, not just a CLAUDE.md line — a prose rule alone will be violated ~10-15% of the time (https://www.anthropiccertifications.com/learn/agentic-architecture/workflow-enforcement).
- A PreToolUse gate that denies-once-then-allows (forcing the agent to state impact facts before the retry) is a legitimate use of call interception to keep knowledge live and force a checkpoint; a PostToolUse check that validates what was just written is result transformation/inspection (https://www.anthropiccertifications.com/learn/agentic-architecture/agent-sdk-hooks).
