import pytest

from backend.core import Kernel
from backend.engines.localization import Language, Locale, LocaleResolution, LocalizationEngine, TranslationResource
from backend.engines.localization.engine import InvalidLocalization


def _configured(kernel: Kernel) -> LocalizationEngine:
    engine = kernel.container.resolve("engine.localization", LocalizationEngine)
    engine.register_language(Language("eng", "Test English", "Test English")); engine.register_language(Language("bn", "Bangla", "বাংলা"))
    engine.register_locale(Locale("en-US", "eng")); engine.register_locale(Locale("bn-BD", "bn"))
    return engine


def test_explicit_locale_precedence_translation_and_fallback(data_kernel: Kernel) -> None:
    engine = _configured(data_kernel)
    engine.register_translations(TranslationResource("engine.content", "public", "en-US", {"content.title": "Title"}))
    engine.register_translations(TranslationResource("engine.content", "public", "bn-BD", {"content.title": "শিরোনাম"}))
    assert engine.resolve_locale(LocaleResolution(explicit="bn-BD", user="en-US")) == "bn-BD"
    assert engine.translate(owner="engine.content", namespace="public", key="content.title", locale_id="bn-BD").value == "শিরোনাম"
    missing = engine.translate(owner="engine.content", namespace="public", key="content.missing", locale_id="bn-BD", fallback_locales=("en-US",))
    assert not missing.resolved


def test_namespace_isolation_conflict_and_invalid_locale(data_kernel: Kernel) -> None:
    engine = _configured(data_kernel)
    resource = TranslationResource("plugin.one", "public", "en-US", {"plugin.label": "One"})
    engine.register_translations(resource)
    with pytest.raises(InvalidLocalization): engine.register_translations(resource)
    assert not engine.translate(owner="plugin.two", namespace="public", key="plugin.label", locale_id="en-US").resolved
    with pytest.raises(InvalidLocalization): engine.resolve_locale(LocaleResolution(explicit="../../etc"))
