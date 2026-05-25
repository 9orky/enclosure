<!-- Generated from feature ui/templates/docs.tmpl files. Do not edit by hand. -->

# Architecture Clusters Docs

Use `enclosure architecture clusters` to inspect dependency pressure by grouped source areas.

## When To Use It

- Before a broad refactor.
- When choosing a low-risk starting point.
- When a change may affect shared or high-traffic code.

## How To Respond

- Treat high pressure as a blast-radius signal, not a policy violation.
- Inspect incoming edges before changing a cluster that many files rely on.
- Inspect outgoing edges when a cluster appears to coordinate too much.
- Pair cluster output with boundary checks before changing import direction.

## Related Commands

- `enclosure architecture health --docs`
- `enclosure architecture map --docs`
- `enclosure architecture boundaries --docs`
