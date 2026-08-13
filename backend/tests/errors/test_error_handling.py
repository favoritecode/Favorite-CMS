from backend.engines.errors import (
    ApplicationFailure,
    ErrorCategory,
    ErrorHandlingEngine,
    InfrastructureFailure,
    ValidationFailure,
)


def test_validation_failure_is_normalized_as_controlled_error() -> None:
    record = ErrorHandlingEngine().normalize(
        ValidationFailure("Input is invalid"), source="core.validation"
    )
    assert record.category is ErrorCategory.VALIDATION
    assert record.public().message == "Input is invalid"


def test_expected_application_and_infrastructure_failures_remain_distinct() -> None:
    handler = ErrorHandlingEngine()
    application = handler.normalize(ApplicationFailure("Operation unavailable"), source="core")
    infrastructure = handler.normalize(InfrastructureFailure("Dependency unavailable"), source="core")
    assert application.category is ErrorCategory.APPLICATION
    assert infrastructure.category is ErrorCategory.INFRASTRUCTURE


def test_unexpected_error_has_safe_public_output() -> None:
    record = ErrorHandlingEngine().normalize(
        RuntimeError("token=secret at C:\\private\\service.py"), source="core.kernel"
    )
    public = record.public()
    assert public.category is ErrorCategory.INTERNAL
    assert public.message == "An internal error occurred"
    assert "secret" not in repr(public)
    assert "private" not in repr(public)


def test_sensitive_controlled_message_is_replaced() -> None:
    record = ErrorHandlingEngine().normalize(
        ApplicationFailure("database_url contains password"), source="core"
    )
    assert record.public().message == "The operation could not be completed"


def test_error_context_is_minimized() -> None:
    record = ErrorHandlingEngine().normalize(
        ValidationFailure("Invalid"),
        source="core",
        context={"request_id": "r1", "password": "secret", "payload": {"private": True}},
    )
    assert record.context == {"request_id": "r1"}

