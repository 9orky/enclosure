from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class Port(Protocol):
    def name(self) -> str:
        ...


@runtime_checkable
class InboundPort(Port, Protocol):
    pass


@runtime_checkable
class OutboundPort(Port, Protocol):
    pass


__all__ = [
    "InboundPort",
    "OutboundPort",
    "Port",
]
