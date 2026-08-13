"""Small validation helpers shared by platform data contracts."""

from __future__ import annotations

import json
import re
from types import MappingProxyType
from typing import Mapping


IDENTIFIER = re.compile(r"^[a-z][a-z0-9]*(?:[._-][a-z0-9]+)*$")


def identifier(value: str, label: str = "Identifier") -> str:
    normalized = value.strip()
    if len(normalized) > 255 or not IDENTIFIER.fullmatch(normalized):
        raise ValueError(f"{label} is invalid")
    return normalized


def text(value: str, label: str, *, maximum: int = 1000) -> str:
    normalized = value.strip()
    if not normalized or len(normalized) > maximum:
        raise ValueError(f"{label} is invalid")
    return normalized


def json_mapping(value: Mapping[str, object], label: str) -> Mapping[str, object]:
    copied = dict(value)
    if any(not isinstance(key, str) or not key.strip() for key in copied):
        raise ValueError(f"{label} is invalid")
    try:
        encoded = json.dumps(copied, separators=(",", ":"), sort_keys=True)
        decoded = json.loads(encoded)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{label} is invalid") from exc
    if len(encoded) > 1_000_000:
        raise ValueError(f"{label} is too large")
    return MappingProxyType(decoded)


def dump_mapping(value: Mapping[str, object]) -> str:
    return json.dumps(dict(value), separators=(",", ":"), sort_keys=True)


def load_mapping(value: str) -> Mapping[str, object]:
    decoded = json.loads(value)
    if not isinstance(decoded, dict):
        raise ValueError("Stored structured value is invalid")
    return MappingProxyType(decoded)
