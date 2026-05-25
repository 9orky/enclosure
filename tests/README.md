# Test Layout

Tests are grouped by the public seam a human is likely to inspect first.

- `shared/` covers reusable `enclosure.shared` behavior and cross-feature support.
- `features/` mirrors `src/enclosure/features` for feature-owned behavior.
- `ui/` covers CLI and documentation surfaces that span feature modules.
- `support/` contains test-only helpers and fixture quality checks.
- `fixtures/projects/` contains copyable project workspaces used by functional tests.

Project fixtures should stay realistic enough to support human review and modwire
coverage. Every supported language needs a minimal project with imports, classes,
functions, methods, properties, and ignored files.
