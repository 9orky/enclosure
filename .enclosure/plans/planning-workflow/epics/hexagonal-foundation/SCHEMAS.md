# Hexagonal Foundation Schemas

These schemas are implementation contracts shown as a display projection. The
native sources are `flows.mermaid`, `uml.mermaid`, and `tree.mermaid`; during
projection updates their content is pasted into the sections below.

`tree.mermaid` defines the expected files, `uml.mermaid` defines expected
symbols and file ownership, and `flows.mermaid` defines how feature-owned ports
and adapters use the shared shape.

## Flow

```mermaid
%% contract: flow
%%{init: {"theme": "base", "themeVariables": {"primaryColor": "#e0f2fe", "primaryTextColor": "#172033", "primaryBorderColor": "#0284c7", "lineColor": "#64748b", "tertiaryColor": "#f8fafc"}}}%%
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
      app_service["application service\nuses ports"]
      domain_model["domain model\nno outward imports"]
    end

    port_shape -. shapes .-> event_store
    port_shape -. shapes .-> projection_store
    port_shape -. shapes .-> schema_provider
    adapter_shape -. shapes .-> sqlite_store
    adapter_shape -. shapes .-> filesystem_projection
    adapter_shape -. shapes .-> modwire_provider
    adapter_binding --> adapter_shape
    adapter_binding --> port_shape
    app_service --> event_store
    app_service --> projection_store
    app_service --> schema_provider
    sqlite_store --> event_store
    filesystem_projection --> projection_store
    modwire_provider --> schema_provider
    app_service --> domain_model

    classDef shared fill:#e0f2fe,stroke:#0284c7,color:#172033;
    classDef port fill:#f3e8ff,stroke:#9333ea,color:#172033;
    classDef adapter fill:#dcfce7,stroke:#16a34a,color:#172033;
    classDef core fill:#ffedd5,stroke:#ea580c,color:#172033;
    class port_shape,adapter_shape,adapter_binding shared;
    class event_store,projection_store,schema_provider port;
    class sqlite_store,filesystem_projection,modwire_provider adapter;
    class app_service,domain_model core;
```

## UML

```mermaid
%% contract: symbols
%%{init: {"theme": "base", "themeVariables": {"primaryColor": "#eef2ff", "primaryTextColor": "#172033", "primaryBorderColor": "#64748b", "lineColor": "#64748b"}}}%%
classDiagram
    class Port {
      <<Protocol: shared/hexagonal/ports.py>>
    }

    class InboundPort {
      <<Protocol: shared/hexagonal/ports.py>>
    }

    class OutboundPort {
      <<Protocol: shared/hexagonal/ports.py>>
    }

    class Adapter {
      <<Protocol: shared/hexagonal/adapters.py>>
      +port()
    }

    class AdapterBinding {
      <<file:shared/hexagonal/adapters.py>>
      +str adapter_name
      +str port_name
      +str module_path
    }

    class HexagonalDependencyRule {
      <<file:shared/hexagonal/dependencies.py>>
      +allows(source_layer, target_layer)
      +requires_port(source_layer, target_layer)
    }

    Port <|-- InboundPort
    Port <|-- OutboundPort
    Adapter --> Port
    AdapterBinding --> Adapter
    AdapterBinding --> Port
    HexagonalDependencyRule --> Port
```

## Tree

```mermaid
%% contract: files
%%{init: {"theme": "base", "themeVariables": {"labelColor": "#172033", "lineColor": "#64748b"}}}%%
treeView-beta
  "shared"
    "hexagonal"
      "__init__.py"
      "ports.py"
      "adapters.py"
      "dependencies.py"
```
