# Changelog

All notable changes to `enclosure` will live here.

The format loosely follows Keep a Changelog, without pretending releases are a sacred ritual.

## [Unreleased]

## [3.0.0] - 2026-06-23

### Added

- Migration guide for upgrading project-local `.enclosure/` contracts from 2.x
  to 3.x.
- `workspace sync migrate` guidance for refreshing packaged shared rules and
  assistant instructions while preserving local rules, recipes, and
  `workspace.recipe.roles_map`.
- Method documentation for artifact authority, execution refinement, shell
  preview, dependency graph reasoning, recipe algebra, rule routing,
  verification, and common anti-patterns.
- Pattern catalog and fit module documentation.

### Changed

- The local contract model is now backed by typed config defaults rather than a
  packaged `resources/enclosure.yaml` file.
- Flow examples prefer `architecture.boundaries.flow.realms` while keeping
  legacy `module_tag` compatibility for existing 2.x contracts.
- Workspace sync docs now call out migration review and post-migration checks.

## [0.1.0] - 2026-05-25

### Added

- Release automation for CI, build verification, GitHub release assets, and PyPI publishing through Trusted Publishing.
- Project bootstrap and update flows for the generated `.enclosure/` contract surface.
- Packaged shared rule corpus and rule schema validation.
- Architecture checking for dependency boundaries and flow rules.
- Hotspot and summary commands that help humans and coding agents find risky parts of a codebase early.
- Python, TypeScript/JavaScript, and PHP dependency extractors.
