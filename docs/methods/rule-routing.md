# Rule Routing Method

Rule routing is the method for selecting the smallest rule set needed for a
task. It avoids both under-reading and reading the entire corpus as a substitute
for judgment.

Rule documents are Markdown with operational metadata. Fields such as
`doc_class`, `tags`, `child_paths`, `tightens_paths`, `escalation_paths`,
`entrypoint`, and `read_strategy` make the rule tree navigable.

## Route Construction

The route is derived from three inputs:

- explicit tags,
- project paths,
- task category.

Use the CLI to derive the route:

```sh
enclosure workspace rules route --task calibration
enclosure workspace rules route --tag structure
enclosure workspace rules route --path src/orders/catalog/domain
```

## Shared Then Local

The method is shared-first, local-second:

1. Start at `.enclosure/rules/INDEX.md`.
2. Enter the shared branch that answers the structural question.
3. Add local supplements only after the shared branch is known.
4. Stop at the shallowest document that answers the current uncertainty.

Local rules tighten shared rules. They should not duplicate shared policy or
become a second independent rule system.

## Graph Invariants

Rule routing depends on graph integrity:

- Entry points must be reachable.
- Navigation documents must point to known child documents.
- Local documents must tighten at least one shared anchor.
- Direct reads are reserved for entry points.
- Route metadata should identify why each document is read.

Validate this with:

```sh
enclosure workspace rules
```

## Method Failure

Routing has failed when:

- the agent reads by habit instead of route,
- local guidance is opened before the matching shared rule,
- a local document restates generic policy,
- rule links exist but do not form a reachable graph,
- a task proceeds without a known owner, seam, or dependency direction.
