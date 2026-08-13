from __future__ import annotations

from pathlib import Path

import pytest

from tools import build_distribution
from tools.build_distribution import load_manifest


def test_release_version_includes_runtime_metadata_consistency() -> None:
    assert load_manifest()["version"] == "0.1.0"


def test_distribution_rejects_source_symlinks(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = tmp_path / "runtime.txt"
    source.write_text("runtime", encoding="utf-8")
    original = Path.is_symlink
    monkeypatch.setattr(
        Path,
        "is_symlink",
        lambda candidate: candidate == source or original(candidate),
    )

    with pytest.raises(ValueError, match="Symlink is prohibited"):
        build_distribution._reject_source_symlinks(source)


def test_release_version_conflict_fails_closed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setitem(
        build_distribution.RUNTIME_VERSION_FILES,
        "backend/main.py",
        'version="9.9.9"',
    )

    with pytest.raises(ValueError, match="Runtime version metadata conflicts"):
        load_manifest()
