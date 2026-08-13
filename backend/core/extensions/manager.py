"""Phase 1 lifecycle boundary without installation or package mutation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from packaging.specifiers import SpecifierSet
from packaging.version import Version

from backend.core.extensions.manifest import ExtensionManifest, ExtensionState, ManifestValidationError


class ExtensionRuntime(Protocol):
    def register(self) -> None: ...
    def activate(self) -> None: ...
    def deactivate(self) -> None: ...
    def unregister(self) -> None: ...


@dataclass
class _Entry:
    manifest: ExtensionManifest
    state: ExtensionState = ExtensionState.INSTALLED
    runtime: ExtensionRuntime | None = None
    failure: str | None = None


class ExtensionManager:
    def __init__(self, core_version: str) -> None:
        self._core_version = core_version
        self._entries: dict[str, _Entry] = {}

    def register(self, manifest: ExtensionManifest, runtime: ExtensionRuntime | None = None) -> None:
        if manifest.id in self._entries:
            raise ManifestValidationError(f"Duplicate extension identifier: {manifest.id}")
        if not manifest.supports_core(self._core_version):
            raise ManifestValidationError(f"Extension is incompatible with Core: {manifest.id}")
        self._entries[manifest.id] = _Entry(manifest=manifest, runtime=runtime)

    def validate_dependencies(self, extension_id: str) -> None:
        entry = self._entry(extension_id)
        for dependency_id, constraint in entry.manifest.dependencies.items():
            dependency = self._entries.get(dependency_id)
            if dependency is None:
                raise ManifestValidationError(f"Required extension dependency is missing: {dependency_id}")
            if Version(dependency.manifest.version) not in SpecifierSet(constraint):
                raise ManifestValidationError(f"Required extension dependency is incompatible: {dependency_id}")
        self._assert_acyclic(extension_id, set(), set())

    def validate_all_dependencies(self) -> None:
        for identifier in sorted(self._entries):
            if self._entries[identifier].state is not ExtensionState.UNINSTALLED:
                self.validate_dependencies(identifier)

    def attach_runtime(self, extension_id: str, runtime: ExtensionRuntime) -> None:
        entry = self._entry(extension_id)
        if entry.state is ExtensionState.ENABLED:
            raise ManifestValidationError("An enabled Extension runtime cannot be replaced")
        entry.runtime = runtime

    def uninstall(self, extension_id: str) -> None:
        entry = self._entry(extension_id)
        if entry.state is ExtensionState.ENABLED:
            raise ManifestValidationError("An enabled Extension cannot be uninstalled")
        entry.runtime = None
        entry.state = ExtensionState.UNINSTALLED
        entry.failure = None

    def enable(self, extension_id: str) -> bool:
        entry = self._entry(extension_id)
        try:
            self.validate_dependencies(extension_id)
            if entry.runtime is not None:
                _call_optional(entry.runtime, "register")
                entry.runtime.activate()
            entry.state = ExtensionState.ENABLED
            entry.failure = None
            return True
        except Exception as exc:
            if entry.runtime is not None:
                try:
                    _call_optional(entry.runtime, "unregister")
                except Exception:
                    pass
            entry.state = ExtensionState.ERROR
            entry.failure = type(exc).__name__
            return False

    def disable(self, extension_id: str) -> bool:
        entry = self._entry(extension_id)
        try:
            enabled_dependents = [item.manifest.id for item in self._entries.values()
                                  if item.state is ExtensionState.ENABLED and extension_id in item.manifest.dependencies]
            if enabled_dependents:
                raise ManifestValidationError("Enabled extensions depend on this Extension")
            if entry.runtime is not None:
                entry.runtime.deactivate()
                _call_optional(entry.runtime, "unregister")
            entry.state = ExtensionState.DISABLED
            entry.failure = None
            return True
        except Exception as exc:
            entry.state = ExtensionState.ERROR
            entry.failure = type(exc).__name__
            return False

    def enable_all(self, extension_type: str | None = None) -> tuple[str, ...]:
        enabled: list[str] = []
        for identifier in self.activation_order(extension_type):
            if self._entry(identifier).state is ExtensionState.ENABLED:
                continue
            if self.enable(identifier): enabled.append(identifier)
        return tuple(enabled)

    def disable_all(self, extension_type: str | None = None) -> tuple[str, ...]:
        disabled: list[str] = []
        for identifier in reversed(self.activation_order(extension_type)):
            if self._entry(identifier).state is ExtensionState.ENABLED and self.disable(identifier):
                disabled.append(identifier)
        return tuple(disabled)

    def activation_order(self, extension_type: str | None = None) -> tuple[str, ...]:
        result: list[str] = []
        visiting: set[str] = set()
        visited: set[str] = set()
        def visit(identifier: str) -> None:
            if identifier in visiting:
                raise ManifestValidationError("Circular extension dependency detected")
            if identifier in visited:
                return
            visiting.add(identifier)
            entry = self._entry(identifier)
            for dependency in sorted(entry.manifest.dependencies):
                if dependency not in self._entries:
                    raise ManifestValidationError(f"Required extension dependency is missing: {dependency}")
                visit(dependency)
            visiting.remove(identifier); visited.add(identifier)
            if extension_type is None or entry.manifest.type.value == extension_type: result.append(identifier)
        for identifier in sorted(self._entries): visit(identifier)
        return tuple(result)

    def replace(self, extension_id: str, manifest: ExtensionManifest,
                runtime: ExtensionRuntime | None) -> bool:
        entry = self._entry(extension_id)
        if manifest.id != extension_id or manifest.type is not entry.manifest.type or not manifest.supports_core(self._core_version):
            return False
        old_manifest, old_runtime, old_state = entry.manifest, entry.runtime, entry.state
        entry.state = ExtensionState.UPDATING
        try:
            if old_state is ExtensionState.ENABLED and old_runtime is not None:
                old_runtime.deactivate()
                _call_optional(old_runtime, "unregister")
            entry.manifest, entry.runtime = manifest, runtime
            self.validate_all_dependencies()
            if old_state is ExtensionState.ENABLED and runtime is not None:
                _call_optional(runtime, "register")
                runtime.activate()
            entry.state = old_state
            entry.failure = None
            return True
        except Exception as exc:
            try:
                if runtime is not None:
                    _call_optional(runtime, "unregister")
                entry.manifest, entry.runtime = old_manifest, old_runtime
                if old_state is ExtensionState.ENABLED and old_runtime is not None:
                    _call_optional(old_runtime, "register")
                    old_runtime.activate()
                entry.state = old_state
                entry.failure = type(exc).__name__
            except Exception:
                entry.state = ExtensionState.ERROR
                entry.failure = type(exc).__name__
            return False

    def manifest(self, extension_id: str) -> ExtensionManifest:
        return self._entry(extension_id).manifest

    def registered(self, extension_type: str | None = None) -> tuple[str, ...]:
        return tuple(sorted(identifier for identifier, entry in self._entries.items()
                            if extension_type is None or entry.manifest.type.value == extension_type))

    def state(self, extension_id: str) -> ExtensionState:
        return self._entry(extension_id).state

    def failure(self, extension_id: str) -> str | None:
        return self._entry(extension_id).failure

    def _entry(self, extension_id: str) -> _Entry:
        try:
            return self._entries[extension_id]
        except KeyError as exc:
            raise ManifestValidationError(f"Extension is not registered: {extension_id}") from exc

    def _assert_acyclic(self, identifier: str, visiting: set[str], visited: set[str]) -> None:
        if identifier in visiting:
            raise ManifestValidationError("Circular extension dependency detected")
        if identifier in visited:
            return
        visiting.add(identifier)
        entry = self._entry(identifier)
        for dependency_id in entry.manifest.dependencies:
            if dependency_id in self._entries:
                self._assert_acyclic(dependency_id, visiting, visited)
        visiting.remove(identifier)
        visited.add(identifier)


def _call_optional(runtime: ExtensionRuntime, method: str) -> None:
    callback = getattr(runtime, method, None)
    if callback is not None:
        callback()
