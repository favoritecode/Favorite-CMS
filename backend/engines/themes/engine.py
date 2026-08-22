"""Theme package lifecycle and safe presentation-resource catalogue."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path, PurePosixPath
from typing import Protocol

from backend.config import Configuration
from backend.core.container import ServiceContainer
from backend.core.extensions import ExtensionDiscovery, ExtensionManager, ExtensionManifest, ExtensionState, ExtensionType, ManifestValidationError


class ThemeRuntime(Protocol):
    def activate(self) -> None: ...
    def deactivate(self) -> None: ...


@dataclass(frozen=True)
class ThemePackage:
    root: Path
    templates: tuple[str, ...] = ()
    layouts: tuple[str, ...] = ()
    components: tuple[str, ...] = ()
    widgets: tuple[str, ...] = ()
    assets: tuple[str, ...] = ()

    def validate(self) -> None:
        root = self.root.resolve(strict=True)
        for logical in (*self.templates, *self.layouts, *self.components, *self.widgets, *self.assets):
            relative = PurePosixPath(logical)
            if relative.is_absolute() or not relative.parts or ".." in relative.parts or "" in relative.parts:
                raise ManifestValidationError("Theme resource identifier is invalid")
            target = root.joinpath(*relative.parts)
            if target.is_symlink() or not target.is_file():
                raise ManifestValidationError("Theme resource is missing or unsafe")
            resolved = target.resolve(strict=True)
            if root not in resolved.parents:
                raise ManifestValidationError("Theme resource escapes its package")


class _BoundTheme:
    def __init__(self, runtime: ThemeRuntime, package: ThemePackage) -> None:
        self.runtime = runtime; self.package = package
    def register(self) -> None: self.package.validate()
    def activate(self) -> None: self.runtime.activate()
    def deactivate(self) -> None: self.runtime.deactivate()
    def unregister(self) -> None: pass


class ThemeEngine:
    engine_id = "themes"
    dependencies = ("plugins", "settings", "localization", "menu", "seo", "media")

    def __init__(self, root: Path = Path("themes")) -> None:
        self._root = root
        self._manager: ExtensionManager | None = None
        self._configuration: Configuration | None = None
        self._packages: dict[str, ThemePackage] = {}
        self._active: str | None = None
        self.discovery_failures: tuple[str, ...] = ()
        self.ready = False

    @property
    def active_theme(self) -> str | None: return self._active

    def initialize(self, container: ServiceContainer) -> None:
        self._manager = container.resolve("core.extensions", ExtensionManager)
        self._configuration = container.resolve("core.configuration", Configuration) if container.contains("core.configuration") else None
        container.register("engine.themes", self)

    def start(self) -> None:
        failures: list[str] = []
        if self._root.exists():
            for item in ExtensionDiscovery().discover(self._root, ExtensionType.THEME):
                try:
                    self._manager_required().register(item.manifest)
                    catalogue = _resource_catalogue(item.path)
                    if catalogue is not None:
                        self.bind(item.manifest.id, ThemePackage(item.path, **catalogue), _ResourceThemeRuntime())
                except ManifestValidationError: failures.append(item.manifest.id)
        self.discovery_failures = tuple(failures)
        self.ready = True
        if self._configuration is None: configured = ""
        else:
            try: configured = self._configuration.get("theme.active", str)
            except Exception: configured = ""
        if configured and not self.activate(configured): raise ManifestValidationError("Configured Theme activation failed")

    def shutdown(self) -> None:
        if self._active is not None:
            self._manager_required().disable(self._active)
            self._active = None
        self.ready = False

    def bind(self, extension_id: str, package: ThemePackage, runtime: ThemeRuntime) -> None:
        self._theme_manifest(extension_id)
        package.validate()
        self._manager_required().attach_runtime(extension_id, _BoundTheme(runtime, package))
        self._packages[extension_id] = package

    def install_package(self, manifest: ExtensionManifest, package: ThemePackage) -> None:
        if manifest.type is not ExtensionType.THEME:
            raise ManifestValidationError("Extension is not a Theme")
        package.validate()
        self._manager_required().register(manifest)
        self.bind(manifest.id, package, _ResourceThemeRuntime())

    def uninstall(self, extension_id: str) -> None:
        if extension_id == self._active:
            raise ManifestValidationError("The active Theme cannot be uninstalled")
        self._theme_manifest(extension_id)
        self._manager_required().remove(extension_id)
        self._packages.pop(extension_id, None)

    def activate(self, extension_id: str) -> bool:
        manifest = self._theme_manifest(extension_id)
        if extension_id not in self._packages:
            raise ManifestValidationError("Theme package is not explicitly registered")
        for dependency in manifest.dependencies:
            if self._manager_required().state(dependency) is not ExtensionState.ENABLED:
                return False
        previous = self._active
        if previous == extension_id: return True
        if not self._manager_required().enable(extension_id): return False
        if previous is not None and not self._manager_required().disable(previous):
            self._manager_required().disable(extension_id)
            if not self._manager_required().enable(previous):
                self._active = None
                return False
            self._active = previous
            return False
        self._active = extension_id
        return True

    def deactivate(self, extension_id: str) -> bool:
        if extension_id == self._active:
            raise ManifestValidationError("The active Theme must be replaced before deactivation")
        return self._manager_required().disable(extension_id)

    def package(self, extension_id: str) -> ThemePackage:
        self._theme_manifest(extension_id)
        try: return self._packages[extension_id]
        except KeyError as exc: raise ManifestValidationError("Theme package is not registered") from exc

    def resource_text(self, extension_id: str, reference: str, *, maximum_bytes: int = 262_144) -> str:
        """Read one declared, validated presentation resource without exposing its path."""
        package = self.package(extension_id)
        declared = {*package.templates, *package.layouts, *package.components,
                    *package.widgets, *package.assets}
        if reference not in declared:
            raise ManifestValidationError("Theme resource is not declared")
        package.validate()
        target = package.root.resolve(strict=True).joinpath(*PurePosixPath(reference).parts)
        try:
            data = target.read_bytes()
            if len(data) > maximum_bytes: raise ManifestValidationError("Theme resource is too large")
            return data.decode("utf-8")
        except (OSError, UnicodeError) as exc:
            raise ManifestValidationError("Theme resource could not be read") from exc

    def manifest(self, extension_id: str) -> ExtensionManifest:
        """Return validated public Theme metadata without exposing the manager."""
        return self._theme_manifest(extension_id)

    def update(self, extension_id: str, manifest: ExtensionManifest,
               package: ThemePackage, runtime: ThemeRuntime) -> bool:
        if manifest.type is not ExtensionType.THEME: return False
        try: package.validate()
        except ManifestValidationError: return False
        result = self._manager_required().replace(extension_id, manifest, _BoundTheme(runtime, package))
        if result: self._packages[extension_id] = package
        return result

    def _theme_manifest(self, extension_id: str) -> ExtensionManifest:
        manifest = self._manager_required().manifest(extension_id)
        if manifest.type is not ExtensionType.THEME:
            raise ManifestValidationError("Extension is not a Theme")
        return manifest

    def _manager_required(self) -> ExtensionManager:
        if self._manager is None: raise RuntimeError("Theme Engine is not initialized")
        return self._manager


class _ResourceThemeRuntime:
    def activate(self) -> None: pass
    def deactivate(self) -> None: pass


def _resource_catalogue(root: Path) -> dict[str, tuple[str, ...]] | None:
    path = root / "resources.json"
    if not path.is_file() or path.is_symlink(): return None
    try: value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc: raise ManifestValidationError("Theme Resource catalogue is invalid") from exc
    if not isinstance(value, dict) or set(value) != {"templates", "layouts", "components", "widgets", "assets"}: raise ManifestValidationError("Theme Resource catalogue is invalid")
    result: dict[str, tuple[str, ...]] = {}
    for key, entries in value.items():
        if not isinstance(entries, list) or any(not isinstance(item, str) for item in entries): raise ManifestValidationError("Theme Resource catalogue is invalid")
        result[key] = tuple(entries)
    return result
