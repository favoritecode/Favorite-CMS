from __future__ import annotations

import io
from pathlib import Path

import pytest

from backend.cli import _parser, main
from backend.config import Configuration, MappingSource
from backend.config.engine import BOOTSTRAP_SCHEMA
from backend.operations import DeploymentValidator, HealthStatus
from backend.operations.health import HealthReport
from tools.build_distribution import validate


def _environment(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("FAVORITE_ENV", "test")
    monkeypatch.setenv("FAVORITE_DATABASE_URL", f"sqlite+pysqlite:///{tmp_path / 'phase18.db'}")
    monkeypatch.setenv("FAVORITE_STORAGE_ROOT", str(tmp_path / "storage"))
    monkeypatch.setenv("FAVORITE_STORAGE_PROVIDER", "mounted")
    monkeypatch.setenv("FAVORITE_AUTH_JWT_SECRET", "phase-eighteen-signing-secret-at-least-thirty-two-bytes")
    monkeypatch.setenv("FAVORITE_ACTIVE_THEME", "favorite.theme.starter")


def test_operator_help_describes_explicit_commands_and_authorization(capsys) -> None:
    parser = _parser()
    help_text = parser.format_help()
    assert "migrate" in help_text and "install" in help_text and "status" in help_text
    with pytest.raises(SystemExit) as result:
        parser.parse_args(["install", "--help"])
    assert result.value.code == 0
    install_help = capsys.readouterr().out
    assert "--role" in install_help and "--authorization" in install_help and "--password-stdin" in install_help


def test_cli_status_is_uninstalled_and_never_prints_configuration_secrets(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys) -> None:
    _environment(tmp_path, monkeypatch)
    secret = "phase-eighteen-signing-secret-at-least-thirty-two-bytes"
    database_url = f"sqlite+pysqlite:///{tmp_path / 'phase18.db'}"
    assert main(["status"]) == 0
    output = capsys.readouterr()
    assert "Installation: uninstalled" in output.out
    assert secret not in output.out + output.err and database_url not in output.out + output.err


def test_cli_failure_has_stable_exit_code_and_redacted_output(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys) -> None:
    _environment(tmp_path, monkeypatch)
    monkeypatch.setattr("sys.stdin", io.StringIO("short\n"))
    result = main(["install", "--email", "operator@example.invalid", "--display-name", "Operator",
                   "--role", "operator", "--authorization",
                   "admin.diagnostics.view:application.admin.platform:view:admin_diagnostics", "--password-stdin"])
    output = capsys.readouterr()
    assert result == 1
    assert "failed safely" in output.err
    assert "short" not in output.out + output.err and "sqlite+pysqlite" not in output.out + output.err


def test_distribution_rejects_private_keys_and_populated_secret_environment(tmp_path: Path) -> None:
    package = tmp_path / "package"; package.mkdir()
    (package / "runtime.txt").write_text("safe", encoding="utf-8")
    validate(package)
    (package / "private.pem").write_text("-----BEGIN PRIVATE KEY-----\nredacted\n", encoding="utf-8")
    with pytest.raises(ValueError, match="Private key material"):
        validate(package)
    (package / "private.pem").unlink()
    (package / ".env.production.example").write_text("FAVORITE_AUTH_JWT_SECRET=not-empty\n", encoding="utf-8")
    with pytest.raises(ValueError, match="Populated secret configuration"):
        validate(package)


def test_production_validation_fails_closed_for_development_providers() -> None:
    config = Configuration.resolve(BOOTSTRAP_SCHEMA, (MappingSource("phase18", {
        "environment": "production", "debug": False, "database.url": "sqlite:///local.db",
        "storage.root": "storage/files", "storage.provider": "local",
        "authentication.jwt_secret": "configured-but-not-logged",
    }, 1),))
    class Database: provider = "sqlite"
    class Migrations:
        def pending(self): return ()
    class Storage:
        provider_name = "local"
        def healthcheck(self): return True
    class Health:
        def readiness(self): return HealthReport(True, True, HealthStatus.HEALTHY)
    report = DeploymentValidator(config, Database(), Migrations(), Storage(), Health()).validate_production()
    assert not report.valid
    assert "postgresql" in report.failures and "production_storage" in report.failures


def test_frontend_api_endpoint_is_server_only() -> None:
    source = Path("frontend/lib/admin-api.ts").read_text(encoding="utf-8")
    assert "process.env.FAVORITE_API_URL" in source
    assert "NEXT_PUBLIC_" not in source
