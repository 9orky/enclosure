# Planning Workflow

## Navigation

- Stage specification: [STAGES.md](../STAGES.md)
- Previous stage: [DRAFT.md](DRAFT.md)
- Technical view: [UML.md](UML.md)

| plan_item_id | source use case | plan section | epic package |
| --- | --- | --- | --- |
| `hexagonal-foundation` | [Hexagonal Foundation](DRAFT.md#hexagonal-foundation) | [hexagonal-foundation](#hexagonal-foundation) | [epics/hexagonal-foundation](epics/hexagonal-foundation/EPIC.md) |
| `event-sourced-core` | [Event-Sourced Planning Core](DRAFT.md#event-sourced-planning-core) | [event-sourced-core](#event-sourced-core) | [epics/event-sourced-core](epics/event-sourced-core/EPIC.md) |
| `projected-documents` | [Projected Planning Documents](DRAFT.md#projected-planning-documents) | [projected-documents](#projected-documents) | [epics/projected-documents](epics/projected-documents/EPIC.md) |
| `stage-gates-open-questions` | [Stage Gates and Open Questions](DRAFT.md#stage-gates-and-open-questions) | [stage-gates-open-questions](#stage-gates-open-questions) | [epics/stage-gates-open-questions](epics/stage-gates-open-questions/EPIC.md) |
| `guided-cli-agent-guardrails` | [Guided CLI and Agent Guardrails](DRAFT.md#guided-cli-and-agent-guardrails) | [guided-cli-agent-guardrails](#guided-cli-agent-guardrails) | [epics/guided-cli-agent-guardrails](epics/guided-cli-agent-guardrails/EPIC.md) |
| `schema-contract-verification` | [Schema Contract Verification](DRAFT.md#schema-contract-verification) | [schema-contract-verification](#schema-contract-verification) | [epics/schema-contract-verification](epics/schema-contract-verification/EPIC.md) |

## Purpose

Create a local event-sourced planning workflow that promotes a markdown draft
into a plan contract and then into implementation-ready epic packages.

The example projection chain is:

```text
DRAFT.md -> PLAN.md + UML.md -> epics/<epic>/*
```

The six plan items below are derived from the six draft use cases in
`DRAFT.md`. Their ids intentionally reuse the draft slugs so the example proves
the closed loop.

## Value

The workflow gives users one visible path from rough intent to epic packages,
preserves planning context across agent sessions, makes uncertainty explicit,
and gives agents stable contracts instead of making them infer intent from chat
history.

## Id Map

| draft use case id | plan item id | epic id |
| --- | --- | --- |
| `hexagonal-foundation` | `hexagonal-foundation` | `hexagonal-foundation` |
| `event-sourced-core` | `event-sourced-core` | `event-sourced-core` |
| `projected-documents` | `projected-documents` | `projected-documents` |
| `stage-gates-open-questions` | `stage-gates-open-questions` | `stage-gates-open-questions` |
| `guided-cli-agent-guardrails` | `guided-cli-agent-guardrails` | `guided-cli-agent-guardrails` |
| `schema-contract-verification` | `schema-contract-verification` | `schema-contract-verification` |

The stage split rule for this example is one plan item per draft use case and
one epic package per accepted plan item.

## Use Cases

### hexagonal-foundation

#### Name

Hexagonal Foundation

#### Source Use Case

`hexagonal-foundation`

#### Intent

Define shared port, adapter, and dependency-shape vocabulary before the planning
module starts adding concrete event stores, projection stores, schema providers,
or CLI adapters.

#### Accepted Constraints

- Shared contracts do not contain planning-specific behavior.
- Domain code remains independent of application, infrastructure, and UI.
- Concrete planning ports remain owned by the planning module.

#### Planned Outcome

`shared.hexagonal` exposes protocol-style contracts and adapter metadata that
the planning module can use without collapsing concrete planning behavior into
shared code.

#### Acceptance Notes

- Later planning ports can opt into the shared shape.
- Adapter declarations identify the port they implement.
- Dependency rules remain visible in schema contracts.

### event-sourced-core

#### Name

Event-Sourced Planning Core

#### Source Use Case

`event-sourced-core`

#### Intent

Create the authoritative planning model so plan creation, stage transitions,
question changes, projection registration, and roll requests are stored as
events and reconstructed into current state.

#### Accepted Constraints

- SQLite-backed event persistence is the local authority.
- Only one active plan may exist.
- Projectors consume events and do not treat markdown as the database.

#### Planned Outcome

The workspace can create one active plan, append durable events, and reconstruct
the current plan state through the planning application.

#### Acceptance Notes

- Starting a plan records durable state.
- Failed commands do not leave partial event state.
- Downstream projectors can consume ordered planning events.

### projected-documents

#### Name

Projected Planning Documents

#### Source Use Case

`projected-documents`

#### Intent

Render event-sourced planning facts into deterministic markdown and native
schema files while preserving reviewed enrichment by stable identity.

#### Accepted Constraints

- `DRAFT.md`, `PLAN.md`, `UML.md`, and epic packages are projections.
- Each stage owns its input type, output type, output cardinality, and slots.
- `SCHEMAS.md` is display-only; native Mermaid files are schema sources.

#### Planned Outcome

The planner can scaffold, parse, validate, accept, and rerender stage
projections without losing enrichment attached to derived stable identities.

#### Acceptance Notes

- Every stage implements the same stage interface.
- Roll recomputes forward from the draft seed.
- Drift is reported instead of silently overwritten.

### stage-gates-open-questions

#### Name

Stage Gates and Open Questions

#### Source Use Case

`stage-gates-open-questions`

#### Intent

Make uncertainty explicit so stages cannot advance while blocking questions
remain unresolved or while agent-suggested unblocking lacks user confirmation.

#### Accepted Constraints

- Every question needs an explanation.
- Blocking questions stop advancement.
- Agent-suggested non-blocking classifications require user confirmation.
- Deferred questions need a revisit stage.

#### Planned Outcome

Every stage can add, classify, confirm, and evaluate Open Questions before
accepting stage output.

#### Acceptance Notes

- Gate checks report blocking question ids.
- User confirmation is recorded as an event.
- Agents can create uncertainty but cannot silently unblock it.

### guided-cli-agent-guardrails

#### Name

Guided CLI and Agent Guardrails

#### Source Use Case

`guided-cli-agent-guardrails`

#### Intent

Expose the planning workflow through a small command loop that derives the
active plan and current stage from events, then tells users and agents which
actions are valid.

#### Accepted Constraints

- Public commands are `start`, `next`, `agent`, and `roll`.
- Commands derive active plan and current stage from event state.
- Agent guidance must not grant arbitrary mutation permissions.

#### Planned Outcome

Users can start, advance, ask for bounded agent guidance, and roll projections
without knowing internal stage names or manually passing plan identifiers.

#### Acceptance Notes

- `next` reports allowed moves and blocking reasons.
- `agent` returns bounded current-stage context.
- `roll` refreshes projected children forward from the draft seed.

### schema-contract-verification

#### Name

Schema Contract Verification

#### Source Use Case

`schema-contract-verification`

#### Intent

Compare accepted Mermaid file, symbol, and flow contracts with actual
implementation structure so agents can repair drift precisely.

#### Accepted Constraints

- `tree.mermaid` defines expected files.
- `uml.mermaid` defines expected symbols and file annotations.
- `flows.mermaid` defines parseable command, use-case, domain, and output flow.
- Actual schemas come from filesystem and modwire-derived structure.

#### Planned Outcome

The planner can parse planned contracts, derive actual schemas, compare them,
and report missing, extra, or mismatched implementation targets.

#### Acceptance Notes

- Drift reports name exact files and symbols.
- Repair instructions point agents back to the accepted schema contracts.
- Planned native Mermaid files remain the source for verification.

## Plan Decisions

### decision-reuse-slug-through-stage-chain

#### Decision

Use the draft use case slug as the plan item id and epic id unless a stage split
rule explicitly creates variants.

#### Rationale

Stable ids make the example projection chain inspectable and allow roll to
preserve enrichment by derived identity.

### decision-epic-packages-are-terminal

#### Decision

The first predictable planning contract stops at accepted epic packages.

#### Rationale

Epic packages are the first artifact that contains narrative, stories, native
schema contracts, and a verification path.

### decision-native-mermaid-files-own-schema-source

#### Decision

`flows.mermaid`, `uml.mermaid`, and `tree.mermaid` are the schema sources.
`SCHEMAS.md` is a display projection.

#### Rationale

Native files can be parsed and compared with implementation structure more
reliably than prose-only documentation.

## Open Questions

There are no blocking plan-stage Open Questions in this worked example.

### Should the six draft use cases be split into more than six epics?

The stage could theoretically create variants, but the current use cases already
match the existing epic packages and dependency graph.

#### Answer

No. This example uses one accepted plan item per draft use case and one epic
package per accepted plan item.

## Epic Projection

| plan item id | epic package | depends on |
| --- | --- | --- |
| `hexagonal-foundation` | `epics/hexagonal-foundation/` | none |
| `event-sourced-core` | `epics/event-sourced-core/` | `hexagonal-foundation` |
| `projected-documents` | `epics/projected-documents/` | `hexagonal-foundation`, `event-sourced-core` |
| `stage-gates-open-questions` | `epics/stage-gates-open-questions/` | `hexagonal-foundation`, `event-sourced-core` |
| `guided-cli-agent-guardrails` | `epics/guided-cli-agent-guardrails/` | `hexagonal-foundation`, `event-sourced-core`, `projected-documents`, `stage-gates-open-questions` |
| `schema-contract-verification` | `epics/schema-contract-verification/` | `hexagonal-foundation`, `event-sourced-core`, `projected-documents` |

## Success Criteria

- `DRAFT.md` shows the six source use cases and slug-derived ids.
- `PLAN.md` reuses those six ids as plan item ids.
- `UML.md` presents the same six ids in the technical object and flow contract.
- Every epic package declares the same source chain.
- Native Mermaid contracts remain the schema sources for each epic.
- Roll can preserve enrichment because ids are stable across stages.
