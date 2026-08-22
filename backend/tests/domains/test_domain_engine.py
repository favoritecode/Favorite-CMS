from pathlib import Path

import pytest

from backend.bootstrap import build_kernel
from backend.database.migrations import DatabaseMigrationEngine
from backend.engines.authentication import AuthenticationEngine
from backend.engines.domains import DomainEngine, DomainEntityContract, DomainField, DomainFieldKind, InvalidDomain
from backend.engines.permissions import PermissionDefinition, PermissionEngine, RoleGrant
from backend.engines.users import UserEngine


OWNER = "favorite.plugin.catalog"
PERMISSIONS = {action: f"{OWNER}.{action}" for action in ("create", "read", "update", "delete")}


def _contract() -> DomainEntityContract:
    return DomainEntityContract("product", OWNER, "Products", (
        DomainField("name", DomainFieldKind.STRING, True, 120),
        DomainField("price", DomainFieldKind.DECIMAL, True),
        DomainField("status", DomainFieldKind.ENUM, True, choices=("draft", "published")),
        DomainField("featured_media", DomainFieldKind.MEDIA),
    ), PERMISSIONS)


def _prepare(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("FAVORITE_ENV", "test"); monkeypatch.setenv("FAVORITE_DATABASE_URL", f"sqlite+pysqlite:///{tmp_path / 'domain.db'}")
    monkeypatch.setenv("FAVORITE_STORAGE_ROOT", str(tmp_path / "storage")); monkeypatch.setenv("FAVORITE_AUTH_JWT_SECRET", "domain-test-signing-key-at-least-thirty-two-bytes")
    monkeypatch.setenv("FAVORITE_ACTIVE_THEME", "favorite.theme.starter")
    first = build_kernel(); first.bootstrap(); migrations = first.container.resolve("engine.migrations", DatabaseMigrationEngine)
    migrations.initialize_history(); migrations.upgrade(); first.shutdown()
    kernel = build_kernel(); kernel.bootstrap(); permissions = kernel.container.resolve("engine.permissions", PermissionEngine)
    for action, permission_id in PERMISSIONS.items():
        permissions.register(PermissionDefinition(permission_id, OWNER, action, "plugin_domain")); permissions.grant_role(RoleGrant("catalog-manager", permission_id, OWNER))
    users = kernel.container.resolve("engine.users", UserEngine); user = users.find_by_email("catalog@example.test") or users.create(email="catalog@example.test", display_name="Catalog", role="catalog-manager")
    authentication = kernel.container.resolve("engine.authentication", AuthenticationEngine); authentication.set_password(user.user_id, "correct horse battery staple")
    login = authentication.login(email="catalog@example.test", password="correct horse battery staple"); assert login.token is not None
    return kernel, authentication.resolve(login.token.reveal())


def test_plugin_domain_contract_validates_persists_and_is_owner_scoped(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    kernel, authentication = _prepare(tmp_path, monkeypatch)
    try:
        domains = kernel.container.resolve("engine.domains", DomainEngine); plugin = domains.for_plugin(OWNER); plugin.register(_contract())
        record = plugin.create("product", {"name": "Neutral product", "price": "19.90", "status": "draft"}, authentication)
        assert record.values == {"name": "Neutral product", "price": "19.90", "status": "draft"}
        assert plugin.get("product", record.record_id, authentication).record_id == record.record_id
        changed = plugin.update("product", record.record_id, {"name": "Neutral product", "price": 20, "status": "published"}, authentication)
        assert changed.values["price"] == "20" and plugin.list("product", authentication) == (changed,)
        with pytest.raises(InvalidDomain): plugin.create("product", {"name": "Broken", "price": "not-money", "status": "draft"}, authentication)
        with pytest.raises(InvalidDomain): domains.for_plugin("favorite.plugin.other").register(_contract())
        plugin.unregister_all()
        assert domains.contracts(OWNER) == ()
    finally: kernel.shutdown()


def test_domain_records_survive_restart_without_plugin_contract_leakage(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    kernel, authentication = _prepare(tmp_path, monkeypatch)
    domains = kernel.container.resolve("engine.domains", DomainEngine); plugin = domains.for_plugin(OWNER); plugin.register(_contract())
    record = plugin.create("product", {"name": "Persistent", "price": "8.50", "status": "draft"}, authentication)
    kernel.shutdown()
    restored, restored_auth = _prepare(tmp_path, monkeypatch)
    try:
        restored_plugin = restored.container.resolve("engine.domains", DomainEngine).for_plugin(OWNER); restored_plugin.register(_contract())
        assert restored_plugin.get("product", record.record_id, restored_auth).values["name"] == "Persistent"
    finally: restored.shutdown()
