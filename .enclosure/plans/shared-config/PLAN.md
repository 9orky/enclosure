# Shared Config

Status: Step 01 implemented; Step 02 ready for implementation after Step 01 verification

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
- src/enclosure/shared/config/architecture/root.py
- src/enclosure/shared/config/architecture/boundaries.py
- src/enclosure/shared/config/architecture/tag.py
- src/enclosure/shared/config/architecture/boundary_rule.py
- src/enclosure/shared/config/architecture/flow.py
- src/enclosure/shared/config/architecture/clusters.py
- src/enclosure/shared/config/architecture/health.py
- src/enclosure/shared/config/architecture/map.py
- src/enclosure/shared/config/architecture/pressure.py
- src/enclosure/shared/config/architecture/shape.py
- src/enclosure/shared/config/workspace/
- src/enclosure/shared/config/workspace/root.py
- src/enclosure/shared/config/workspace/guidance.py
- src/enclosure/shared/config/workspace/recipe.py
- src/enclosure/shared/config/workspace/rules.py
- src/enclosure/shared/config/workspace/sync.py
- src/enclosure/shared/config/pattern/
- src/enclosure/shared/config/pattern/fit.py
- src/enclosure/shared/config/health/
- tests/shared/config/

## Goal

Create `enclosure.shared.config` as an independent package with a thin public API. It becomes the sole owner of config pydantic classes, manifest loading, whole-graph validation, and dot-path manifest querying.

The runtime caller API is:

```python
from enclosure.shared.config import settings
```

`settings` is a facade class instance. The most important bootstrapped value is
`settings.metadata.project_root`; after shared config loads, it is the single
source of truth for the project root across the whole application. During normal
command runtime, `settings` is loaded first and `Path.cwd()` is treated as that
project root. Metadata also owns canonical non-null paths derived from that root, such as target, plans,
recipes, rules, cache, dev, and instruction paths. Callers query config data
through `settings.query("...")` using dot paths. The value behind a selected path
can be a scalar, pydantic object, list, or tuple depending on what the key points
to.

The design fails fast and fails loud. Manifest loading, graph assembly, and pydantic validation happen before consumers get useful config data. Invalid manifest input fails immediately with a clear error instead of letting downstream modules recover from partial config.

## Source Of Truth

[UML.md](UML.md) is the source of truth for implementation. Implementers must strictly follow the package layout, class names, relationships, public seam, step boundary, and independence rules shown there.

If the text plan and UML conflict, stop and update the documents before coding. Do not silently choose one interpretation during implementation.

## Independence Rule

`shared.config` is completed before integration starts.

Step 01 must build a ready standalone package. During that step, `src/enclosure/shared/config/` must not import existing enclosure feature modules, existing bounded-context config modules, or other shared modules/packages. It may use the Python standard library plus direct third-party dependencies required for this package, such as `pydantic` and `yaml`.

No module inside `shared.config` may know anything about existing features and modules as part of Step 01. Existing feature integration happens only after Step 01.

Integration is staged by bounded-context root. Step 02 migrates the architecture
bounded context plus the current architecture extraction helper. Step 03
migrates the remaining bounded contexts after the architecture migration
succeeds. No integration step may add missing `shared.config` capabilities. If
integration discovers that the package is incomplete, return to Step 01,
complete the package independently, then resume the blocked integration step.

## Root Boundary Rule

Every step may edit only the roots declared by that step.

- Step 01 root: `src/enclosure/shared/config/` and `tests/shared/config/`.
- Step 02 roots: `src/enclosure/features/architecture/`,
  `src/enclosure/shared/architecture_code.py`, and
  `tests/features/architecture/`.
- Step 03 roots: one remaining bounded-context or cleanup root at a time, as declared by the active Step 03 migration unit.

If work appears to require edits outside the active root boundary, stop and move
that work to the step or migration unit that owns that root. Do not mix roots in
a single step.

## Target Users Or Callers

Step 01 target is the standalone `shared.config` package and its tests.

Step 02 target callers are architecture bounded-context modules and the current
architecture extraction helper that need runtime configuration:

- `architecture.*` features that consume architecture config.
- `src/enclosure/shared/architecture_code.py`, because it is the existing
  architecture extraction entry point used by architecture commands.

Step 03 target callers are the remaining bounded contexts and later integration
surfaces that need runtime configuration:

- `workspace.*` features that consume workspace config.
- pattern callers that read config data.
- health callers that read config data.
- later shared helpers and CLI flows that are outside the architecture root.

Callers should not import config models from bounded contexts after their
bounded-context migration step. Runtime callers should import `settings` from
`enclosure.shared.config` and query the validated graph through the facade.

Callers that need project location or standard workspace paths must use
`settings.metadata`. They must not rediscover the project root from the current
working directory, config path, or workspace layout helpers. The project root and
common paths are bootstrapped once by `shared.config` and passed downward from
metadata.

## Proposed Module Ownership

`src/enclosure/shared/config/` owns:

- all config pydantic classes needed for the manifest graph;
- topic subpackages for config classes, including `architecture`, `workspace`, `pattern`, and `health`;
- concise module names inside those subpackages without a redundant `config` suffix;
- manifest YAML loading implemented independently of existing enclosure modules;
- whole-graph pydantic validation;
- the `settings` facade instance;
- project root and standard workspace path metadata;
- dot-path manifest traversal;
- config errors.

Bounded contexts such as `architecture.config`, `workspace.config`,
`workspace.rules.domain.config`, and `pattern.catalog.domain.config` no longer
own config classes or config loading after their migration step. Their config
code should be deleted after equivalent replacements already exist in the
completed Step 01 package.

## Public Seam

The runtime public seam is intentionally thin:

```python
from enclosure.shared.config import settings
```

Required behavior:

- `settings` is a singleton facade class instance.
- `settings.metadata.project_root` is the application-wide source of truth for the project root.
- `settings.metadata.canonical_config_path` is the canonical manifest output path.
- `settings.metadata` exposes standard workspace paths as non-null `Path` values.
- `settings.query("...")` exposes the validated config graph through dot paths.
- `settings.dump_manifest()` dumps the currently loaded validated graph to YAML.
- Dot-path traversal may return scalars, pydantic objects, lists, or tuples.
- Missing paths raise `AttributeError`.
- Config loading and validation failures raise loud config errors before useful settings access succeeds.

The public seam should not expose:

- dict-style manifest access;
- generic `.get(...)` fallback access;
- public lazy `load()` or `manifest` facade members;
- bounded-context config loaders;
- backwards-compatible config bridges;
- raw YAML parsing helpers as caller-facing API.
- project-root discovery helpers as caller-facing API.
- `enclosure.shared.layout` as a middle layer for project-root or path ownership.
- bootstrap overrides through `settings.dump_manifest(...)`; project-specific
  bootstrap mutation belongs outside the public facade method.

## Private Internals

Private implementation details should include:

- manifest filename selection and YAML loading from the cwd-derived project root;
- manifest construction from the cwd-derived project root;
- accepted manifest filename checks for `.enclosure/enclosure.yaml` and `.enclosure/enclosure.yml`;
- top-level mapping validation;
- whole-manifest pydantic validation into a root settings model;
- generic manifest defaults declared on config model fields wherever possible;
- default-manifest YAML dumping from the validated pydantic graph;
- dot-path object wrapping for validated graph traversal;
- manual declaration of every config class inside `shared.config`;
- error wrapping that reports unreadable manifests, invalid YAML, wrong top-level shape, and pydantic validation failures clearly.

Do not add backwards-compatibility bridges. The migration removes old config ownership rather than wrapping it.

## Expected Layers

- Domain: config error types, strict model base, topic subpackages for pydantic config classes, root settings model, dot-path query object, facade class.
- Infrastructure: manifest filename selection and YAML file loading from the cwd-derived project root.
- Application: the exported `settings` instance that coordinates eager load, validation, metadata access, and query access.
- UI: absent.

## Inputs, Outputs, And Data

Inputs:

- `.enclosure/enclosure.yaml` or `.enclosure/enclosure.yml`.
- Manually declared config pydantic classes inside `shared.config`.

Outputs:

- A validated root pydantic config object for the whole config graph.
- `settings.query("...")`, a dot-path query surface over the validated graph.
- `settings.dump_manifest()`, a YAML representation of the validated graph.
- `Manifest.dump_default()`, a YAML representation of the generic default graph.
- Stable project root and standard workspace path metadata.
  `settings.metadata.project_root` is the application-wide SSOT after config
  bootstrap, and metadata path fields are the source of truth for standard
  workspace locations.

Data behavior:

- Existing manifest schema should remain valid unless whole-graph validation reveals a real validation defect.
- Existing nested config defaults should remain effective and generic defaults should be declared on the pydantic classes where possible.
- Generated manifests should be able to come from the default pydantic graph once integration replaces packaged template reads.
- `settings` construction treats `Path.cwd()` as project root and does not search upward.
- `Manifest` owns the accepted manifest filenames and raises `ConfigError` if no manifest file exists.
- `ConfigMetadata` stores only `project_root`; every layout path is a derived property.
- No partial or best-effort config should be exposed after load or validation failure.
- Missing dot-path attributes raise `AttributeError`.

## Dependencies

Allowed in Step 01:

- Python standard library.
- `pydantic` for whole-graph validation.
- `yaml` through the existing PyYAML dependency.

Avoid in Step 01:

- Imports from existing enclosure feature modules.
- Imports from existing bounded-context config modules.
- Imports from other `enclosure.shared.*` modules.
- Dynamic plugin registration or discovery.

Avoid in all steps:

- Feature modules loading raw YAML directly.
- Feature modules calling section-level validators after migration.
- Manifest access through dictionaries, key strings, or fallback-heavy generic getters.
- Feature modules, shared helpers, or CLI flows resolving the project root independently after migration.
- Keeping `enclosure.shared.layout` as a shared middle layer after migration. Standard paths belong to `settings.metadata`; specialized paths belong to the feature that owns the concept.

## Recipe Or Scaffold

Use the existing compact config-support shape only as a loose reference. The implementation itself should be independent and package-shaped rather than a feature module:

- no command UI;
- thin `__init__.py`;
- internal support modules;
- topic subpackages for config classes.

Because `src/enclosure/shared` is outside `architecture.root`, follow shared package style while keeping Step 01 independent from existing enclosure feature and shared modules.

## Design Artifacts

- [Shared config UML](UML.md)
- [Step 01](PLAN_STEP_01.md)
- [Step 02](PLAN_STEP_02.md)
- [Step 03](PLAN_STEP_03.md)

## Phases

Phase 1: Complete standalone `shared.config`.

Owner: `src/enclosure/shared/config/`.
Inputs: manifest schema requirements and standalone tests.
Outputs: a ready `shared.config` package with config classes, independent manifest loading, whole-graph validation, `settings`, and dot-path manifest querying.
Acceptance: `shared.config` is complete after this phase and imports no existing enclosure feature modules, bounded-context config modules, or other shared modules/packages.

Phase 2: Integrate architecture bounded context.

Owner: `src/enclosure/features/architecture/`,
`src/enclosure/shared/architecture_code.py`, and architecture tests.
Inputs: completed Step 01 package.
Outputs: architecture config callers use `from enclosure.shared.config import settings`; architecture bounded-context config ownership is removed inside the architecture root.
Acceptance: no compatibility bridges are introduced, edits stay inside the architecture step roots, integration does not change the standalone ownership rules established in Step 01, and Step 02 does not add new `shared.config` capabilities.

Phase 3: Integrate remaining bounded contexts.

Owner: remaining bounded-context roots and their tests.
Inputs: completed Step 01 package and successful Step 02 architecture migration.
Outputs: workspace, pattern, health, and later allowed integration surfaces use
`from enclosure.shared.config import settings`; runtime project-root and
standard workspace path access comes from `settings.metadata`; remaining
bounded-context config ownership is removed; duplicate loader, project-root
discovery, standard path construction, packaged default config template,
`shared.layout`, and section-validation code are deleted within the allowed
roots for each migration unit.
Acceptance: edits stay inside the root boundary for each migration unit, no
compatibility bridges are introduced, and Step 03 does not add new
`shared.config` capabilities.

## Code Reduction Opportunities

- Delete `src/enclosure/features/architecture/config/` after moving `ArchitectureConfig` into `shared.config.architecture`.
- Delete `src/enclosure/features/workspace/config/` in Step 03 after moving `WorkspaceConfig` and nested workspace config ownership into `shared.config.workspace`.
- Delete nested config modules such as `workspace.rules.domain.config` and `pattern.catalog.domain.config` in Step 03 after their classes exist in the completed Step 01 package.
- Replace duplicate `load_config()` functions with the single `settings` facade.
- Replace project-root discovery helpers with `settings.metadata.project_root`.
- Replace standard workspace path helpers with metadata path fields.
- Delete `src/enclosure/shared/layout.py`; move specialized helpers such as recipe manifest path construction into their owning feature module.
- Remove `config.section(...)` if no internal shared-config implementation still needs section-level validation.
- Collapse repeated `ConfigError` aliases into one shared error type.
- Simplify tests that separately validate architecture and workspace config sections by validating the full root graph once and adding focused tests for nested validators.
- Reduce import forwarding in bounded-context `__init__.py` files that only re-export config classes.

## Acceptance

- `shared.config` is a package, not a single module.
- Implementation strictly follows [UML.md](UML.md).
- Step 01 completes `shared.config` as an independent ready solution.
- During Step 01, `shared.config` imports no existing enclosure feature modules, bounded-context config modules, or other shared modules/packages.
- `shared.config` owns all config pydantic classes needed for the manifest graph.
- Config classes are grouped under topic subpackages such as `architecture`, `workspace`, `pattern`, and `health`.
- Module names inside those subpackages omit redundant `config` suffixes.
- `shared.config` loads the whole manifest and validates the full config graph through pydantic.
- `from enclosure.shared.config import settings` is the public API.
- `settings` is a facade class instance.
- `settings.metadata.project_root` is the application-wide source of truth for project root.
- `settings.metadata` is the source of truth for standard workspace paths.
- Step 02 architecture callers do not resolve or rediscover project root
  independently inside the architecture root or the architecture extraction
  helper.
- Step 03 callers do not resolve or rediscover project root independently inside their migration roots.
- `src/enclosure/shared/layout.py` is removed during the step that owns the final remaining callers and the shared root.
- `settings.query("...")` is queryable by dot paths.
- Dot-path queries can return scalar values, config objects, lists, or tuples.
- Missing dot-path attributes raise `AttributeError`.
- Loading or validation failures fail fast and fail loud.
- Step 02 integrates the completed package into architecture without backwards-compatibility bridges.
- Step 03 integrates the completed package into remaining bounded contexts without backwards-compatibility bridges.
- Integration steps do not add new `shared.config` capabilities; missing package capability sends the work back to Step 01.
- Bounded-context config classes and loaders are removed during integration.
- Code reduction opportunities are applied where directly unlocked by the migration.

## Verification Checklist

- [ ] Run Step 01 standalone shared config tests.
- [ ] Compare implementation against [UML.md](UML.md).
- [ ] Confirm `src/enclosure/shared/config/` imports no existing enclosure feature modules, bounded-context config modules, or other shared modules/packages.
- [ ] Run shared config tests covering root graph validation and dot-path queries.
- [ ] Run tests for features migrated from bounded-context config imports.
- [ ] Run tests that cover invalid manifests and fail-fast behavior.
- [ ] Run `uv run pytest tests/shared/config`.
- [ ] Run `enclosure health`.
- [ ] Run `enclosure workspace health` if workspace files changed.
- [ ] Run `enclosure architecture boundaries`.
- [ ] Run `enclosure architecture shape`.
- [ ] Run `enclosure architecture health` if architecture-sensitive code changed.

## Open Questions

- Resolved: `settings.query("...")` uses an internal query wrapper over validated pydantic models and returns selected values directly.
- Resolved: `settings.metadata.project_root` is the application-wide SSOT for project root, `settings.metadata.canonical_config_path` is the canonical manifest output path, and standard workspace paths live on metadata as non-null `Path` values.
- Should validators preserve current error message wording exactly, or is clearer root-graph pydantic output acceptable?

## Notes For The Implementing Agent

Treat Step 01 as a standalone package build. Do not import existing feature modules, old config modules, or other shared helpers to make the package work.

Only after Step 01 is complete should Step 02 touch architecture callers. Only
after Step 02 succeeds should Step 03 touch remaining bounded contexts. This
keeps implementation risk low: first prove `shared.config`, then prove the
architecture migration, then migrate the rest root by root.

Do the integration as a deliberate break from bounded-context config ownership. There are no backwards-compatibility bridges in this plan.
