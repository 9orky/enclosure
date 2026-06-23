# Migrating Local Contracts From 2.x To 3.x

This guide is for agents and maintainers upgrading an existing project-local
`.enclosure/` contract after installing Enclosure 3.x.

The short path is:

```bash
enclosure workspace sync migrate
enclosure workspace rules
enclosure workspace recipe --check
enclosure health
```

Run those commands from the repository root that owns the `.enclosure/`
directory.

## What Changed

Enclosure 3.x keeps the same contract surface, but tightens how generated and
project-owned assets are separated.

- Packaged shared rules live under `.enclosure/rules/shared/` and can be
  refreshed from the CLI.
- Project rules live under `.enclosure/rules/local/` and remain project-owned.
- `AGENTS.md` and `.github/copilot-instructions.md` are refreshed as packaged
  assistant entry instructions.
- `.enclosure/enclosure.yaml` is validated through typed config defaults before
  checks run.
- `workspace.guidance` and newer report-limit sections may be added to older
  contracts.
- `architecture.boundaries.flow.realms` is the preferred 3.x shape for module
  flow. The legacy `flow.module_tag` key remains accepted for compatibility.
- Recipe manifests remain `schema_version: 1`; existing recipes do not need a
  schema-version bump.

## Before You Start

Save or review any local edits first:

```bash
git status --short
```

Then upgrade the CLI with your normal package manager. For a `pipx` install:

```bash
pipx upgrade enclosure
```

If the project has no `.enclosure/` directory yet, do not use this migration
guide. Run first-run setup instead:

```bash
enclosure workspace sync init
enclosure --llm
enclosure workspace rules route --task calibration
enclosure health
```

## Migration Steps

1. Start in `.enclosure/` and read the project contract.

   Confirm the local instruction says agents should start there. Read
   `.enclosure/enclosure.yaml`, `.enclosure/rules/INDEX.md`, and the shallowest
   matching route for the work you are about to do. Run the CLI commands below
   from the repository root after this reading pass.

2. Run the migrator.

   ```bash
   enclosure workspace sync migrate
   ```

   The migrator refreshes packaged shared rules and assistant instruction files,
   creates required workspace folders, and merges missing config keys into
   `.enclosure/enclosure.yaml`.

3. Review the write summary.

   Treat `Updated` shared rule files and assistant instruction files as expected.
   Treat `Preserved` local files as project-owned decisions. Do not overwrite
   preserved files just to make the generated tree look uniform.

4. Review config warnings before continuing.

   If `migrate` prints config warnings, pause before broad architecture work.
   Warnings mean part of the existing config could not be merged automatically
   or needs human review under the 3.x config model.

5. Validate the migrated contract.

   ```bash
   enclosure workspace rules
   enclosure workspace recipe --check
   enclosure health
   ```

   If the project has active architecture checks in CI, also run the focused
   checks that match the changed contract:

   ```bash
   enclosure architecture boundaries
   enclosure architecture shape
   enclosure architecture health
   ```

## Manual Review Checklist

- Keep `.enclosure/rules/local/**` local. Move project-specific edits out of
  `.enclosure/rules/shared/**` before future syncs overwrite shared guidance.
- Keep `.enclosure/recipes/**` local. `migrate` does not rewrite recipe
  manifests or templates.
- Keep `workspace.recipe.roles_map` project-owned. The migrator preserves this
  map instead of replacing it with package defaults.
- Check `workspace.recipe.skip` for generated caches, build outputs, or local
  tool directories that should not be compared to recipes.
- Prefer `architecture.boundaries.flow.realms` for new flow config:

  ```yaml
  architecture:
    boundaries:
      flow:
        layers: [ui, application, infrastructure, domain]
        realms:
          - { name: module, module_tag: module }
        analyzers: [backward-flow, no-cycles]
  ```

  A 2.x contract using `module_tag: feature` can keep working, but a reviewed
  3.x contract should move the module tag into `realms` when the architecture is
  already understood. The migrator does not add empty legacy `module_tag` or
  `module_tags` keys to contracts that already use `realms`.

## Agent Handoff Prompt

Use this prompt inside projects that need a local contract upgrade:

```text
Upgrade this repository's .enclosure contract from Enclosure 2.x to 3.x.

Start in .enclosure/ and stay anchored there while discovering guidance. Read
.enclosure/enclosure.yaml, .enclosure/rules/INDEX.md, and the relevant route.
After that reading pass, run Enclosure CLI commands from the repository root.

Run `enclosure workspace sync migrate`, then review updated, preserved, and
warning lines. Do not overwrite .enclosure/rules/local/**, .enclosure/recipes/**,
or workspace.recipe.roles_map unless the project owner explicitly approves the
contract change.

Finish by running `enclosure workspace rules`, `enclosure workspace recipe
--check`, and `enclosure health`. Also run focused architecture checks if the
migration changed boundaries, shape, or flow settings.

Report the files changed, config warnings, rule/recipe/health results, and any
manual architecture decisions that still need human approval.
```

## Rollback

The migration edits normal repository files. If the result is wrong, inspect the
diff and revert only the migration changes you do not want to keep. Do not remove
local rules or recipes unless the project owner confirms they are obsolete.
