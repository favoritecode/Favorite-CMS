"""Deterministic Favorite CMS distribution staging and ZIP assembly."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import stat
import tomllib
import zipfile
from pathlib import PurePosixPath

ROOT = Path(__file__).parents[1]
MANIFEST = ROOT / "distribution" / "manifest.json"
PROHIBITED_PARTS = {".git", ".github", ".venv", ".idea", ".vscode", "node_modules", ".next", "__pycache__", "tests", "test-results", ".pytest_cache", "coverage", "favorite_cms.egg-info"}
PROHIBITED_SUFFIXES = {".pyc", ".pyo", ".db", ".sqlite", ".sqlite3", ".log", ".tsbuildinfo"}
PROHIBITED_NAMES = {".env", ".env.local", ".env.production", ".DS_Store", "Thumbs.db", "playwright.config.ts"}
SENSITIVE_MARKERS = (b"correct horse battery staple", b"playwright-signing-key", b"operator@example.test", b"viewer@example.test")
PRIVATE_KEY_MARKERS = (b"-----BEGIN PRIVATE KEY-----", b"-----BEGIN RSA PRIVATE KEY-----", b"-----BEGIN OPENSSH PRIVATE KEY-----")
ENV_SECRET_KEYS = {"FAVORITE_DATABASE_URL", "FAVORITE_AUTH_JWT_SECRET"}
RUNTIME_VERSION_FILES = {
    "backend/bootstrap/application.py": 'core_version="{version}"',
    "backend/main.py": 'version="{version}"',
    "backend/operations/installation.py": 'version: str = "{version}"',
    "backend/recovery/engine.py": 'platform_version: str = "{version}"',
    "backend/update/engine.py": 'supports_core("{version}")',
}


def load_manifest() -> dict[str, object]:
    value = json.loads(MANIFEST.read_text(encoding="utf-8"))
    if not isinstance(value, dict): raise ValueError("Distribution manifest is invalid")
    python_version = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"]["version"]
    frontend_version = json.loads((ROOT / "frontend" / "package.json").read_text(encoding="utf-8"))["version"]
    if value.get("version") != python_version or frontend_version != python_version:
        raise ValueError("Distribution version metadata conflicts with the Python package version")
    _validate_runtime_versions(str(python_version))
    return value


def _validate_runtime_versions(version: str) -> None:
    for relative, expected in RUNTIME_VERSION_FILES.items():
        source = (ROOT / relative).read_text(encoding="utf-8")
        if expected.format(version=version) not in source:
            raise ValueError(f"Runtime version metadata conflicts: {relative}")


def stage(destination: Path) -> Path:
    manifest = load_manifest(); package_root = destination / f"favorite-cms-{manifest['version']}"
    if destination.exists(): shutil.rmtree(destination)
    package_root.mkdir(parents=True)
    for entry in manifest["must_ship"]:
        relative = PurePosixPath(str(entry))
        if relative.is_absolute() or not relative.parts or ".." in relative.parts:
            raise ValueError(f"Distribution input path is unsafe: {entry}")
        source = ROOT.joinpath(*relative.parts); target = package_root.joinpath(*relative.parts)
        if not source.exists(): raise FileNotFoundError(f"Required distribution input is missing: {entry}")
        _reject_source_symlinks(source)
        if source.is_dir(): shutil.copytree(source, target, ignore=_ignore)
        else: target.parent.mkdir(parents=True, exist_ok=True); shutil.copy2(source, target)
    shutil.copy2(MANIFEST, package_root / "distribution-manifest.json")
    _write_metadata(package_root, manifest)
    validate(package_root)
    return package_root


def validate(package_root: Path) -> None:
    files = tuple(path for path in package_root.rglob("*") if path.is_file())
    if not files: raise ValueError("Distribution is empty")
    for path in files:
        relative = path.relative_to(package_root)
        if path.is_symlink(): raise ValueError(f"Symlink is prohibited in distribution: {relative.as_posix()}")
        if any(part in PROHIBITED_PARTS for part in relative.parts) or path.suffix.casefold() in PROHIBITED_SUFFIXES or path.name in PROHIBITED_NAMES:
            raise ValueError(f"Prohibited distribution file: {relative.as_posix()}")
        data = path.read_bytes()
        if any(marker in data for marker in SENSITIVE_MARKERS): raise ValueError(f"Test credential marker found: {relative.as_posix()}")
        if any(marker in data for marker in PRIVATE_KEY_MARKERS): raise ValueError(f"Private key material found: {relative.as_posix()}")
        if path.name.startswith(".env"):
            _validate_environment_template(relative, data)


def _reject_source_symlinks(source: Path) -> None:
    candidates = (source,) if not source.is_dir() else (source, *source.rglob("*"))
    for candidate in candidates:
        if candidate.is_symlink():
            try:
                display = candidate.relative_to(ROOT).as_posix()
            except ValueError:
                display = candidate.name
            raise ValueError(f"Symlink is prohibited in distribution input: {display}")


def _validate_environment_template(relative: Path, data: bytes) -> None:
    try:
        lines = data.decode("utf-8").splitlines()
    except UnicodeDecodeError as exc:
        raise ValueError(f"Environment template is not UTF-8: {relative.as_posix()}") from exc
    for line in lines:
        value = line.strip()
        if not value or value.startswith("#") or "=" not in value:
            continue
        key, configured = value.split("=", 1)
        if key.strip() in ENV_SECRET_KEYS and configured.strip():
            raise ValueError(f"Populated secret configuration found: {relative.as_posix()}")


def archive(package_root: Path, output: Path) -> tuple[Path, Path]:
    output.mkdir(parents=True, exist_ok=True); zip_path = output / f"{package_root.name}.zip"
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as bundle:
        for path in sorted(package_root.rglob("*"), key=lambda item: item.relative_to(package_root.parent).as_posix()):
            if not path.is_file(): continue
            name = path.relative_to(package_root.parent).as_posix(); info = zipfile.ZipInfo(name, (1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED; info.external_attr = (stat.S_IFREG | 0o644) << 16
            bundle.writestr(info, path.read_bytes(), compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
    digest = hashlib.sha256(zip_path.read_bytes()).hexdigest(); checksum = output / f"{package_root.name}.sha256"
    checksum.write_text(f"{digest}  {zip_path.name}\n", encoding="ascii", newline="\n")
    return zip_path, checksum


def _ignore(directory: str, names: list[str]) -> set[str]:
    base = Path(directory)
    return {name for name in names if name in PROHIBITED_PARTS or name in PROHIBITED_NAMES or (base / name).suffix.casefold() in PROHIBITED_SUFFIXES}


def _write_metadata(package_root: Path, manifest: dict[str, object]) -> None:
    entries = []
    for path in sorted(package_root.rglob("*")):
        if path.is_file(): entries.append({"path": path.relative_to(package_root).as_posix(), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
    metadata = {"distribution_id": manifest["distribution_id"], "product": manifest["product"], "version": manifest["version"], "timestamp_policy": "reproducible-no-build-timestamp", "files": entries}
    (package_root / "package-metadata.json").write_text(json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(); parser.add_argument("--staging", type=Path, default=ROOT / "build" / "distribution")
    parser.add_argument("--output", type=Path, default=ROOT / "dist"); parser.add_argument("--archive", action="store_true")
    args = parser.parse_args(argv); package = stage(args.staging); print(f"Validated staging package: {package}")
    if args.archive:
        zip_path, checksum = archive(package, args.output); print(f"Archive: {zip_path}"); print(f"Checksum: {checksum}")
    return 0


if __name__ == "__main__": raise SystemExit(main())
