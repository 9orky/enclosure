# Recipe Algebra Method

Recipe algebra is the method for reasoning about module shape. A recipe is not a
framework or architecture proof. It is a mechanical contract for files, package
seams, slots, and rendered templates.

## Recipe Roles

Current roles are:

- `container`: names a family of archetypes.
- `archetype`: declares a complete module shape.
- `fragment`: declares a reusable partial shape.

The current catalog includes compact support modules, report CLI modules,
workspace CLI modules, domain-package CLI modules, pattern modules, and reusable
slot fragments.

## Slot States

Slots are local vocabulary. In this repository they include names such as
`domain`, `application`, `infrastructure`, and `ui`, but the recipe system does
not require those names globally.

Slot states are:

- `absent`: the slot must not exist for this shape.
- `file`: the slot is a single file.
- `package`: the slot is a package seam.
- `split-files`: the slot owns explicitly listed child files.
- `split-packages`: the slot owns explicitly listed child packages.

## Composition Law

A composed recipe can be modeled as:

```text
Recipe = BaseArchetype + Fragment*
valid(Recipe) iff
  includes are acyclic
  referenced recipes exist
  slot merges are compatible
  required seams are present
  no file/package sibling contradiction exists
```

Composition is slot-wise merge. A merge is invalid when two inputs assign
contradictory states to the same slot, such as `domain: file` plus
`domain: package`.

## Drift Semantics

Drift is the difference between expected paths and actual paths:

- missing required seams,
- missing required files,
- forbidden file/package combinations,
- extra root files outside declared slots,
- mapped module missing from the governed tree,
- role map pointing at a missing recipe.

Check drift with:

```sh
enclosure workspace recipe --drifts
```

Validate manifests and rendering with:

```sh
enclosure workspace recipe --check
```

## Design Method

- Add an archetype only when an existing rung cannot honestly describe the
  shape.
- Add a fragment when the same slot addition repeats across archetypes.
- Prefer compact files until stable internal responsibilities justify package
  growth.
- Prefer package seams when private internals are expected to grow.
- Keep shape in manifests and starter content in templates.
- Do not use recipes to hide dependency or ownership violations.
