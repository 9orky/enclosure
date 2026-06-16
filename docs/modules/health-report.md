<!-- Generated from feature ui/templates/docs.tmpl files. Do not edit by hand. -->

# Enclosure Health Docs

Use `enclosure health` as the broad preflight for the current repository.

## Common Workflows

- Start with `enclosure health` before architecture-sensitive work.
- Use `enclosure workspace health` when workspace contract, rule, or recipe findings appear.
- Use `enclosure architecture health` when code architecture findings appear.
- Keep the health ladder simple: root rollup first, then one local health command, then a focused command only when needed.

## Reading Results

- Use `--v` for compact status, `--vv` for the standard report, and `--vvv` for expanded lower-level detail.
- Root health collects workspace and architecture health without replacing their local detail reports.
- Workspace and architecture sections show the same categories that their local health commands expand.
- Error findings are blocking and make the command exit nonzero.
- Attention findings provide context but do not block by themselves.

## Related Commands

- `enclosure workspace health --docs`
- `enclosure architecture health --docs`
- `enclosure workspace rules --docs`
- `enclosure architecture boundaries --docs`
