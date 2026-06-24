# User Stories

## run-stage-loop

As a user, I want each planning step to behave the same way so that I can review
projected files, ask the agent for updates, and accept the result with `next`.

Acceptance criteria:

- The current stage receives typed input data and scaffolds projected files.
- The agent updates only the current stage projection and context.
- User acceptance records stage output data that seeds the next stage.
- The same loop works for draft, plan, and epic projections.

## derive-output-slots

As a developer, I want each stage to derive output slots deterministically so
that roll can refresh generated structure without losing filled content.

Acceptance criteria:

- A stage derives each output slot from upstream stable identity, stage id, and
  stage-owned variant key.
- The stage implementation owns output type, output cardinality, and variant
  rules.
- Generated fields are refreshed during roll.
- Existing enrichment is preserved when the derived slot identity still exists.
- Orphaned enrichment is reported as drift when the upstream identity no longer
  maps to a derived slot.

## add-stage-class

As a developer, I want to add a stage by adding one class in one file so that the
workflow grows without changing the command loop.

Acceptance criteria:

- The shared stage interface declares intake, scaffold, agent context, accept,
  and output behavior.
- Each concrete stage owns the input data it expects.
- Each concrete stage owns the output data it passes to the next stage.
- The stage registry can discover or register a new stage without command
  changes.

## keep-user-stage-agnostic

As a user, I want parameterless commands so that I do not need to know internal
stage names or step identifiers.

Acceptance criteria:

- `start`, `next`, `agent`, and `roll` derive the active plan and current stage.
- Command output explains what changed without requiring stage vocabulary.
- `agent` receives enough bounded context to update the current projection.
- `next` advances only from the current accepted stage output.

## roll-from-draft-through-children

As a user, I want `roll` to refresh the whole planning chain from `DRAFT.md` so
that child projections can be updated consistently.

Acceptance criteria:

- `roll` starts from the draft seed.
- `roll` continues forward through child stages using the same stage interface.
- `roll` does not read child projection shape back into the draft seed.
- Roll output preserves enrichment attached to derived stable identities.
- Unresolved conflicts halt with a report instead of overwriting reviewed
  enrichment.

## project-schema-page

As a developer, I want `SCHEMAS.md` generated from native Mermaid files so that
schema diagrams have one native source of truth.

Acceptance criteria:

- `flows.mermaid`, `uml.mermaid`, and `tree.mermaid` remain native projection
  targets.
- `SCHEMAS.md` pastes those native files into the proper markdown sections
  during projection updates.
- Edits to `SCHEMAS.md` generated sections are not treated as schema source
  edits.
