# Step 01: Standalone Shared Scaffolding Package

Status: Planned; implement after acceptance

## Goal

Implement `src/enclosure/shared/scaffolding/` as a complete independent package.

This step finishes the package before any existing caller is integrated. The
output must be a ready solution for manifest discovery, manifest validation,
relative path safety, variable parsing, input resolution, target defaults,
template rendering, and selective file writes.

Step 01 must not be a wrapper around existing implementation. It is a fresh
shared package whose behavior is derived from the UML contract and verified by
standalone tests.

## Source Of Truth

[UML.md](UML.md) is the source of truth for Step 01 implementation. The
standalone package must strictly follow the package layout, file names, DTO
names, behavior functions, relationships, public seam, and independence boundary
shown in the UML.

If the step plan and UML conflict, stop and update the documents before coding.

## Independence Contract

This step must not import:

- existing enclosure feature modules;
- existing recipe or pattern modules;
- existing scaffolding consumers.

Allowed dependencies are the Python standard library plus direct package
dependencies needed by `shared.scaffolding`, such as `pydantic`, `yaml`,
`enclosure.shared.templates`, and `enclosure.shared.naming`.

No production code under `src/enclosure/features/` may be imported by Step 01.
No compatibility bridge may be added from old recipe or pattern modules into
`shared.scaffolding`.

This step may create standalone tests that exercise only the package-root
`shared.scaffolding` seam.

## Root Boundary

Step 01 may edit only the shared scaffolding package root and its matching shared
tests, exactly as specified by [UML.md](UML.md).

Step 01 may update the shared-scaffold plan documents while defining the
package. It must not edit existing feature modules, recipe modules, pattern
modules, CLI flows, resources, or tests outside the Step 01 roots declared in
the UML.

## Work Items

- Implement the package layout exactly as defined in [UML.md](UML.md).
- Keep `__init__.py` export-only.
- Export only the `scaffolding` facade instance and required DTOs/errors named by the UML public seam.
- Keep nested manifest/value-object DTOs internal unless the UML is first updated.
- Implement behavior directly inside `shared.scaffolding`; do not delegate to existing feature-module repositories, renderers, materializers, config loaders, or manifest parsers.
- Implement manifest discovery and YAML validation for the existing `recipe.yaml` shape.
- Implement relative path validation without exporting path value objects.
- Implement variable parsing, input resolution, target defaults, and naming context behind the public render behavior.
- Implement template target/content rendering behind the public render behavior.
- Implement selective file writes behind the public write behavior.
- Add standalone tests through the package-root seam only.

## Acceptance

- Implementation strictly follows [UML.md](UML.md).
- The package-root seam exports only the names listed in the UML public seam.
- `__init__.py` contains no behavior implementation.
- The package imports no existing feature modules, recipe modules, pattern modules, or scaffolding consumers.
- The package does not import or wrap existing recipe/pattern repositories, renderers, materializers, config loaders, or manifest parsers.
- Existing recipe and pattern code remain untouched in this step.
- The package is complete enough to integrate `workspace.recipe` in Step 02 without adding more shared-scaffolding capabilities.

## Verification

- [ ] Run standalone shared scaffolding tests.
- [ ] Compare Step 01 implementation against [UML.md](UML.md).
- [ ] Run an import scan proving `src/enclosure/shared/scaffolding/` has no imports from existing feature modules, recipe modules, pattern modules, or scaffolding consumers.
- [ ] Run a forbidden-delegation scan proving Step 01 does not call old recipe/pattern repository, renderer, materializer, config loader, or manifest parser symbols.
- [ ] Verify valid manifest loading through the package-root seam.
- [ ] Verify invalid YAML, non-mapping YAML, unsupported `schema_version`, and unsafe paths fail loudly.
- [ ] Verify variable parsing and input resolution through the package-root seam.
- [ ] Verify target and content rendering through the package-root seam.
- [ ] Verify selective writes through the package-root seam.
