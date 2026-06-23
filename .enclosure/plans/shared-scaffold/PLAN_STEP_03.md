# Implementation Tree

```text
src/enclosure/features/pattern/catalog/
  domain/
    pattern-specific report/result language remains
    duplicate manifest model removed
  infrastructure/
    repository and manifest parser duplicates removed
    shared scaffolding facade used at the package root seam
  application/
    describe/validate use shared scaffold objects or thin pattern summaries
src/enclosure/features/pattern/fit/
  domain.py
    fit-specific preview/result dataclasses remain
    duplicate scaffold models/include helpers removed
  infrastructure.py
    repository/render/materializer duplicates removed
  application.py
    preview/materialize use shared scaffolding load/compose/render/write behavior
tests/features/pattern/
  catalog and fit proof tests
```

Status: Pending Step 02 completion; not ready for implementation.

# Goal

Move remaining modules to the proven shared scaffolding facade seam and clean up the temporary complexity left by the extraction.

This step should finish the reduction: the same manifest/include/render/write behavior should exist in one shared package, and pattern modules should only retain feature-specific orchestration and result language.

# Step Contract

- Inputs: completed Step 02 recipe proof.
- Outputs: pattern catalog and pattern fit consume `from enclosure.shared.scaffolding import scaffolding`; duplicate local scaffold behavior is removed.
- Scope: `src/enclosure/features/pattern/catalog/`, `src/enclosure/features/pattern/fit/`, focused pattern tests, and cleanup of temporary compatibility code from recipe integration if it is now proven unnecessary.
- Out of scope: changing command names, changing manifest schema, merging pattern fit into pattern catalog, adding new scaffold features.
- Owner: pattern modules own pattern vocabulary and user-facing behavior; `shared.scaffolding` owns scaffold mechanics.
- Dependency direction: pattern modules import only the shared package root facade; `shared.scaffolding` remains feature-independent.
- Step 03 must treat `shared.scaffolding` as complete. If remaining modules need new shared behavior, stop and update `UML.md` and Step 01 before continuing.

## Step 02 Dependency

Do not start Step 03 until Step 02 proves the shared seam in
`workspace.recipe`.

The expected reusable integration pattern is:

- load manifests through `scaffolding.load_all()` and `scaffolding.load()`;
- compose includes through `scaffolding.compose()`;
- render files through `scaffolding.render()`;
- materialize selected paths through `scaffolding.write()`;
- keep pattern vocabulary, summaries, catalog validation, preview statuses, and
  CLI output local to pattern modules.

# Execution

1. Resolve `scaffold_root` in pattern code from `settings.metadata.recipes_dir`; pass that path into shared calls and do not let shared code import settings.
2. Replace pattern catalog repository and manifest loading with `scaffolding.load_all()` and `scaffolding.load()`.
3. Map shared `Scaffold` objects into pattern catalog summaries only if the catalog templates/application require pattern-specific names.
4. Replace pattern catalog include traversal and composed ladder metadata reads with shared `scaffolding.compose()` where the behavior is generic.
5. Keep pattern catalog role composition strings and catalog validation local.
6. Delete `pattern.catalog.domain.manifest` types that duplicate shared scaffold models.
7. Delete `pattern.catalog.infrastructure.manifests` once all callers use the shared scaffolding facade.
8. Replace pattern fit repository with shared scaffolding facade loading.
9. Replace pattern fit include traversal, input aggregation, renderer, and materializer with `scaffolding.render()` and `scaffolding.write()`.
10. Remove pattern fit local target context, defaults, variable context, target normalization, and manifest DTO helpers.
11. Keep pattern fit preview statuses local: `create`, `skip_exists`, and `skip_config`.
12. Review `workspace.recipe` after pattern integration and remove any aliases or wrappers that were kept only for migration confidence.
13. Run a search for duplicate scaffold symbols and remove remaining private copies unless they are feature-specific by behavior, not just by name.
14. Do not add back-calls from `shared.scaffolding` into pattern or recipe code.
15. Do not add new shared scaffolding API unless Step 01 and [UML.md](UML.md)
    are reopened first.

# Verification

- Add focused pattern catalog tests for listing/loading the current fixture manifests through the public feature seam.
- Add focused pattern fit tests for missing pattern, empty scaffold, create preview, skip-existing, skip-config, and materialize.
- Run `uv run pytest tests/shared/scaffolding tests/features/workspace/recipe tests/features/pattern`.
- Run `uv run ruff check src tests`.
- Run `enclosure health` if the command is available from the local environment.
- Confirm with `rg` that `_PatternManifest`, `FilePatternRepository`, `FilePatternRenderer`, `FilePatternMaterializer`, pattern-local `_load_yaml_mapping`, local include traversal helpers, local input aggregation helpers, and duplicate pattern `RelativePath`/`PatternInputSpec`/`PatternFile` definitions no longer remain outside intentional feature result models.
- Confirm `src/enclosure/shared/scaffolding/` still has no imports from `src/enclosure/features/`.

# Completion

Step 03 is complete when recipe, pattern catalog, and pattern fit all use one shared scaffolding facade implementation, duplicate behavior is deleted, tests pass, and no cleanup wrappers remain without a current caller.

Step 03 remains blocked until Step 02 is accepted and completed.
