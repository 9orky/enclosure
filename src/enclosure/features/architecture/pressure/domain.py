from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from modwire import CodeMap
from pydantic import field_validator

from enclosure.shared import architecture, config, limits


class PressureConfig(config.StrictConfigModel):
    top: int

    @field_validator("top")
    @classmethod
    def top_is_limit(cls, value: int) -> int:
        return limits.validate_report_limit(value)


@dataclass(frozen=True)
class CallablePressure:
    callable_id: str
    qualified_name: str
    source_id: str
    line_start: int
    kind: str
    declared_args: int
    calls_count: int
    resolved_calls_count: int
    unresolved_calls_count: int
    called_by_count: int

    @property
    def location(self) -> str:
        return f"{self.source_id}.py:{self.line_start}"

    def to_json_dict(self) -> dict[str, object]:
        return {
            "callable_id": self.callable_id,
            "qualified_name": self.qualified_name,
            "source_id": self.source_id,
            "line_start": self.line_start,
            "location": self.location,
            "kind": self.kind,
            "declared_args": self.declared_args,
            "calls_count": self.calls_count,
            "resolved_calls_count": self.resolved_calls_count,
            "unresolved_calls_count": self.unresolved_calls_count,
            "called_by_count": self.called_by_count,
        }


@dataclass(frozen=True)
class ExportPressure:
    source_id: str
    exported_count: int
    reexported_count: int
    source_modules: tuple[str, ...]
    symbols: tuple[str, ...]

    @property
    def location(self) -> str:
        return f"{self.source_id}.py"

    def to_json_dict(self) -> dict[str, object]:
        return {
            "source_id": self.source_id,
            "location": self.location,
            "exported_count": self.exported_count,
            "reexported_count": self.reexported_count,
            "source_modules": list(self.source_modules),
            "symbols": list(self.symbols),
        }


@dataclass(frozen=True)
class ArchitecturePressureReport:
    project_root: Path
    config_path: Path
    config_format: str
    language: str
    runtime_command: str = ""
    files_found: int = 0
    files_excluded: int = 0
    files_checked: int = 0
    top: int = 10
    callable_count: int = 0
    call_count: int = 0
    resolved_call_count: int = 0
    unresolved_call_count: int = 0
    most_calling: tuple[CallablePressure, ...] = ()
    most_called: tuple[CallablePressure, ...] = ()
    wide_signatures: tuple[CallablePressure, ...] = ()
    reexport_hubs: tuple[ExportPressure, ...] = ()
    public_api_hubs: tuple[ExportPressure, ...] = ()

    def to_json_dict(self) -> dict[str, object]:
        return {
            **architecture.metadata_json(self),
            "top": self.top,
            "callable_count": self.callable_count,
            "call_count": self.call_count,
            "resolved_call_count": self.resolved_call_count,
            "unresolved_call_count": self.unresolved_call_count,
            "most_calling": [
                pressure.to_json_dict() for pressure in self.most_calling
            ],
            "most_called": [
                pressure.to_json_dict() for pressure in self.most_called
            ],
            "wide_signatures": [
                pressure.to_json_dict() for pressure in self.wide_signatures
            ],
            "reexport_hubs": [
                pressure.to_json_dict() for pressure in self.reexport_hubs
            ],
            "public_api_hubs": [
                pressure.to_json_dict() for pressure in self.public_api_hubs
            ],
        }


@dataclass(frozen=True)
class DescribedArchitecturePressure:
    callable_count: int
    call_count: int
    resolved_call_count: int
    unresolved_call_count: int
    most_calling: tuple[CallablePressure, ...]
    most_called: tuple[CallablePressure, ...]
    wide_signatures: tuple[CallablePressure, ...]
    reexport_hubs: tuple[ExportPressure, ...]
    public_api_hubs: tuple[ExportPressure, ...]


def describe_architecture_pressure(
    code_map: CodeMap,
    *,
    top: int,
) -> DescribedArchitecturePressure:
    checked_top = limits.validate_report_limit(top)
    callable_pressures = tuple(
        _callable_pressure(code_map, callable_id)
        for callable_id in code_map.callable_ids()
    )
    call_count = sum(
        len(source_file.calls)
        for source_file in code_map.extraction_result.files.values()
    )
    resolved_call_count = sum(
        1
        for source_file in code_map.extraction_result.files.values()
        for source_call in source_file.calls
        if source_call.resolution == "resolved"
    )
    export_pressures = tuple(_export_pressures(code_map))

    return DescribedArchitecturePressure(
        callable_count=len(callable_pressures),
        call_count=call_count,
        resolved_call_count=resolved_call_count,
        unresolved_call_count=call_count - resolved_call_count,
        most_calling=limits.apply_limit(
            sorted(
                callable_pressures,
                key=lambda pressure: (
                    -pressure.calls_count,
                    -pressure.resolved_calls_count,
                    -pressure.called_by_count,
                    pressure.callable_id,
                ),
            ),
            checked_top,
        ),
        most_called=limits.apply_limit(
            sorted(
                callable_pressures,
                key=lambda pressure: (
                    -pressure.called_by_count,
                    -pressure.calls_count,
                    -pressure.resolved_calls_count,
                    pressure.callable_id,
                ),
            ),
            checked_top,
        ),
        wide_signatures=limits.apply_limit(
            sorted(
                callable_pressures,
                key=lambda pressure: (
                    -pressure.declared_args,
                    -pressure.called_by_count,
                    -pressure.calls_count,
                    pressure.callable_id,
                ),
            ),
            checked_top,
        ),
        reexport_hubs=limits.apply_limit(
            (
                pressure
                for pressure in export_pressures
                if pressure.reexported_count > 1
            ),
            checked_top,
        ),
        public_api_hubs=limits.apply_limit(
            sorted(
                export_pressures,
                key=lambda pressure: (
                    -pressure.exported_count,
                    -pressure.reexported_count,
                    pressure.source_id,
                ),
            ),
            checked_top,
        ),
    )


def _callable_pressure(code_map: CodeMap, callable_id: str) -> CallablePressure:
    source_callable = code_map.callable(callable_id)
    calls = code_map.calls_from(callable_id)
    resolved_calls_count = sum(
        1 for source_call in calls if source_call.resolution == "resolved"
    )
    return CallablePressure(
        callable_id=source_callable.id,
        qualified_name=source_callable.qualified_name,
        source_id=source_callable.source_id,
        line_start=source_callable.line_start,
        kind=source_callable.kind,
        declared_args=source_callable.declared_args,
        calls_count=len(calls),
        resolved_calls_count=resolved_calls_count,
        unresolved_calls_count=len(calls) - resolved_calls_count,
        called_by_count=len(code_map.calls_to(callable_id)),
    )


def _export_pressures(code_map: CodeMap) -> tuple[ExportPressure, ...]:
    pressures = []
    for source_id, source_file in code_map.extraction_result.files.items():
        if not source_id.endswith("__init__"):
            continue
        exports = tuple(
            source_export
            for source_export in source_file.exports
            if source_export.name != source_id
        )
        if not exports:
            continue
        pressures.append(
            ExportPressure(
                source_id=source_id,
                exported_count=len(exports),
                reexported_count=sum(
                    1 for source_export in exports if source_export.is_reexport
                ),
                source_modules=tuple(
                    sorted(
                        {
                            source_export.normalized_path
                            for source_export in exports
                            if source_export.normalized_path
                        }
                    )
                ),
                symbols=tuple(sorted(source_export.name for source_export in exports)),
            )
        )
    return tuple(
        sorted(
            pressures,
            key=lambda pressure: (
                -pressure.reexported_count,
                -pressure.exported_count,
                pressure.source_id,
            ),
        )
    )


__all__ = [
    "ArchitecturePressureReport",
    "CallablePressure",
    "DescribedArchitecturePressure",
    "ExportPressure",
    "PressureConfig",
    "describe_architecture_pressure",
]
