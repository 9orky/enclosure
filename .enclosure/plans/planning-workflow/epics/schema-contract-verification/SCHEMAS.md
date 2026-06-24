---
plan_id: planning-workflow
epic_id: schema-contract-verification
title: Schema Contract Verification Schemas
status: dry-run
stage: epics
source: event_store
generated_from: eventsourcing projection
sync_policy: projection
managed_files:
  - EPIC.md
  - USER_STORIES.md
  - SCHEMAS.md
  - flows.mermaid
  - uml.mermaid
  - tree.mermaid
native_sources:
  flows: flows.mermaid
  uml: uml.mermaid
  tree: tree.mermaid
contract_roles:
  flows: use-case contract
  uml: symbol contract
  tree: file contract
---

# Schema Contract Verification Schemas

These schemas are implementation contracts. `tree.mermaid` defines the expected files, `uml.mermaid` defines expected symbols and file ownership, and `flows.mermaid` defines the expected schema verification use cases.

## Flow

```mermaid
%% contract: use_cases
%%{init: {"theme": "base", "themeVariables": {"primaryColor": "#e0f2fe", "primaryTextColor": "#172033", "primaryBorderColor": "#0284c7", "lineColor": "#64748b", "tertiaryColor": "#f8fafc"}}}%%
flowchart LR
    subgraph commands["Commands"]
      cmd_parse["command: workspace plan contracts parse"]
      cmd_actual["command: workspace plan contracts actual"]
      cmd_compare["command: workspace plan contracts check"]
      cmd_report["command: workspace plan contracts report"]
    end

    subgraph use_cases["Use Cases"]
      uc_parse["usecase: ParsePlannedContracts\nfile: application/use_cases/parse_planned_contracts.py\nclass: ParsePlannedContracts"]
      uc_actual["usecase: DeriveActualSchemas\nfile: application/use_cases/derive_actual_schemas.py\nclass: DeriveActualSchemas"]
      uc_compare["usecase: CompareSchemaContracts\nfile: application/use_cases/compare_schema_contracts.py\nclass: CompareSchemaContracts"]
      uc_report["usecase: ReportContractDrift\nfile: application/use_cases/report_contract_drift.py\nclass: ReportContractDrift"]
    end

    subgraph models_ports["Models / Ports"]
      expected["model: ExpectedSchema"]
      modwire["port: ModwireSchemaProvider"]
      actual["model: ActualSchema"]
      drift["model: DriftReport"]
    end

    subgraph outputs["Outputs"]
      agent["output: AgentRepairInstruction"]
    end

    cmd_parse --> uc_parse
    cmd_actual --> uc_actual
    cmd_compare --> uc_compare
    cmd_report --> uc_report
    uc_parse --> expected
    uc_actual --> modwire
    modwire --> actual
    expected --> uc_compare
    actual --> uc_compare
    uc_compare --> drift
    drift --> uc_report
    uc_report --> agent

    classDef command fill:#e0f2fe,stroke:#0284c7,color:#172033;
    classDef usecase fill:#dcfce7,stroke:#16a34a,color:#172033;
    classDef model fill:#fef9c3,stroke:#ca8a04,color:#172033;
    classDef port fill:#f3e8ff,stroke:#9333ea,color:#172033;
    classDef output fill:#f1f5f9,stroke:#64748b,color:#172033;
    class cmd_parse,cmd_actual,cmd_compare,cmd_report command;
    class uc_parse,uc_actual,uc_compare,uc_report usecase;
    class expected,actual,drift model;
    class modwire port;
    class agent output;
```

## UML

```mermaid
%% contract: symbols
%%{init: {"theme": "base", "themeVariables": {"primaryColor": "#eef2ff", "primaryTextColor": "#172033", "primaryBorderColor": "#64748b", "lineColor": "#64748b"}}}%%
classDiagram
    class ParsePlannedContracts {
      <<file:application/use_cases/parse_planned_contracts.py>>
      +execute(epic_id)
    }

    class DeriveActualSchemas {
      <<file:application/use_cases/derive_actual_schemas.py>>
      +execute(scope)
    }

    class CompareSchemaContracts {
      <<file:application/use_cases/compare_schema_contracts.py>>
      +execute(expected, actual)
    }

    class ReportContractDrift {
      <<file:application/use_cases/report_contract_drift.py>>
      +execute(report)
    }

    class ContractParser {
      <<file:application/contract_parser.py>>
      +parse_tree()
      +parse_uml()
      +parse_use_cases()
    }

    class ActualSchemaProvider {
      <<file:application/actual_schema.py>>
      +query_modwire()
      +normalize_symbols()
    }

    class ContractComparator {
      <<file:application/contract_compare.py>>
      +compare_files()
      +compare_symbols()
      +compare_use_cases()
    }

    class DriftReport {
      <<file:application/drift_report.py>>
      +list_missing()
      +list_extra()
      +list_mismatched()
      +render_agent_guidance()
    }

    ParsePlannedContracts --> ContractParser
    DeriveActualSchemas --> ActualSchemaProvider
    CompareSchemaContracts --> ContractComparator
    ReportContractDrift --> DriftReport
    ContractParser --> ContractComparator
    ActualSchemaProvider --> ContractComparator
    ContractComparator --> DriftReport
```

## Tree

```mermaid
%% contract: files
%%{init: {"theme": "base", "themeVariables": {"labelColor": "#172033", "lineColor": "#64748b"}}}%%
treeView-beta
  "workspace_plan"
    "application"
      "contract_parser.py"
      "actual_schema.py"
      "contract_compare.py"
      "drift_report.py"
      "use_cases"
        "parse_planned_contracts.py"
        "derive_actual_schemas.py"
        "compare_schema_contracts.py"
        "report_contract_drift.py"
    "infrastructure"
      "modwire_schema_provider.py"
```
