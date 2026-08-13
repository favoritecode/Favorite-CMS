from dataclasses import dataclass, field
from pathlib import Path
import json

import pytest

from backend.core.container import ServiceContainer
from backend.core.extensions import ExtensionManager, ExtensionManifest, ExtensionState, ManifestValidationError
from backend.engines.plugins import PluginContext, PluginEngine
from backend.engines.themes import ThemeEngine, ThemePackage
from backend.tests.extensions.conftest import manifest_data


@dataclass
class PluginRuntime:
    fail_activate: bool = False
    calls: list[str] = field(default_factory=list)
    context: PluginContext | None = None
    def register(self, context: PluginContext) -> None: self.context = context; self.calls.append("register")
    def activate(self) -> None:
        self.calls.append("activate")
        if self.fail_activate: raise RuntimeError("activation failed")
    def deactivate(self) -> None: self.calls.append("deactivate")
    def unregister(self) -> None: self.calls.append("unregister")


@dataclass
class ThemeRuntime:
    fail_activate: bool = False
    fail_deactivate: bool = False
    active: bool = False
    def activate(self) -> None:
        if self.fail_activate: raise RuntimeError("activation failed")
        self.active = True
    def deactivate(self) -> None:
        if self.fail_deactivate: raise RuntimeError("deactivation failed")
        self.active = False


def container_for(manager: ExtensionManager) -> ServiceContainer:
    container = ServiceContainer(); container.register("core.extensions", manager)
    return container


def plugin_manifest(identifier: str, **values: object) -> ExtensionManifest:
    return ExtensionManifest.from_mapping(manifest_data(id=identifier, **values))


def theme_manifest(identifier: str, **values: object) -> ExtensionManifest:
    return ExtensionManifest.from_mapping(manifest_data(id=identifier, type="theme", **values))


def test_plugin_explicit_registration_permission_gate_and_failure_isolation(tmp_path: Path) -> None:
    manager = ExtensionManager("0.1.0")
    manager.register(plugin_manifest("favorite.plugin.secure", permissions=["content.write"]))
    manager.register(plugin_manifest("favorite.plugin.healthy"))
    engine = PluginEngine(tmp_path / "absent"); engine.initialize(container_for(manager)); engine.start()
    with pytest.raises(ManifestValidationError, match="permissions"):
        engine.bind("favorite.plugin.secure", PluginRuntime())
    broken = PluginRuntime(fail_activate=True); healthy = PluginRuntime()
    engine.bind("favorite.plugin.secure", broken, granted_permissions=frozenset({"content.write"}))
    engine.bind("favorite.plugin.healthy", healthy)
    assert not engine.activate("favorite.plugin.secure")
    assert manager.state("favorite.plugin.secure") is ExtensionState.ERROR
    assert engine.activate("favorite.plugin.healthy")
    assert healthy.context is not None
    with pytest.raises(ManifestValidationError, match="non-public"):
        healthy.context.service("engine.database", object)
    with pytest.raises(ManifestValidationError, match="non-public"):
        healthy.context.service("engine.storage", object)


def test_dependencies_are_ordered_and_cycles_fail_closed(tmp_path: Path) -> None:
    manager = ExtensionManager("0.1.0")
    manager.register(plugin_manifest("favorite.plugin.base"))
    manager.register(plugin_manifest("favorite.plugin.child", dependencies={"favorite.plugin.base": ">=1"}))
    engine = PluginEngine(tmp_path / "none"); engine.initialize(container_for(manager)); engine.start()
    base = PluginRuntime(); child = PluginRuntime()
    engine.bind("favorite.plugin.base", base); engine.bind("favorite.plugin.child", child)
    assert engine.activate("favorite.plugin.child")
    assert manager.state("favorite.plugin.base") is ExtensionState.ENABLED
    assert manager.state("favorite.plugin.child") is ExtensionState.ENABLED

    cyclic = ExtensionManager("0.1.0")
    cyclic.register(plugin_manifest("favorite.plugin.a", dependencies={"favorite.plugin.b": ">=1"}))
    cyclic.register(plugin_manifest("favorite.plugin.b", dependencies={"favorite.plugin.a": ">=1"}))
    with pytest.raises(ManifestValidationError, match="Circular"):
        cyclic.activation_order()


def test_plugin_update_rolls_back_runtime_on_activation_failure(tmp_path: Path) -> None:
    manager = ExtensionManager("0.1.0")
    old_manifest = plugin_manifest("favorite.plugin.update")
    manager.register(old_manifest)
    engine = PluginEngine(tmp_path / "none"); engine.initialize(container_for(manager)); engine.start()
    old = PluginRuntime(); engine.bind(old_manifest.id, old); assert engine.activate(old_manifest.id)
    replacement = plugin_manifest("favorite.plugin.update", version="1.1.0")
    assert not engine.update(old_manifest.id, replacement, PluginRuntime(fail_activate=True))
    assert manager.manifest(old_manifest.id).version == "1.0.0"
    assert manager.state(old_manifest.id) is ExtensionState.ENABLED


def test_update_rejects_breaking_an_existing_dependency_constraint() -> None:
    manager = ExtensionManager("0.1.0")
    base = plugin_manifest("favorite.plugin.base")
    child = plugin_manifest("favorite.plugin.child", dependencies={base.id: "<2"})
    manager.register(base); manager.register(child)
    assert not manager.replace(base.id, plugin_manifest(base.id, version="2.0.0"), None)
    assert manager.manifest(base.id).version == "1.0.0"


def make_package(root: Path, name: str) -> ThemePackage:
    directory = root / name; directory.mkdir(); (directory / "page.html").write_text("safe", encoding="utf-8")
    return ThemePackage(directory, templates=("page.html",))


def test_theme_resource_security_and_atomic_switch(tmp_path: Path) -> None:
    manager = ExtensionManager("0.1.0")
    first_id, second_id = "favorite.theme.first", "favorite.theme.second"
    manager.register(theme_manifest(first_id)); manager.register(theme_manifest(second_id))
    engine = ThemeEngine(tmp_path / "none"); engine.initialize(container_for(manager)); engine.start()
    first, second = ThemeRuntime(), ThemeRuntime(fail_activate=True)
    engine.bind(first_id, make_package(tmp_path, "first"), first)
    engine.bind(second_id, make_package(tmp_path, "second"), second)
    assert engine.activate(first_id)
    assert not engine.activate(second_id)
    assert engine.active_theme == first_id and first.active
    with pytest.raises(ManifestValidationError, match="active Theme"):
        engine.deactivate(first_id)

    unsafe_root = tmp_path / "unsafe"; unsafe_root.mkdir()
    with pytest.raises(ManifestValidationError, match="invalid"):
        ThemePackage(unsafe_root, templates=("../secret",)).validate()


def test_theme_update_preserves_external_state_and_rejects_missing_resource(tmp_path: Path) -> None:
    manager = ExtensionManager("0.1.0"); identifier = "favorite.theme.update"
    manager.register(theme_manifest(identifier))
    engine = ThemeEngine(tmp_path / "none"); engine.initialize(container_for(manager)); engine.start()
    runtime = ThemeRuntime(); package = make_package(tmp_path, "old")
    engine.bind(identifier, package, runtime); assert engine.activate(identifier)
    invalid = ThemePackage(tmp_path / "old", templates=("missing.html",))
    assert not engine.update(identifier, theme_manifest(identifier, version="2.0.0"), invalid, ThemeRuntime())
    assert engine.package(identifier) is package


def test_duplicate_discovery_isolated_without_executing_package_code(tmp_path: Path) -> None:
    payload = dict(manifest_data(id="favorite.plugin.duplicate"))
    for name in ("a", "b"):
        folder = tmp_path / name; folder.mkdir()
        (folder / "plugin.json").write_text(json.dumps(payload), encoding="utf-8")
        (folder / "danger.py").write_text("raise RuntimeError('must not execute')", encoding="utf-8")
    manager = ExtensionManager("0.1.0")
    engine = PluginEngine(tmp_path); engine.initialize(container_for(manager)); engine.start()
    assert engine.ready
    assert manager.registered("plugin") == ("favorite.plugin.duplicate",)
    assert engine.discovery_failures == ("favorite.plugin.duplicate",)
