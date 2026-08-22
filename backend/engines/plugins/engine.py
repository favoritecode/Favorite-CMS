"""Plugin lifecycle host. Discovery never imports executable code."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Mapping, Protocol, TypeVar

from backend.core.container import ServiceContainer
from backend.core.extensions import ExtensionDiscovery, ExtensionManager, ExtensionManifest, ExtensionState, ExtensionType, ManifestValidationError


class PluginRuntime(Protocol):
    def register(self, context: "PluginContext") -> None: ...
    def activate(self) -> None: ...
    def deactivate(self) -> None: ...
    def unregister(self) -> None: ...


T = TypeVar("T")


@dataclass(frozen=True)
class PluginContext:
    plugin_id: str
    permissions: frozenset[str]
    _services: Mapping[str, object]

    def service(self, name: str, expected_type: type[T]) -> T:
        try:
            value = self._services[name]
        except KeyError as exc:
            raise ManifestValidationError("Plugin requested a non-public service") from exc
        if name in {"engine.routing", "engine.api", "engine.rendering", "engine.observability", "application.admin"}:
            value = value.for_plugin(self.plugin_id)  # type: ignore[attr-defined]
        if not isinstance(value, expected_type):
            raise ManifestValidationError("Plugin public service has an unexpected type")
        return value


class _BoundRuntime:
    def __init__(self, runtime: PluginRuntime, context: PluginContext) -> None:
        self.runtime = runtime
        self.context = context
    def register(self) -> None: self.runtime.register(self.context)
    def activate(self) -> None: self.runtime.activate()
    def deactivate(self) -> None: self.runtime.deactivate()
    def unregister(self) -> None: self.runtime.unregister()


class PluginEngine:
    engine_id = "plugins"
    dependencies = ("settings", "content", "media", "search", "localization", "menu", "seo")
    _PUBLIC_SERVICES = (
        "engine.settings", "engine.content", "engine.media", "engine.search",
        "engine.localization", "engine.menu", "engine.seo", "engine.events",
        "engine.queue", "engine.notifications", "engine.permissions",
    )

    def __init__(self, root: Path = Path("plugins")) -> None:
        self._root = root
        self._manager: ExtensionManager | None = None
        self._public_services: dict[str, object] = {}
        self._services: Mapping[str, object] = MappingProxyType(self._public_services)
        self._bound: set[str] = set()
        self._grants: dict[str, frozenset[str]] = {}
        self._packages: dict[str, Path] = {}
        self.discovery_failures: tuple[str, ...] = ()
        self.ready = False

    def initialize(self, container: ServiceContainer) -> None:
        self._manager = container.resolve("core.extensions", ExtensionManager)
        services: dict[str, object] = {}
        for name in self._PUBLIC_SERVICES:
            try: services[name] = container.resolve(name)
            except Exception: continue
        self._public_services.update(services)
        container.register("engine.plugins", self)

    def start(self) -> None:
        failures: list[str] = []
        if self._root.exists():
            for item in ExtensionDiscovery().discover(self._root, ExtensionType.PLUGIN):
                try:
                    self._manager_required().register(item.manifest)
                    self._packages[item.manifest.id] = item.path
                except ManifestValidationError: failures.append(item.manifest.id)
        self.discovery_failures = tuple(failures)
        self.ready = True

    def shutdown(self) -> None:
        self._manager_required().disable_all(ExtensionType.PLUGIN.value)
        self.ready = False

    def bind(self, extension_id: str, runtime: PluginRuntime,
             *, granted_permissions: frozenset[str] = frozenset()) -> None:
        manifest = self._plugin_manifest(extension_id)
        if not set(manifest.permissions).issubset(granted_permissions):
            raise ManifestValidationError("Plugin permissions were not granted")
        context = PluginContext(extension_id, granted_permissions, self._services)
        self._manager_required().attach_runtime(extension_id, _BoundRuntime(runtime, context))
        self._bound.add(extension_id)
        self._grants[extension_id] = frozenset(granted_permissions)

    def bind_declarative(self, extension_id: str,
                         *, granted_permissions: frozenset[str]) -> None:
        """Bind a validated data-only first-party package without importing package code."""
        if extension_id in self._bound:
            return
        try:
            package = self._packages[extension_id]
        except KeyError as exc:
            raise ManifestValidationError("Plugin package is unavailable") from exc
        from backend.engines.plugins.first_party import load_first_party_runtime
        self.bind(extension_id, load_first_party_runtime(package, extension_id),
                  granted_permissions=granted_permissions)

    def install_declarative_package(self, manifest: ExtensionManifest, package: Path) -> None:
        """Register an already validated data-only package; never import package code."""
        if manifest.type is not ExtensionType.PLUGIN:
            raise ManifestValidationError("Extension is not a Plugin")
        self._manager_required().register(manifest)
        self._packages[manifest.id] = package

    def bind_uploaded_declarative(self, extension_id: str, *, granted_permissions: frozenset[str]) -> None:
        if extension_id in self._bound: return
        self.bind(extension_id, _DeclarativeUploadedRuntime(), granted_permissions=granted_permissions)

    def uninstall(self, extension_id: str) -> None:
        if self._manager_required().state(extension_id) is ExtensionState.ENABLED:
            raise ManifestValidationError("An active Plugin cannot be uninstalled")
        self._cleanup_phase7(extension_id)
        self._manager_required().remove(extension_id)
        self._packages.pop(extension_id, None); self._bound.discard(extension_id); self._grants.pop(extension_id, None)

    def update_uploaded_declarative(self, extension_id: str, manifest: ExtensionManifest, package: Path,
                                    *, granted_permissions: frozenset[str]) -> bool:
        if manifest.type is not ExtensionType.PLUGIN or not set(manifest.permissions).issubset(granted_permissions):
            return False
        context = PluginContext(extension_id, granted_permissions, self._services)
        result = self._manager_required().replace(extension_id, manifest, _BoundRuntime(_DeclarativeUploadedRuntime(), context))
        if result:
            self._packages[extension_id] = package; self._bound.add(extension_id); self._grants[extension_id] = granted_permissions
        return result

    def is_bound(self, extension_id: str) -> bool:
        self._plugin_manifest(extension_id)
        return extension_id in self._bound

    def granted_permissions(self, extension_id: str) -> tuple[str, ...]:
        """Return reviewed capabilities without exposing the private runtime context."""
        self._plugin_manifest(extension_id)
        return tuple(sorted(self._grants.get(extension_id, frozenset())))

    def publish_phase_service(self, name: str, service: object) -> None:
        """Publish only the documented late-bound Phase 7 extension contracts."""
        if name not in {"engine.routing", "engine.api", "engine.rendering", "engine.observability", "application.admin"}:
            raise ManifestValidationError("Service is not an approved Plugin extension contract")
        if name in self._public_services:
            raise ManifestValidationError("Plugin extension contract is already published")
        self._public_services[name] = service

    def activate(self, extension_id: str) -> bool:
        self._plugin_manifest(extension_id)
        if extension_id not in self._bound:
            raise ManifestValidationError("Plugin runtime is not explicitly registered")
        for identifier in self._manager_required().activation_order():
            if identifier == extension_id or identifier in self._plugin_manifest(extension_id).dependencies:
                if identifier not in self._bound or not self._manager_required().enable(identifier):
                    self._cleanup_phase7(extension_id)
                    return False
        return self._manager_required().state(extension_id) is ExtensionState.ENABLED

    def deactivate(self, extension_id: str) -> bool:
        self._plugin_manifest(extension_id)
        result = self._manager_required().disable(extension_id)
        if result: self._cleanup_phase7(extension_id)
        return result

    def manifest(self, extension_id: str) -> ExtensionManifest:
        """Return validated public Plugin metadata without exposing the manager."""
        return self._plugin_manifest(extension_id)

    def update(self, extension_id: str, manifest: ExtensionManifest, runtime: PluginRuntime,
               *, granted_permissions: frozenset[str] = frozenset()) -> bool:
        if manifest.type is not ExtensionType.PLUGIN or not set(manifest.permissions).issubset(granted_permissions):
            return False
        context = PluginContext(extension_id, granted_permissions, self._services)
        result = self._manager_required().replace(extension_id, manifest, _BoundRuntime(runtime, context))
        if result:
            self._bound.add(extension_id); self._grants[extension_id] = frozenset(granted_permissions)
        return result

    def _plugin_manifest(self, extension_id: str) -> ExtensionManifest:
        manifest = self._manager_required().manifest(extension_id)
        if manifest.type is not ExtensionType.PLUGIN:
            raise ManifestValidationError("Extension is not a Plugin")
        return manifest

    def _manager_required(self) -> ExtensionManager:
        if self._manager is None: raise RuntimeError("Plugin Engine is not initialized")
        return self._manager

    def _cleanup_phase7(self, owner: str) -> None:
        for name in ("engine.observability", "application.admin", "engine.api", "engine.rendering", "engine.routing"):
            service = self._public_services.get(name)
            if service is not None:
                service.unregister_owner(owner)  # type: ignore[attr-defined]


class _DeclarativeUploadedRuntime:
    """No-code runtime for uploaded declarative Plugin packages."""
    def register(self, context: PluginContext) -> None: self._context = context
    def activate(self) -> None: pass
    def deactivate(self) -> None: pass
    def unregister(self) -> None: pass
