# Anti-Patterns Method

Anti-patterns name recurring failures so reviews can identify them quickly.

## API Widening

Adding exports only so nearby code can reach an internal helper.

Better method: move responsibility to the correct owner or add a narrow
caller-driven seam.

## Deep Imports

Importing from another module's private file instead of its public seam.

Better method: use the seam, create the seam, or move the responsibility.

## Barrel Exports

Exporting everything from a package because callers might need it.

Better method: export only real caller needs.

## Contract Suppression

Changing exclusions, thresholds, tags, boundaries, recipes, or rules to hide a
failing check.

Better method: understand the failure, then fix the smallest owner.

## Shape Theater

Adding empty layers, packages, or templates because a pattern might need them
later.

Better method: keep compact files until real responsibilities justify package
growth.

## SSOT Fork

Copying configuration, policy, or domain rules into another module for local
convenience.

Better method: keep one owner and expose a narrow seam.

## Application Dumping

Putting factories, parsing, policies, adapters, and orchestration all into the
application layer.

Better method: separate domain policy, infrastructure adapters, and use-case
orchestration according to ownership.

## Silent Failure

Catching errors and continuing without reporting an explicit violation or
failure state.

Better method: return a typed report, raise a clear error, or surface the
failure at the command boundary.
