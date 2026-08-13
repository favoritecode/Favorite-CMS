"""Generic Theme and Plugin manifest contracts from Document 008."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
import re
from types import MappingProxyType
from typing import Mapping

from packaging.specifiers import InvalidSpecifier, SpecifierSet
from packaging.version import InvalidVersion, Version


class ExtensionType(StrEnum):
    THEME = "theme"
    PLUGIN = "plugin"


class ExtensionState(StrEnum):
    NOT_INSTALLED = "not_installed"
    INSTALLED = "installed"
    ENABLED = "enabled"
    DISABLED = "disabled"
    UPDATING = "updating"
    ERROR = "error"
    UNINSTALLED = "uninstalled"


class ManifestValidationError(ValueError):
    pass


_IDENTIFIER = re.compile(r"^[a-z][a-z0-9-]*\.(?:plugin|theme)\.[a-z][a-z0-9-]*$")


@dataclass(frozen=True)
class ExtensionManifest:
    id: str
    type: ExtensionType
    name: str
    version: str
    description: str
    author: str
    license: str
    homepage: str
    repository: str
    minimum_core_version: str
    maximum_core_version: str
    dependencies: Mapping[str, str]
    optional_dependencies: Mapping[str, str]
    permissions: tuple[str, ...]

    @classmethod
    def from_mapping(cls, data: Mapping[str, object]) -> ExtensionManifest:
        required = (
            "id", "type", "name", "version", "description", "author", "license",
            "homepage", "repository", "minimumCoreVersion", "maximumCoreVersion",
        )
        missing = [key for key in required if not isinstance(data.get(key), str) or not str(data[key]).strip()]
        if missing:
            raise ManifestValidationError(f"Missing required manifest fields: {', '.join(missing)}")
        try:
            extension_type = ExtensionType(str(data["type"]))
        except ValueError as exc:
            raise ManifestValidationError("Manifest type must be plugin or theme") from exc
        identifier = str(data["id"])
        if not _IDENTIFIER.fullmatch(identifier):
            raise ManifestValidationError("Extension identifier is invalid")
        if f".{extension_type.value}." not in identifier:
            raise ManifestValidationError("Extension identifier and type do not match")
        for key in ("version", "minimumCoreVersion", "maximumCoreVersion"):
            try:
                Version(str(data[key]))
            except InvalidVersion as exc:
                raise ManifestValidationError(f"Manifest version field is invalid: {key}") from exc
        minimum = Version(str(data["minimumCoreVersion"]))
        maximum = Version(str(data["maximumCoreVersion"]))
        if minimum > maximum:
            raise ManifestValidationError("Minimum Core version exceeds maximum Core version")

        dependencies = _dependencies(data.get("dependencies"), "dependencies")
        optional = _dependencies(data.get("optionalDependencies"), "optionalDependencies")
        raw_permissions = data.get("permissions", [])
        if not isinstance(raw_permissions, list) or any(
            not isinstance(item, str) or not item.strip() for item in raw_permissions
        ):
            raise ManifestValidationError("Manifest permissions must be an array of identifiers")
        permissions = tuple(dict.fromkeys(str(item).strip() for item in raw_permissions))
        if identifier in dependencies or identifier in optional:
            raise ManifestValidationError("An extension cannot depend on itself")
        return cls(
            id=identifier,
            type=extension_type,
            name=str(data["name"]),
            version=str(data["version"]),
            description=str(data["description"]),
            author=str(data["author"]),
            license=str(data["license"]),
            homepage=str(data["homepage"]),
            repository=str(data["repository"]),
            minimum_core_version=str(data["minimumCoreVersion"]),
            maximum_core_version=str(data["maximumCoreVersion"]),
            dependencies=MappingProxyType(dict(dependencies)),
            optional_dependencies=MappingProxyType(dict(optional)),
            permissions=permissions,
        )

    def supports_core(self, core_version: str) -> bool:
        version = Version(core_version)
        return Version(self.minimum_core_version) <= version <= Version(self.maximum_core_version)


def _dependencies(value: object, field: str) -> Mapping[str, str]:
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise ManifestValidationError(f"Manifest field must be an object: {field}")
    result: dict[str, str] = {}
    for identifier, constraint in value.items():
        if not isinstance(identifier, str) or not _IDENTIFIER.fullmatch(identifier):
            raise ManifestValidationError(f"Dependency identifier is invalid: {field}")
        if not isinstance(constraint, str):
            raise ManifestValidationError(f"Dependency version constraint is invalid: {identifier}")
        try:
            SpecifierSet(constraint)
        except InvalidSpecifier as exc:
            raise ManifestValidationError(f"Dependency version constraint is invalid: {identifier}") from exc
        result[identifier] = constraint
    return result
