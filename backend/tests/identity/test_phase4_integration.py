from backend.bootstrap import build_kernel
from backend.config import Configuration, SecretValue
from backend.core import Kernel
from backend.core.exceptions import EngineLifecycleError
from backend.engines.authentication import AuthenticationEngine
from backend.engines.logging import LogCategory, LogSource, LogSourceKind, LoggingEngine
from backend.engines.permissions import PermissionEngine
from backend.engines.users import UserEngine
import pytest


def test_phase4_engines_share_core_lifecycle(identity_kernel: Kernel) -> None:
    users = identity_kernel.container.resolve("engine.users", UserEngine)
    authentication = identity_kernel.container.resolve("engine.authentication", AuthenticationEngine)
    permissions = identity_kernel.container.resolve("engine.permissions", PermissionEngine)
    assert users.ready and authentication.ready and permissions.ready
    identity_kernel.shutdown()
    assert not users.ready and not authentication.ready and not permissions.ready


def test_security_sensitive_logging_is_redacted() -> None:
    logging = LoggingEngine()
    record = logging.info(
        "access token abc password value",
        source=LogSource(LogSourceKind.ENGINE, "authentication"),
        category=LogCategory.ENGINE,
        context={"token": "raw", "operation_id": "login-1"},
    )
    assert record is not None
    assert record.message == "Sensitive operational message redacted"
    assert "raw" not in repr(record.context)


def test_authentication_secret_is_excluded_from_configuration_diagnostics(
    identity_kernel: Kernel,
) -> None:
    configuration = identity_kernel.container.resolve("core.configuration", Configuration)
    secret = configuration.get("authentication.jwt_secret", SecretValue)
    assert str(secret) == "[REDACTED]"
    assert "authentication.jwt_secret" not in configuration.snapshot()


def test_default_development_bootstrap_remains_operational() -> None:
    kernel = build_kernel()
    kernel.bootstrap()
    assert kernel.container.resolve("engine.authentication", AuthenticationEngine).ready
    kernel.shutdown()


def test_production_requires_explicit_authentication_secret(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("FAVORITE_ENV", "production")
    monkeypatch.delenv("FAVORITE_AUTH_JWT_SECRET", raising=False)
    kernel = build_kernel()
    with pytest.raises(EngineLifecycleError, match="authentication"):
        kernel.bootstrap()
