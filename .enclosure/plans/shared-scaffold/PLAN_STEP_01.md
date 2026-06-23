# Step 01: Standalone Shared Scaffolding Package

Status: Complete; stable; closed for Step 02 handoff.

## Target Shape

This step describes the implemented and verified shared scaffolding package.

The Step 01 file layout, class names, properties, methods, relationships, and
public seam are owned by [UML.md](UML.md). Do not duplicate the file tree here.

## Goal

Implement `src/enclosure/shared/scaffolding/` as a complete independent package.

This step finishes the package before any existing caller is integrated. The
output must be a ready solution for manifest discovery, manifest validation,
relative path safety, variable parsing, include composition, composed input
resolution, target defaults, template rendering, and selective file writes.

Step 01 must not be a wrapper around existing implementation. It is a fresh
shared package whose behavior is derived from the UML contract and verified by
standalone tests.

## Source Of Truth

[UML.md](UML.md) is the source of truth for Step 01 implementation. The
standalone package must strictly follow the package layout, file names, DTO
names, class methods, relationships, public seam, and independence boundary
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

- [x] Implement the package layout exactly as defined in [UML.md](UML.md).
- [x] Keep `__init__.py` export-only.
- [x] Export only the `scaffolding` facade instance and required DTOs/errors named by the UML public seam.
- [x] Keep nested manifest/value-object DTOs internal unless the UML is first updated.
- [x] Keep internal class behavior stateless with respect to caller roots; pass
  `scaffold_root` and `target_root` as operation inputs through the facade.
- [x] Do not introduce standalone helper functions. Private behavior belongs to
  private classes and private methods.
- [x] Implement behavior directly inside `shared.scaffolding`; do not delegate to existing feature-module repositories, renderers, materializers, config loaders, or manifest parsers.
- [x] Implement scaffold manifest discovery and YAML validation for the existing
  `recipe.yaml` file name, with the filename owned in `_ScaffoldManifestRepository`.
- [x] Rename the public scaffold source-folder field to `source_root`; keep it
  distinct from caller-provided `scaffold_root`.
- [x] Implement relative path validation without exporting path value objects.
- [x] Implement include traversal, missing include failures, cycle detection, and
  ordered scaffold composition in `_ScaffoldComposer`, exposed through
  `scaffolding.compose(...)` and used by `scaffolding.render(...)`.
- [x] Implement variable parsing, composed input resolution, target defaults, and
  naming context behind the public render behavior.
- [x] Implement template target/content rendering behind the public render behavior.
- [x] Implement selective file writes behind the public write behavior.
- [x] Add standalone tests through the package-root seam only.

## Acceptance

- Implementation strictly follows [UML.md](UML.md).
- The package-root seam exports only the names listed in the UML public seam.
- `__init__.py` contains no behavior implementation.
- Internal modules remain internal; feature code imports only the package root.
- Internal class behavior does not import settings and does not bind `scaffold_root` or
  `target_root` in constructors.
- The package imports no existing feature modules, recipe modules, pattern modules, or scaffolding consumers.
- The package does not import or wrap existing recipe/pattern repositories, renderers, materializers, config loaders, or manifest parsers.
- Existing recipe and pattern code remain untouched in this step.
- The package is complete enough to integrate `workspace.recipe` in Step 02 without adding more shared-scaffolding capabilities.

## Verification

- [x] Run standalone shared scaffolding tests.
- [x] Compare Step 01 implementation against [UML.md](UML.md).
- [x] Run an import scan proving `src/enclosure/shared/scaffolding/` has no imports from existing feature modules, recipe modules, pattern modules, or scaffolding consumers.
- [x] Run a forbidden-delegation scan proving Step 01 does not call old recipe/pattern repository, renderer, materializer, config loader, or manifest parser symbols.
- [x] Verify valid manifest loading through the package-root seam.
- [x] Verify invalid YAML, non-mapping YAML, unsupported `schema_version`, and unsafe paths fail loudly.
- [x] Verify `scaffold_root`, `target_root`, and `source_root` semantics through the package-root seam.
- [x] Verify include composition order, missing include errors, and cycle detection through the package-root seam.
- [x] Verify variable parsing and composed input resolution through the package-root seam.
- [x] Verify target and content rendering through the package-root seam.
- [x] Verify selective writes through the package-root seam.

## Completion

Step 01 is closed. `enclosure.shared.scaffolding` is stable for Step 02 and
must be treated as complete during workspace recipe integration.

Final checks:

- `uv run pytest tests/shared/scaffolding`
- `uv run pytest`
- `uv run ruff check src tests`
- public export check for only `RenderedScaffoldFile`, `Scaffold`,
  `ScaffoldError`, and `scaffolding`
- AST shape check proving no module-level functions in
  `src/enclosure/shared/scaffolding`
- forbidden import/delegation scan proving no feature, recipe, or pattern
  dependency from shared scaffolding
- real `.enclosure/recipes` smoke render through the package-root seam
