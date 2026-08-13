"""Core-specific contract failures."""


class CoreError(RuntimeError):
    pass


class DuplicateServiceError(CoreError):
    pass


class MissingServiceError(CoreError):
    pass


class EngineLifecycleError(CoreError):
    pass

