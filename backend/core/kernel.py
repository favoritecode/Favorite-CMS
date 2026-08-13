"""Business-neutral Core lifecycle controller."""

from __future__ import annotations

from backend.config import Configuration
from backend.core.container import ServiceContainer
from backend.core.engine_manager import EngineManager
from backend.core.extensions import ExtensionManager
from backend.engines.errors import ErrorHandlingEngine, ErrorRecord
from backend.engines.logging import LogCategory, LogSource, LogSourceKind, LoggingEngine


class Kernel:
    def __init__(
        self,
        *,
        configuration: Configuration,
        logging: LoggingEngine,
        errors: ErrorHandlingEngine,
        extensions: ExtensionManager,
        engines: EngineManager | None = None,
    ) -> None:
        self.configuration = configuration
        self.logging = logging
        self.errors = errors
        self.extensions = extensions
        self.engines = engines or EngineManager()
        self.container = ServiceContainer()
        self.ready = False
        self.failure: ErrorRecord | None = None

    def bootstrap(self) -> None:
        if self.ready:
            return
        try:
            self.container.register("core.configuration", self.configuration)
            self.container.register("core.logging", self.logging)
            self.container.register("core.errors", self.errors)
            self.container.register("core.extensions", self.extensions)
            self.container.register("core.engines", self.engines)
            self.engines.initialize_and_start(self.container)
            self.ready = True
            self.failure = None
            self.logging.info(
                "Core bootstrap completed",
                source=LogSource(LogSourceKind.CORE, "core.kernel"),
                category=LogCategory.CORE,
            )
        except Exception as exc:
            self.ready = False
            self.failure = self.errors.normalize(exc, source="core.kernel")
            self.logging.error(
                self.failure.safe_message,
                source=LogSource(LogSourceKind.CORE, "core.kernel"),
                category=LogCategory.CORE,
                context={"error_id": self.failure.error_id},
            )
            raise

    def shutdown(self) -> None:
        self.engines.shutdown()
        self.ready = False

