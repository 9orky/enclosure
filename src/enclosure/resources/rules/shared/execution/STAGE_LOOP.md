---
doc_class: execution
rule_kind: execution
audience: agent
purpose: Define planning as the workspace plan stage loop from draft through epics.
applies_when:
  - A workspace plan is being started, authored, advanced, restored, or recovered.
  - An agent needs to configure the work before implementation.
tags:
  - execution
  - workspace-plan
  - stage-loop
stage: stage_loop
same_artifact_family: execution
read_directly: false
escalation_paths: []
---

# Stage Loop

## Core Rule

- Planning is the agent's process of self-configuring workspace plan stages
  until epics are materialized.
- The user may also run this process, but the agent is preferred because it can
  keep discovery, stage artifacts, questions, and verification aligned.
- The draft stage is only the first stage. Do not stop after draft unless the
  active plan is blocked, explicitly paused, or closed by the user.

## Loop

- Inspect the active plan with `workspace plan`.
- Use `workspace plan agent` before authoring the current stage.
- Write only the current stage artifact paths with `workspace plan put PATH`.
- Record blockers with `workspace plan ask TITLE EXPLANATION`.
- Resolve gate questions with `workspace plan answer TITLE ANSWER`.
- Advance with `workspace plan next`; repeat until the plan reaches epics and
  then completes.
- Use `workspace plan restore` when projected files are missing or stale.

## Artifact Rules

- Keep stage artifacts inside the active `.enclosure/plans/<slug>/` projection.
- Treat markdown files as projections of the event stream, not as independent
  state.
- Do not create ad hoc execution artifacts outside the
  workspace plan stage loop.
- If a stage includes Mermaid contracts, apply [CONTRACT_DIAGRAMS.md](CONTRACT_DIAGRAMS.md).

## Review Checks

- The active stage is known before writing.
- Each stage artifact matches the file model reported by `workspace plan agent`.
- Draft has either advanced, recorded a blocker, or been explicitly paused.
- Epics exist before the workspace plan is considered complete.
