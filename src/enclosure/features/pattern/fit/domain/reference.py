from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PatternFitConfig:
    skip: tuple[str, ...] = ()

    @classmethod
    def from_config(cls, value: object) -> PatternFitConfig:
        return cls(skip=tuple(getattr(value, "skip", ())))


__all__ = ["PatternFitConfig"]
