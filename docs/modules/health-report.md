<!-- Generated from feature ui/templates/docs.tmpl files. Do not edit by hand. -->

# Enclosure Health Docs

Use `enclosure health` as the broad preflight for the current repository.

## Common Workflows

- Start with `enclosure health` before architecture-sensitive work.
- Use `enclosure workspace health` when workspace contract, rule, or recipe findings appear.
- Use `enclosure architecture health` when code architecture findings appear.
- Drill into focused commands only after the broad report points at a concern.

## Reading Results

- Workspace and architecture sections summarize their own health reports.
- Error findings are blocking and make the command exit nonzero.
- Attention findings provide context but do not block by themselves.

## Related Commands

- `enclosure workspace health --docs`
- `enclosure architecture health --docs`
- `enclosure workspace rules --docs`
- `enclosure architecture boundaries --docs`
