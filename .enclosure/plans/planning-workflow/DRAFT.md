# Planning Workflow Draft

## Navigation

- Stage specification: [STAGES.md](../STAGES.md)
- Plan contract: [PLAN.md](PLAN.md)
- Technical view: [UML.md](UML.md)

| use_case_id | draft section | plan item | epic package |
| --- | --- | --- | --- |
| `hexagonal-foundation` | [Hexagonal Foundation](#hexagonal-foundation) | [hexagonal-foundation](PLAN.md#hexagonal-foundation) | [epics/hexagonal-foundation](epics/hexagonal-foundation/EPIC.md) |
| `event-sourced-core` | [Event-Sourced Planning Core](#event-sourced-planning-core) | [event-sourced-core](PLAN.md#event-sourced-core) | [epics/event-sourced-core](epics/event-sourced-core/EPIC.md) |
| `projected-documents` | [Projected Planning Documents](#projected-planning-documents) | [projected-documents](PLAN.md#projected-documents) | [epics/projected-documents](epics/projected-documents/EPIC.md) |
| `stage-gates-open-questions` | [Stage Gates and Open Questions](#stage-gates-and-open-questions) | [stage-gates-open-questions](PLAN.md#stage-gates-open-questions) | [epics/stage-gates-open-questions](epics/stage-gates-open-questions/EPIC.md) |
| `guided-cli-agent-guardrails` | [Guided CLI and Agent Guardrails](#guided-cli-and-agent-guardrails) | [guided-cli-agent-guardrails](PLAN.md#guided-cli-agent-guardrails) | [epics/guided-cli-agent-guardrails](epics/guided-cli-agent-guardrails/EPIC.md) |
| `schema-contract-verification` | [Schema Contract Verification](#schema-contract-verification) | [schema-contract-verification](PLAN.md#schema-contract-verification) | [epics/schema-contract-verification](epics/schema-contract-verification/EPIC.md) |

## Abstract

Build a local planning workflow that turns a user's rough intent into
implementation-ready epic packages. The workflow keeps markdown pleasant to
review, but records accepted planning facts as events and regenerates markdown
as projections.

This draft is the worked example for the stage specification in `../STAGES.md`.
Its six use cases are the six epic packages that already exist under `epics/`.

## Naming Convention

Use case ids are derived from use case headings:

```text
Heading: Hexagonal Foundation
Slug:    hexagonal-foundation
```

Rules:

- lowercase the heading;
- remove punctuation;
- replace whitespace with `-`;
- collapse repeated `-`;
- keep the slug stable after promotion.

The same slug is reused across the projection chain unless a later stage split
rule explicitly creates variants:

```text
use_case_id -> plan_item_id -> epic_id
hexagonal-foundation -> hexagonal-foundation -> hexagonal-foundation
```

## Use Cases

### Hexagonal Foundation

Define shared port, adapter, and dependency-shape vocabulary before the planning
module starts adding concrete infrastructure.

#### Constraints

- Shared contracts must not contain planning-specific behavior.
- Domain code must remain independent of application, infrastructure, and UI.
- Concrete planning ports stay owned by the planning module.

#### Agent Prose

The planning module needs a small hexagonal foundation so later epics can define
ports and adapters consistently. This use case creates the common interface
shape and dependency vocabulary that later planning components will follow.

### Event-Sourced Planning Core

Create the authoritative planning model so plan facts are appended as durable
events and reconstructed into current state.

#### Constraints

- SQLite-backed event persistence is the local authority.
- Only one active plan may exist.
- Projectors consume events; they do not treat markdown as the database.

#### Agent Prose

The planning workflow needs a reliable source of truth before projections,
questions, or CLI behavior can be trusted. This use case owns plan creation,
event append behavior, active-plan state, and reconstruction from event history.

### Projected Planning Documents

Render event-sourced planning facts into deterministic markdown and native
schema files while preserving reviewed enrichment by stable identity.

#### Constraints

- `DRAFT.md`, `PLAN.md`, `UML.md`, and epic packages are projections.
- Each stage owns its input type, output type, output cardinality, and slots.
- `SCHEMAS.md` is display-only; native Mermaid files are schema sources.

#### Agent Prose

Users should review familiar files, while the system keeps facts in events. This
use case defines stage projections, slot derivation, enrichment preservation,
schema page generation, and forward-only roll from the draft seed.

### Stage Gates and Open Questions

Make uncertainty explicit so stages cannot advance while important questions
remain unresolved.

#### Constraints

- Every question needs an explanation.
- Blocking questions stop advancement.
- Agent-suggested non-blocking classifications require user confirmation.
- Deferred questions need a revisit stage.

#### Agent Prose

The workflow should not force premature certainty, but it must prevent silent
uncertainty. This use case gives each stage a question loop, gate policy, and
confirmation rules so the user controls what can unblock promotion.

### Guided CLI and Agent Guardrails

Expose the planning workflow through a small command loop that tells users and
agents what is allowed at the current stage.

#### Constraints

- Public commands are `start`, `next`, `agent`, and `roll`.
- Commands derive the active plan and current stage from event state.
- Agent guidance must not grant arbitrary mutation permissions.

#### Agent Prose

The planning workflow should be usable without making users memorize stage
names. This use case owns the command surface, next-action guidance, bounded
agent instructions, and safe roll behavior.

### Schema Contract Verification

Compare accepted Mermaid contracts with actual implementation structure so
agents can repair drift precisely.

#### Constraints

- `tree.mermaid` defines expected files.
- `uml.mermaid` defines expected symbols and file annotations.
- `flows.mermaid` defines parseable command, use-case, domain, and output flow.
- Actual schemas come from filesystem and modwire-derived structure.

#### Agent Prose

Epic schemas should become enforceable implementation contracts. This use case
parses planned Mermaid files, derives actual implementation schemas, compares
them, and reports missing or mismatched files and symbols.

## Open Questions

There are no blocking draft questions in this worked example.

### Should the first predictable contract continue past epics?

The early discussion considered post-epic automation, but that would expand the
first contract and blur the terminal artifact.

#### Answer

No. The first predictable planning contract stops at implementation-ready epic
packages. Post-epic implementation automation can be planned later.

## Derived Draft Objects

| use_case_id | name | agent_prose_node |
| --- | --- | --- |
| `hexagonal-foundation` | Hexagonal Foundation | present |
| `event-sourced-core` | Event-Sourced Planning Core | present |
| `projected-documents` | Projected Planning Documents | present |
| `stage-gates-open-questions` | Stage Gates and Open Questions | present |
| `guided-cli-agent-guardrails` | Guided CLI and Agent Guardrails | present |
| `schema-contract-verification` | Schema Contract Verification | present |

The next stage receives these six stable use case ids, their descriptions,
constraints, answered questions, and agent prose.
