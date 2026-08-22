from dataclasses import dataclass
import pytest
from backend.core import Kernel
from backend.core.extensions import ExtensionManifest, ExtensionState
from backend.engines.plugins import PluginContext, PluginEngine
from backend.engines.routing import InvalidRoute, PluginRouting, RouteDefinition, RouteNotFound, RouteType, RoutingEngine
from backend.tests.extensions.conftest import manifest_data

@dataclass
class RoutePlugin:
    route_owner: str
    context: PluginContext | None = None
    def register(self, context: PluginContext) -> None:
        self.context = context
        routing = context.service("engine.routing", PluginRouting)
        routing.register(RouteDefinition("plugin.route.page", self.route_owner, RouteType.API, "/plugin-page", ("GET",), "plugin.route.target"))
    def activate(self) -> None: pass
    def deactivate(self) -> None: pass
    def unregister(self) -> None: pass

def test_plugin_route_is_owner_scoped_and_removed_on_disable(phase7_kernel: Kernel) -> None:
    identifier = "favorite.plugin.routes"; manager = phase7_kernel.extensions
    manager.register(ExtensionManifest.from_mapping(manifest_data(id=identifier, permissions=["routing.register"])))
    plugins = phase7_kernel.container.resolve("engine.plugins", PluginEngine)
    runtime = RoutePlugin(identifier); plugins.bind(identifier, runtime, granted_permissions=frozenset({"routing.register"}))
    assert plugins.activate(identifier)
    routing = phase7_kernel.container.resolve("engine.routing", RoutingEngine)
    assert routing.resolve("GET", "/plugin-page").owner == identifier
    assert plugins.deactivate(identifier)
    with pytest.raises(RouteNotFound): routing.resolve("GET", "/plugin-page")

def test_plugin_cannot_claim_another_route_owner(phase7_kernel: Kernel) -> None:
    identifier = "favorite.plugin.attacker"; manager = phase7_kernel.extensions
    manager.register(ExtensionManifest.from_mapping(manifest_data(id=identifier, permissions=["routing.register"])))
    plugins = phase7_kernel.container.resolve("engine.plugins", PluginEngine)
    plugins.bind(identifier, RoutePlugin("engine.api"), granted_permissions=frozenset({"routing.register"}))
    assert not plugins.activate(identifier)
    assert manager.state(identifier) is ExtensionState.ERROR
