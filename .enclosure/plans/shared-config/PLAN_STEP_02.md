# Step 02: Migrate Architecture Bounded Context

Status: Implemented; Step 03 handoff ready

## Implementation Summary

- `src/enclosure/shared/architecture_code.py`
  - `extract_architecture_code() -> ArchitectureCodeMap`
  - `_architecture_root(project_root: Path, architecture_config: object) -> Path`
  - `_extraction_exclusions(architecture_config: object) -> tuple[str, ...]`
  - `_matching_config(architecture_config: object) -> object`
- `src/enclosure/features/architecture/config/`
  - source files deleted
  - ignored `__pycache__` remnants may still exist locally
- `src/enclosure/features/architecture/boundaries/domain.py`
  - removed `BoundaryRule`, `ConfigTagRule`, `FlowRealmRule`, `FlowRuleSet`, and
    `BoundariesConfig` config ownership
  - keep `BoundariesReport`
- `src/enclosure/features/architecture/clusters/domain.py`
  - removed `ClustersConfig` config ownership
  - keep report and cluster domain types
- `src/enclosure/features/architecture/health/domain.py`
  - removed `HealthConfig` config ownership
  - keep report and finding domain types
- `src/enclosure/features/architecture/map/domain.py`
  - removed `MapConfig` config ownership
  - keep report, dependency, and map domain types
- `src/enclosure/features/architecture/pressure/domain.py`
  - removed `PressureConfig` config ownership
  - keep report and pressure domain types
- `src/enclosure/features/architecture/shape/domain.py`
  - removed `ImportCrossingType`, `ShapeConfigError`, and `ShapeConfig` config
    ownership
  - keep `ShapeViolation`, `ShapeReport`, and shape evaluation functions
- `src/enclosure/features/architecture/*/__init__.py`
  - removed exports that expose deleted architecture-owned config classes
- `tests/features/architecture/`
  - updated tests to construct or patch architecture inputs through
    `enclosure.shared.config.settings`, `settings.metadata`, and
    `settings.query("architecture...")`

## Goal

Integrate the completed `shared.config` package from Step 01 into the
architecture bounded context and its current extraction helper.

This step is the pilot migration. It proves that architecture callers can use
`settings`, `settings.query("architecture...")`, and `settings.metadata` without
changing any other bounded context.

This step must treat `shared.config` as finished. Do not add new package
capabilities here unless Step 01 is first updated and completed again.

## Step Contract

Inputs:

- A completed and verified Step 01 `src/enclosure/shared/config/` package.
- [UML.md](UML.md), which is the source of truth for integration boundaries.
- Existing architecture production code and tests under the roots below.

Outputs:

- Architecture runtime config access goes through
  `from enclosure.shared.config import settings`.
- Architecture config data is read with `settings.query("architecture")` or
  narrower `settings.query("architecture...")` calls.
- Architecture project-root and standard path access comes from
  `settings.metadata`.
- Old architecture-owned config loaders and pydantic config classes are removed
  from the declared Step 02 roots instead of wrapped.

Scope:

- Replace config loading and project-root ownership for the architecture bounded
  context only.
- Update architecture tests only where they cover this migration.
- Keep architecture reports, analyzers, templates, and command semantics
  otherwise unchanged.

Out of scope:

- Adding or changing `shared.config` capabilities.
- Migrating workspace, pattern, health, other shared-helper, CLI, or
  packaged-resource callers outside the declared Step 02 roots.
- Removing `enclosure.shared.layout`; that is a Step 03 shared-helper cleanup
  unit after remaining callers move.
- Adding backwards-compatible imports, bridge modules, or compatibility aliases.

Owner:

- `src/enclosure/features/architecture/`
- `tests/features/architecture/`
- The shared helper file `src/enclosure/shared/architecture_code.py` is the only
  allowed non-architecture source edit because it is the current architecture
  extraction entry point and imports architecture config directly.

Dependency direction:

- Architecture callers may depend on `enclosure.shared.config`.
- `enclosure.shared.config` must not depend on architecture callers.
- Downstream architecture functions receive the already-loaded architecture
  config object and metadata-derived paths; they must not load raw YAML,
  validate manifest sections, or rediscover project root.

Stop conditions:

- If architecture integration needs missing `shared.config` behavior, stop,
  update Step 01 and [UML.md](UML.md), complete Step 01 independently, then
  resume Step 02.
- If work requires edits outside the roots declared here, stop and move that
  work to Step 03 or to the owning step.

## Execution Record

1. Verified the Step 01 prerequisite with `uv run pytest tests/shared/config`.
2. Replaced `src/enclosure/shared/architecture_code.py` with
   `settings.metadata` and `settings.query("architecture")`.
3. Removed architecture-owned config source files and config class exports.
4. Updated architecture tests to use shared-config classes, `settings.metadata`,
   and `settings.query("architecture...")`.
5. Scanned Step 02 roots for forbidden config remnants.
6. Ran architecture-focused verification and documented non-Step-02 failures.

## Verification

- [x] Compared Step 02 architecture integration against [UML.md](UML.md).
- [x] `uv run pytest tests/shared/config`: 16 passed.
- [x] `uv run pytest tests/features/architecture`: 29 passed.
- [x] `enclosure architecture boundaries`: passed.
- [x] Forbidden-remnant scan across Step 02 roots: no matches.
- [x] `enclosure architecture shape`: executed; fails on 25 known findings in
  `workspace/recipe`, `workspace/rules`, and `workspace/sync`, which are outside
  Step 02 roots and belong to Step 03.
- [x] `enclosure architecture health`: executed; fails because it includes the
  same Step 03-owned shape findings plus non-blocking pressure/coherence
  findings.

## Completion

Step 02 is complete:

- Architecture production callers use `from enclosure.shared.config import settings`
  where runtime config is needed.
- Architecture integration strictly follows [UML.md](UML.md).
- Architecture edits stay inside the declared Step 02 root boundary.
- Architecture callers use `settings.query("architecture...")` for architecture config data.
- Architecture callers use `settings.metadata.project_root` as the runtime source of project-root truth.
- Architecture callers use `settings.metadata.canonical_config_path` when the canonical manifest output path is needed.
- Architecture callers do not rediscover, infer, or resolve the project root independently.
- Architecture feature modules do not load raw YAML.
- Architecture feature modules do not validate raw manifest sections directly.
- `src/enclosure/features/architecture/config/` is deleted, not wrapped.
- Architecture-owned pydantic config classes are removed from architecture
  production modules after equivalent Step 01 classes exist.
- No backwards-compatibility bridges are introduced.
- `shared.config` remains independent of architecture and other feature modules.
- Step 02 adds no new `shared.config` capabilities.
- Verification checklist passes or any remaining failures are documented as
  unrelated pre-existing failures.
