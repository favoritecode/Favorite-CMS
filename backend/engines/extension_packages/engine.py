"""Storage-backed, transactional local ZIP installation for declarative extensions."""
from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO
import json
from pathlib import Path, PurePosixPath
import re
from tempfile import TemporaryDirectory
from zipfile import BadZipFile, ZipFile, ZipInfo

from packaging.version import Version
from sqlalchemy import Column, MetaData, String, Table, delete, insert, select, update

from backend.core.container import ServiceContainer
from backend.core.extensions import ExtensionManager, ExtensionManifest, ExtensionState, ExtensionType, ManifestValidationError
from backend.database import DatabaseEngine
from backend.database.migrations import DatabaseMigrationEngine, Migration
from backend.engines.errors import ValidationFailure
from backend.engines.plugins import PluginEngine
from backend.engines.storage import StorageEngine, StorageReference, StorageScope
from backend.engines.themes import ThemeEngine, ThemePackage


class PackageError(ValidationFailure): pass


@dataclass(frozen=True)
class PackageResult:
    extension_id: str
    extension_type: str
    version: str
    action: str


_metadata = MetaData()
_packages = Table("favorite_extension_packages", _metadata,
    Column("extension_id", String(255), primary_key=True), Column("extension_type", String(16), nullable=False),
    Column("version", String(64), nullable=False), Column("previous_version", String(64)),
    Column("archive_identifier", String(512), nullable=False), Column("active", String(5), nullable=False, default="false"),
    Column("granted_permissions", String(4096), nullable=False, default="[]"))


def package_migration() -> Migration:
    return Migration("platform.extension_package.001", "engine.extension_packages",
                     lambda connection: _metadata.create_all(connection, tables=[_packages]))


class ExtensionPackageEngine:
    engine_id = "extension_packages"
    dependencies = ("database", "migrations", "storage", "plugins", "themes")
    maximum_archive_bytes = 5_000_000
    maximum_extracted_bytes = 20_000_000
    maximum_files = 500

    def __init__(self) -> None:
        self._database: DatabaseEngine | None = None
        self._storage: StorageEngine | None = None
        self._plugins: PluginEngine | None = None
        self._themes: ThemeEngine | None = None
        self._manager: ExtensionManager | None = None
        self._materialized: dict[str, TemporaryDirectory[str]] = {}
        self.ready = False

    def initialize(self, container: ServiceContainer) -> None:
        self._database = container.resolve("engine.database", DatabaseEngine)
        self._storage = container.resolve("engine.storage", StorageEngine)
        self._plugins = container.resolve("engine.plugins", PluginEngine)
        self._themes = container.resolve("engine.themes", ThemeEngine)
        self._manager = container.resolve("core.extensions", ExtensionManager)
        container.resolve("engine.migrations", DatabaseMigrationEngine).register(package_migration())
        container.register("engine.extension_packages", self)

    def start(self) -> None:
        self.ready = True
        try:
            with self._database_required().session() as session:
                rows = session.execute(select(_packages).order_by(_packages.c.extension_id)).mappings().all()
            for row in rows:
                reference = StorageReference(str(row["archive_identifier"]), self._scope(), self._storage_required().provider_name)
                manifest, files = self.validate(self._storage_required().retrieve(reference, scope=self._scope()),
                                                expected_type=ExtensionType(str(row["extension_type"])))
                self._register_materialized(manifest, files)
                if str(row["active"]).casefold() == "true":
                    grants = frozenset(json.loads(str(row["granted_permissions"])))
                    if manifest.type is ExtensionType.PLUGIN:
                        self._plugins_required().bind_uploaded_declarative(manifest.id, granted_permissions=grants)
                        self._plugins_required().activate(manifest.id)
                    else: self._themes_required().activate(manifest.id)
        except Exception:
            # A pre-migration boot intentionally has no package registry.
            pass

    def shutdown(self) -> None:
        for directory in self._materialized.values(): directory.cleanup()
        self._materialized.clear(); self.ready = False

    def validate(self, archive: bytes, *, expected_type: ExtensionType | None = None) -> tuple[ExtensionManifest, dict[str, bytes]]:
        if not isinstance(archive, bytes) or not archive or len(archive) > self.maximum_archive_bytes:
            raise PackageError("Extension archive is empty or exceeds the 5 MB limit")
        try:
            with ZipFile(BytesIO(archive)) as package:
                files = self._validated_files(package, package.infolist())
        except (BadZipFile, OSError, RuntimeError) as exc:
            raise PackageError("Extension archive is malformed") from exc
        names = [name for name in ("theme.json", "plugin.json") if name in files]
        if len(names) != 1: raise PackageError("Extension archive must contain one root manifest")
        try:
            payload = json.loads(files[names[0]].decode("utf-8"))
            if not isinstance(payload, dict): raise ValueError
            manifest = ExtensionManifest.from_mapping(payload)
        except (UnicodeError, json.JSONDecodeError, ValueError, ManifestValidationError) as exc:
            raise PackageError("Extension manifest is invalid") from exc
        if expected_type is not None and manifest.type is not expected_type:
            raise PackageError("Extension package type does not match the requested operation")
        if names[0] != ("theme.json" if manifest.type is ExtensionType.THEME else "plugin.json"):
            raise PackageError("Extension manifest type is inconsistent")
        self._validate_theme(files) if manifest.type is ExtensionType.THEME else self._validate_plugin(files, manifest)
        return manifest, files

    def install(self, archive: bytes, *, expected_type: ExtensionType) -> PackageResult:
        manifest, files = self.validate(archive, expected_type=expected_type)
        if manifest.id in self._manager_required().registered():
            raise PackageError("Extension is already installed; use Update for a newer package")
        directory = self._materialize(files); reference: StorageReference | None = None
        try:
            self._register(manifest, Path(directory.name)); self._manager_required().validate_dependencies(manifest.id)
            reference = self._storage_required().store(self._scope(), self._archive_id(manifest), archive)
            with self._database_required().transaction() as session:
                session.execute(insert(_packages).values(extension_id=manifest.id, extension_type=manifest.type.value,
                    version=manifest.version, previous_version=None, archive_identifier=reference.identifier,
                    active="false", granted_permissions="[]"))
            self._materialized[manifest.id] = directory
            return PackageResult(manifest.id, manifest.type.value, manifest.version, "installed")
        except Exception as exc:
            try: self._unregister(manifest)
            except Exception: pass
            if reference is not None:
                try: self._storage_required().delete(reference, scope=self._scope())
                except Exception: pass
            directory.cleanup()
            if isinstance(exc, PackageError): raise
            if isinstance(exc, ManifestValidationError):
                reason = str(exc).casefold()
                if "incompatible" in reason:
                    raise PackageError("Extension is incompatible with this Core version or its dependencies") from exc
                if "dependency" in reason:
                    raise PackageError("Extension dependencies are not satisfied") from exc
                raise PackageError("Extension manifest could not be registered") from exc
            raise PackageError("Extension installation failed safely") from exc

    def update(self, extension_id: str, archive: bytes) -> PackageResult:
        current = self._manager_required().manifest(extension_id)
        manifest, files = self.validate(archive, expected_type=current.type)
        if manifest.id != extension_id: raise PackageError("Update package identifier does not match")
        if Version(manifest.version) <= Version(current.version): raise PackageError("Update version must be newer")
        directory = self._materialize(files); old_directory = self._materialized.get(extension_id)
        if old_directory is None: directory.cleanup(); raise PackageError("Bundled extensions cannot be replaced by uploaded packages")
        grants = self._plugins_required().granted_permissions(extension_id) if current.type is ExtensionType.PLUGIN else ()
        reference: StorageReference | None = None
        try:
            # Persist the candidate first; a Storage failure cannot mutate the working runtime.
            reference = self._storage_required().store(self._scope(), self._archive_id(manifest), archive)
            if not self._replace(extension_id, manifest, Path(directory.name), frozenset(grants)):
                raise PackageError("Extension update failed; the previous version remains active")
            try:
                with self._database_required().transaction() as session:
                    session.execute(update(_packages).where(_packages.c.extension_id == extension_id).values(
                        version=manifest.version, previous_version=current.version, archive_identifier=reference.identifier))
            except Exception as exc:
                self._replace(extension_id, current, Path(old_directory.name), frozenset(grants))
                raise PackageError("Extension update persistence failed; the previous version was restored") from exc
            self._materialized[extension_id] = directory; old_directory.cleanup()
            return PackageResult(extension_id, current.type.value, manifest.version, "updated")
        except Exception:
            directory.cleanup()
            if reference is not None:
                try: self._storage_required().delete(reference, scope=self._scope())
                except Exception: pass
            raise

    def uninstall(self, extension_id: str) -> PackageResult:
        manifest = self._manager_required().manifest(extension_id)
        if extension_id == "favorite.theme.starter": raise PackageError("The bundled Starter Theme cannot be uninstalled")
        if self._manager_required().state(extension_id) is ExtensionState.ENABLED:
            raise PackageError("Deactivate the extension before uninstalling it")
        with self._database_required().session() as session:
            row = session.execute(select(_packages).where(_packages.c.extension_id == extension_id)).mappings().first()
        if row is None: raise PackageError("Bundled extensions cannot be uninstalled")
        reference = StorageReference(str(row["archive_identifier"]), self._scope(), self._storage_required().provider_name)
        directory = self._materialized.get(extension_id)
        if directory is None: raise PackageError("Installed package materialization is unavailable")
        archive = self._storage_required().retrieve(reference, scope=self._scope())
        self._unregister(manifest)
        self._materialized.pop(extension_id, None)
        try:
            self._storage_required().delete(reference, scope=self._scope())
            with self._database_required().transaction() as session:
                session.execute(delete(_packages).where(_packages.c.extension_id == extension_id))
        except Exception as exc:
            try:
                self._storage_required().store(self._scope(), reference.identifier, archive, overwrite=True)
                self._register(manifest, Path(directory.name)); self._materialized[extension_id] = directory
            except Exception: pass
            raise PackageError("Extension uninstall failed; the installed package was preserved") from exc
        directory.cleanup()
        return PackageResult(extension_id, manifest.type.value, manifest.version, "uninstalled")

    def set_lifecycle(self, extension_id: str, *, extension_type: ExtensionType, active: bool, granted_permissions: tuple[str, ...] = ()) -> None:
        """Persist uploaded-package lifecycle only after the owning Engine succeeds."""
        with self._database_required().transaction() as session:
            if extension_type is ExtensionType.THEME and active:
                session.execute(update(_packages).where(_packages.c.extension_type == ExtensionType.THEME.value).values(active="false"))
            session.execute(update(_packages).where(_packages.c.extension_id == extension_id).values(
                active="true" if active else "false", granted_permissions=json.dumps(sorted(set(granted_permissions)))))

    def managed_ids(self) -> frozenset[str]:
        """Return package-managed identifiers without exposing archive or Storage details."""
        with self._database_required().session() as session:
            values = session.execute(select(_packages.c.extension_id)).scalars().all()
        return frozenset(str(value) for value in values)

    def _validated_files(self, package: ZipFile, infos: list[ZipInfo]) -> dict[str, bytes]:
        if len(infos) > self.maximum_files: raise PackageError("Extension archive contains too many files")
        files: dict[str, bytes] = {}; seen: set[str] = set(); total = 0
        for info in infos:
            name = info.filename.replace("\\", "/"); path = PurePosixPath(name)
            if not name or path.is_absolute() or ".." in path.parts or ":" in path.parts[0] or name.startswith("/"):
                raise PackageError("Extension archive contains an unsafe path")
            normalized = path.as_posix().rstrip("/"); key = normalized.casefold()
            if key in seen: raise PackageError("Extension archive contains duplicate or conflicting paths")
            seen.add(key); mode = info.external_attr >> 16
            if mode and (mode & 0o170000) not in (0, 0o100000, 0o040000):
                raise PackageError("Extension archive contains an unsupported link or special file")
            if info.is_dir(): continue
            total += info.file_size
            if total > self.maximum_extracted_bytes: raise PackageError("Extension extracted content exceeds the 20 MB limit")
            files[normalized] = package.read(info)
        return files

    def _validate_theme(self, files: dict[str, bytes]) -> None:
        if "resources.json" not in files: raise PackageError("Theme resource catalogue is required")
        try: catalogue = json.loads(files["resources.json"].decode("utf-8"))
        except Exception as exc: raise PackageError("Theme resource catalogue is invalid") from exc
        keys = {"templates", "layouts", "components", "widgets", "assets"}
        if not isinstance(catalogue, dict) or set(catalogue) != keys: raise PackageError("Theme resource catalogue is invalid")
        declared: set[str] = set()
        for values in catalogue.values():
            if not isinstance(values, list) or any(not isinstance(item, str) for item in values): raise PackageError("Theme resource catalogue is invalid")
            declared.update(values)
        required = {"templates/page.html", "layouts/base.html", "components/header.html", "components/footer.html", "assets/starter.css"}
        if not required.issubset(declared): raise PackageError("Theme package is missing required public presentation resources")
        if any(item not in files for item in declared): raise PackageError("Theme declared resource is missing")
        if set(files) != {"theme.json", "resources.json", *declared}: raise PackageError("Theme package contains undeclared files")
        for name in declared:
            try: text = files[name].decode("utf-8")
            except UnicodeError as exc: raise PackageError("Theme resources must be UTF-8 text") from exc
            lowered = text.casefold()
            if name.endswith(".html") and (re.search(r"<\s*(script|iframe|object|embed)\b", lowered) or
                                             re.search(r"\bon[a-z]+\s*=", lowered) or "javascript:" in lowered):
                raise PackageError("Theme resources cannot contain executable browser content")
            if name.endswith(".css") and ("@import" in lowered or "expression(" in lowered or
                                            re.search(r"url\s*\(\s*['\"]?\s*(https?:|//|javascript:)", lowered)):
                raise PackageError("Theme styles cannot load or execute external content")

    def _validate_plugin(self, files: dict[str, bytes], manifest: ExtensionManifest) -> None:
        dangerous = {".py", ".pyc", ".pyd", ".so", ".dll", ".exe", ".js", ".mjs", ".cjs", ".sh", ".bat", ".cmd", ".ps1"}
        if any(PurePosixPath(name).suffix.casefold() in dangerous for name in files):
            raise PackageError("Uploaded Plugins must be declarative and cannot contain executable code")
        if set(files) - {"plugin.json", "contributions.json", "README.md", "LICENSE", "LICENSE.txt"}:
            raise PackageError("Plugin package contains unsupported files")
        if "contributions.json" in files:
            try: value = json.loads(files["contributions.json"].decode("utf-8"))
            except Exception as exc: raise PackageError("Plugin contributions are invalid") from exc
            if value == {"contributions": []}: return
            keys = {"schemaVersion", "permissions", "entities", "tools", "blocks"}
            if (not isinstance(value, dict) or set(value) != keys or value.get("schemaVersion") != 1
                    or any(not isinstance(value.get(key), list) for key in keys - {"schemaVersion"})
                    or len(value["permissions"]) > 100 or len(value["entities"]) > 50 or len(value["tools"]) > 50
                    or value["blocks"]):
                raise PackageError("Plugin contributions are invalid")
            required = set()
            if value["permissions"]: required.add("permission.register")
            if value["entities"]: required.add("domain.register")
            if value["tools"]: required.add("tool.register")
            if not required.issubset(set(manifest.permissions)):
                raise PackageError("Plugin manifest is missing required contribution capabilities")
            if any(not isinstance(item, dict) for key in ("permissions", "entities", "tools") for item in value[key]):
                raise PackageError("Plugin contributions are invalid")

    def _materialize(self, files: dict[str, bytes]) -> TemporaryDirectory[str]:
        directory = TemporaryDirectory(prefix="favorite-extension-"); root = Path(directory.name)
        for name, data in files.items():
            target = root.joinpath(*PurePosixPath(name).parts); target.parent.mkdir(parents=True, exist_ok=True); target.write_bytes(data)
        return directory

    def _register_materialized(self, manifest: ExtensionManifest, files: dict[str, bytes]) -> None:
        directory = self._materialize(files); self._register(manifest, Path(directory.name)); self._materialized[manifest.id] = directory
    def _register(self, manifest: ExtensionManifest, root: Path) -> None:
        if manifest.type is ExtensionType.THEME: self._themes_required().install_package(manifest, self._theme_package(root))
        else: self._plugins_required().install_declarative_package(manifest, root)
    def _replace(self, extension_id: str, manifest: ExtensionManifest, root: Path, grants: frozenset[str]) -> bool:
        return (self._themes_required().update(extension_id, manifest, self._theme_package(root), _ThemeRuntime())
                if manifest.type is ExtensionType.THEME else
                self._plugins_required().update_uploaded_declarative(extension_id, manifest, root, granted_permissions=grants))
    def _unregister(self, manifest: ExtensionManifest) -> None:
        self._themes_required().uninstall(manifest.id) if manifest.type is ExtensionType.THEME else self._plugins_required().uninstall(manifest.id)
    def _theme_package(self, root: Path) -> ThemePackage:
        value = json.loads((root / "resources.json").read_text(encoding="utf-8"))
        return ThemePackage(root, **{key: tuple(items) for key, items in value.items()})
    def _scope(self) -> StorageScope: return StorageScope("packages", "extensions")
    def _archive_id(self, manifest: ExtensionManifest) -> str: return f"{manifest.type.value}/{manifest.id}/{manifest.version}.zip"
    def _database_required(self) -> DatabaseEngine:
        if self._database is None: raise PackageError("Package persistence is unavailable")
        return self._database
    def _storage_required(self) -> StorageEngine:
        if self._storage is None: raise PackageError("Package Storage is unavailable")
        return self._storage
    def _plugins_required(self) -> PluginEngine:
        if self._plugins is None: raise PackageError("Plugin Engine is unavailable")
        return self._plugins
    def _themes_required(self) -> ThemeEngine:
        if self._themes is None: raise PackageError("Theme Engine is unavailable")
        return self._themes
    def _manager_required(self) -> ExtensionManager:
        if self._manager is None: raise PackageError("Extension lifecycle is unavailable")
        return self._manager


class _ThemeRuntime:
    def activate(self) -> None: pass
    def deactivate(self) -> None: pass
