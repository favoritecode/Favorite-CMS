import pytest

from backend.core import Kernel
from backend.engines.search import SearchDocument, SearchEngine, SearchQuery, SearchableType
from backend.engines.search.engine import InvalidSearch, ResourceVisibility
from backend.tests.platform_data.conftest import permission


def test_search_index_query_pagination_and_removal(data_kernel: Kernel) -> None:
    permission(data_kernel, "tests.search.read", "read", "article", allow_public=True)
    available = {"1": True, "2": True}
    engine = data_kernel.container.resolve("engine.search", SearchEngine)
    engine.register_type(SearchableType("article", "tests", "tests.search.read",
                                        lambda resource_id: ResourceVisibility(available.get(resource_id, False), True),
                                        frozenset({"category"})))
    engine.index(SearchDocument("2", "article", "Beta", "second text", labels=("news",), metadata={"category": "b"}))
    engine.index(SearchDocument("1", "article", "Alpha", "first searchable text", labels=("news",), metadata={"category": "a"}))
    assert [item.resource_id for item in engine.query(SearchQuery(text="text", page_size=1))] == ["1"]
    assert engine.live("second", limit=5)[0].title == "Beta"
    assert engine.query(SearchQuery(resource_type="article", filters={"category": "a"}))[0].resource_id == "1"
    engine.remove("article", "2"); assert engine.query(SearchQuery(text="second")) == ()


def test_search_visibility_rechecks_source_and_failure_isolated(data_kernel: Kernel) -> None:
    permission(data_kernel, "tests.search.read", "read", "article", allow_public=True)
    states = {"visible": ResourceVisibility(True, True), "gone": ResourceVisibility(False, True)}
    engine = data_kernel.container.resolve("engine.search", SearchEngine)
    engine.register_type(SearchableType("article", "tests", "tests.search.read", lambda key: states[key]))
    engine.index(SearchDocument("visible", "article", "Visible", "text")); engine.index(SearchDocument("gone", "article", "Gone", "text"))
    assert [item.resource_id for item in engine.query(SearchQuery(text="text"))] == ["visible"]
    states["visible"] = ResourceVisibility(False, True); assert engine.query(SearchQuery()) == ()
    with pytest.raises(InvalidSearch): engine.query(SearchQuery(page_size=101))
    with pytest.raises(InvalidSearch): engine.query(SearchQuery(resource_type="article", filters={"unknown": True}))
