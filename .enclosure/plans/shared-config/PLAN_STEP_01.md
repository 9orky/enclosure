# Step 01: Standalone Shared Config Package

Status: Draft

## Goal

Implement `src/enclosure/shared/config/` as a complete independent package.

This step finishes the package before any existing caller is integrated. The output must be a ready solution with manifest loading, whole-graph pydantic validation, the `settings` facade, and dot-notation manifest querying.

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

## File Tree

- src/enclosure/shared/config/
- src/enclosure/shared/config/__init__.py
- src/enclosure/shared/config/facade.py
- src/enclosure/shared/config/query.py
- src/enclosure/shared/config/base.py
- src/enclosure/shared/config/errors.py
- src/enclosure/shared/config/metadata.py
- src/enclosure/shared/config/loader.py
- src/enclosure/shared/config/loaded_manifest.py
- src/enclosure/shared/config/root.py
- src/enclosure/shared/config/architecture/
- src/enclosure/shared/config/workspace/
- src/enclosure/shared/config/pattern/
- src/enclosure/shared/config/health/
- tests/shared/config/

## Work Items

- Convert `src/enclosure/shared/config.py` into the `src/enclosure/shared/config/` package.
- Export only `settings` and intentionally public support types from `__init__.py`.
- Implement `StrictConfigModel`, `ConfigError`, `ConfigMetadata`, `LoadedManifest`, `ManifestLoader`, `ManifestQuery`, `SettingsFacade`, and `EnclosureSettings`.
- Implement all config pydantic classes inside topic subpackages without importing existing feature modules.
- Implement independent config file discovery for `.enclosure/enclosure.yaml` and `.enclosure/enclosure.yml`.
- Implement whole-manifest YAML loading and top-level mapping validation.
- Implement whole-graph pydantic validation through `EnclosureSettings`.
- Implement dot-notation manifest traversal through `settings.manifest`.
- Ensure missing manifest attributes raise `AttributeError`.
- Ensure manifest load and validation failures raise loud config errors before partial settings are exposed.
- Add standalone tests for valid config, invalid YAML, non-mapping YAML, invalid nested values, missing attributes, list traversal, object traversal, and import independence.

## Acceptance

- `from enclosure.shared.config import settings` works.
- Implementation strictly follows [UML.md](UML.md).
- `settings.manifest` supports dot notation.
- Dot-notation queries can return scalar values, pydantic objects, lists, tuples, and nested query objects.
- The full manifest graph validates at once.
- No partial settings are exposed after load or validation failure.
- `src/enclosure/shared/config/` imports no existing enclosure feature modules, bounded-context config modules, or other shared modules/packages.
- The package is complete enough to integrate existing callers without adding more config-package capabilities in Step 02.

## Verification

- [ ] Run standalone shared config tests.
- [ ] Compare Step 01 implementation against [UML.md](UML.md).
- [ ] Run an import scan proving `src/enclosure/shared/config/` has no imports from existing features, old config modules, or other shared modules/packages.
- [ ] Validate the current `.enclosure/enclosure.yaml` through `EnclosureSettings`.
- [ ] Verify `settings.manifest.architecture.root`.
- [ ] Verify `settings.manifest.architecture.shape`.
- [ ] Verify list access through a dot-selected list such as architecture boundary tags.
