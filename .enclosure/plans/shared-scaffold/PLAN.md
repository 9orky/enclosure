# File Tree

```text
.enclosure/plans/shared-scaffold/
  PLAN.md
  UML.md
src/enclosure/shared/scaffolding/
  __init__.py
  facade.py
  domain.py
  manifest.py
  context.py
  render.py
  errors.py
  write.py
src/enclosure/features/workspace/recipe/
src/enclosure/features/pattern/catalog/
src/enclosure/features/pattern/fit/
tests/shared/scaffolding/
tests/features/workspace/recipe/
tests/features/pattern/
```

# Goal

Extract manifest-backed scaffolding behavior into one shared package with a narrow facade seam, then make recipe and pattern features consume that seam instead of carrying separate manifest, path, render, and write implementations.

The target owner is `enclosure.shared.scaffolding`. It owns generic scaffolding mechanics only: manifest loading, relative path validation, input/file/ladder models, context building, rendering, and selective materialization. Feature modules keep their product language, reports, CLI behavior, drift checks, bench reports, and templates.

The implementation target is code and complexity reduction. The shared API should be smaller than the duplicated behavior it replaces, and each integration should remove local code rather than introduce adapters that preserve the same complexity under new names.

# Phases

## Phase 1: Fresh Shared Scaffolding Package

- Objective: create the new SSOT package for generic scaffold behavior.
- Owner: `src/enclosure/shared/scaffolding/`.
- Inputs: behavioral requirements observed in current recipe, pattern fit, and pattern catalog code; no imports from those modules.
- Outputs: a complete package-root `scaffolding` facade instance backed by `ScaffoldFacade`; private helpers for YAML parsing, conversion, rendering, and writing.
- Acceptance: shared tests prove manifest loading, schema validation, path normalization, context defaults, rendering, and materialization without importing or modifying feature internals.

## Phase 2: Workspace Recipe Proof

- Objective: integrate one bounded context as proof that the shared package reduces code without changing behavior.
- Owner: `src/enclosure/features/workspace/recipe/`.
- Inputs: shared scaffolding package and existing recipe application/report behavior.
- Outputs: recipe code delegates manifest discovery, rendering, variable parsing, and file writing to `from enclosure.shared.scaffolding import scaffolding`; recipe-specific drift, bench, and report logic stays local.
- Acceptance: existing workspace recipe CLI functional tests pass unchanged, and duplicated recipe manifest/render/write helpers are removed.

## Phase 3: Remaining Modules and Cleanups

- Objective: move remaining pattern modules to the proven shared seam and delete obsolete duplicate code.
- Owner: `src/enclosure/features/pattern/catalog/`, `src/enclosure/features/pattern/fit/`, and cleanup in affected recipe files.
- Inputs: proven shared scaffolding package and recipe integration pattern.
- Outputs: pattern catalog and pattern fit delegate scaffold mechanics to shared code; feature-local wrappers, aliases, and dead helper code are removed.
- Acceptance: run `uv run pytest tests/shared tests/features/workspace/recipe tests/features/pattern` and `uv run ruff check src tests`; follow with `enclosure health` if available in the active environment.

# Acceptance

- `enclosure.shared.scaffolding.__init__` is the only public shared scaffolding seam.
- `__init__.py` is export-only and contains no behavior implementation.
- No feature imports `enclosure.shared.scaffolding` internals.
- Recipe and pattern features no longer define independent copies of scaffold manifest parsing, file rendering, path normalization, or selective materialization.
- Existing CLI commands keep their current output and exit behavior unless a test exposes an existing bug that is approved as a contract change.
- The shared package does not import from `enclosure.features`.
- Step 02 and Step 03 treat `shared.scaffolding` as complete; missing shared behavior requires updating UML and Step 01 before integration continues.

# Open Questions

- Should `pattern.fit` remain a visible feature after the extraction, or should it be folded into `pattern.catalog` later as a separate follow-up?
- Should role and slot-state values remain validated strings permanently, or should enums be introduced later only if they reduce consumer code?
- Should nested scaffold DTO types stay reachable only through `Scaffold`, or should any be promoted to package-root exports after the proof integration?
