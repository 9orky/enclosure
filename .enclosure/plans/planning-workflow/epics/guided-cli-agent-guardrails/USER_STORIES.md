---
plan_id: planning-workflow
epic_id: guided-cli-agent-guardrails
title: Guided CLI and Agent Guardrails Stories
status: dry-run
stage: epics
source: event_store
generated_from: eventsourcing projection
sync_policy: projection
managed_files:
  - EPIC.md
  - USER_STORIES.md
  - SCHEMAS.md
  - flows.mermaid
  - uml.mermaid
  - tree.mermaid
stories:
  - id: show-plan-status
    title: Show active plan status
    status: candidate
  - id: start-plan
    title: Start the first active plan
    status: candidate
  - id: guide-next-action
    title: Guide the next valid action
    status: candidate
  - id: prepare-agent-context
    title: Prepare constrained agent context
    status: candidate
---

# User Stories

## show-plan-status

As a user, I want a single status command so that I know where the active plan is
and what blocks it.

Acceptance criteria:

- Status shows active plan name and stage.
- Status shows strict sync result.
- Status lists blocking and deferred questions.

## start-plan

As a user, I want to start a plan with a name so that the planner creates the
event-backed plan and first draft projection.

Acceptance criteria:

- Start rejects a second active plan.
- Start creates the plan folder projection.
- Start creates marked input blocks for first answers.

## guide-next-action

As a user, I want `workspace plan next` to import answers and tell me the next
valid moves so that I do not guess the workflow.

Acceptance criteria:

- Next imports marked input blocks.
- Next runs strict sync and gate checks.
- Next prints allowed commands and reasons for blocked commands.

## prepare-agent-context

As a user working with Codex, I want `workspace plan agent` to provide bounded
instructions so that the agent works inside the current plan state.

Acceptance criteria:

- Agent context lists allowed commands.
- Agent context lists forbidden actions.
- Agent context says when user confirmation is required.
