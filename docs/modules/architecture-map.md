<!-- Generated from feature ui/templates/docs.tmpl files. Do not edit by hand. -->

# Architecture Map Docs

Use `enclosure architecture map` to see configured modules, layers, cross-module dependencies, unknown files, and hotspots.

## When To Use It

- Before deciding where new behavior belongs.
- When entering an unfamiliar repository.
- Before adding a dependency between modules.

## How To Respond

- Use module and layer names from the map when planning changes.
- Inspect public seams before adding cross-module imports.
- Avoid guessing ownership for unknown files; check local rules and configuration first.
- Treat hotspots as risk signals, not automatic failures.

## Related Commands

- `enclosure architecture health --docs`
- `enclosure architecture boundaries --docs`
- `enclosure architecture clusters --docs`
