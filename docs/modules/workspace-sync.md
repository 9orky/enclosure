<!-- Generated from feature ui/templates/docs.tmpl files. Do not edit by hand. -->

# Workspace Sync Docs

Use `enclosure workspace sync` to create or refresh `.enclosure/`.

## When To Use It

- Run `enclosure workspace sync init` when `.enclosure/` is missing.
- Use `enclosure workspace sync init --language <language>` when a workspace has
  no supported source files or multiple plausible source extractors.
- Run `update` after upgrading the CLI or refreshing shared guidance.
- Run `migrate` to merge new config keys.
- Review preserved local files; they contain project-owned decisions.

## How To Respond

- Do not overwrite local rule decisions just to refresh shared assets.
- Review `.enclosure/enclosure.yaml` after initialization.
- Run `enclosure --llm` for the agent operating loop.
- Run `enclosure workspace rules route --task calibration` for the initial route.
- Run `enclosure health` after reviewing the generated contract.
- Treat migrate warnings as blockers before broad contract work.

## Related Commands

- `enclosure workspace sync init --language typescript`
- `enclosure workspace rules route --task calibration`
- `enclosure health --docs`
