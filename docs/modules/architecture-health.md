<!-- Generated from feature ui/templates/docs.tmpl files. Do not edit by hand. -->

# Architecture Health Docs

Use `enclosure architecture health` for the architecture drilldown after root `enclosure health`.

## When To Use It

- Before starting non-trivial work.
- After changing imports, module seams, or feature structure.
- Before summarizing architecture-sensitive changes.

## How To Respond

- Use `--v` for compact status, `--vv` for the standard report, and `--vvv` for expanded module detail.
- This command is the architecture collector: boundaries, shape, map, clusters, pressure, and coherence all appear here.
- Fix boundary and shape findings first.
- Treat unknown files as classification signals.
- Treat hotspots, pressure, clusters, and coherence as stage-loop signals even when no blocking errors exist.
- Use focused commands when the health report points at a specific concern.

## Related Commands

- `enclosure architecture boundaries --docs`
- `enclosure architecture shape --docs`
- `enclosure architecture map --docs`
- `enclosure architecture pressure --docs`
- `enclosure architecture clusters --docs`
- `enclosure architecture coherence --docs`
