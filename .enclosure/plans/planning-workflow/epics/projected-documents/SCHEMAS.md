---
plan_id: planning-workflow
epic_id: projected-documents
title: Projected Planning Documents Schemas
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

# Projected Documents Schemas

These schemas are implementation contracts. `tree.mermaid` defines the expected files, `uml.mermaid` defines expected symbols and file ownership, and `flows.mermaid` defines the expected projection, scaffolding, roll-update, and import use cases.

## Flow

```mermaid
%% contract: use_cases
%%{init: {"theme": "base", "themeVariables": {"primaryColor": "#e0f2fe", "primaryTextColor": "#172033", "primaryBorderColor": "#0284c7", "lineColor": "#64748b", "tertiaryColor": "#f8fafc"}}}%%
flowchart LR
    subgraph commands["Commands / Events"]
      event_seeded["event: PlanSeededFromDraft"]
      event_changed["event: PlanChanged"]
      cmd_next["command: workspace plan next"]
      cmd_check["command: workspace plan check"]
      event_schema["event: SchemaBundleChanged"]
      event_halted["event: RollUpdateHalted"]
    end

    subgraph use_cases["Use Cases"]
      uc_render["usecase: RenderPlanProjection\nfile: application/use_cases/render_plan_projection.py\nclass: RenderPlanProjection"]
      uc_scaffold_plan["usecase: ScaffoldPlanContract\nfile: application/use_cases/scaffold_plan_contract.py\nclass: ScaffoldPlanContract"]
      uc_scaffold_epic["usecase: ScaffoldEpicPackage\nfile: application/use_cases/scaffold_epic_package.py\nclass: ScaffoldEpicPackage"]
      uc_roll["usecase: RollUpdateProjection\nfile: application/use_cases/roll_update_projection.py\nclass: RollUpdateProjection"]
      uc_import["usecase: ImportInputBlocks\nfile: application/use_cases/import_input_blocks.py\nclass: ImportInputBlocks"]
      uc_sync["usecase: CheckProjectionSync\nfile: application/use_cases/check_projection_sync.py\nclass: CheckProjectionSync"]
      uc_schema["usecase: RenderSchemaBundle\nfile: application/use_cases/render_schema_bundle.py\nclass: RenderSchemaBundle"]
    end

    subgraph services["Services"]
      renderer["service: ProjectionRenderer"]
      scaffolder["service: ProjectionScaffolder"]
      rollup["service: RollUpdateReporter"]
      importer["service: InputBlockImporter"]
      checker["service: SyncChecker"]
    end

    subgraph outputs["Events / Gates / Projections"]
      files["projection: markdown and mermaid files"]
      events["event: DraftInputBlockImported"]
      gate["gate: strict sync"]
      halted["halt: unresolved roll update"]
    end

    event_seeded --> uc_scaffold_plan
    event_changed --> uc_render
    cmd_next --> uc_roll
    cmd_next --> uc_import
    cmd_check --> uc_sync
    event_halted --> halted
    event_schema --> uc_schema
    uc_scaffold_plan --> scaffolder
    uc_scaffold_epic --> scaffolder
    uc_roll --> rollup
    uc_render --> renderer
    uc_import --> importer
    uc_sync --> checker
    uc_schema --> renderer
    scaffolder --> files
    rollup --> halted
    renderer --> files
    importer --> events
    checker --> gate

    classDef command fill:#e0f2fe,stroke:#0284c7,color:#172033;
    classDef usecase fill:#dcfce7,stroke:#16a34a,color:#172033;
    classDef service fill:#fef9c3,stroke:#ca8a04,color:#172033;
    classDef output fill:#f1f5f9,stroke:#64748b,color:#172033;
    class event_seeded,event_changed,cmd_next,cmd_check,event_schema,event_halted command;
    class uc_render,uc_scaffold_plan,uc_scaffold_epic,uc_roll,uc_import,uc_sync,uc_schema usecase;
    class renderer,scaffolder,rollup,importer,checker service;
    class files,events,gate,halted output;
```

## UML

```mermaid
%% contract: symbols
%%{init: {"theme": "base", "themeVariables": {"primaryColor": "#eef2ff", "primaryTextColor": "#172033", "primaryBorderColor": "#64748b", "lineColor": "#64748b"}}}%%
classDiagram
    class RenderPlanProjection {
      <<file:application/use_cases/render_plan_projection.py>>
      +execute(plan_id)
    }

    class ScaffoldPlanContract {
      <<file:application/use_cases/scaffold_plan_contract.py>>
      +execute(plan_id)
    }

    class ScaffoldEpicPackage {
      <<file:application/use_cases/scaffold_epic_package.py>>
      +execute(epic_id)
    }

    class RollUpdateProjection {
      <<file:application/use_cases/roll_update_projection.py>>
      +execute(plan_id)
    }

    class ImportInputBlocks {
      <<file:application/use_cases/import_input_blocks.py>>
      +execute(plan_id)
    }

    class CheckProjectionSync {
      <<file:application/use_cases/check_projection_sync.py>>
      +execute(plan_id)
    }

    class RenderSchemaBundle {
      <<file:application/use_cases/render_schema_bundle.py>>
      +execute(epic_id)
    }

    class ProjectionRenderer {
      <<file:application/projections.py>>
      +render_plan()
      +render_epic()
      +render_schemas()
    }

    class ProjectionScaffolder {
      <<file:application/scaffolding.py>>
      +scaffold_plan_contract()
      +scaffold_epic_package()
      +preserve_enrichment()
    }

    class RollUpdateReporter {
      <<file:application/roll_updates.py>>
      +detect_unresolved_changes()
      +report_halt()
    }

    class InputBlockImporter {
      <<file:application/input_blocks.py>>
      +extract_answers()
      +import_answers()
    }

    class SyncChecker {
      <<file:application/sync.py>>
      +check_projection()
      +assert_clean()
    }

    RenderPlanProjection --> ProjectionRenderer
    ScaffoldPlanContract --> ProjectionScaffolder
    ScaffoldEpicPackage --> ProjectionScaffolder
    RollUpdateProjection --> RollUpdateReporter
    RollUpdateProjection --> ProjectionScaffolder
    RenderSchemaBundle --> ProjectionRenderer
    ImportInputBlocks --> InputBlockImporter
    CheckProjectionSync --> SyncChecker
    ProjectionRenderer --> SyncChecker
    ProjectionScaffolder --> SyncChecker
    RollUpdateReporter --> SyncChecker
    InputBlockImporter --> SyncChecker
```

## Tree

```mermaid
%% contract: files
%%{init: {"theme": "base", "themeVariables": {"labelColor": "#172033", "lineColor": "#64748b"}}}%%
treeView-beta
  "workspace_plan"
    "application"
      "projections.py"
      "scaffolding.py"
      "roll_updates.py"
      "input_blocks.py"
      "sync.py"
      "use_cases"
        "render_plan_projection.py"
        "scaffold_plan_contract.py"
        "scaffold_epic_package.py"
        "roll_update_projection.py"
        "import_input_blocks.py"
        "check_projection_sync.py"
        "render_schema_bundle.py"
    "infrastructure"
      "markdown_renderer.py"
      "copier_renderer.py"
      "frontmatter_io.py"
```
