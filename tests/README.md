# Test Layout

Tests are grouped by public package seams and should avoid deep imports,
monkeypatching, or mocking.

- `shared/` covers reusable `enclosure.shared` behavior through exported seams.
