import json
from pathlib import Path

from backend.core.extensions import ExtensionDiscovery, ExtensionType
from backend.tests.extensions.conftest import manifest_data


def test_discovery_reads_valid_manifest_without_importing_code(tmp_path: Path) -> None:
    extension = tmp_path / "example"
    extension.mkdir()
    (extension / "plugin.json").write_text(json.dumps(manifest_data()), encoding="utf-8")
    (extension / "danger.py").write_text("raise RuntimeError('must not execute')", encoding="utf-8")
    discovered = ExtensionDiscovery().discover(tmp_path, ExtensionType.PLUGIN)
    assert [item.manifest.id for item in discovered] == ["favorite.plugin.example"]


def test_discovery_ignores_invalid_manifest_and_continues(tmp_path: Path) -> None:
    invalid = tmp_path / "invalid"
    invalid.mkdir()
    (invalid / "plugin.json").write_text("not-json", encoding="utf-8")
    valid = tmp_path / "valid"
    valid.mkdir()
    (valid / "plugin.json").write_text(
        json.dumps(manifest_data(id="favorite.plugin.valid")), encoding="utf-8"
    )
    discovered = ExtensionDiscovery().discover(tmp_path, ExtensionType.PLUGIN)
    assert [item.manifest.id for item in discovered] == ["favorite.plugin.valid"]

