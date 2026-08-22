"""Bounded Blogger Atom export parsing for the Content-owned import workflow."""
from __future__ import annotations

from dataclasses import dataclass
import re
from urllib.parse import unquote, urlsplit
from xml.etree import ElementTree

from backend.admin.article import normalize_slug, sanitize_article_html, valid_slug
from backend.engines.api import APIValidationError


MAX_BLOGGER_EXPORT_BYTES = 25_000_000
MAX_BLOGGER_ENTRIES = 5_000
MAX_CONTENT_BODY_CHARACTERS = 2_000_000
MAX_IMPORTED_BODY_CHARACTERS = 50_000_000
_UNSAFE_XML = re.compile(br"<!\s*(?:DOCTYPE|ENTITY)", re.IGNORECASE)


@dataclass(frozen=True)
class BloggerEntry:
    type_id: str
    title: str
    slug: str
    body: str
    labels: tuple[str, ...]
    published: bool


def parse_blogger_export(value: object) -> tuple[tuple[BloggerEntry, ...], int]:
    if not isinstance(value, str):
        raise APIValidationError("Blogger export must be UTF-8 XML text")
    payload = value.encode("utf-8")
    if not payload or len(payload) > MAX_BLOGGER_EXPORT_BYTES:
        raise APIValidationError("Blogger export must be between 1 byte and 25 MB")
    if _UNSAFE_XML.search(payload):
        raise APIValidationError("Blogger export contains unsupported XML declarations")
    try:
        root = ElementTree.fromstring(payload)
    except ElementTree.ParseError as exc:
        raise APIValidationError("Blogger export XML is malformed") from exc

    entries: list[BloggerEntry] = []
    ignored = 0
    total_body = 0
    for node in (item for item in root.iter() if _local(item.tag) == "entry"):
        kind = _entry_kind(node)
        if kind not in {"post", "page"}:
            ignored += 1
            continue
        if len(entries) >= MAX_BLOGGER_ENTRIES:
            raise APIValidationError("Blogger export contains more than 5,000 posts/pages")
        title = _child_text(node, "title").strip() or f"Untitled Blogger {kind}"
        if len(title) > 500:
            raise APIValidationError("A Blogger title exceeds 500 characters")
        body = sanitize_article_html(_child_text(node, "content"))
        if not body:
            body = "<p>Imported Blogger entry has no supported article content.</p>"
        if len(body) > MAX_CONTENT_BODY_CHARACTERS:
            raise APIValidationError(f'Blogger entry "{title[:80]}" exceeds 2,000,000 characters')
        total_body += len(body)
        if total_body > MAX_IMPORTED_BODY_CHARACTERS:
            raise APIValidationError("Blogger export contains more than 50 MB of sanitized article content")
        entries.append(BloggerEntry(
            kind, title, _entry_slug(node, title), body, _entry_labels(node), not _entry_is_draft(node),
        ))
    if not entries:
        raise APIValidationError("Blogger export contains no posts or pages")
    return tuple(entries), ignored


def unique_import_slug(preferred: str, used: set[str]) -> str:
    base = preferred[:120].rstrip("-") or "blogger-entry"
    candidate = base
    suffix = 2
    while candidate in used:
        marker = f"-{suffix}"
        candidate = f"{base[:120 - len(marker)].rstrip('-')}{marker}"
        suffix += 1
    used.add(candidate)
    return candidate


def _local(tag: object) -> str:
    return str(tag).rsplit("}", 1)[-1]


def _child_text(node: ElementTree.Element, name: str) -> str:
    child = next((item for item in node if _local(item.tag) == name), None)
    return "" if child is None else "".join(child.itertext())


def _entry_kind(node: ElementTree.Element) -> str:
    for child in node:
        if _local(child.tag) != "category":
            continue
        term = child.attrib.get("term", "")
        if term.endswith("#post"): return "post"
        if term.endswith("#page"): return "page"
    return ""


def _entry_slug(node: ElementTree.Element, title: str) -> str:
    for child in node:
        if _local(child.tag) != "link" or child.attrib.get("rel") != "alternate":
            continue
        path = urlsplit(child.attrib.get("href", "")).path.rstrip("/")
        value = unquote(path.rsplit("/", 1)[-1])
        if value.casefold().endswith(".html"): value = value[:-5]
        normalized = normalize_slug(value)
        if valid_slug(normalized): return normalized
    fallback = re.sub(r"[^\w]+", "-", normalize_slug(title), flags=re.UNICODE).strip("-")[:120]
    return fallback if valid_slug(fallback) else "blogger-entry"


def _entry_labels(node: ElementTree.Element) -> tuple[str, ...]:
    values: list[str] = []
    for child in node:
        if _local(child.tag) != "category": continue
        term = " ".join(child.attrib.get("term", "").split()).strip()
        if not term or term.startswith("http://schemas.google.com/blogger/"): continue
        if len(term) > 40 or term.casefold() in {item.casefold() for item in values}: continue
        values.append(term)
        if len(values) == 20: break
    return tuple(values)


def _entry_is_draft(node: ElementTree.Element) -> bool:
    for child in node.iter():
        if _local(child.tag) == "draft" and (child.text or "").strip().casefold() == "yes":
            return True
    return False
