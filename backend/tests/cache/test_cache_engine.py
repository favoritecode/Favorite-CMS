from time import sleep

from backend.config import ConfigField, Configuration, ConfigurationSchema, MappingSource
from backend.core.container import ServiceContainer
from backend.engines.cache import CacheEngine, CacheKey, CacheScope, InMemoryCacheProvider
from backend.engines.logging import LoggingEngine, MemoryLogOutput


def started_cache(provider: object | None = None) -> CacheEngine:
    schema = ConfigurationSchema((ConfigField("cache.enabled", bool, required=True),))
    configuration = Configuration.resolve(
        schema, (MappingSource("test", {"cache.enabled": True}, 1),)
    )
    container = ServiceContainer()
    container.register("core.configuration", configuration)
    container.register("core.logging", LoggingEngine())
    cache = CacheEngine(provider)  # type: ignore[arg-type]
    cache.initialize(container)
    cache.start()
    return cache


def test_set_get_exists_delete_and_miss() -> None:
    cache = started_cache(InMemoryCacheProvider())
    key = CacheKey(CacheScope("resource", "platform"), "item-1")
    assert not cache.get(key).hit
    assert cache.set(key, {"representation": 1})
    assert cache.exists(key)
    assert cache.get(key).value == {"representation": 1}
    assert cache.delete(key)
    assert not cache.get(key).hit


def test_expired_entry_is_a_cache_miss() -> None:
    cache = started_cache(InMemoryCacheProvider())
    key = CacheKey(CacheScope("resource", "platform"), "expiring")
    assert cache.set(key, "temporary", ttl_seconds=0.01)
    sleep(0.02)
    assert not cache.get(key).hit


def test_scope_clear_does_not_affect_unrelated_scope() -> None:
    cache = started_cache(InMemoryCacheProvider())
    scope_a = CacheScope("private", "plugin-a")
    scope_b = CacheScope("private", "plugin-b")
    key_a = CacheKey(scope_a, "item")
    key_b = CacheKey(scope_b, "item")
    cache.set(key_a, "a")
    cache.set(key_b, "b")
    assert cache.clear(scope_a)
    assert not cache.get(key_a).hit
    assert cache.get(key_b).value == "b"


def test_provider_failure_degrades_to_miss_without_false_success() -> None:
    class BrokenProvider:
        def healthcheck(self) -> bool: return True
        def get(self, key: str): raise RuntimeError("unavailable")
        def set(self, key: str, value: object, ttl_seconds: float | None): raise RuntimeError("unavailable")
        def delete(self, key: str): raise RuntimeError("unavailable")
        def exists(self, key: str): raise RuntimeError("unavailable")
        def clear_prefix(self, prefix: str): raise RuntimeError("unavailable")

    cache = started_cache(BrokenProvider())
    key = CacheKey(CacheScope("resource", "platform"), "item")
    assert not cache.set(key, "not-authoritative")
    assert not cache.ready
    assert not cache.get(key).hit


def test_failure_is_logged_without_cached_value() -> None:
    class BrokenProvider:
        def healthcheck(self) -> bool: return True
        def get(self, key: str): raise RuntimeError("secret cached value")
        def set(self, *args: object): raise RuntimeError
        def delete(self, *args: object): raise RuntimeError
        def exists(self, *args: object): raise RuntimeError
        def clear_prefix(self, *args: object): raise RuntimeError

    output = MemoryLogOutput()
    schema = ConfigurationSchema((ConfigField("cache.enabled", bool, required=True),))
    configuration = Configuration.resolve(schema, (MappingSource("test", {"cache.enabled": True}, 1),))
    container = ServiceContainer()
    container.register("core.configuration", configuration)
    container.register("core.logging", LoggingEngine(outputs=(output,)))
    cache = CacheEngine(BrokenProvider())  # type: ignore[arg-type]
    cache.initialize(container)
    cache.start()
    cache.get(CacheKey(CacheScope("resource", "platform"), "item"))
    assert output.records
    assert "cached value" not in repr(output.records)

