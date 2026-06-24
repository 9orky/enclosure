# User Stories

## Navigation

- Epic: [Hexagonal Foundation](EPIC.md)
- Source chain: [DRAFT.md](../../DRAFT.md#hexagonal-foundation) -> [PLAN.md](../../PLAN.md#hexagonal-foundation) -> [UML.md](../../UML.md#slug-identity-contract)
- Siblings: [SCHEMAS.md](SCHEMAS.md), [flows.mermaid](flows.mermaid), [uml.mermaid](uml.mermaid), [tree.mermaid](tree.mermaid)

## define-port-shape

As a module author, I want a shared port interface shape so that planning ports
are recognizable and consistent across epics.

Acceptance criteria:

- A shared port protocol exists in `shared.hexagonal`.
- Feature-specific ports can inherit or satisfy the shared protocol.
- The shared protocol does not prescribe feature-specific methods.

## define-adapter-shape

As an infrastructure author, I want adapters to declare which port they
implement so that dependency direction is visible in code and schemas.

Acceptance criteria:

- A shared adapter contract or metadata type exists.
- Adapter declarations reference the implemented port.
- Adapters are allowed to depend inward on domain and port types.

## enforce-hexagonal-dependencies

As an agent, I want clear dependency rules for ports and adapters so that new
planning code does not bypass module boundaries.

Acceptance criteria:

- Application services depend on ports instead of infrastructure internals.
- Infrastructure implements ports and stays outside domain logic.
- Domain objects do not import application, infrastructure, or UI code.
- Shared hexagonal contracts contain no concrete planning behavior.
