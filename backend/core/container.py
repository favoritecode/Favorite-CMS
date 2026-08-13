"""Small explicit service registry for public shared contracts."""

from __future__ import annotations

from typing import TypeVar, cast

from backend.core.exceptions import DuplicateServiceError, MissingServiceError

T = TypeVar("T")


class ServiceContainer:
    def __init__(self) -> None:
        self._services: dict[str, object] = {}

    def register(self, key: str, service: object) -> None:
        if not key or not key.strip():
            raise ValueError("Service key must not be empty")
        if key in self._services:
            raise DuplicateServiceError(f"Service is already registered: {key}")
        self._services[key] = service

    def resolve(self, key: str, expected_type: type[T] | None = None) -> T:
        try:
            service = self._services[key]
        except KeyError as exc:
            raise MissingServiceError(f"Required service is not registered: {key}") from exc
        if expected_type is not None and not isinstance(service, expected_type):
            raise MissingServiceError(f"Registered service does not satisfy contract: {key}")
        return cast(T, service)

    def contains(self, key: str) -> bool:
        return key in self._services

