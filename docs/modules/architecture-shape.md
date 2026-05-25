<!-- Generated from feature ui/templates/docs.tmpl files. Do not edit by hand. -->

# Architecture Shape Docs

Use `enclosure architecture shape` to validate configured file, symbol, argument, import, and line-count limits.

## When To Use It

- After editing imports.
- After adding or changing functions, methods, classes, or constructor arguments.
- Before finishing work that changes public code shape.

## How To Respond

- Split code only when it improves ownership or readability.
- Prefer direct imports when alias rules require them.
- Join imports from the same source when configured.
- Keep configured limits in `.enclosure/enclosure.yaml` rather than scattering exceptions.

## Related Commands

- `enclosure architecture health --docs`
- `enclosure architecture boundaries --docs`
- `enclosure architecture map --docs`
