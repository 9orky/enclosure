# Computational Model Method

Enclosure treats a repository as a typed filesystem and dependency graph. The
method is to make architecture observable as data, then compare project reality
against an explicit contract.

The local contract is `.enclosure/enclosure.yaml`. It defines the governed root,
excluded paths, structural tags, boundary rules, layer flow, analyzers, report
limits, and recipe role mappings. Runtime modules under `src/enclosure/features/`
interpret that contract.

## Objects

- Paths are the primary objects. They become meaningful when classified by root,
  tag, recipe role, and layer.
- Tags are predicates over paths, such as `feature`, `module`, `domain`,
  `application`, `infrastructure`, and `ui`.
- Dependencies are directed edges between source objects.
- Seams are allowed crossing points between ownership regions.
- Rules are graph and path policies.
- Recipes are mechanical shape contracts.
- Templates are witnesses used to render a recipe shape.
- Checks are computations over the observed tree and contract.

## Derivation

The method follows this derivation:

1. Load the project contract.
2. Build the governed tree from `architecture.root`.
3. Exclude configured paths.
4. Classify remaining paths with boundary tags.
5. Build dependency edges.
6. Evaluate boundary and layer predicates.
7. Compare mapped modules against recipe roles.
8. Report violations as contract failures or implementation drift.

This makes enclosure more than a set of conventions. A convention becomes useful
only when it is represented as a path predicate, dependency predicate, shape
obligation, or rule graph edge.

## What Drives Enclosure

Four artifact families drive the system:

- `.enclosure/enclosure.yaml` supplies executable local facts.
- `.enclosure/rules/` supplies decision policy and route structure.
- `.enclosure/recipes/` supplies module shape contracts and templates.
- `src/enclosure/features/` supplies interpreters and analyzers.

The method is not "read all docs, then code." The method is:

1. Identify the target path or task.
2. Route to the smallest relevant rule set.
3. Determine owner, seam, and dependency direction.
4. Preview generated shape when a recipe is involved.
5. Change the smallest owning artifact.
6. Run focused checks.

## Failure Interpretation

Failures should be classified before fixing:

- Invalid dependency: graph edge violates a boundary or layer predicate.
- Recipe drift: observed files do not match the mapped recipe role.
- Rule graph issue: routing metadata cannot produce a valid read path.
- Shape issue: source structure exceeds or contradicts configured limits.
- Behavioral issue: tests fail through a public seam.

The method rejects check suppression as a default response. Contract changes are
valid only when the old contract was wrong.
