<!-- Generated from feature ui/templates/docs.tmpl files. Do not edit by hand. -->

# Workspace Sync Docs

Use `enclosure workspace sync` to create, refresh, or migrate `.enclosure/`.

## When To Use It

- Run `enclosure workspace sync init` when `.enclosure/` is missing.
- Use `enclosure workspace sync init --language <language>` when a workspace has
  no supported source files or multiple plausible source extractors.
- Run `update` after upgrading the CLI or refreshing shared guidance.
- Run `migrate` after upgrading from 2.x to 3.x to refresh packaged shared
  assets and merge new config keys.
- Review preserved local files; they contain project-owned decisions.

## How To Respond

- Do not overwrite local rule decisions just to refresh shared assets.
- Review `.enclosure/enclosure.yaml` after initialization.
- Run `enclosure --llm` for the agent operating loop.
- Run `enclosure workspace rules route --task calibration` for the initial route.
- After migration, run `enclosure workspace rules`, `enclosure workspace recipe
  --check`, and `enclosure health`.
- Treat migrate warnings as blockers before broad contract work.

## Related Commands

- `enclosure workspace sync init --language typescript`
- `enclosure workspace sync migrate`
- `enclosure workspace rules route --task calibration`
- `enclosure health --docs`
