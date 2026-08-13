from dataclasses import dataclass
from pathlib import Path
from backend.core import Kernel
from backend.core.extensions import ExtensionManifest
from backend.engines.rendering import PresentationOperation, RenderingEngine, RenderResource, ResourceKind, ResourceOrigin
from backend.engines.routing import RouteDefinition, RouteType, RoutingEngine
from backend.engines.themes import ThemeEngine, ThemePackage
from backend.tests.extensions.conftest import manifest_data

@dataclass
class Runtime:
    active: bool = False
    def activate(self) -> None: self.active = True
    def deactivate(self) -> None: self.active = False

def activate_theme(kernel: Kernel, tmp_path: Path) -> str:
    identifier = "favorite.theme.phase7"; root = tmp_path / "theme"; root.mkdir(); (root / "page.html").write_text("theme", encoding="utf-8")
    manager = kernel.extensions
    manifest = ExtensionManifest.from_mapping(manifest_data(id=identifier, type="theme")); manager.register(manifest)
    themes = kernel.container.resolve("engine.themes", ThemeEngine); themes.bind(identifier, ThemePackage(root, templates=("page.html",)), Runtime()); assert themes.activate(identifier)
    return identifier

def test_theme_override_pipeline_and_optional_failure(phase7_kernel: Kernel, tmp_path: Path) -> None:
    theme = activate_theme(phase7_kernel, tmp_path)
    rendering = phase7_kernel.container.resolve("engine.rendering", RenderingEngine)
    routing = phase7_kernel.container.resolve("engine.routing", RoutingEngine)
    rendering.register_resource(RenderResource("page.main", ResourceKind.TEMPLATE, ResourceOrigin.PLATFORM, "engine.rendering", lambda values: "platform"))
    rendering.register_resource(RenderResource("page.main", ResourceKind.TEMPLATE, ResourceOrigin.THEME, theme, lambda values: "theme:" + str(values["model"]), theme_id=theme, package_reference="page.html"))
    rendering.register_resource(RenderResource("widget.optional", ResourceKind.WIDGET, ResourceOrigin.PLUGIN, "favorite.plugin.test", lambda values: (_ for _ in ()).throw(RuntimeError("broken")), optional=True))
    rendering.register_operation(PresentationOperation("page.show", "engine.content", lambda route: route.parameters["identifier"], "page.main", widgets=("widget.optional",)))
    definition = RouteDefinition("content.page.show", "engine.content", RouteType.PRESENTATION, "/page/{identifier}", ("GET",), "page.show")
    routing.register(definition)
    response = rendering.render(routing.resolve("GET", "/page/hello"))
    assert response.status == 200 and response.body == "theme:hello"

def test_missing_theme_or_resource_is_safe(phase7_kernel: Kernel) -> None:
    rendering = phase7_kernel.container.resolve("engine.rendering", RenderingEngine); routing = phase7_kernel.container.resolve("engine.routing", RoutingEngine)
    rendering.register_operation(PresentationOperation("page.missing", "engine.content", lambda route: {}, "missing.template"))
    routing.register(RouteDefinition("content.page.missing", "engine.content", RouteType.PRESENTATION, "/missing-page", ("GET",), "page.missing"))
    response = rendering.render(routing.resolve("GET", "/missing-page"))
    assert response.status == 404 and "private" not in response.body.lower()

def test_rendering_does_not_resolve_routes(phase7_kernel: Kernel) -> None:
    rendering = phase7_kernel.container.resolve("engine.rendering", RenderingEngine)
    assert not hasattr(rendering, "resolve") and not hasattr(rendering, "_routing")
