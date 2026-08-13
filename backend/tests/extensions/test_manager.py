from dataclasses import dataclass

import pytest

from backend.core.extensions import ExtensionManager, ExtensionManifest, ExtensionState, ManifestValidationError
from backend.tests.extensions.conftest import manifest_data


@dataclass
class Runtime:
    fail: bool = False
    active: bool = False

    def activate(self) -> None:
        if self.fail:
            raise RuntimeError("broken")
        self.active = True

    def deactivate(self) -> None:
        if self.fail:
            raise RuntimeError("broken")
        self.active = False


def test_dependency_validation_and_lifecycle_boundary() -> None:
    manager = ExtensionManager("0.1.0")
    dependency = ExtensionManifest.from_mapping(
        manifest_data(id="favorite.plugin.base", name="Base")
    )
    dependent = ExtensionManifest.from_mapping(
        manifest_data(
            id="favorite.plugin.dependent",
            name="Dependent",
            dependencies={"favorite.plugin.base": ">=1.0,<2"},
        )
    )
    runtime = Runtime()
    manager.register(dependency)
    manager.register(dependent, runtime)
    assert manager.enable(dependent.id)
    assert manager.state(dependent.id) is ExtensionState.ENABLED
    assert runtime.active
    assert manager.disable(dependent.id)
    assert manager.state(dependent.id) is ExtensionState.DISABLED


def test_missing_dependency_is_clear_validation_failure() -> None:
    manager = ExtensionManager("0.1.0")
    manifest = ExtensionManifest.from_mapping(
        manifest_data(dependencies={"favorite.plugin.missing": ">=1"})
    )
    manager.register(manifest)
    with pytest.raises(ManifestValidationError, match="missing"):
        manager.validate_dependencies(manifest.id)


def test_failed_extension_is_isolated() -> None:
    manager = ExtensionManager("0.1.0")
    broken = ExtensionManifest.from_mapping(manifest_data(id="favorite.plugin.broken"))
    healthy = ExtensionManifest.from_mapping(manifest_data(id="favorite.plugin.healthy"))
    manager.register(broken, Runtime(fail=True))
    manager.register(healthy, Runtime())
    assert not manager.enable(broken.id)
    assert manager.state(broken.id) is ExtensionState.ERROR
    assert manager.enable(healthy.id)
    assert manager.state(healthy.id) is ExtensionState.ENABLED


def test_incompatible_core_version_is_rejected() -> None:
    manager = ExtensionManager("0.1.0")
    incompatible = ExtensionManifest.from_mapping(
        manifest_data(minimumCoreVersion="2.0.0", maximumCoreVersion="3.0.0")
    )
    with pytest.raises(ManifestValidationError, match="incompatible"):
        manager.register(incompatible)

