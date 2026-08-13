"""Persistent navigation data, independent from Routing and Rendering."""

from __future__ import annotations

from dataclasses import dataclass, replace
import json
from typing import Callable

from sqlalchemy import Column, MetaData, String, Table, Text, delete, insert, select, update

from backend.core.container import ServiceContainer
from backend.database import DatabaseEngine
from backend.database.migrations import DatabaseMigrationEngine, Migration
from backend.engines.authentication import AuthenticationContext
from backend.engines.data_contracts import identifier, text
from backend.engines.errors import ApplicationFailure, ValidationFailure
from backend.engines.permissions import AuthorizationContext, PermissionEngine


class MenuError(ApplicationFailure): pass
class InvalidMenu(ValidationFailure): pass
Availability = Callable[["MenuDestination"], bool]


@dataclass(frozen=True)
class MenuDestination:
    kind: str
    reference: str
    def __post_init__(self) -> None:
        identifier(self.kind, "Destination kind"); text(self.reference, "Destination reference", maximum=2048)


@dataclass(frozen=True)
class Menu:
    menu_id: str
    owner: str
    purpose: str
    scope: str


@dataclass(frozen=True)
class MenuItem:
    item_id: str
    menu_id: str
    label: str
    destination: MenuDestination
    parent_id: str | None = None
    order: int = 0
    public: bool = True
    permission_id: str | None = None


@dataclass(frozen=True)
class MenuLocation:
    location_id: str
    owner: str
    purpose: str


@dataclass(frozen=True)
class ResolvedMenu:
    menu: Menu
    items: tuple[MenuItem, ...]


_metadata = MetaData()
_menus = Table("favorite_menus", _metadata, Column("menu_id", String(255), primary_key=True),
               Column("owner", String(255), nullable=False), Column("purpose", String(500), nullable=False),
               Column("scope", String(255), nullable=False))
_items = Table("favorite_menu_items", _metadata, Column("item_id", String(255), primary_key=True),
               Column("menu_id", String(255), nullable=False), Column("label", String(500), nullable=False),
               Column("destination", Text, nullable=False), Column("parent_id", String(255), nullable=True),
               Column("item_order", String(32), nullable=False), Column("is_public", String(5), nullable=False),
               Column("permission_id", String(255), nullable=True))
_locations = Table("favorite_menu_locations", _metadata, Column("location_id", String(255), primary_key=True),
                   Column("owner", String(255), nullable=False), Column("purpose", String(500), nullable=False))
_assignments = Table("favorite_menu_assignments", _metadata,
                     Column("location_id", String(255), primary_key=True), Column("menu_id", String(255), nullable=False))


def menu_migration() -> Migration:
    return Migration("platform.menu.001", "engine.menu",
                     lambda connection: _metadata.create_all(connection, tables=[_menus, _items, _locations, _assignments]))


class MenuEngine:
    engine_id = "menu"
    dependencies = ("database", "migrations", "permissions")
    def __init__(self) -> None:
        self._database: DatabaseEngine | None = None; self._permissions: PermissionEngine | None = None
        self._destinations: dict[str, Availability] = {}; self.ready = False
    def initialize(self, container: ServiceContainer) -> None:
        self._database = container.resolve("engine.database", DatabaseEngine)
        self._permissions = container.resolve("engine.permissions", PermissionEngine)
        container.resolve("engine.migrations", DatabaseMigrationEngine).register(menu_migration())
        container.register("engine.menu", self)
    def start(self) -> None: self.ready = True
    def shutdown(self) -> None: self.ready = False
    def register_destination(self, kind: str, availability: Availability) -> None:
        kind = identifier(kind, "Destination kind")
        if kind in self._destinations or not callable(availability): raise InvalidMenu("Destination contract is invalid")
        self._destinations[kind] = availability
    def create(self, menu: Menu) -> None:
        identifier(menu.menu_id, "Menu"); identifier(menu.owner, "Menu owner"); identifier(menu.scope, "Menu scope")
        with self._db().transaction() as session: session.execute(insert(_menus).values(**menu.__dict__))
    def register_location(self, location: MenuLocation) -> None:
        identifier(location.location_id, "Menu Location"); identifier(location.owner, "Location owner")
        with self._db().transaction() as session: session.execute(insert(_locations).values(**location.__dict__))
    def assign(self, location_id: str, menu_id: str) -> None:
        self._load_menu(menu_id)
        with self._db().transaction() as session:
            if session.execute(select(_locations.c.location_id).where(_locations.c.location_id == location_id)).scalar_one_or_none() is None:
                raise InvalidMenu("Menu Location is not registered")
            current = session.execute(select(_assignments.c.location_id).where(_assignments.c.location_id == location_id)).scalar_one_or_none()
            if current is None: session.execute(insert(_assignments).values(location_id=location_id, menu_id=menu_id))
            else: session.execute(update(_assignments).where(_assignments.c.location_id == location_id).values(menu_id=menu_id))
    def add_item(self, item: MenuItem) -> None:
        self._validate_item(item)
        with self._db().transaction() as session: session.execute(insert(_items).values(**_item_values(item)))
    def update_item(self, item: MenuItem) -> None:
        self._validate_item(item, updating=True)
        with self._db().transaction() as session:
            session.execute(update(_items).where(_items.c.item_id == item.item_id).values(**_item_values(item)))
    def remove_item(self, item_id: str) -> None:
        with self._db().transaction() as session:
            if session.execute(select(_items.c.item_id).where(_items.c.parent_id == item_id)).first() is not None:
                raise InvalidMenu("Menu Item has children")
            session.execute(delete(_items).where(_items.c.item_id == item_id))
    def remove(self, menu_id: str) -> None:
        self._load_menu(menu_id)
        with self._db().transaction() as session:
            session.execute(delete(_assignments).where(_assignments.c.menu_id == menu_id))
            session.execute(delete(_items).where(_items.c.menu_id == menu_id))
            session.execute(delete(_menus).where(_menus.c.menu_id == menu_id))
    def resolve(self, *, menu_id: str | None = None, location_id: str | None = None,
                authentication: AuthenticationContext | None = None) -> ResolvedMenu:
        if (menu_id is None) == (location_id is None): raise InvalidMenu("Menu request is invalid")
        if location_id is not None:
            with self._db().session() as session:
                menu_id = session.execute(select(_assignments.c.menu_id).where(_assignments.c.location_id == location_id)).scalar_one_or_none()
            if menu_id is None: raise MenuError("Menu Location has no assignment")
        menu = self._load_menu(menu_id or "")
        with self._db().session() as session:
            items = tuple(_item(row) for row in session.execute(select(_items).where(_items.c.menu_id == menu.menu_id)).mappings())
        self._validate_hierarchy(items)
        visible = []
        for item in sorted(items, key=lambda value: (value.parent_id or "", value.order, value.item_id)):
            resolver = self._destinations.get(item.destination.kind)
            if resolver is None:
                continue
            try:
                if not resolver(item.destination): continue
            except Exception: continue
            if item.permission_id is not None:
                decision = self._permissions_required().evaluate(item.permission_id, AuthorizationContext(
                    "read", "menu_destination", authentication, item.destination.reference, public=item.public))
                if not decision.allowed: continue
            elif not item.public: continue
            visible.append(item)
        return ResolvedMenu(menu, tuple(visible))
    def _validate_item(self, item: MenuItem, updating: bool = False) -> None:
        identifier(item.item_id, "Menu Item"); text(item.label, "Menu Item label", maximum=500)
        self._load_menu(item.menu_id)
        if item.order < 0 or item.destination.kind not in self._destinations or item.parent_id == item.item_id:
            raise InvalidMenu("Menu Item is invalid")
        with self._db().session() as session:
            rows = tuple(_item(row) for row in session.execute(select(_items).where(_items.c.menu_id == item.menu_id)).mappings())
        if item.parent_id is not None and all(parent.item_id != item.parent_id for parent in rows):
            raise InvalidMenu("Menu parent is invalid")
        proposed = tuple(value for value in rows if value.item_id != item.item_id) + (item,)
        self._validate_hierarchy(proposed)
    def _validate_hierarchy(self, items: tuple[MenuItem, ...]) -> None:
        mapping = {item.item_id: item for item in items}
        if len(mapping) != len(items): raise InvalidMenu("Menu Item identifiers conflict")
        for item in items:
            seen = {item.item_id}; parent = item.parent_id
            while parent is not None:
                if parent in seen or parent not in mapping: raise InvalidMenu("Menu hierarchy is invalid")
                seen.add(parent); parent = mapping[parent].parent_id
    def _load_menu(self, menu_id: str) -> Menu:
        with self._db().session() as session:
            row = session.execute(select(_menus).where(_menus.c.menu_id == menu_id)).mappings().first()
        if row is None: raise MenuError("Menu was not found")
        return Menu(str(row["menu_id"]), str(row["owner"]), str(row["purpose"]), str(row["scope"]))
    def _db(self) -> DatabaseEngine:
        if not self.ready or self._database is None: raise MenuError("Menu Engine is unavailable")
        return self._database
    def _permissions_required(self) -> PermissionEngine:
        if self._permissions is None: raise MenuError("Permission service is unavailable")
        return self._permissions


def _item_values(item: MenuItem) -> dict[str, object]:
    return {"item_id": item.item_id, "menu_id": item.menu_id, "label": item.label,
            "destination": json.dumps({"kind": item.destination.kind, "reference": item.destination.reference}),
            "parent_id": item.parent_id, "item_order": str(item.order), "is_public": str(item.public).lower(),
            "permission_id": item.permission_id}
def _item(row: object) -> MenuItem:
    destination = json.loads(str(row["destination"]))
    return MenuItem(str(row["item_id"]), str(row["menu_id"]), str(row["label"]),
                    MenuDestination(destination["kind"], destination["reference"]),
                    None if row["parent_id"] is None else str(row["parent_id"]), int(str(row["item_order"])),
                    str(row["is_public"]) == "true", None if row["permission_id"] is None else str(row["permission_id"]))
