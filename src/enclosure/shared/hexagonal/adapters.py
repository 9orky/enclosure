from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from . import ports


@runtime_checkable
class Adapter(Protocol):
    def port(self) -> ports.Port:
        ...


@dataclass(frozen=True)
class AdapterBinding:
    adapter_name: str
    port_name: str
    module_path: str

    def binds(self, port: ports.Port) -> bool:
        return self.port_name == port.name()


__all__ = [
    "Adapter",
    "AdapterBinding",
]
