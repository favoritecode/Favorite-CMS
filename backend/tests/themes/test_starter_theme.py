from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from backend.core.extensions import ExtensionDiscovery, ExtensionType, ManifestValidationError
from backend.engines.themes import ThemeEngine, ThemePackage
from backend.main import create_app
from backend.tests.e2e_app import seed


ROOT = Path("themes/favorite.theme.starter")


def _environment(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("FAVORITE_ENV", "test")
    monkeypatch.setenv("FAVORITE_DATABASE_URL", f"sqlite+pysqlite:///{tmp_path / 'theme.db'}")
    monkeypatch.setenv("FAVORITE_STORAGE_ROOT", str(tmp_path / "storage"))
    monkeypatch.setenv("FAVORITE_AUTH_JWT_SECRET", "starter-theme-test-secret-at-least-thirty-two-bytes")
    monkeypatch.setenv("FAVORITE_ACTIVE_THEME", "favorite.theme.starter")


def test_starter_manifest_catalogue_and_declared_resources() -> None:
    discovered = ExtensionDiscovery().discover(ROOT.parent, ExtensionType.THEME)
    starter = next(item for item in discovered if item.manifest.id == "favorite.theme.starter")
    assert starter.manifest.name == "Favorite Starter"
    assert str(starter.manifest.version) == "1.0.0"
    catalogue = json.loads((ROOT / "resources.json").read_text(encoding="utf-8"))
    package = ThemePackage(ROOT, **{key: tuple(value) for key, value in catalogue.items()})
    package.validate()
    assert set(package.components) == {"components/header.html", "components/footer.html"}
    assert {"templates/page.html", "layouts/base.html", "assets/starter.css"} <= {
        *package.templates, *package.layouts, *package.assets
    }


def test_missing_required_theme_resource_is_rejected(tmp_path: Path) -> None:
    (tmp_path / "page.html").write_text("page", encoding="utf-8")
    with pytest.raises(ManifestValidationError):
        ThemePackage(tmp_path, templates=("page.html",), layouts=("missing-layout.html",)).validate()


def test_declared_resource_reader_rejects_undeclared_and_missing(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _environment(tmp_path, monkeypatch)
    with TestClient(create_app(on_started=seed)) as client:
        themes = client.app.state.kernel.container.resolve("engine.themes", ThemeEngine)
        assert "site-header" in themes.resource_text("favorite.theme.starter", "components/header.html")
        with pytest.raises(ManifestValidationError):
            themes.resource_text("favorite.theme.starter", "theme.json")


def test_active_starter_renders_home_listing_detail_search_and_safe_missing(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _environment(tmp_path, monkeypatch)
    with TestClient(create_app(on_started=seed)) as client:
        home = client.get("/site/welcome")
        assert home.status_code == 200
        assert 'name="theme" content="favorite.theme.starter"' in home.text
        assert "Welcome to Favorite CMS" in home.text and "Latest published content" in home.text
        listing = client.get("/site/content")
        assert listing.status_code == 200 and "Browser" not in listing.text
        assert "Welcome to Favorite CMS" in listing.text
        content_id = listing.text.split('/site/content/')[1].split('"')[0]
        detail = client.get(f"/site/content/{content_id}")
        assert detail.status_code == 200 and "Rendered by the backend presentation pipeline." in detail.text
        search = client.get("/site/search/backend%20presentation")
        assert search.status_code == 200 and "Welcome to Favorite CMS" in search.text
        empty = client.get("/site/search/no-such-resource")
        assert empty.status_code == 200 and "No matching content found" in empty.text
        missing = client.get("/site/content/00000000-0000-0000-0000-000000000000")
        assert missing.status_code == 404
        assert "traceback" not in missing.text.casefold() and str(tmp_path) not in missing.text


def test_failed_theme_activation_preserves_renderable_starter(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _environment(tmp_path, monkeypatch)
    with TestClient(create_app(on_started=seed)) as client:
        themes = client.app.state.kernel.container.resolve("engine.themes", ThemeEngine)
        assert themes.active_theme == "favorite.theme.starter"
        assert themes.activate("tests.theme.failing") is False
        assert themes.active_theme == "favorite.theme.starter"
        response = client.get("/site/welcome")
        assert response.status_code == 200 and "Favorite Starter" in response.text
