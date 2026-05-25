from __future__ import annotations

from pathlib import Path


class EnclosureProjectLayout:
    enclosure_dir_names = (".enclosure",)
    config_file_stem = "enclosure"
    config_extensions = (".yaml", ".yml")
    bootstrap_instructions_dir_name = ".github"
    bootstrap_instructions_file_name = "copilot-instructions.md"
    agent_instructions_file_name = "AGENTS.md"

    def discover_project_root(self, start: Path) -> Path:
        search_start = Path(start).expanduser().resolve()
        if not search_start.is_dir():
            search_start = search_start.parent
        if self.is_managed_target_dir(search_start):
            return search_start.parent

        for candidate in (search_start, *search_start.parents):
            if self.has_workspace_marker(candidate):
                return candidate
        return search_start

    def is_managed_target_dir(self, path: Path) -> bool:
        return path.name in self.enclosure_dir_names and any(
            (path / self.config_file_name(suffix)).is_file()
            for suffix in self.config_extensions
        )

    def has_workspace_marker(self, project_root: Path) -> bool:
        return any(
            (project_root / dir_name).is_dir()
            for dir_name in self.enclosure_dir_names
        )

    def target_dir_candidates(self, project_root: Path) -> tuple[Path, ...]:
        return tuple(project_root / dir_name for dir_name in self.enclosure_dir_names)

    def managed_target_dirs(self, project_root: Path) -> tuple[Path, ...]:
        existing_dirs = tuple(
            path for path in self.target_dir_candidates(project_root) if path.is_dir()
        )
        if len(existing_dirs) > 1:
            labels = ", ".join(path.name for path in existing_dirs)
            raise ValueError(
                f"Found multiple enclosure directories: {labels}. Delete one of them and rerun enclosure."
            )
        if existing_dirs:
            return existing_dirs
        return self.target_dir_candidates(project_root)

    def target_dir(self, project_root: Path) -> Path:
        return self.managed_target_dirs(project_root)[0]

    def recipes_dir(self, project_root: Path) -> Path:
        return self.target_dir(project_root) / "recipes"

    def cache_dir(self, project_root: Path) -> Path:
        return self.dev_dir(project_root) / "cache"

    def dev_dir(self, project_root: Path) -> Path:
        return Path(project_root) / ".dev"

    def rules_dir(self, project_root: Path) -> Path:
        return self.target_dir(project_root) / "rules"

    def local_rules_dir(self, project_root: Path) -> Path:
        return self.rules_dir(project_root) / "local"

    def config_path(self, project_root: Path, suffix: str | None) -> Path:
        return self.target_dir(project_root) / self.config_file_name(suffix)

    def config_file_name(self, suffix: str | None) -> str:
        active_suffix = suffix or self.config_extensions[0]
        return f"{self.config_file_stem}{active_suffix}"

    def config_candidate_paths(self, project_root: Path) -> tuple[Path, ...]:
        return tuple(
            target_dir / self.config_file_name(suffix)
            for target_dir in self.managed_target_dirs(project_root)
            for suffix in self.config_extensions
        )

    def find_config_path(self, roots: tuple[Path, ...]) -> Path | None:
        seen: set[Path] = set()
        for root in roots:
            for candidate in self.config_candidate_paths(root):
                config_path = candidate.resolve(strict=False)
                if config_path in seen:
                    continue
                seen.add(config_path)
                if config_path.is_file():
                    return config_path
        return None

    def config_candidate_labels(self) -> tuple[str, ...]:
        return tuple(
            f"{dir_name}/{self.config_file_name(suffix)}"
            for dir_name in self.enclosure_dir_names
            for suffix in self.config_extensions
        )

    def bootstrap_instruction_path(self, project_root: Path) -> Path:
        return (
            project_root
            / self.bootstrap_instructions_dir_name
            / self.bootstrap_instructions_file_name
        )

    def agent_instruction_path(self, project_root: Path) -> Path:
        return project_root / self.agent_instructions_file_name

    def recipe_root(self, project_root: Path) -> Path:
        target_root = project_root.resolve()

        for candidate in (target_root, *target_root.parents):
            recipes_dir = self.recipes_dir(candidate)
            if recipes_dir.is_dir():
                return recipes_dir

            config_path = self.config_path(candidate, None)
            if config_path.is_file():
                return config_path.parent / "recipes"

        return self.recipes_dir(target_root)


_CURRENT_LAYOUT = EnclosureProjectLayout()


def current_project_root() -> Path:
    return _CURRENT_LAYOUT.discover_project_root(Path.cwd())


def current_layout() -> EnclosureProjectLayout:
    return _CURRENT_LAYOUT


def current_recipes_root() -> Path:
    return _CURRENT_LAYOUT.recipe_root(current_project_root())


def current_config_mapping() -> tuple[Path, Path, dict[str, object]]:
    from enclosure.shared import config

    project_root = current_project_root()
    config_path = _CURRENT_LAYOUT.find_config_path((project_root,))
    if config_path is not None:
        return project_root, config_path, config.load_yaml_mapping(
            config_path,
            label="Config file",
            error_type=RuntimeError,
        )

    searched = ", ".join(_CURRENT_LAYOUT.config_candidate_labels())
    raise RuntimeError(f"Could not find a configuration file. Looked for {searched}.")


__all__ = [
    "EnclosureProjectLayout",
    "current_config_mapping",
    "current_layout",
    "current_project_root",
    "current_recipes_root",
]
