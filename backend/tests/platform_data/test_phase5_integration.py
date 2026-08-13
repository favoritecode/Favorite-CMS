from backend.core import Kernel
from backend.engines.content import ContentEngine
from backend.engines.localization import LocalizationEngine
from backend.engines.media import MediaEngine
from backend.engines.menu import MenuEngine
from backend.engines.search import SearchEngine
from backend.engines.seo import SeoEngine
from backend.engines.settings import SettingsEngine


def test_phase5_lifecycle_is_deterministic(data_kernel: Kernel) -> None:
    engines = [data_kernel.container.resolve(key, kind) for key, kind in (
        ("engine.settings", SettingsEngine), ("engine.content", ContentEngine), ("engine.media", MediaEngine),
        ("engine.search", SearchEngine), ("engine.localization", LocalizationEngine), ("engine.menu", MenuEngine),
        ("engine.seo", SeoEngine),
    )]
    assert all(engine.ready for engine in engines)
    data_kernel.shutdown(); assert all(not engine.ready for engine in engines)
