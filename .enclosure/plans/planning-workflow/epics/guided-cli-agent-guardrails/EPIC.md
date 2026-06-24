# Guided CLI and Agent Guardrails

## Value

This epic makes the planning workflow usable from VS Code with Codex while
limiting unexpected agent behavior. The CLI tells users and agents what state
the plan is in and which commands are currently valid.

## Outcome

The command loop is simple: start a plan, review the current stage projection,
accept with `next`, ask the agent for constrained guidance, and roll from the
draft seed when the projected chain needs to be refreshed.

## Navigation

Previous dependencies:

- Event-Sourced Planning Core
- Projected Planning Documents
- Stage Gates and Open Questions

Next dependent epic: none.

## Contract Role

`tree.mermaid` defines CLI and guidance files. `uml.mermaid` defines CLI,
next-action, agent-guidance, roll, and use-case symbols. `flows.mermaid` defines
the start, next, agent, and roll command loop.

## Boundaries

This epic does not own the domain rules themselves. It owns how users and agents
invoke those rules safely.

## Acceptance Criteria

- `workspace plan start` creates the active plan and first projection without
  requiring parameters.
- `workspace plan next` accepts the current stage output, checks gates, and
  reports allowed moves.
- `workspace plan agent` produces constrained agent guidance.
- `workspace plan roll` starts from the draft seed and refreshes child stages
  forward through the same stage loop.
- The agent guidance never grants permission to run arbitrary plan mutations.
