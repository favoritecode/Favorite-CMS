import pytest

from backend.core import Kernel
from backend.engines.menu import Menu, MenuDestination, MenuEngine, MenuItem, MenuLocation
from backend.engines.menu.engine import InvalidMenu
from backend.tests.platform_data.conftest import permission


def test_menu_hierarchy_order_assignment_and_resolution(data_kernel: Kernel) -> None:
    engine = data_kernel.container.resolve("engine.menu", MenuEngine); engine.register_destination("reference", lambda destination: destination.reference != "gone")
    engine.create(Menu("main", "platform", "Main navigation", "platform")); engine.register_location(MenuLocation("primary", "theme.test", "Primary")); engine.assign("primary", "main")
    engine.add_item(MenuItem("parent", "main", "Parent", MenuDestination("reference", "home"), order=2))
    engine.add_item(MenuItem("first", "main", "First", MenuDestination("reference", "page"), order=1))
    engine.add_item(MenuItem("child", "main", "Child", MenuDestination("reference", "child"), parent_id="parent"))
    engine.add_item(MenuItem("unavailable", "main", "Gone", MenuDestination("reference", "gone"), order=3))
    resolved = engine.resolve(location_id="primary")
    assert [item.item_id for item in resolved.items] == ["first", "parent", "child"]


def test_menu_rejects_invalid_hierarchy_and_preserves_destination(data_kernel: Kernel) -> None:
    engine = data_kernel.container.resolve("engine.menu", MenuEngine); engine.register_destination("reference", lambda destination: True)
    engine.create(Menu("main", "platform", "Main", "platform")); engine.add_item(MenuItem("parent", "main", "Parent", MenuDestination("reference", "home")))
    with pytest.raises(InvalidMenu): engine.add_item(MenuItem("bad", "main", "Bad", MenuDestination("reference", "x"), parent_id="missing"))
    with pytest.raises(InvalidMenu): engine.update_item(MenuItem("parent", "main", "Parent", MenuDestination("reference", "home"), parent_id="parent"))
    engine.add_item(MenuItem("child", "main", "Child", MenuDestination("reference", "child"), parent_id="parent"))
    with pytest.raises(InvalidMenu): engine.remove_item("parent")
    engine.remove("main")
    with pytest.raises(Exception): engine.resolve(menu_id="main")


def test_protected_menu_item_is_hidden_without_permission(data_kernel: Kernel) -> None:
    permission(data_kernel, "tests.menu.read", "read", "menu_destination")
    engine = data_kernel.container.resolve("engine.menu", MenuEngine); engine.register_destination("reference", lambda destination: True)
    engine.create(Menu("protected", "platform", "Protected", "platform"))
    engine.add_item(MenuItem("private", "protected", "Private", MenuDestination("reference", "admin"), public=False, permission_id="tests.menu.read"))
    assert engine.resolve(menu_id="protected").items == ()
