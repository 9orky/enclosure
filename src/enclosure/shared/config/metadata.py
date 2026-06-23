from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ConfigMetadata:
    project_root: Path

    @property
    def target_dir(self) -> Path:
        return self.project_root / ".enclosure"

    @property
    def canonical_config_path(self) -> Path:
        return self.target_dir / "enclosure.yaml"

    @property
    def recipes_dir(self) -> Path:
        return self.target_dir / "recipes"

    @property
    def plans_dir(self) -> Path:
        return self.target_dir / "plans"

    @property
    def cache_dir(self) -> Path:
        return self.target_dir / ".cache"

    @property
    def dev_dir(self) -> Path:
        return self.project_root / ".dev"

    @property
    def rules_dir(self) -> Path:
        return self.target_dir / "rules"

    @property
    def local_rules_dir(self) -> Path:
        return self.rules_dir / "local"

    @property
    def bootstrap_instruction_path(self) -> Path:
        return self.project_root / ".github" / "copilot-instructions.md"

    @property
    def agent_instruction_path(self) -> Path:
        return self.project_root / "AGENTS.md"


__all__ = ["ConfigMetadata"]
