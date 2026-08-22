"""Plugin lifecycle host. Discovery never imports executable code."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Mapping, Protocol, TypeVar
import json

from backend.core.container import ServiceContainer
from backend.core.extensions import ExtensionDiscovery, ExtensionManager, ExtensionManifest, ExtensionState, ExtensionType, ManifestValidationError


class PluginRuntime(Protocol):
    def register(self, context: "PluginContext") -> None: ...
    def activate(self) -> None: ...
    def deactivate(self) -> None: ...
    def unregister(self) -> None: ...


T = TypeVar("T")
_SERVICE_CAPABILITIES = {
    "engine.settings": "settings.access", "engine.content": "content.read", "engine.media": "media.read",
    "engine.search": "search.read", "engine.localization": "localization.read", "engine.menu": "menu.read",
    "engine.seo": "seo.register", "engine.events": "events.access", "engine.queue": "queue.submit",
    "engine.notifications": "notification.send", "engine.permissions": "permission.register",
    "engine.domains": "domain.register", "engine.tools": "tool.register", "engine.routing": "routing.register",
    "engine.api": "api.register", "engine.rendering": "rendering.register", "engine.observability": "health.register",
    "application.admin": "admin.register",
}


@dataclass(frozen=True)
class PluginContext:
    plugin_id: str
    permissions: frozenset[str]
    _services: Mapping[str, object]

    def service(self, name: str, expected_type: type[T]) -> T:
        capability = _SERVICE_CAPABILITIES.get(name)
        if capability is not None and capability not in self.permissions:
            raise ManifestValidationError("Plugin capability was not granted")
        try:
            value = self._services[name]
        except KeyError as exc:
            raise ManifestValidationError("Plugin requested a non-public service") from exc
        if name in {"engine.routing", "engine.api", "engine.rendering", "engine.observability", "engine.domains", "engine.tools", "engine.permissions", "application.admin"}:
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
    dependencies = ("settings", "content", "domains", "tools", "media", "search", "localization", "menu", "seo")
    _PUBLIC_SERVICES = (
        "engine.settings", "engine.content", "engine.media", "engine.search",
        "engine.localization", "engine.menu", "engine.seo", "engine.domains", "engine.tools", "engine.events",
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
        try: runtime = load_first_party_runtime(package, extension_id)
        except ManifestValidationError: runtime = _DeclarativeUploadedRuntime(package, extension_id)
        self.bind(extension_id, runtime, granted_permissions=granted_permissions)

    def install_declarative_package(self, manifest: ExtensionManifest, package: Path) -> None:
        """Register an already validated data-only package; never import package code."""
        if manifest.type is not ExtensionType.PLUGIN:
            raise ManifestValidationError("Extension is not a Plugin")
        self._manager_required().register(manifest)
        self._packages[manifest.id] = package

    def bind_uploaded_declarative(self, extension_id: str, *, granted_permissions: frozenset[str]) -> None:
        if extension_id in self._bound: return
        try: package = self._packages[extension_id]
        except KeyError as exc: raise ManifestValidationError("Plugin package is unavailable") from exc
        self.bind(extension_id, _DeclarativeUploadedRuntime(package, extension_id), granted_permissions=granted_permissions)

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
        result = self._manager_required().replace(
            extension_id,
            manifest,
            _BoundRuntime(_DeclarativeUploadedRuntime(package, extension_id), context),
        )
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
        domains = self._public_services.get("engine.domains")
        if domains is not None: domains.unregister_owner(owner)  # type: ignore[attr-defined]
        tools = self._public_services.get("engine.tools")
        if tools is not None: tools.unregister_owner(owner)  # type: ignore[attr-defined]
        permissions = self._public_services.get("engine.permissions")
        if permissions is not None: permissions.unregister_owner(owner)  # type: ignore[attr-defined]
        for name in ("engine.observability", "application.admin", "engine.api", "engine.rendering", "engine.routing"):
            service = self._public_services.get(name)
            if service is not None:
                service.unregister_owner(owner)  # type: ignore[attr-defined]


class _DeclarativeUploadedRuntime:
    """No-code runtime for uploaded declarative Domain/Tool Plugin packages."""
    def __init__(self, package: Path, plugin_id: str) -> None: self._package = package; self._plugin_id = plugin_id
    def register(self, context: PluginContext) -> None:
        from backend.engines.domains import DomainEntityContract, DomainField, DomainFieldKind, PluginDomains
        from backend.engines.permissions import PermissionDefinition, PluginPermissions
        from backend.engines.tools import PluginTools, ToolContract, ToolFieldKind, ToolInputField
        path = self._package / "contributions.json"
        if not path.exists(): return
        try: value = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc: raise ManifestValidationError("Plugin contributions are invalid") from exc
        if value == {"contributions": []}: return
        if not isinstance(value, dict) or set(value) != {"schemaVersion", "permissions", "entities", "tools", "blocks"} or value["schemaVersion"] != 1:
            raise ManifestValidationError("Plugin contributions are invalid")
        if not all(isinstance(value[key], list) for key in ("permissions", "entities", "tools", "blocks")) or value["blocks"]:
            raise ManifestValidationError("Plugin contributions are invalid")
        try:
            if value["permissions"]:
                permissions = context.service("engine.permissions", PluginPermissions)
                for item in value["permissions"]:
                    permissions.register(PermissionDefinition(str(item["id"]), self._plugin_id, str(item["action"]), str(item["resource"]),
                        allow_owner=bool(item.get("allowOwner", False)), allow_public=bool(item.get("allowPublic", False))))
            if value["entities"]:
                domains = context.service("engine.domains", PluginDomains)
                for item in value["entities"]:
                    fields = tuple(DomainField(str(field["id"]), DomainFieldKind(str(field["type"])), bool(field.get("required", False)),
                        int(field["maxLength"]) if "maxLength" in field else None, tuple(str(choice) for choice in field.get("choices", []))) for field in item["fields"])
                    domains.register(DomainEntityContract(str(item["id"]), self._plugin_id, str(item["label"]), fields,
                        {key: str(permission) for key, permission in item["permissions"].items()}))
            if value["tools"]:
                tools = context.service("engine.tools", PluginTools)
                for item in value["tools"]:
                    fields = tuple(ToolInputField(str(field["id"]), ToolFieldKind(str(field["type"])), bool(field.get("required", False)),
                        int(field["maxLength"]) if "maxLength" in field else None, tuple(str(choice) for choice in field.get("choices", []))) for field in item["fields"])
                    tools.register(ToolContract(str(item["id"]), self._plugin_id, str(item["label"]), str(item.get("description", "")), fields,
                        str(item["executePermission"]), str(item.get("worker", "default")), bool(item.get("public", False))))
        except (KeyError, TypeError, ValueError) as exc: raise ManifestValidationError("Plugin contributions are invalid") from exc
    def activate(self) -> None: pass
    def deactivate(self) -> None: pass
    def unregister(self) -> None: pass
