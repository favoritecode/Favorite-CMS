"""Provider-neutral, rebuildable in-process search index."""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Callable, Mapping

from backend.core.container import ServiceContainer
from backend.engines.authentication import AuthenticationContext
from backend.engines.data_contracts import identifier, json_mapping, text
from backend.engines.errors import ApplicationFailure, ValidationFailure
from backend.engines.permissions import AuthorizationContext, PermissionEngine


class SearchError(ApplicationFailure): pass
class InvalidSearch(ValidationFailure): pass


@dataclass(frozen=True)
class ResourceVisibility:
    available: bool
    public: bool
    owner_user_id: str | None = None


VisibilityResolver = Callable[[str], ResourceVisibility]


@dataclass(frozen=True)
class SearchableType:
    resource_type: str
    owner: str
    read_permission: str
    resolve_visibility: VisibilityResolver
    allowed_filters: frozenset[str] = frozenset()

    def __post_init__(self) -> None:
        identifier(self.resource_type, "Searchable Resource Type"); identifier(self.owner, "Search owner")
        if not self.read_permission.strip() or not callable(self.resolve_visibility):
            raise InvalidSearch("Searchable Resource contract is invalid")


@dataclass(frozen=True)
class SearchDocument:
    resource_id: str
    resource_type: str
    title: str
    searchable_text: str
    description: str | None = None
    labels: tuple[str, ...] = ()
    resource_reference: str | None = None
    media_reference: str | None = None
    metadata: Mapping[str, object] = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        if not self.resource_id.strip(): raise InvalidSearch("Search Resource identifier is invalid")
        identifier(self.resource_type, "Searchable Resource Type")
        text(self.title, "Search title", maximum=500)
        if len(self.searchable_text) > 100_000: raise InvalidSearch("Searchable text is too large")
        object.__setattr__(self, "metadata", json_mapping(self.metadata or {}, "Search metadata"))


@dataclass(frozen=True)
class SearchQuery:
    text: str = ""
    resource_type: str | None = None
    labels: tuple[str, ...] = ()
    filters: Mapping[str, object] = None  # type: ignore[assignment]
    order_by: str = "title"
    page: int = 1
    page_size: int = 20


@dataclass(frozen=True)
class SearchResult:
    resource_id: str
    resource_type: str
    title: str
    description: str | None
    labels: tuple[str, ...]
    resource_reference: str | None
    media_reference: str | None
    metadata: Mapping[str, object]


class SearchEngine:
    engine_id = "search"
    dependencies = ("permissions",)

    def __init__(self) -> None:
        self._types: dict[str, SearchableType] = {}; self._documents: dict[tuple[str, str], SearchDocument] = {}
        self._permissions: PermissionEngine | None = None; self.ready = False
    def initialize(self, container: ServiceContainer) -> None:
        self._permissions = container.resolve("engine.permissions", PermissionEngine)
        container.register("engine.search", self)
    def start(self) -> None: self.ready = True
    def shutdown(self) -> None: self.ready = False; self._documents.clear()

    def register_type(self, contract: SearchableType) -> None:
        if contract.resource_type in self._types: raise InvalidSearch("Searchable Type is already registered")
        self._types[contract.resource_type] = contract
    def index(self, document: SearchDocument) -> None:
        self._require_ready(); self._type(document.resource_type)
        self._documents[(document.resource_type, document.resource_id)] = document
    def remove(self, resource_type: str, resource_id: str) -> None:
        self._require_ready(); self._type(resource_type); self._documents.pop((resource_type, resource_id), None)
    def query(self, query: SearchQuery,
              authentication: AuthenticationContext | None = None) -> tuple[SearchResult, ...]:
        self._require_ready(); normalized = " ".join(query.text.split()).casefold()
        if len(normalized) > 500 or query.page < 1 or not 1 <= query.page_size <= 100:
            raise InvalidSearch("Search Query is invalid")
        if query.order_by not in {"title", "resource_id"}: raise InvalidSearch("Search ordering is unsupported")
        filters = json_mapping(query.filters or {}, "Search filters")
        documents = list(self._documents.values())
        if query.resource_type is not None:
            contract = self._type(query.resource_type)
            if set(filters) - contract.allowed_filters: raise InvalidSearch("Search filter is unsupported")
            documents = [item for item in documents if item.resource_type == query.resource_type]
        elif filters: raise InvalidSearch("Search filters require a Resource Type")
        if normalized:
            documents = [item for item in documents if normalized in f"{item.title} {item.searchable_text}".casefold()]
        if query.labels:
            requested = set(query.labels); documents = [item for item in documents if requested.issubset(item.labels)]
        for key, value in filters.items():
            documents = [item for item in documents if item.metadata.get(key) == value]
        documents.sort(key=lambda item: (getattr(item, query.order_by).casefold(), item.resource_type, item.resource_id))
        visible: list[SearchResult] = []
        for item in documents:
            contract = self._type(item.resource_type)
            try: state = contract.resolve_visibility(item.resource_id)
            except Exception: continue
            if not state.available:
                self._documents.pop((item.resource_type, item.resource_id), None); continue
            decision = self._permissions_required().evaluate(contract.read_permission, AuthorizationContext(
                "read", item.resource_type, authentication, item.resource_id, state.owner_user_id, state.public))
            if decision.allowed:
                visible.append(SearchResult(item.resource_id, item.resource_type, item.title, item.description,
                                           item.labels, item.resource_reference, item.media_reference, item.metadata))
        start = (query.page - 1) * query.page_size
        return tuple(visible[start:start + query.page_size])
    def live(self, text_value: str, *, limit: int,
             authentication: AuthenticationContext | None = None) -> tuple[SearchResult, ...]:
        if not 1 <= limit <= 20: raise InvalidSearch("Live Search limit is invalid")
        return self.query(SearchQuery(text=text_value, page_size=limit), authentication)
    def _type(self, resource_type: str) -> SearchableType:
        try: return self._types[resource_type]
        except KeyError as exc: raise InvalidSearch("Searchable Type is not registered") from exc
    def _permissions_required(self) -> PermissionEngine:
        if self._permissions is None: raise SearchError("Permission service is unavailable")
        return self._permissions
    def _require_ready(self) -> None:
        if not self.ready: raise SearchError("Search Engine is unavailable")
