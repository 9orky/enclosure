# User Stories

## classify-open-questions

As a planner, I want every open question classified so that uncertainty is
visible and actionable.

Acceptance criteria:

- Questions include `question`, `status`, and `explanation`.
- Valid statuses are blocking, answered, deferred, accepted risk, and obsolete.
- Deferred questions include a revisit stage.

## enforce-stage-gates

As the workflow, I want blocking questions to prevent advancement so that plans
do not move forward with hidden uncertainty.

Acceptance criteria:

- Gate checks fail when blocking questions exist.
- Gate checks report the blocking question ids.
- Gate checks are recorded as events.

## require-user-unblocking

As a user, I want agents to ask or block freely but require my confirmation to
unblock so that the agent cannot approve its own assumptions.

Acceptance criteria:

- Agents can add blocking questions.
- Agent-suggested non-blocking classifications are pending until confirmed.
- User confirmation appends an event.
