# Step 02: Migrate Architecture Bounded Context

Status: Draft

## Goal

Integrate the completed `shared.config` package from Step 01 into the
architecture bounded context only.

This step is the pilot migration. It proves that architecture callers can use
`settings`, `settings.query("architecture...")`, and `settings.metadata` without
changing any other bounded context.

This step must treat `shared.config` as finished. Do not add new package
capabilities here unless Step 01 is first updated and completed again.

## Source Of Truth

[UML.md](UML.md) is the source of truth for integration boundaries. Step 02 must
strictly follow the caller direction, deleted old ownership, no-bridge rule, and
independence boundary shown in the UML.

If architecture integration needs behavior not represented in the UML, stop,
update Step 01 and the UML, complete Step 01 independently, then resume Step 02.

## Root Boundary

Step 02 may edit only these roots:

- `src/enclosure/features/architecture/`
- `tests/features/architecture/`

Step 02 must not edit:

- `src/enclosure/shared/config/`
- non-architecture bounded contexts such as `workspace`, `pattern`, or `health`
- shared helpers outside the architecture root
- CLI, resource, or UI files outside the architecture root

If an architecture migration appears to require edits outside this root
boundary, stop and move that work to Step 03 or return to Step 01 if it is a
missing `shared.config` capability.

## Integration Boundary

Architecture callers may depend on `shared.config`, but `shared.config` must not
begin depending on architecture callers.

No backwards-compatibility bridges are allowed.

No architecture caller may call a project-root discovery helper, walk upward
from the current working directory, or infer the project root from config paths.
Any architecture code that needs the project root or a common workspace path
must read it from `settings.metadata` and pass that value downward.

## File Tree

- `src/enclosure/features/architecture/`
- `src/enclosure/features/architecture/config/` (delete after callers move)
- `tests/features/architecture/`

## Work Items

- Replace architecture config imports with `from enclosure.shared.config import settings`.
- Replace architecture section-level config loading with `settings.query("architecture")` or narrower `settings.query("architecture...")` calls.
- Replace architecture project-root discovery with `settings.metadata.project_root` inside the architecture root.
- Replace architecture canonical config-path construction with `settings.metadata.canonical_config_path` when the architecture root needs to report or reference the canonical manifest path.
- Pass `settings.metadata.project_root` and queried architecture settings into downstream architecture functions and reports instead of resolving them locally.
- Delete `src/enclosure/features/architecture/config/` after all architecture callers move.
- Remove architecture duplicate `load_config()` functions and repeated config error aliases.
- Remove architecture section-level config validation after equivalent shared-config validation is already covered by Step 01 tests.
- Update architecture tests that previously validated independent architecture sections to use the shared root graph or focused shared-config validators.
- Update architecture tests that patched project-root discovery to patch or construct architecture inputs around `settings.metadata.project_root`.
- Run architecture-focused verification.

## Acceptance

- Architecture production callers use `from enclosure.shared.config import settings`.
- Architecture integration strictly follows [UML.md](UML.md).
- Architecture edits stay inside the Step 02 root boundary.
- Architecture callers use `settings.query("architecture...")` for architecture config data.
- Architecture callers use `settings.metadata.project_root` as the runtime source of project-root truth.
- Architecture callers use `settings.metadata.canonical_config_path` when the canonical manifest output path is needed.
- Architecture callers do not rediscover, infer, or resolve the project root independently.
- Architecture feature modules do not load raw YAML.
- Architecture feature modules do not validate raw manifest sections directly.
- `src/enclosure/features/architecture/config/` is deleted, not wrapped.
- No backwards-compatibility bridges are introduced.
- `shared.config` remains independent of architecture and other feature modules.
- Step 02 adds no new `shared.config` capabilities.

## Verification

- [ ] Compare Step 02 architecture integration against [UML.md](UML.md).
- [ ] Run `uv run pytest tests/shared/config`.
- [ ] Run architecture tests affected by config migration.
- [ ] Run `uv run pytest tests/features/architecture`.
- [ ] Run `enclosure architecture boundaries`.
- [ ] Run `enclosure architecture shape`.
- [ ] Run `enclosure architecture health`.
