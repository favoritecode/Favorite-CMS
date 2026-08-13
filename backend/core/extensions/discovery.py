"""Manifest-only discovery; extension code is never imported by discovery."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path

from backend.core.extensions.manifest import ExtensionManifest, ExtensionType


@dataclass(frozen=True)
class DiscoveredExtension:
    path: Path
    manifest: ExtensionManifest


class ExtensionDiscovery:
    def discover(self, root: Path, extension_type: ExtensionType) -> tuple[DiscoveredExtension, ...]:
        resolved_root = root.resolve(strict=True)
        manifest_name = "plugin.json" if extension_type is ExtensionType.PLUGIN else "theme.json"
        discovered: list[DiscoveredExtension] = []
        for candidate in sorted(resolved_root.iterdir(), key=lambda item: item.name):
            if not candidate.is_dir() or candidate.is_symlink():
                continue
            resolved_candidate = candidate.resolve(strict=True)
            if resolved_root not in resolved_candidate.parents:
                continue
            manifest_path = resolved_candidate / manifest_name
            if not manifest_path.is_file() or manifest_path.is_symlink():
                continue
            try:
                payload = json.loads(manifest_path.read_text(encoding="utf-8"))
                if not isinstance(payload, dict):
                    continue
                manifest = ExtensionManifest.from_mapping(payload)
                if manifest.type is not extension_type:
                    continue
                discovered.append(DiscoveredExtension(resolved_candidate, manifest))
            except (OSError, UnicodeError, json.JSONDecodeError, ValueError):
                continue
        return tuple(discovered)

