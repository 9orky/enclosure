# Hexagonal Foundation Schemas

## Navigation

- Epic: [Hexagonal Foundation](EPIC.md)
- Source chain: [DRAFT.md](../../DRAFT.md#hexagonal-foundation) -> [PLAN.md](../../PLAN.md#hexagonal-foundation) -> [UML.md](../../UML.md#slug-identity-contract)
- Native sources: [flows.mermaid](flows.mermaid), [uml.mermaid](uml.mermaid), [tree.mermaid](tree.mermaid)
- Siblings: [USER_STORIES.md](USER_STORIES.md)

These schemas are implementation contracts shown as a display projection. The
native sources are `flows.mermaid`, `uml.mermaid`, and `tree.mermaid`; during
projection updates their content is pasted into the sections below.

`tree.mermaid` defines the expected files, `uml.mermaid` defines expected
symbols and file ownership, and `flows.mermaid` defines how feature-owned ports
and adapters use the shared shape.

## Flow

```mermaid
%% contract: flow
%%{init: {"theme": "base", "themeVariables": {"primaryColor": "#dbeafe", "primaryTextColor": "#172033", "primaryBorderColor": "#2563eb", "secondaryColor": "#e0f2fe", "secondaryBorderColor": "#0284c7", "tertiaryColor": "#f8fafc", "lineColor": "#2563eb"}}}%%
flowchart LR
    subgraph foundation["Shared Hexagonal Contracts"]
      port_shape["interface: Port\nfile: shared/hexagonal/ports.py\nclass: Port"]
      adapter_shape["interface: Adapter\nfile: shared/hexagonal/adapters.py\nclass: Adapter"]
      adapter_binding["model: AdapterBinding\nfile: shared/hexagonal/adapters.py\nclass: AdapterBinding"]
    end

    subgraph feature_ports["Feature-Owned Ports"]
      event_store["port: EventStore\nowned by workspace.plan"]
      projection_store["port: ProjectionStore\nowned by workspace.plan"]
      schema_provider["port: ModwireSchemaProvider\nowned by workspace.plan"]
    end

    subgraph feature_adapters["Feature-Owned Adapters"]
      sqlite_store["adapter: SQLiteEventStore"]
      filesystem_projection["adapter: FilesystemProjectionStore"]
      modwire_provider["adapter: ModwireSchemaProviderAdapter"]
    end

    subgraph app_domain["Application / Domain"]
      app_service["service: application service\nuses ports"]
      domain_model["domain: domain model\nno outward imports"]
    end

    subgraph outputs["Outputs"]
      dependency_rule{"decision: dependency crosses layer?"}
      allowed["output: dependency allowed"]
      blocked["halt: dependency blocked"]
    end

    port_shape -. shapes .-> event_store
    port_shape -. shapes .-> projection_store
    port_shape -. shapes .-> schema_provider
    adapter_shape -. shapes .-> sqlite_store
    adapter_shape -. shapes .-> filesystem_projection
    adapter_shape -. shapes .-> modwire_provider
    adapter_binding -->|describes| adapter_shape
    adapter_binding -->|binds to| port_shape
    app_service -->|depends on| event_store
    app_service -->|depends on| projection_store
    app_service -->|depends on| schema_provider
    sqlite_store -. implements .-> event_store
    filesystem_projection -. implements .-> projection_store
    modwire_provider -. implements .-> schema_provider
    app_service -->|uses| domain_model
    app_service -->|checked by| dependency_rule
    dependency_rule -->|through port| allowed
    dependency_rule -->|deep import| blocked

    classDef shared fill:#e0f2fe,stroke:#0284c7,color:#172033;
    classDef port fill:#f3e8ff,stroke:#9333ea,color:#172033;
    classDef adapter fill:#dcfce7,stroke:#16a34a,color:#172033;
    classDef core fill:#ffedd5,stroke:#ea580c,color:#172033;
    classDef output fill:#f1f5f9,stroke:#64748b,color:#172033;
    class port_shape,adapter_shape,adapter_binding shared;
    class event_store,projection_store,schema_provider port;
    class sqlite_store,filesystem_projection,modwire_provider adapter;
    class app_service,domain_model core;
    class dependency_rule,allowed,blocked output;
```

## UML

```mermaid
%% contract: symbols
%%{init: {"theme": "base", "themeVariables": {"primaryColor": "#f5f3ff", "primaryTextColor": "#172033", "primaryBorderColor": "#7c3aed", "secondaryColor": "#ede9fe", "secondaryBorderColor": "#6d28d9", "tertiaryColor": "#faf5ff", "lineColor": "#7c3aed"}}}%%
classDiagram
    class Port {
      <<Interface: shared/hexagonal/ports.py>>
      +name() str
    }

    class InboundPort {
      <<Interface: shared/hexagonal/ports.py>>
      +name() str
    }

    class OutboundPort {
      <<Interface: shared/hexagonal/ports.py>>
      +name() str
    }

    class Adapter {
      <<Interface: shared/hexagonal/adapters.py>>
      +port() Port
    }

    class AdapterBinding {
      <<file:shared/hexagonal/adapters.py>>
      +str adapter_name
      +str port_name
      +str module_path
    }

    class HexagonalDependencyRule {
      <<file:shared/hexagonal/dependencies.py>>
      +allows(str, str) bool
      +requires_port(str, str) bool
    }

    Port <|-- InboundPort : specializes
    Port <|-- OutboundPort : specializes
    Adapter "1" --> "1" Port : exposes
    AdapterBinding "1" --> "1" Adapter : describes
    AdapterBinding "1" --> "1" Port : binds
    HexagonalDependencyRule "1" ..> "1" Port : requires boundary
```

## Tree

```mermaid
%% contract: files
%%{init: {"theme": "base", "themeVariables": {"primaryColor": "#ecfdf5", "primaryTextColor": "#064e3b", "primaryBorderColor": "#059669", "labelColor": "#064e3b", "lineColor": "#059669", "tertiaryColor": "#f0fdf4"}}}%%
treeView-beta
  "shared"
    "__init__.py"
    "hexagonal"
      "__init__.py"
      "ports.py"
      "adapters.py"
      "dependencies.py"
```
