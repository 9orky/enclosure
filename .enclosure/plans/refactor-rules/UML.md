# Workspace Recipe Refactor UML

## Target File Tree

```text
src/enclosure/features/workspace/recipe/
  __init__.py
  domain.py
  infrastructure.py
  application/
    __init__.py
    commands.py
    queries.py
    bench.py
    catalog.py
    drift.py
    generation.py
  ui/
    __init__.py
    bench_html.py
    cli.py
    templates/
      bench_all_result.tmpl
      bench_result.tmpl
      check_report.tmpl
      docs.tmpl
      drift_report.tmpl
      dry_run_result.tmpl
      generate_result.tmpl
      llm.tmpl
      recipe_list.tmpl
      recipe_summary.tmpl
```

```text
tests/features/workspace/recipe/
  test_catalog.py
  test_generation.py
  test_drift.py
  test_bench.py
  test_cli.py
```

## UML Schema

### Package Diagram

```mermaid
flowchart LR
  PackageAPI["recipe/__init__.py<br/>public facade"]
  CLI["ui/cli.py<br/>Typer command"]
  Html["ui/bench_html.py<br/>bench HTML presenter"]
  Commands["application/commands.py<br/>write use cases"]
  Queries["application/queries.py<br/>read use cases"]
  Generation["application/generation.py<br/>preview + materialize"]
  Drift["application/drift.py<br/>recipe drift"]
  Bench["application/bench.py<br/>bench reports"]
  Catalog["application/catalog.py<br/>catalog + roles"]
  Infra["infrastructure.py<br/>workspace config + recipe catalog + filesystem"]
  Domain["domain.py<br/>reports + DTOs"]

  PackageAPI --> Commands
  PackageAPI --> Queries
  CLI --> Commands
  CLI --> Queries
  CLI --> Html
  Html --> Domain
  Commands --> Generation
  Queries --> Catalog
  Queries --> Drift
  Queries --> Bench
  Generation --> Catalog
  Generation --> Infra
  Drift --> Catalog
  Drift --> Infra
  Bench --> Catalog
  Bench --> Drift
  Bench --> Infra
  Catalog --> Infra
  Catalog --> Domain
  Generation --> Domain
  Drift --> Domain
  Bench --> Domain
  Infra --> Domain
```

### Facade Diagram

```mermaid
flowchart TB
  Public["recipe/__init__.py"]
  PublicTypes["exported domain types"]
  PublicQueries["query facade<br/>list_recipes<br/>show_recipe<br/>check_recipes<br/>check_recipe_drifts<br/>bench_preview<br/>bench_all_preview"]
  PublicCommands["command facade<br/>describe_recipe_generation<br/>generate_recipe"]
  Domain["domain.py"]
  Queries["application/queries.py"]
  Commands["application/commands.py"]

  Public --> PublicTypes
  Public --> PublicQueries
  Public --> PublicCommands
  PublicTypes --> Domain
  PublicQueries --> Queries
  PublicCommands --> Commands
```

### Class Diagram

```mermaid
classDiagram
  class RecipeCommandContext {
    +Location project_root
    +Location recipe_root
  }

  class RecipeCheckViolation {
    +str code
    +str message
    +str recipe_name
  }

  class RecipeCheckReport {
    +Location project_root
    +Location recipe_root
    +int recipes_discovered
    +int recipes_checked
    +int rendered_paths_checked
    +tuple violations
    +passed() bool
  }

  class RecipePreviewStatus {
    <<enumeration>>
    CREATE
    SKIP_EXISTS
    SKIP_CONFIG
  }

  class RecipePreviewFile {
    +Location source_path
    +Location target_path
    +Location relative_path
    +RecipePreviewStatus status
    +str content
  }

  class RecipeDrift {
    +str module_name
    +str role_name
    +str ladder_family
    +str ladder_rung
    +tuple missing_files
    +tuple extra_files
    +has_drift() bool
  }

  class RecipeDriftReport {
    +Location project_root
    +Location recipe_root
    +Location subject_root
    +int modules_checked
    +tuple drifts
    +tuple violations
    +passed() bool
    +has_drifts() bool
  }

  class RecipeBenchModule {
    +str module_name
    +tuple actual_files
    +tuple expected_files
    +tuple residue_files
    +tuple slot_growth_files
    +tuple content_weights
    +tuple missing_files
    +tuple file_contents
    +has_residue() bool
    +has_warp() bool
  }

  class RecipeBenchReport {
    +Location project_root
    +Location recipe_root
    +Location subject_root
    +str selected_module
    +str role_name
    +str classification
    +tuple same_role_modules
    +tuple recurrence
    +tuple slot_growth_recurrence
    +tuple content_weight_recurrence
    +RecipeBenchModule selected
    +passed() bool
  }

  class RecipeBenchAllReport {
    +Location project_root
    +Location recipe_root
    +Location subject_root
    +str classification
    +tuple reports
    +tuple violations
    +passed() bool
  }

  class WorkspaceRelations {
    +Location project_root
    +Location recipe_root
    +Location subject_root
    +Mapping role_map
    +tuple skip_patterns
    +tuple subject_selectors
  }

  class RecipePolicy {
    +should_skip(location) bool
    +role_for(subject_name) str
    +subject_names() tuple
  }

  class RecipeWorkspace {
    +project_root() Location
    +recipe_root() Location
    +subject_root() Location
    +workspace_relations() WorkspaceRelations
    +recipe_policy() RecipePolicy
    +load_recipes() tuple
    +load_recipe(name) Scaffold
    +render_recipe(recipe, target_path, variables) tuple
    +write_files(files, create_paths) None
    +actual_files(subject_path) set
  }

  class RecipeCatalog {
    +list_recipes() tuple
    +show_recipe(name) RecipeSummary
    +recipe_for_role(role) Scaffold
    +validate_catalog() tuple
    +validate_roles_map() tuple
    +sample_variables(recipe) dict
  }

  class RecipeGenerationService {
    +describe(recipe_name, target_path, variables) RecipeGenerationReport
    +generate(recipe_name, target_path, variables) GenerateRecipeResult
    +check(recipe_name, target_path, variables) RecipeCheckReport
  }

  class RecipeDriftService {
    +build_report() RecipeDriftReport
    +expected_files(recipe, target_path) set
    +actual_files(subject_path) set
    +drift_files(expected, actual) tuple
  }

  class RecipeBenchService {
    +build_module_report(module_name) RecipeBenchReport
    +build_workspace_report() RecipeBenchAllReport
    +recurrence(modules, signal) tuple
    +classify(selected, modules) str
  }

  class RecipeBenchHtmlPresenter {
    +render_module(report) str
    +render_workspace(report) str
  }

  RecipeCheckReport o-- RecipeCheckViolation
  RecipeDriftReport o-- RecipeDrift
  RecipeDriftReport o-- RecipeCheckViolation
  RecipeBenchReport o-- RecipeBenchModule
  RecipeBenchReport o-- RecipeCheckViolation
  RecipeBenchAllReport o-- RecipeBenchReport
  RecipeBenchAllReport o-- RecipeCheckViolation
  RecipePreviewFile --> RecipePreviewStatus
  RecipePolicy --> WorkspaceRelations

  RecipeWorkspace --> WorkspaceRelations
  RecipeWorkspace --> RecipePolicy
  RecipeCatalog --> RecipeWorkspace
  RecipeCatalog --> RecipeCheckViolation
  RecipeGenerationService --> RecipeCatalog
  RecipeGenerationService --> RecipeWorkspace
  RecipeGenerationService --> RecipeCheckReport
  RecipeGenerationService --> RecipePreviewFile
  RecipeDriftService --> RecipeCatalog
  RecipeDriftService --> RecipeWorkspace
  RecipeDriftService --> RecipeDriftReport
  RecipeBenchService --> RecipeCatalog
  RecipeBenchService --> RecipeDriftService
  RecipeBenchService --> RecipeWorkspace
  RecipeBenchService --> RecipeBenchReport
  RecipeBenchService --> RecipeBenchAllReport
  RecipeBenchHtmlPresenter --> RecipeBenchReport
  RecipeBenchHtmlPresenter --> RecipeBenchAllReport
```

### Check Sequence

```mermaid
sequenceDiagram
  participant CLI as ui/cli.py
  participant Queries as application/queries.py
  participant Generation as application/generation.py
  participant Catalog as application/catalog.py
  participant Infra as infrastructure.py

  CLI->>Queries: check_recipes(recipe_name, target_path, variables)
  Queries->>Generation: check(...)
  Generation->>Catalog: validate_catalog()
  Catalog->>Infra: load_recipes()
  Generation->>Catalog: validate_roles_map()
  Generation->>Infra: render_recipe(...)
  Generation-->>Queries: RecipeCheckReport
  Queries-->>CLI: RecipeCheckReport
```

### Drift Sequence

```mermaid
sequenceDiagram
  participant CLI as ui/cli.py
  participant Queries as application/queries.py
  participant Drift as application/drift.py
  participant Catalog as application/catalog.py
  participant Infra as infrastructure.py

  CLI->>Queries: check_recipe_drifts()
  Queries->>Drift: build_report()
  Drift->>Catalog: validate_catalog()
  Drift->>Catalog: recipe_for_role(role_name)
  Drift->>Infra: subject_root()
  Drift->>Infra: actual_files(subject_path)
  Drift->>Infra: render_recipe(role_recipe, target_path, variables)
  Drift-->>Queries: RecipeDriftReport
  Queries-->>CLI: RecipeDriftReport
```

### Generate Sequence

```mermaid
sequenceDiagram
  participant API as recipe/__init__.py
  participant Commands as application/commands.py
  participant Generation as application/generation.py
  participant Catalog as application/catalog.py
  participant Infra as infrastructure.py

  API->>Commands: generate_recipe(recipe_name, target_path, variables)
  Commands->>Generation: generate(...)
  Generation->>Infra: load_recipe(name)
  Generation->>Catalog: sample_variables(recipe)
  Generation->>Infra: render_recipe(...)
  Generation->>Generation: plan create and skipped paths
  Generation->>Infra: write_files(rendered_files, create_paths)
  Generation-->>Commands: GenerateRecipeResult
  Commands-->>API: GenerateRecipeResult
```

### Bench Sequence

```mermaid
sequenceDiagram
  participant CLI as ui/cli.py
  participant Queries as application/queries.py
  participant Bench as application/bench.py
  participant Drift as application/drift.py
  participant Catalog as application/catalog.py
  participant Infra as infrastructure.py

  CLI->>Queries: bench_preview(module_name)
  Queries->>Bench: build_module_report(module_name)
  Bench->>Catalog: recipe_for_role(role_name)
  Bench->>Infra: subject_root()
  Bench->>Drift: expected and actual file comparison
  Bench->>Bench: recurrence and content-weight analysis
  Bench->>Bench: classify report
  Bench-->>Queries: RecipeBenchReport
  Queries-->>CLI: RecipeBenchReport
```

### Bench HTML Sequence

```mermaid
sequenceDiagram
  participant CLI as ui/cli.py
  participant Queries as application/queries.py
  participant Bench as application/bench.py
  participant Html as ui/bench_html.py

  CLI->>Queries: bench_preview(module_name)
  Queries->>Bench: build_module_report(module_name)
  Bench-->>Queries: RecipeBenchReport
  Queries-->>CLI: RecipeBenchReport
  CLI->>Html: render_module(report)
  Html-->>CLI: html
```
