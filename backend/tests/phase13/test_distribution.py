from __future__ import annotations

import io
import json
from pathlib import Path
import zipfile

from backend.cli import main
from backend.core.extensions import ExtensionDiscovery, ExtensionType
from backend.engines.themes import ThemePackage
from tools.build_distribution import archive, stage, validate


def _environment(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("FAVORITE_ENV", "test")
    monkeypatch.setenv("FAVORITE_DATABASE_URL", f"sqlite+pysqlite:///{tmp_path / 'install.db'}")
    monkeypatch.setenv("FAVORITE_STORAGE_ROOT", str(tmp_path / "mounted"))
    monkeypatch.setenv("FAVORITE_STORAGE_PROVIDER", "mounted")
    monkeypatch.setenv("FAVORITE_AUTH_JWT_SECRET", "phase-thirteen-signing-secret-at-least-thirty-two-bytes")
    monkeypatch.setenv("FAVORITE_ACTIVE_THEME", "favorite.theme.starter")


def _install_arguments(action: str = "view") -> list[str]:
    return ["install", "--email", "initial@example.test", "--display-name", "Initial Operator",
            "--role", "distribution-operator", "--authorization",
            f"admin.diagnostics.view:application.admin.platform:{action}:admin_diagnostics", "--password-stdin"]


def test_starter_theme_is_a_real_valid_resource_package() -> None:
    root = Path("themes/favorite.theme.starter")
    discovered = ExtensionDiscovery().discover(root.parent, ExtensionType.THEME)
    assert tuple(item.manifest.id for item in discovered) == ("favorite.theme.starter",)
    resources = json.loads((root / "resources.json").read_text(encoding="utf-8"))
    ThemePackage(root, **{key: tuple(value) for key, value in resources.items()}).validate()


def test_migrate_install_status_and_repeated_install(tmp_path: Path, monkeypatch, capsys) -> None:
    _environment(tmp_path, monkeypatch)
    assert main(["migrate"]) == 0
    monkeypatch.setattr("sys.stdin", io.StringIO("a secure initial password\n"))
    assert main(_install_arguments()) == 0
    monkeypatch.setattr("sys.stdin", io.StringIO("a secure initial password\n"))
    assert main(_install_arguments()) == 0
    assert main(["status"]) == 0
    output = capsys.readouterr()
    assert "Installation: installed" in output.out and "Pending migrations: 0" in output.out
    assert "a secure initial password" not in output.out + output.err


def test_failed_installation_is_retryable(tmp_path: Path, monkeypatch, capsys) -> None:
    _environment(tmp_path, monkeypatch); assert main(["migrate"]) == 0
    monkeypatch.setattr("sys.stdin", io.StringIO("a secure initial password\n"))
    assert main(_install_arguments("manage")) == 1
    monkeypatch.setattr("sys.stdin", io.StringIO("a secure initial password\n"))
    assert main(_install_arguments()) == 0
    assert "password" not in capsys.readouterr().out.casefold()


def test_distribution_is_filtered_and_reproducible(tmp_path: Path) -> None:
    first = stage(tmp_path / "first"); second = stage(tmp_path / "second")
    validate(first); validate(second)
    first_zip, _ = archive(first, tmp_path / "out-one"); second_zip, _ = archive(second, tmp_path / "out-two")
    assert first_zip.read_bytes() == second_zip.read_bytes()
    with zipfile.ZipFile(first_zip) as bundle:
        names = set(bundle.namelist())
    assert any(name.endswith("backend/main.py") for name in names)
    assert any(name.endswith("themes/favorite.theme.starter/theme.json") for name in names)
    assert any(name.endswith("plugins/favorite.plugin.example/plugin.json") for name in names)
    for identifier in ("seo", "contact", "sitemap", "analytics"):
        assert any(name.endswith(f"plugins/favorite.plugin.{identifier}/plugin.json") for name in names)
    assert not any("/tests/" in name or "__pycache__" in name or name.endswith((".db", ".pyc")) for name in names)
