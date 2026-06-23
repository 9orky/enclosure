# Step 01: Standalone Shared Config Package

Status: Implemented; verify before Step 02

## Goal

Implement `src/enclosure/shared/config/` as a complete independent package.

This step finishes the package before any existing caller is integrated. The output must be a ready solution with manifest loading, whole-graph pydantic validation, the `settings` facade, and dot-path manifest querying.

## Source Of Truth

[UML.md](UML.md) is the source of truth for Step 01 implementation. The standalone package must strictly follow the package layout, class names, relationships, public seam, and independence boundary shown in the UML.

If the step plan and UML conflict, stop and update the documents before coding.

## Independence Contract

This step must not import:

- existing enclosure feature modules;
- existing bounded-context config modules;
- other `enclosure.shared.*` modules or packages.

Allowed dependencies are the Python standard library plus direct package dependencies needed by `shared.config`, such as `pydantic` and `yaml`.

This step may create standalone tests under `tests/shared/config/` that exercise only `shared.config`.

## Root Boundary

Step 01 may edit only these roots:

- `src/enclosure/shared/config/`
- `tests/shared/config/`

Step 01 may update the shared-config plan documents while defining the package.
It must not edit existing feature modules, bounded-context config modules, shared
helpers outside `src/enclosure/shared/config/`, CLI flows, resources, or tests
outside `tests/shared/config/`.

## File Tree

- src/enclosure/shared/config/
- src/enclosure/shared/config/__init__.py
- src/enclosure/shared/config/facade.py
- src/enclosure/shared/config/query.py
- src/enclosure/shared/config/base.py
- src/enclosure/shared/config/errors.py
- src/enclosure/shared/config/metadata.py
- src/enclosure/shared/config/manifest.py
- src/enclosure/shared/config/root.py
- src/enclosure/shared/config/architecture/
- src/enclosure/shared/config/workspace/
- src/enclosure/shared/config/pattern/
- src/enclosure/shared/config/health/
- tests/shared/config/

## Work Items

- Convert `src/enclosure/shared/config.py` into the `src/enclosure/shared/config/` package.
- Export `settings` as the runtime caller seam and keep support exports such as
  `ConfigError` and `StrictConfigModel` limited to package tests and migration
  internals.
- Implement `StrictConfigModel`, `ConfigError`, `ConfigMetadata`, `Manifest`, `ManifestQuery`, `SettingsFacade`, and `EnclosureSettings`.
- Implement all config pydantic classes inside topic subpackages without importing existing feature modules.
- Declare generic config defaults on pydantic config fields wherever possible.
- Implement manifest loading from `Path.cwd()` as project root, with accepted filenames `.enclosure/enclosure.yaml` and `.enclosure/enclosure.yml`.
- Populate `ConfigMetadata.project_root` as the application-wide source of truth for project root after bootstrap.
- Populate common metadata paths as `@property` values derived from the bootstrapped root, including target, canonical config path, recipes, plans, cache, dev, rules, local rules, bootstrap instruction, and agent instruction paths.
- Implement whole-manifest YAML loading and top-level mapping validation.
- Implement whole-graph pydantic validation through `EnclosureSettings`.
- Implement dot-path manifest traversal through `settings.query("...")`.
- Implement `SettingsFacade.dump_manifest()` with no parameters to dump the currently loaded validated graph.
- Implement static `Manifest.dump_default()` to dump the generic default config graph from `EnclosureSettings()`.
- Ensure missing manifest attributes raise `AttributeError`.
- Ensure manifest load and validation failures raise loud config errors before partial settings are exposed.
- Add standalone tests for valid config, invalid YAML, non-mapping YAML, invalid nested values, missing attributes, list traversal, object traversal, and import independence.

## Acceptance

- `from enclosure.shared.config import settings` works.
- Runtime callers use `settings` as the public config seam.
- Implementation strictly follows [UML.md](UML.md).
- `settings.query("...")` supports dot paths.
- `settings.dump_manifest()` returns YAML for the validated settings graph.
- `settings.metadata.project_root` provides the bootstrapped project root.
- `settings.metadata.canonical_config_path` provides the canonical manifest output path.
- `settings.metadata` provides common workspace paths as non-null `Path` values.
- `Manifest.dump_default()` returns valid YAML for the generic default settings graph.
- Dot-path queries can return scalar values, pydantic objects, lists, and tuples.
- The full manifest graph validates at once.
- The generic default manifest graph is valid and dumpable from pydantic defaults.
- No partial settings facade is exposed after load or validation failure.
- `src/enclosure/shared/config/` imports no existing enclosure feature modules, bounded-context config modules, or other shared modules/packages.
- The package is complete enough to integrate existing callers without adding more config-package capabilities in Step 02.

## Verification

- [ ] Run standalone shared config tests.
- [ ] Compare Step 01 implementation against [UML.md](UML.md).
- [ ] Run an import scan proving `src/enclosure/shared/config/` has no imports from existing features, old config modules, or other shared modules/packages.
- [ ] Validate the current `.enclosure/enclosure.yaml` through `EnclosureSettings`.
- [ ] Verify `settings.metadata.project_root`.
- [ ] Verify `settings.metadata.canonical_config_path`.
- [ ] Verify path metadata such as `settings.metadata.plans_dir`, `settings.metadata.recipes_dir`, and `settings.metadata.rules_dir`.
- [ ] Verify `settings.query("architecture.root")`.
- [ ] Verify `settings.query("architecture.shape")`.
- [ ] Verify `settings.dump_manifest()`.
- [ ] Verify `Manifest.dump_default()` validates through `EnclosureSettings`.
- [ ] Verify list access through a dot-selected list such as architecture boundary tags.
