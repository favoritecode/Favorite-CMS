from __future__ import annotations

import hashlib
import json
from pathlib import Path
import tomllib
import zipfile

from backend.bootstrap import build_kernel
from backend.database.migrations import DatabaseMigrationEngine
from backend.engines.authentication import AuthenticationEngine
from backend.engines.api import APIEngine
from backend.engines.localization import LocalizationEngine
from backend.engines.media import MediaEngine, MediaType
from backend.engines.permissions import PermissionEngine, RoleGrant
from backend.engines.search import SearchEngine, SearchQuery
from backend.engines.settings import SettingScope, SettingScopeKind, SettingsEngine
from backend.engines.users import UserEngine
from backend.engines.routing import RoutingEngine
from tools.build_distribution import archive, load_manifest, stage, validate


def test_release_version_is_consistent() -> None:
    manifest = load_manifest()
    python = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))["project"]["version"]
    frontend = json.loads(Path("frontend/package.json").read_text(encoding="utf-8"))["version"]
    assert manifest["version"] == python == frontend == "0.1.0"


def test_release_archives_are_reproducible_and_checksums_verify(tmp_path: Path) -> None:
    first = stage(tmp_path / "stage-one"); second = stage(tmp_path / "stage-two")
    validate(first); validate(second)
    first_zip, first_checksum = archive(first, tmp_path / "first")
    second_zip, _ = archive(second, tmp_path / "second")
    assert first_zip.read_bytes() == second_zip.read_bytes()
    digest = hashlib.sha256(first_zip.read_bytes()).hexdigest()
    assert first_checksum.read_text(encoding="ascii") == f"{digest}  favorite-cms-0.1.0.zip\n"
    with zipfile.ZipFile(first_zip) as bundle:
        names = bundle.namelist()
        assert bundle.testzip() is None
        assert names == sorted(names)
        assert all(not Path(name).is_absolute() and ".." not in Path(name).parts for name in names)
        required = ("backend/main.py", "backend/cli.py", "frontend/package.json", "frontend/pnpm-lock.yaml",
                    "themes/favorite.theme.starter/theme.json", "plugins/favorite.plugin.example/plugin.json",
                    "plugins/favorite.plugin.seo/plugin.json", "plugins/favorite.plugin.contact/plugin.json",
                    "plugins/favorite.plugin.sitemap/plugin.json", "plugins/favorite.plugin.analytics/plugin.json")
        for suffix in required: assert any(name.endswith(suffix) for name in names)
        prohibited = ("/.git/", "/.github/", "/.venv/", "/node_modules/", "/__pycache__/", "/backend/tests/",
                      "/frontend/tests/", "/test-results/", "/.next/")
        assert not any(any(marker in f"/{name}" for marker in prohibited) or name.endswith((".pyc", ".db", ".sqlite", ".log")) for name in names)


def test_clean_platform_contracts_support_installed_cms_workflows(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("FAVORITE_ENV", "test")
    monkeypatch.setenv("FAVORITE_DATABASE_URL", f"sqlite+pysqlite:///{tmp_path / 'clean.db'}")
    monkeypatch.setenv("FAVORITE_STORAGE_ROOT", str(tmp_path / "clean-storage"))
    monkeypatch.setenv("FAVORITE_STORAGE_PROVIDER", "mounted")
    monkeypatch.setenv("FAVORITE_AUTH_JWT_SECRET", "phase-seventeen-clean-signing-secret-value")
    monkeypatch.setenv("FAVORITE_ACTIVE_THEME", "favorite.theme.starter")
    kernel = build_kernel()
    try:
        kernel.bootstrap(); migrations = kernel.container.resolve("engine.migrations", DatabaseMigrationEngine)
        migrations.initialize_history(); migrations.upgrade()
        users = kernel.container.resolve("engine.users", UserEngine); auth = kernel.container.resolve("engine.authentication", AuthenticationEngine)
        permissions = kernel.container.resolve("engine.permissions", PermissionEngine); role = "release-operator"
        for permission_id in tuple(f"platform.content.{action}" for action in ("create", "read", "update", "delete", "publish", "archive")) + tuple(
            f"platform.media.{action}" for action in ("create", "read", "update", "delete")) + ("platform.setting.read", "platform.setting.write"):
            permissions.grant_role(RoleGrant(role, permission_id, "application.admin.platform"))
        for permission_id in ("admin.content.manage", "admin.media.manage", "admin.settings.manage"):
            permissions.grant_role(RoleGrant(role, permission_id, "application.admin.platform"))
        user = users.create(email="release@example.test", display_name="Release Operator", role=role)
        auth.set_password(user.user_id, "release candidate password"); token = auth.login(email=user.email, password="release candidate password").token
        assert token is not None; context = auth.resolve(token.reveal())
        api = kernel.container.resolve("engine.api", APIEngine); routing = kernel.container.resolve("engine.routing", RoutingEngine)
        created = api.handle(routing.resolve("POST", "/admin/api/content"), credential=token.reveal(), body={
            "type_id": "page", "title": "Clean release page", "data": {"slug": "clean-release", "body": "Independent package content"}})
        page_id = created.body["data"]["id"]
        published = api.handle(routing.resolve("PATCH", "/admin/api/content"), credential=token.reveal(), body={
            "id": page_id, "title": "Clean release page", "data": {"slug": "clean-release", "body": "Independent package content"}, "action": "publish"})
        assert published.status == 200 and published.body["data"]["state"] == "published"
        assert kernel.container.resolve("engine.search", SearchEngine).query(SearchQuery(text="Independent package"))[0].resource_id == page_id
        media = kernel.container.resolve("engine.media", MediaEngine)
        uploaded = media.upload(media_type=MediaType.DOCUMENT, file_name="release.txt", mime_type="text/plain", data=b"release", metadata={}, public=False, authentication=context)
        assert media.list(context)[0].media_id == uploaded.media_id and not hasattr(uploaded, "storage_identifier")
        settings = kernel.container.resolve("engine.settings", SettingsEngine); scope = SettingScope(SettingScopeKind.PLATFORM, "application.admin.platform")
        assert settings.set("site_title", scope, "Clean Favorite CMS", context).value == "Clean Favorite CMS"
        translated = kernel.container.resolve("engine.localization", LocalizationEngine).translate(
            owner="application.admin.platform", namespace="public", key="public.welcome", locale_id="fr", fallback_locales=("en",))
        assert translated.value == "Welcome" and translated.fallback_used
    finally:
        kernel.shutdown()
