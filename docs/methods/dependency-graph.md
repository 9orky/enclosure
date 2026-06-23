# Dependency Graph Method

The dependency graph method evaluates imports and dependency edges against
ownership, seam, and layer rules.

## Valid Edge Predicate

An edge `A -> B` is valid only when:

- `B` is the owner or public seam of the target responsibility,
- the edge does not bypass private internals,
- source and target tags satisfy configured boundary rules,
- the edge respects configured layer order,
- the edge does not create a cycle,
- the edge does not widen an API for local convenience.

Boundary violations are failed proofs of ownership, reachability, or direction.
They are not merely import style issues.

## Local Layer Order

The local flow is:

```text
ui -> application -> infrastructure -> domain
```

Read this as outer-to-inner. Outer layers may depend inward through seams. Inner
layers must not depend outward.

Consequences:

- `domain` must not import `application`, `infrastructure`, or `ui`.
- `infrastructure` must not import `application` or `ui`.
- `application` must not import `ui`.
- `ui` must not import `infrastructure`.
- cross-module imports should go through module seams.

## Review Procedure

For every new dependency:

1. Identify the responsibility being reached.
2. Identify the owning boundary.
3. Identify the public seam.
4. Confirm the edge targets that seam.
5. Confirm the edge points in the allowed direction.
6. Confirm the edge does not introduce a cycle.

If any answer is unknown, route to architecture and structure rules before
editing.

## Counterexample Standard

A good violation report should provide:

- source path,
- target path,
- source tags,
- target tags,
- violated rule,
- shortest import chain when transitive.

This standard turns architecture failure into a concrete repair task.
