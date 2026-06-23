from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path, PureWindowsPath

from .errors import ScaffoldError


@dataclass(frozen=True)
class _RelativePath:
    value: Path

    def __post_init__(self) -> None:
        object.__setattr__(self, "value", _relative_path_value(self.value))

    def as_posix(self) -> str:
        return self.value.as_posix()

    def resolve_from(self, source_root: Path) -> Path:
        return Path(source_root) / self.value


def _normalize_relative_path(value: Path | str, label: str) -> Path:
    normalized_text = str(value).strip().replace("\\", "/")
    normalized_value = Path(normalized_text)
    if normalized_value.is_absolute() or PureWindowsPath(normalized_text).is_absolute():
        raise ScaffoldError(f"{label} must be relative")
    if not normalized_value.parts:
        raise ScaffoldError(f"{label} must not be empty")
    if any(part in {".", ".."} for part in normalized_value.parts):
        raise ScaffoldError(f"{label} must not traverse outside the target root")
    return normalized_value


def _relative_path(value: Path | str, label: str = "Scaffold paths") -> _RelativePath:
    return _RelativePath(_normalize_relative_path(value, label))


def _relative_path_value(value: Path | str, label: str = "Scaffold paths") -> Path:
    return _normalize_relative_path(value, label)


def _relative_path_text(value: Path | str, label: str = "Scaffold paths") -> str:
    return _relative_path_value(value, label).as_posix()
