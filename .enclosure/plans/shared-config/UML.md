# Shared Config UML

Status: Draft

This diagram describes the intended `enclosure.shared.config` package outcome for the shared config plan. It uses Mermaid so it can live in Markdown preview.

Mermaid namespace labels in this document are diagram groupings. They mirror package areas but are not import paths or module names.

## Source Of Truth

This UML document is the source of truth for implementation. The package layout, class names, relationships, public seam, step boundary, and independence rules shown here must be strictly followed.

If another plan document conflicts with this UML, stop and update the documents before coding.

## Independence Boundary

Step 01 completes everything inside `enclosure.shared.config` without importing existing enclosure feature modules, bounded-context config modules, or other shared modules/packages. Step 02 then integrates existing callers with the finished package.

## File Layout

- `__init__.py`: exports `settings`
- `facade.py`: `SettingsFacade`
- `query.py`: `ManifestQuery`
- `base.py`: `StrictConfigModel`
- `errors.py`: `ConfigError`
- `metadata.py`: `ConfigMetadata`
- `loader.py`: `ManifestLoader`
- `loaded_manifest.py`: `LoadedManifest`
- `root.py`: `EnclosureSettings`
- `architecture/__init__.py`
- `architecture/root.py`: `ArchitectureConfig`
- `architecture/boundaries.py`: `BoundariesConfig`
- `architecture/tag.py`: `ConfigTagRule`
- `architecture/boundary_rule.py`: `BoundaryRule`
- `architecture/flow.py`: `FlowRuleSet`, `FlowRealmRule`
- `architecture/clusters.py`: `ClustersConfig`
- `architecture/health.py`: `HealthConfig`
- `architecture/map.py`: `MapConfig`
- `architecture/pressure.py`: `PressureConfig`
- `architecture/shape.py`: `ShapeConfig`
- `workspace/__init__.py`
- `workspace/root.py`: `WorkspaceConfig`
- `workspace/guidance.py`: `GuidanceConfig`
- `workspace/recipe.py`: `RecipeConfig`
- `workspace/rules.py`: `RulesConfig`, `LocalRulesConfig`
- `workspace/sync.py`: `SyncConfig`
- `pattern/__init__.py`
- `pattern/fit.py`: `PatternFitConfig`
- `health/__init__.py`

## Class Diagram

```mermaid
classDiagram
direction LR

namespace enclosure_shared_config {
  class settings {
    <<singleton facade>>
  }

  class SettingsFacade {
    <<public>>
    -ManifestLoader loader
    +ManifestQuery manifest
    +ConfigMetadata metadata
    +load() EnclosureSettings
  }

  class ConfigError {
    <<public error>>
  }

  class StrictConfigModel {
    <<pydantic base>>
    +ConfigDict model_config
  }

  class ConfigMetadata {
    <<value object>>
    +Path project_root
    +Path config_path
    +str config_format
  }

  class ManifestQuery {
    <<dot notation only>>
    -object value
    +__getattr__(name) object
    -wrap(value) object
  }

  class ManifestLoader {
    <<private service>>
    +load() LoadedManifest
    -find_config_path() Path
    -load_yaml_mapping(path) dict
  }

  class LoadedManifest {
    <<value object>>
    +ConfigMetadata metadata
    +dict raw_data
  }

  class EnclosureSettings {
    <<root pydantic model>>
    +ArchitectureConfig architecture
    +WorkspaceConfig workspace
  }
}

namespace enclosure_shared_config_architecture {
  class ArchitectureConfig {
    <<architecture/root.py>>
    +str language
    +str root
    +list_str exclusions
    +BoundariesConfig boundaries
    +ClustersConfig clusters
    +HealthConfig health
    +MapConfig map
    +PressureConfig pressure
    +ShapeConfig shape
    +str architecture_root
    +BoundariesConfig rules
  }

  class BoundariesConfig {
    <<architecture/boundaries.py>>
    +list_ConfigTagRule tags
    +list_BoundaryRule rules
    +FlowRuleSet flow
    +list_BoundaryRule boundaries
  }

  class ConfigTagRule {
    <<architecture/tag.py>>
    +str name
    +str match
    +list_str except_
    +list_str exclude
    +tuple_str excluded_patterns
  }

  class BoundaryRule {
    <<architecture/boundary_rule.py>>
    +str source
    +list_str disallow
    +list_str allow
    +bool allow_same_match
  }

  class FlowRuleSet {
    <<architecture/flow.py>>
    +list_str layers
    +str module_tag
    +list_str module_tags
    +list_FlowRealmRule realms
    +list_str analyzers
  }

  class FlowRealmRule {
    <<architecture/flow.py>>
    +str name
    +str module_tag
    +list_str_or_none layers
  }

  class ClustersConfig {
    <<architecture/clusters.py>>
    +int group_depth
    +int top
    +int files_top
  }

  class HealthConfig {
    <<architecture/health.py>>
    +int top
  }

  class MapConfig {
    <<architecture/map.py>>
    +int top
  }

  class PressureConfig {
    <<architecture/pressure.py>>
    +int top
  }

  class ShapeConfig {
    <<architecture/shape.py>>
    +int max_classes_per_file
    +int max_interfaces_per_file
    +int max_types_per_file
    +int max_abstract_classes_per_file
    +int max_functions_per_file
    +int max_methods_per_class
    +int max_declared_args_per_function
    +int max_declared_args_per_method
    +int max_lines_count_per_function
    +int max_lines_count_per_method
    +int max_lines_count_per_class
    +bool allow_optional_function_args
    +bool allow_optional_method_args
    +bool allow_optional_class_properties
    +bool allow_imports_aliases
    +bool enforce_joined_imports
    +list_ImportCrossingType allowed_imports_crossing_types
    +to_modwire_config() ModwireShapeConfig
  }
}

namespace enclosure_shared_config_workspace {
  class WorkspaceConfig {
    <<workspace/root.py>>
    +GuidanceConfig guidance
    +RecipeConfig recipe
    +RulesConfig rules
    +SyncConfig sync
  }

  class GuidanceConfig {
    <<workspace/guidance.py>>
    +int max_template_chars
  }

  class RecipeConfig {
    <<workspace/recipe.py>>
    +tuple_str skip
    +dict_str_str roles_map
    +tuple_str skip_globs
    +should_skip(relative_path) bool
  }

  class RulesConfig {
    <<workspace/rules.py>>
    +LocalRulesConfig local
  }

  class LocalRulesConfig {
    <<workspace/rules.py>>
    +int max_content_chars
  }

  class SyncConfig {
    <<workspace/sync.py>>
  }
}

namespace enclosure_shared_config_pattern {
  class PatternFitConfig {
    <<pattern/fit.py>>
    +tuple_str skip
  }
}

namespace integration_callers {
  class ArchitectureCallers
  class WorkspaceCallers
  class PatternCallers
  class HealthCallers
  class SharedHelpers
  class CliCommands
  class OldArchitectureConfig {
    <<delete>>
  }
  class OldWorkspaceConfig {
    <<delete>>
  }
  class OldRulesConfig {
    <<delete>>
  }
  class OldRecipeConfig {
    <<delete>>
  }
  class OldSyncConfig {
    <<delete>>
  }
  class OldPatternConfig {
    <<delete duplicate>>
  }
}

settings --> SettingsFacade : instance of
SettingsFacade *-- ManifestLoader : loads through
SettingsFacade *-- ConfigMetadata : exposes
SettingsFacade *-- EnclosureSettings : validates whole graph
SettingsFacade --> ManifestQuery : exposes as manifest

ManifestLoader --> LoadedManifest : returns
LoadedManifest *-- ConfigMetadata
ManifestLoader ..> ConfigError : raises on IO/YAML/shape failures
EnclosureSettings ..> ConfigError : validation failures wrapped loudly
ManifestQuery ..> AttributeError : missing attributes

StrictConfigModel <|-- EnclosureSettings
StrictConfigModel <|-- ArchitectureConfig
StrictConfigModel <|-- BoundariesConfig
StrictConfigModel <|-- ConfigTagRule
StrictConfigModel <|-- BoundaryRule
StrictConfigModel <|-- FlowRuleSet
StrictConfigModel <|-- FlowRealmRule
StrictConfigModel <|-- ClustersConfig
StrictConfigModel <|-- HealthConfig
StrictConfigModel <|-- MapConfig
StrictConfigModel <|-- PressureConfig
StrictConfigModel <|-- ShapeConfig
StrictConfigModel <|-- WorkspaceConfig
StrictConfigModel <|-- GuidanceConfig
StrictConfigModel <|-- RecipeConfig
StrictConfigModel <|-- RulesConfig
StrictConfigModel <|-- LocalRulesConfig
StrictConfigModel <|-- SyncConfig
StrictConfigModel <|-- PatternFitConfig

EnclosureSettings *-- ArchitectureConfig
EnclosureSettings *-- WorkspaceConfig

ArchitectureConfig *-- BoundariesConfig
ArchitectureConfig *-- ClustersConfig
ArchitectureConfig *-- HealthConfig
ArchitectureConfig *-- MapConfig
ArchitectureConfig *-- PressureConfig
ArchitectureConfig *-- ShapeConfig

BoundariesConfig *-- "0..*" ConfigTagRule
BoundariesConfig *-- "0..*" BoundaryRule
BoundariesConfig *-- FlowRuleSet
FlowRuleSet *-- "0..*" FlowRealmRule

WorkspaceConfig *-- GuidanceConfig
WorkspaceConfig *-- RecipeConfig
WorkspaceConfig *-- RulesConfig
WorkspaceConfig *-- SyncConfig
RulesConfig *-- LocalRulesConfig

OldArchitectureConfig ..> ArchitectureConfig : replaced by Step 01 class
OldWorkspaceConfig ..> WorkspaceConfig : replaced by Step 01 class
OldRulesConfig ..> RulesConfig : replaced by Step 01 class
OldRecipeConfig ..> RecipeConfig : replaced by Step 01 class
OldSyncConfig ..> SyncConfig : replaced by Step 01 class
OldPatternConfig ..> RecipeConfig : duplicate collapsed

ArchitectureCallers --> settings : Step 02 import settings
WorkspaceCallers --> settings
PatternCallers --> settings
HealthCallers --> settings
SharedHelpers --> settings
CliCommands --> settings

note for SettingsFacade "Step 01: complete standalone package.\nNo imports from existing features, old config modules, or other shared modules/packages."
note for ManifestQuery "Dot notation only.\nNo item access public API.\nNo get/default fallback API."
note for EnclosureSettings "Whole manifest graph validates at once.\nNo section-by-section bounded-context loaders."
note for ArchitectureCallers "Step 02 only: existing callers integrate with the completed package."
```

## Runtime Flow

```mermaid
sequenceDiagram
autonumber
actor Caller
participant Settings as settings: SettingsFacade
participant Loader as ManifestLoader
participant YAML as YAML parser
participant RootModel as EnclosureSettings
participant Query as ManifestQuery

Caller->>Settings: settings.manifest.architecture.root
Settings->>Loader: load()
Loader->>Loader: discover .enclosure/enclosure.yaml or .yml independently
Loader->>YAML: parse config file

alt unreadable file, invalid YAML, or non-mapping top level
  Loader-->>Settings: raise ConfigError
  Settings-->>Caller: fail loud
else raw mapping loaded
  Loader-->>Settings: LoadedManifest(metadata, raw_data)
  Settings->>RootModel: model_validate(raw_data)
  alt pydantic validation error
    RootModel-->>Settings: validation error
    Settings-->>Caller: raise ConfigError
  else valid whole graph
    RootModel-->>Settings: EnclosureSettings
    Settings->>Query: wrap(validated root model)
    Query-->>Settings: ManifestQuery
    Settings-->>Caller: architecture.root value
  end
end
```

## Design Checks

- Mermaid namespace labels are diagram groupings, not Python import paths.
- This UML is the implementation source of truth.
- Step 01 completes `shared.config` independently.
- Step 01 imports no existing enclosure feature modules, bounded-context config modules, or other shared modules/packages.
- Step 02 integrates existing callers with the completed package.
- The only public object is `settings`.
- The root model validates the complete manifest graph.
- All config pydantic classes live in `shared.config`.
- Config classes are grouped under topic subpackages.
- Module names omit redundant `config` suffixes inside `shared.config`.
- Dot-notation traversal is the only query API.
- Old bounded-context config modules are deleted after Step 01 replacements exist, with no compatibility bridges.
