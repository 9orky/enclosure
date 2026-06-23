from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path, PureWindowsPath

from .errors import ScaffoldError


@dataclass(frozen=True)
class _ScaffoldRelativePath:
    value: Path

    def __post_init__(self) -> None:
        paths = _ScaffoldRelativePathNormalizer()
        object.__setattr__(self, "value", paths.normalize(self.value, "Scaffold paths"))

    def as_posix(self) -> str:
        return self.value.as_posix()

    def resolve_from(self, source_root: Path) -> Path:
        return Path(source_root) / self.value


class _ScaffoldRelativePathNormalizer:
    def normalize(self, value: Path | str, label: str) -> Path:
        text = self._text(value)
        path = Path(text)
        self._reject_absolute(path, text, label)
        self._reject_empty(path, label)
        self._reject_traversal(path, label)
        return path

    def relative_path(self, value: Path | str, label: str) -> _ScaffoldRelativePath:
        return _ScaffoldRelativePath(self.normalize(value, label))

    def text(self, value: Path | str, label: str) -> str:
        return self.normalize(value, label).as_posix()

    def target_path(self, target_root: Path, target_path: Path | str) -> Path:
        resolved_target_root = Path(target_root).resolve()
        raw_path = Path(target_path)
        if not raw_path.is_absolute():
            return self.normalize(raw_path, "Target path")
        try:
            relative_path = raw_path.resolve(strict=False).relative_to(resolved_target_root)
        except ValueError as exc:
            raise ScaffoldError("Target path must stay inside the target root") from exc
        return self.normalize(relative_path, "Target path")

    def _text(self, value: Path | str) -> str:
        return str(value).strip().replace("\\", "/")

    def _reject_absolute(self, value: Path, text: str, label: str) -> None:
        if value.is_absolute() or PureWindowsPath(text).is_absolute():
            raise ScaffoldError(f"{label} must be relative")

    def _reject_empty(self, value: Path, label: str) -> None:
        if not value.parts:
            raise ScaffoldError(f"{label} must not be empty")

    def _reject_traversal(self, value: Path, label: str) -> None:
        if any(part in {".", ".."} for part in value.parts):
            raise ScaffoldError(f"{label} must not traverse outside the target root")
