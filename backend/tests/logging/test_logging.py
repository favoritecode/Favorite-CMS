from backend.engines.logging import (
    LogCategory,
    LogLevel,
    LogSource,
    LogSourceKind,
    LoggingEngine,
    MemoryLogOutput,
)


SOURCE = LogSource(LogSourceKind.CORE, "core.test")


def test_creates_structured_log_with_level_and_context() -> None:
    output = MemoryLogOutput()
    logger = LoggingEngine(outputs=(output,), minimum_level=LogLevel.DEBUG)
    record = logger.info(
        "Started",
        source=SOURCE,
        category=LogCategory.CORE,
        context={"request_id": "request-1", "arbitrary": "discarded"},
    )
    assert record is not None
    assert record.level is LogLevel.INFO
    assert record.context == {"request_id": "request-1"}
    assert output.records == [record]


def test_level_filter_drops_lower_severity_records() -> None:
    output = MemoryLogOutput()
    logger = LoggingEngine(outputs=(output,), minimum_level=LogLevel.WARNING)
    assert logger.info("ignored", source=SOURCE, category=LogCategory.CORE) is None
    assert output.records == []


def test_sensitive_message_and_context_are_not_logged() -> None:
    output = MemoryLogOutput()
    logger = LoggingEngine(outputs=(output,))
    record = logger.error(
        "password=visible-secret",
        source=SOURCE,
        category=LogCategory.SYSTEM,
        context={"request_id": "safe", "access_token": "visible-secret"},
    )
    assert record is not None
    assert "visible-secret" not in record.message
    assert "visible-secret" not in repr(record.context)


def test_exception_logging_never_serializes_exception_message() -> None:
    logger = LoggingEngine()
    record = logger.exception(
        RuntimeError("database_url=private"), source=SOURCE, category=LogCategory.SYSTEM
    )
    assert record is not None
    assert "private" not in record.message
    assert record.context["exception_type"] == "RuntimeError"


def test_output_failure_is_isolated() -> None:
    class BrokenOutput:
        def emit(self, record: object) -> None:
            raise RuntimeError("unavailable")

    record = LoggingEngine(outputs=(BrokenOutput(),)).info(
        "continues", source=SOURCE, category=LogCategory.CORE
    )
    assert record is not None

