"""Provider-neutral Locale and Translation Resource resolution."""

from __future__ import annotations

from dataclasses import dataclass
import re
from types import MappingProxyType
from typing import Mapping

from backend.core.container import ServiceContainer
from backend.engines.data_contracts import identifier, text
from backend.engines.errors import ApplicationFailure, ValidationFailure


class LocalizationError(ApplicationFailure): pass
class InvalidLocalization(ValidationFailure): pass

_locale_id = re.compile(r"^[a-z]{2,3}(?:-[A-Z][a-z]{3})?(?:-[A-Z]{2}|-[0-9]{3})?$")
_key = re.compile(r"^[a-z][a-z0-9]*(?:\.[a-z][a-z0-9_-]*)+$")


@dataclass(frozen=True)
class Language:
    language_id: str
    display_name: str
    native_name: str
    direction: str = "ltr"
    enabled: bool = True
    def __post_init__(self) -> None:
        if not re.fullmatch(r"[a-z]{2,3}", self.language_id) or self.direction not in {"ltr", "rtl"}:
            raise InvalidLocalization("Language is invalid")
        text(self.display_name, "Language name", maximum=100); text(self.native_name, "Native language name", maximum=100)


@dataclass(frozen=True)
class Locale:
    locale_id: str
    language_id: str
    enabled: bool = True
    def __post_init__(self) -> None:
        if not _locale_id.fullmatch(self.locale_id) or not re.fullmatch(r"[a-z]{2,3}", self.language_id):
            raise InvalidLocalization("Locale is invalid")


@dataclass(frozen=True)
class TranslationResource:
    owner: str
    namespace: str
    locale_id: str
    entries: Mapping[str, str]
    def __post_init__(self) -> None:
        identifier(self.owner, "Translation owner"); identifier(self.namespace, "Translation namespace")
        if not _locale_id.fullmatch(self.locale_id) or not self.entries: raise InvalidLocalization("Translation Resource is invalid")
        normalized: dict[str, str] = {}
        for key, value in self.entries.items():
            if not _key.fullmatch(key): raise InvalidLocalization("Translation Key is invalid")
            normalized[key] = text(value, "Translation Value", maximum=10_000)
        object.__setattr__(self, "entries", MappingProxyType(normalized))


@dataclass(frozen=True)
class LocaleResolution:
    explicit: str | None = None
    user: str | None = None
    client: str | None = None
    site: str | None = None
    precedence: tuple[str, ...] = ("explicit", "user", "client", "site", "default")
    def __post_init__(self) -> None:
        allowed = {"explicit", "user", "client", "site", "default"}
        if set(self.precedence) != allowed or len(self.precedence) != len(allowed):
            raise InvalidLocalization("Locale precedence is invalid")


@dataclass(frozen=True)
class TranslationResult:
    resolved: bool
    value: str | None
    locale_id: str | None
    fallback_used: bool


class LocalizationEngine:
    engine_id = "localization"
    dependencies: tuple[str, ...] = ()
    def __init__(self) -> None:
        self._languages: dict[str, Language] = {}; self._locales: dict[str, Locale] = {}
        self._resources: dict[tuple[str, str, str], TranslationResource] = {}
        self._default_locale: str | None = None; self.ready = False
    def initialize(self, container: ServiceContainer) -> None: container.register("engine.localization", self)
    def start(self) -> None: self.ready = True
    def shutdown(self) -> None: self.ready = False
    def register_language(self, language: Language) -> None:
        if language.language_id in self._languages: raise InvalidLocalization("Language is already registered")
        self._languages[language.language_id] = language
    def register_locale(self, locale: Locale) -> None:
        language = self._languages.get(locale.language_id)
        if language is None or not language.enabled: raise InvalidLocalization("Locale Language is unavailable")
        if locale.locale_id in self._locales: raise InvalidLocalization("Locale is already registered")
        self._locales[locale.locale_id] = locale
    def set_default(self, locale_id: str) -> None:
        self._require_locale(locale_id); self._default_locale = locale_id
    def resolve_locale(self, request: LocaleResolution) -> str:
        candidates = {"explicit": request.explicit, "user": request.user, "client": request.client,
                      "site": request.site, "default": self._default_locale}
        if any(value is not None and not _locale_id.fullmatch(value) for value in candidates.values()):
            raise InvalidLocalization("Locale input is invalid")
        for source in request.precedence:
            value = candidates[source]
            if value is not None and value in self._locales and self._locales[value].enabled: return value
        raise LocalizationError("No supported Locale could be resolved")
    def register_translations(self, resource: TranslationResource) -> None:
        self._require_locale(resource.locale_id); key = (resource.owner, resource.namespace, resource.locale_id)
        if key in self._resources: raise InvalidLocalization("Translation Resource conflicts with an existing Resource")
        self._resources[key] = resource
    def update_translations(self, resource: TranslationResource) -> None:
        self._require_locale(resource.locale_id); key = (resource.owner, resource.namespace, resource.locale_id)
        if key not in self._resources: raise InvalidLocalization("Translation Resource is not registered")
        self._resources[key] = resource
    def translate(self, *, owner: str, namespace: str, key: str, locale_id: str,
                  fallback_locales: tuple[str, ...] = ()) -> TranslationResult:
        identifier(owner, "Translation owner"); identifier(namespace, "Translation namespace")
        if not _key.fullmatch(key): raise InvalidLocalization("Translation Key is invalid")
        self._require_locale(locale_id)
        chain = (locale_id,) + fallback_locales
        if len(chain) != len(set(chain)): raise InvalidLocalization("Translation fallback is invalid")
        for index, locale in enumerate(chain):
            self._require_locale(locale); resource = self._resources.get((owner, namespace, locale))
            if resource is not None and key in resource.entries:
                return TranslationResult(True, resource.entries[key], locale, index > 0)
        return TranslationResult(False, None, None, False)
    def _require_locale(self, locale_id: str) -> Locale:
        locale = self._locales.get(locale_id)
        if locale is None or not locale.enabled: raise InvalidLocalization("Locale is unsupported")
        return locale
