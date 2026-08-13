from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from backend.bootstrap import build_kernel
from backend.config import Configuration, MappingSource
from backend.config.engine import BOOTSTRAP_SCHEMA
from backend.core.extensions import ExtensionManager, ExtensionManifest
from backend.database.migrations import DatabaseMigrationEngine
from backend.engines.permissions import PermissionDefinition, PermissionEngine, RoleGrant
from backend.engines.themes import ThemeEngine, ThemePackage
from backend.engines.users import UserEngine
from backend.operations import DeploymentValidator, HealthEngine, HealthStatus, InstallationEngine, InstallationRequest, InstallationState
from backend.operations.health import HealthContributor, HealthReport
from backend.operations.installation import RequiredAuthorization
from backend.tests.extensions.conftest import manifest_data
from backend.main import create_app


class ThemeRuntime:
    def activate(self) -> None: pass
    def deactivate(self) -> None: pass


@pytest.fixture
def kernel(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("FAVORITE_ENV", "test")
    monkeypatch.setenv("FAVORITE_DATABASE_URL", f"sqlite+pysqlite:///{tmp_path / 'phase10.db'}")
    monkeypatch.setenv("FAVORITE_STORAGE_ROOT", str(tmp_path / "storage"))
    monkeypatch.setenv("FAVORITE_AUTH_JWT_SECRET", "phase-ten-test-signing-key-at-least-thirty-two-bytes")
    value = build_kernel(); value.bootstrap()
    migrations = value.container.resolve("engine.migrations", DatabaseMigrationEngine)
    migrations.initialize_history(); migrations.upgrade()
    yield value
    value.shutdown()


def activate_theme(kernel, root: Path) -> None:
    identifier = "favorite.theme.operations"
    manifest = ExtensionManifest.from_mapping(manifest_data(id=identifier, type="theme"))
    manager = kernel.container.resolve("core.extensions", ExtensionManager); manager.register(manifest)
    root.mkdir(exist_ok=True); (root / "page.html").write_text("safe", encoding="utf-8")
    themes = kernel.container.resolve("engine.themes", ThemeEngine)
    themes.bind(identifier, ThemePackage(root, templates=("page.html",)), ThemeRuntime())
    assert themes.activate(identifier)


def installation_request() -> InstallationRequest:
    return InstallationRequest("operator@example.com", "Operator", "correct horse battery staple", "operator",
                               (RequiredAuthorization("platform.operate", "operate", "platform"),))


def grant_install_permission(kernel) -> None:
    permissions = kernel.container.resolve("engine.permissions", PermissionEngine)
    permissions.register(PermissionDefinition("platform.operate", "tests", "operate", "platform"))
    permissions.grant_role(RoleGrant("operator", "platform.operate", "tests"))


def test_health_separates_liveness_readiness_and_public_detail(kernel, tmp_path: Path) -> None:
    health = kernel.container.resolve("engine.observability", HealthEngine)
    assert health.liveness().live
    unavailable = health.readiness(details=True)
    assert not unavailable.ready and any(item.component == "theme" for item in unavailable.components)
    assert set(health.public_readiness()) == {"status", "ready"}
    activate_theme(kernel, tmp_path / "theme")
    assert health.readiness().ready


def test_optional_health_failure_is_isolated_and_critical_fails_readiness(kernel, tmp_path: Path) -> None:
    activate_theme(kernel, tmp_path / "theme")
    health = kernel.container.resolve("engine.observability", HealthEngine)
    health.register(HealthContributor("optional.check", "optional.plugin", lambda: (_ for _ in ()).throw(RuntimeError("secret path"))))
    report = health.readiness(details=True)
    assert report.ready and report.status is HealthStatus.DEGRADED
    health.register(HealthContributor("critical.check", "required.plugin", lambda: HealthStatus.UNAVAILABLE, True))
    assert not health.readiness().ready
    health.unregister_owner("required.plugin"); assert health.readiness().ready
    plugin = health.for_plugin("optional.plugin"); plugin.register("plugin.check", lambda: HealthStatus.UNAVAILABLE)
    assert health.readiness().ready
    plugin.unregister_all(); assert all(item.component != "plugin.check" for item in health.readiness(details=True).components)


def test_clean_install_is_explicit_authorized_and_idempotent(kernel, tmp_path: Path) -> None:
    activate_theme(kernel, tmp_path / "theme"); grant_install_permission(kernel)
    installer = kernel.container.resolve("engine.installation", InstallationEngine)
    assert installer.state() is InstallationState.UNINSTALLED
    assert installer.install(installation_request()) is InstallationState.INSTALLED
    alternate = InstallationRequest("other@example.com", "Other", "another correct password", "operator", installation_request().required_authorizations)
    assert installer.install(alternate) is InstallationState.INSTALLED
    assert kernel.container.resolve("engine.users", UserEngine).find_by_email("other@example.com") is None


def test_partial_install_never_marks_complete_and_can_retry(kernel, tmp_path: Path) -> None:
    grant_install_permission(kernel); installer = kernel.container.resolve("engine.installation", InstallationEngine)
    with pytest.raises(Exception, match="active Theme"):
        installer.install(installation_request())
    assert installer.state() is InstallationState.FAILED
    activate_theme(kernel, tmp_path / "theme")
    assert installer.install(installation_request()) is InstallationState.INSTALLED


def test_installation_rejects_missing_authorization_contract(kernel, tmp_path: Path) -> None:
    activate_theme(kernel, tmp_path / "theme")
    installer = kernel.container.resolve("engine.installation", InstallationEngine)
    with pytest.raises(Exception): installer.install(installation_request())
    assert installer.state() is InstallationState.FAILED


@pytest.mark.parametrize("boundary", ["database", "storage", "migrations"])
def test_installation_preflight_failure_never_marks_complete(kernel, monkeypatch: pytest.MonkeyPatch, boundary: str) -> None:
    installer = kernel.container.resolve("engine.installation", InstallationEngine)
    if boundary == "database": monkeypatch.setattr(installer._database, "healthcheck", lambda: False)
    elif boundary == "storage": monkeypatch.setattr(installer._storage, "healthcheck", lambda: False)
    else: monkeypatch.setattr(installer._migrations, "upgrade", lambda: (_ for _ in ()).throw(RuntimeError("migration failed")))
    with pytest.raises(Exception): installer.install(installation_request())
    assert installer.state() is InstallationState.UNINSTALLED


def test_deployment_preflight_is_provider_neutral_and_fail_closed() -> None:
    config = Configuration.resolve(BOOTSTRAP_SCHEMA, (MappingSource("test", {
        "environment": "production", "debug": False, "database.url": "postgresql://redacted",
        "authentication.jwt_secret": "not-logged-secret"
    }, 1),))
    class Database: provider = "postgresql"
    class Migrations:
        def pending(self): return ()
    class Storage:
        provider_name = "approved-production-adapter"
        def healthcheck(self): return True
    class Health:
        def readiness(self): return HealthReport(True, True, HealthStatus.HEALTHY)
    report = DeploymentValidator(config, Database(), Migrations(), Storage(), Health()).validate_production()
    assert report.valid and "postgresql" in report.checks and not report.failures


def test_public_health_routes_are_minimal_and_do_not_expose_topology(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("FAVORITE_ENV", "test")
    monkeypatch.setenv("FAVORITE_DATABASE_URL", f"sqlite+pysqlite:///{tmp_path / 'http.db'}")
    monkeypatch.setenv("FAVORITE_STORAGE_ROOT", str(tmp_path / "storage"))
    monkeypatch.setenv("FAVORITE_AUTH_JWT_SECRET", "phase-ten-http-signing-key-at-least-thirty-two-bytes")
    with TestClient(create_app()) as client:
        live = client.get("/health/live"); ready = client.get("/health/ready")
    assert live.status_code == 200 and live.json()["data"] == {"status": "healthy", "live": True}
    assert ready.status_code == 200 and set(ready.json()["data"]) == {"status", "ready"}
    assert "database" not in ready.text and "plugin" not in ready.text
