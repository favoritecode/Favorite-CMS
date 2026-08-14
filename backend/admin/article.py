"""Canonical article validation and sanitization for Admin and public rendering."""
from __future__ import annotations

from html.parser import HTMLParser
import unicodedata

import nh3


ARTICLE_TAGS = {
    "p", "h1", "h2", "h3", "strong", "em", "u", "s", "a", "img",
    "ul", "ol", "li", "blockquote", "pre", "code", "hr", "br",
}
_CLEANER = nh3.Cleaner(
    tags=ARTICLE_TAGS,
    clean_content_tags={"script", "style", "iframe", "object", "embed", "template", "svg", "math"},
    attributes={
        "a": {"href", "title"},
        "img": {"src", "alt", "title", "width", "height"},
        "p": {"style"}, "h1": {"style"}, "h2": {"style"}, "h3": {"style"},
    },
    tag_attribute_values={"a": {"target": {"_blank"}}},
    url_schemes={"http", "https", "mailto"},
    url_relative="deny",
    filter_style_properties={"text-align"},
    link_rel="noopener noreferrer",
    strip_comments=True,
)


def sanitize_article_html(value: str) -> str:
    return _CLEANER.clean(value.strip()).strip()


def normalize_slug(value: str) -> str:
    return unicodedata.normalize("NFKC", value.strip()).casefold()


def valid_slug(value: str) -> bool:
    if not value or len(value) > 120 or value.startswith("-") or value.endswith("-") or "--" in value:
        return False
    return all(character == "-" or unicodedata.category(character)[0] in {"L", "M", "N"}
               for character in value)


class _TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []

    def handle_data(self, data: str) -> None:
        if data.strip(): self.parts.append(data.strip())


def article_text(value: str) -> str:
    parser = _TextExtractor()
    parser.feed(sanitize_article_html(value))
    parser.close()
    return " ".join(parser.parts)
