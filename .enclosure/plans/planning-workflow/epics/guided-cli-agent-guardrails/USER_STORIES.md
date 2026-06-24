# User Stories

## start-plan

As a user, I want `workspace plan start` to create the active planning loop
without parameters so that I do not need to choose internal identifiers.

Acceptance criteria:

- Start rejects a second active plan.
- Start creates the plan folder projection.
- Start creates the first stage review surface.
- Start derives any required name or identifier from the draft seed or plan
  context.

## guide-next-action

As a user, I want `workspace plan next` to accept the current reviewed stage and
tell me the next valid move so that I do not guess the workflow.

Acceptance criteria:

- Next records the current stage output as events.
- Next runs strict sync and gate checks.
- Next prints allowed commands and reasons for blocked commands.

## prepare-agent-context

As a user working with Codex, I want `workspace plan agent` to provide bounded
instructions so that the agent works inside the current plan state.

Acceptance criteria:

- Agent context lists allowed commands.
- Agent context lists forbidden actions.
- Agent context says when user confirmation is required.

## roll-plan-chain

As a user, I want `workspace plan roll` to refresh projected children forward
from the draft seed so that the plan chain can update consistently after draft
changes.

Acceptance criteria:

- Roll requires no command parameters.
- Roll starts from `DRAFT.md` and continues across child stages.
- Roll does not push child projection shape back into `DRAFT.md`.
- Roll reports unresolved drift instead of overwriting reviewed enrichment.
