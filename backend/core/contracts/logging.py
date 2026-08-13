from __future__ import annotations

from typing import Mapping, Protocol


class Logger(Protocol):
    def info(self, message: str, *, context: Mapping[str, object] | None = None) -> object: ...
    def error(self, message: str, *, context: Mapping[str, object] | None = None) -> object: ...


class LogOutput(Protocol):
    def emit(self, record: object) -> None: ...

