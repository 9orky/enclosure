# Artifact Authority Method

This method classifies enclosure artifacts by authority. It prevents generated
shape, explanatory text, and local convenience from overruling the project
contract.

## Normative Artifacts

Normative artifacts define what the workspace means:

- `.enclosure/enclosure.yaml`
- `.enclosure/rules/shared/`
- `.enclosure/rules/local/`
- `.enclosure/recipes/*/recipe.yaml`

Changing a normative artifact changes the method. Do that only when the previous
contract is false, incomplete, or too weak to describe accepted project reality.

## Generative Artifacts

Generative artifacts instantiate or preview shape:

- `.enclosure/recipes/*/templates/`
- `workspace.recipe.roles_map`
- the configured recipe preview command

Templates are not policy. They are rendered evidence for a manifest. If a
template and manifest disagree, the manifest is the structural source of truth.

## Observed Artifacts

Observed artifacts are current project reality:

- the configured governed source tree
- `tests/`
- command reports

Observed artifacts can be wrong. A working import can still violate ownership.
An existing file tree can still drift from its recipe role.

## Advisory Artifacts

Advisory artifacts explain method and preserve design memory:

- `docs/methods/`
- execution plans
- reports and notes

Advisory artifacts do not define hidden policy. If a rule is mandatory, it
belongs in `.enclosure/rules/` or `.enclosure/enclosure.yaml`.

## Conflict Order

When artifacts conflict, resolve in this order:

1. Current user instruction.
2. Executable local contract.
3. Shared and local rules.
4. Recipe manifests.
5. Runtime implementation.
6. Method documentation.
7. Template convenience.

This order keeps architecture decisions reviewable and prevents explanation from
becoming undeclared policy.
