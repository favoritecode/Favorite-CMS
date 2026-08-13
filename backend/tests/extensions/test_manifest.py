import pytest

from backend.core.extensions import ExtensionManifest, ExtensionType, ManifestValidationError
from backend.tests.extensions.conftest import manifest_data


def test_valid_manifest_preserves_identity_and_type() -> None:
    manifest = ExtensionManifest.from_mapping(manifest_data())
    assert manifest.id == "favorite.plugin.example"
    assert manifest.type is ExtensionType.PLUGIN
    assert manifest.supports_core("0.1.0")


def test_missing_required_metadata_is_rejected() -> None:
    data = dict(manifest_data())
    del data["author"]
    with pytest.raises(ManifestValidationError, match="author"):
        ExtensionManifest.from_mapping(data)


@pytest.mark.parametrize("identifier", ["plugin", "Favorite.plugin.example", "../plugin/example"])
def test_invalid_extension_identity_is_rejected(identifier: str) -> None:
    with pytest.raises(ManifestValidationError, match="identifier"):
        ExtensionManifest.from_mapping(manifest_data(id=identifier))


def test_self_dependency_is_rejected() -> None:
    with pytest.raises(ManifestValidationError, match="itself"):
        ExtensionManifest.from_mapping(
            manifest_data(dependencies={"favorite.plugin.example": ">=1.0"})
        )

