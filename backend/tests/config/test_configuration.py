import pytest

from backend.config import (
    ConfigField,
    Configuration,
    ConfigurationError,
    ConfigurationSchema,
    EnvironmentSource,
    MappingSource,
    SecretValue,
)


def test_configuration_is_typed_and_precedence_is_deterministic() -> None:
    schema = ConfigurationSchema((ConfigField("port", int, required=True),))
    lower = MappingSource("file", {"port": "8000"}, priority=10)
    higher = MappingSource("environment", {"port": "9000"}, priority=20)
    config = Configuration.resolve(schema, (higher, lower))
    assert config.get("port", int) == 9000


def test_missing_required_configuration_fails_safely() -> None:
    schema = ConfigurationSchema((ConfigField("required", str, required=True),))
    with pytest.raises(ConfigurationError, match="required"):
        Configuration.resolve(schema, ())


def test_invalid_configuration_does_not_echo_value() -> None:
    schema = ConfigurationSchema((ConfigField("port", int, required=True),))
    with pytest.raises(ConfigurationError) as error:
        Configuration.resolve(schema, (MappingSource("test", {"port": "private-value"}, 1),))
    assert "private-value" not in str(error.value)


def test_environment_source_reads_only_approved_keys(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("APP_ALLOWED", "yes")
    monkeypatch.setenv("APP_UNRELATED_SECRET", "do-not-read")
    source = EnvironmentSource({"allowed": "APP_ALLOWED"})
    assert source.load() == {"allowed": "yes"}


def test_secret_is_masked_and_excluded_from_snapshot() -> None:
    schema = ConfigurationSchema((ConfigField("credential", str, required=True, secret=True),))
    config = Configuration.resolve(schema, (MappingSource("test", {"credential": "top-secret"}, 1),))
    value = config.get("credential", SecretValue)
    assert value.reveal() == "top-secret"
    assert "top-secret" not in repr(value)
    assert "credential" not in config.snapshot()

