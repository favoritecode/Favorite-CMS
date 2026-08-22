"""Phase 1 composition root in the documented startup order."""

from backend.config import create_bootstrap_configuration
from backend.core import Kernel
from backend.core.engine_manager import EngineManager
from backend.core.extensions import ExtensionManager
from backend.database import DatabaseEngine
from backend.database.migrations import DatabaseMigrationEngine
from backend.engines.cache import CacheEngine
from backend.engines.authentication import AuthenticationEngine
from backend.engines.errors import ErrorHandlingEngine
from backend.engines.events import EventEngine
from backend.engines.logging import JsonConsoleOutput, LogLevel, LoggingEngine
from backend.engines.notifications import NotificationEngine
from backend.engines.queue import QueueEngine
from backend.engines.scheduler import SchedulerEngine
from backend.engines.storage import StorageEngine
from backend.engines.permissions import PermissionEngine
from backend.engines.users import UserEngine
from backend.engines.audit import AuditEngine
from backend.engines.content import ContentEngine
from backend.engines.domains import DomainEngine
from backend.engines.tools import ToolEngine
from backend.engines.localization import LocalizationEngine
from backend.engines.media import MediaEngine
from backend.engines.menu import MenuEngine
from backend.engines.search import SearchEngine
from backend.engines.seo import SeoEngine
from backend.engines.settings import SettingsEngine
from backend.engines.plugins import PluginEngine
from backend.engines.themes import ThemeEngine
from backend.engines.extension_packages import ExtensionPackageEngine
from backend.engines.routing import RoutingEngine
from backend.engines.api import APIEngine
from backend.engines.rendering import RenderingEngine
from backend.admin import AdminEngine, AdminPlatformEngine
from backend.recovery import BackupRecoveryEngine
from backend.update import UpdateEngine
from backend.operations import HealthEngine, InstallationEngine
from backend.tooling import ToolPlatformEngine


def build_kernel(*, console_logging: bool = False) -> Kernel:
    configuration = create_bootstrap_configuration()
    errors = ErrorHandlingEngine()
    outputs = (JsonConsoleOutput(),) if console_logging else ()
    logging = LoggingEngine(
        outputs=outputs,
        minimum_level=LogLevel.DEBUG if configuration.get("debug", bool) else LogLevel.INFO,
    )
    extensions = ExtensionManager(core_version="0.1.0")
    engines = EngineManager()
    engines.register(DatabaseEngine())
    engines.register(DatabaseMigrationEngine())
    engines.register(StorageEngine())
    engines.register(CacheEngine())
    engines.register(EventEngine())
    engines.register(QueueEngine())
    engines.register(NotificationEngine())
    engines.register(SchedulerEngine())
    engines.register(UserEngine())
    engines.register(AuditEngine())
    engines.register(AuthenticationEngine())
    engines.register(PermissionEngine())
    engines.register(SettingsEngine())
    engines.register(ContentEngine())
    engines.register(DomainEngine())
    engines.register(ToolEngine())
    engines.register(MediaEngine())
    engines.register(SearchEngine())
    engines.register(LocalizationEngine())
    engines.register(MenuEngine())
    engines.register(SeoEngine())
    engines.register(PluginEngine())
    engines.register(ThemeEngine())
    engines.register(ExtensionPackageEngine())
    engines.register(RoutingEngine())
    engines.register(APIEngine())
    engines.register(RenderingEngine())
    engines.register(ToolPlatformEngine())
    engines.register(AdminEngine())
    engines.register(BackupRecoveryEngine())
    engines.register(UpdateEngine())
    engines.register(HealthEngine())
    engines.register(InstallationEngine())
    engines.register(AdminPlatformEngine())
    return Kernel(
        configuration=configuration,
        logging=logging,
        errors=errors,
        extensions=extensions,
        engines=engines,
    )
