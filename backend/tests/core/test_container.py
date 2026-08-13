import pytest

from backend.core.container import ServiceContainer
from backend.core.exceptions import DuplicateServiceError, MissingServiceError


def test_registers_and_resolves_explicit_service() -> None:
    container = ServiceContainer()
    service = object()
    container.register("public.example", service)
    assert container.resolve("public.example") is service


def test_rejects_duplicate_registration() -> None:
    container = ServiceContainer()
    container.register("public.example", object())
    with pytest.raises(DuplicateServiceError):
        container.register("public.example", object())


def test_missing_required_service_has_clear_error() -> None:
    with pytest.raises(MissingServiceError, match="not registered"):
        ServiceContainer().resolve("missing")

