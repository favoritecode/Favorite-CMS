"""Capability-gated Tool jobs delegated to an isolated, operator-configured worker."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import StrEnum
import json
import re
from types import MappingProxyType
from typing import Mapping, Protocol
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener
from uuid import UUID, uuid4

from sqlalchemy import Column, MetaData, String, Table, Text, insert, select, update

from backend.config import Configuration, SecretValue
from backend.core.container import ServiceContainer
from backend.database import DatabaseEngine
from backend.database.migrations import DatabaseMigrationEngine, Migration
from backend.engines.authentication import AuthenticationContext
from backend.engines.errors import ApplicationFailure, ValidationFailure
from backend.engines.permissions import AuthorizationContext, PermissionEngine


class ToolError(ApplicationFailure): pass
class InvalidTool(ValidationFailure): pass


class ToolFieldKind(StrEnum):
    TEXT = "text"; URL = "url"; MEDIA = "media"; INTEGER = "integer"; BOOLEAN = "boolean"; SELECT = "select"


class ToolJobStatus(StrEnum):
    PENDING = "pending"; RUNNING = "running"; COMPLETED = "completed"; FAILED = "failed"; CANCELLED = "cancelled"


@dataclass(frozen=True)
class ToolInputField:
    field_id: str
    kind: ToolFieldKind
    required: bool = False
    maximum_length: int | None = None
    choices: tuple[str, ...] = ()
    def __post_init__(self) -> None:
        if not _identifier(self.field_id) or not isinstance(self.kind, ToolFieldKind): raise InvalidTool("Tool input field is invalid")
        if self.maximum_length is not None and not 1 <= self.maximum_length <= 10_000: raise InvalidTool("Tool input length is invalid")
        if self.kind is ToolFieldKind.SELECT and (not self.choices or len(set(self.choices)) != len(self.choices)): raise InvalidTool("Tool choices are invalid")
        if self.kind is not ToolFieldKind.SELECT and self.choices: raise InvalidTool("Tool choices require a select field")


@dataclass(frozen=True)
class ToolContract:
    tool_id: str
    owner: str
    label: str
    description: str
    fields: tuple[ToolInputField, ...]
    execute_permission: str
    worker: str = "default"
    public: bool = False
    def __post_init__(self) -> None:
        if (not _identifier(self.tool_id) or not _identifier(self.owner) or not _identifier(self.worker)
                or not _identifier(self.execute_permission) or not 1 <= len(self.label.strip()) <= 80
                or len(self.description) > 500 or len({field.field_id for field in self.fields}) != len(self.fields)):
            raise InvalidTool("Tool contract is invalid")


@dataclass(frozen=True)
class ToolWorkerSubmission:
    external_id: str
    status: ToolJobStatus


@dataclass(frozen=True)
class ToolWorkerState:
    status: ToolJobStatus
    progress: int = 0
    result: Mapping[str, object] | None = None
    failure: str | None = None


class ToolWorkerProvider(Protocol):
    def healthcheck(self) -> bool: ...
    def submit(self, tool_id: str, job_id: str, values: Mapping[str, object]) -> ToolWorkerSubmission: ...
    def state(self, external_id: str) -> ToolWorkerState: ...
    def cancel(self, external_id: str) -> bool: ...


@dataclass(frozen=True)
class ToolJob:
    job_id: str
    tool_id: str
    owner: str
    status: ToolJobStatus
    progress: int
    result: Mapping[str, object] | None
    failure: str | None
    owner_user_id: str
    created_at: str
    updated_at: str


_metadata = MetaData()
_jobs = Table("favorite_tool_jobs", _metadata,
    Column("job_id", String(36), primary_key=True), Column("tool_id", String(255), nullable=False), Column("owner", String(255), nullable=False),
    Column("worker", String(255), nullable=False), Column("external_id", String(255)), Column("job_values", Text, nullable=False),
    Column("status", String(32), nullable=False), Column("progress", String(4), nullable=False), Column("result", Text), Column("failure", String(500)),
    Column("owner_user_id", String(36), nullable=False), Column("created_at", String(64), nullable=False), Column("updated_at", String(64), nullable=False))


def tool_migration() -> Migration:
    return Migration("platform.tool.001", "engine.tools", lambda connection: _metadata.create_all(connection, tables=[_jobs]),
                     dependencies=("platform.user.001",))


class ToolEngine:
    engine_id = "tools"
    dependencies = ("database", "migrations", "permissions")
    def __init__(self) -> None:
        self._database: DatabaseEngine | None = None; self._permissions: PermissionEngine | None = None
        self._contracts: dict[tuple[str, str], ToolContract] = {}; self._providers: dict[str, ToolWorkerProvider] = {}; self.ready = False
    def initialize(self, container: ServiceContainer) -> None:
        self._database = container.resolve("engine.database", DatabaseEngine); self._permissions = container.resolve("engine.permissions", PermissionEngine)
        container.resolve("engine.migrations", DatabaseMigrationEngine).register(tool_migration()); container.register("engine.tools", self)
        configuration = container.resolve("core.configuration", Configuration)
        if configuration.is_configured("tools.worker_url") and configuration.is_configured("tools.worker_token"):
            self.register_provider("default", HttpToolWorkerProvider(configuration.get("tools.worker_url", str),
                configuration.get("tools.worker_token", SecretValue).reveal(), configuration.get("tools.timeout_seconds", int)))
    def start(self) -> None: self.ready = True
    def shutdown(self) -> None: self.ready = False; self._contracts.clear(); self._providers.clear()
    def for_plugin(self, plugin_id: str) -> "PluginTools": return PluginTools(self, plugin_id)
    def register_provider(self, provider_id: str, provider: ToolWorkerProvider) -> None:
        if not _identifier(provider_id) or provider_id in self._providers: raise InvalidTool("Tool worker provider is invalid")
        self._providers[provider_id] = provider
    def register(self, contract: ToolContract) -> None:
        key = (contract.owner, contract.tool_id)
        if key in self._contracts or any(item.tool_id == contract.tool_id for item in self._contracts.values()): raise InvalidTool("Tool contract is already registered")
        self._contracts[key] = contract
    def unregister_owner(self, owner: str) -> None:
        for key in tuple(self._contracts):
            if key[0] == owner: del self._contracts[key]
    def contracts(self, owner: str | None = None) -> tuple[ToolContract, ...]:
        return tuple(sorted((item for item in self._contracts.values() if owner is None or item.owner == owner), key=lambda item: (item.owner, item.tool_id)))
    def contract(self, tool_id: str) -> ToolContract:
        matches = [item for item in self._contracts.values() if item.tool_id == tool_id]
        if len(matches) != 1: raise InvalidTool("Tool contract is unavailable")
        return matches[0]
    def submit_registered(self, tool_id: str, values: Mapping[str, object], authentication: AuthenticationContext) -> ToolJob:
        contract = self.contract(tool_id); return self.submit(contract.owner, contract.tool_id, values, authentication)
    def status_registered(self, tool_id: str, job_id: str, authentication: AuthenticationContext) -> ToolJob:
        contract = self.contract(tool_id); return self.status(contract.owner, contract.tool_id, job_id, authentication)
    def cancel_registered(self, tool_id: str, job_id: str, authentication: AuthenticationContext) -> bool:
        contract = self.contract(tool_id); return self.cancel(contract.owner, contract.tool_id, job_id, authentication)
    def availability(self, owner: str, tool_id: str) -> str:
        contract = self._contract(owner, tool_id); provider = self._providers.get(contract.worker)
        if provider is None: return "not_configured"
        try: return "available" if provider.healthcheck() else "unavailable"
        except Exception: return "unavailable"
    def submit(self, owner: str, tool_id: str, values: Mapping[str, object], authentication: AuthenticationContext) -> ToolJob:
        contract = self._contract(owner, tool_id); self._authorize(contract, authentication); valid = _validate_input(contract, values)
        provider = self._providers.get(contract.worker)
        if provider is None: raise ToolError("Tool worker is not configured")
        try:
            if not provider.healthcheck(): raise ToolError("Tool worker is unavailable")
        except ToolError: raise
        except Exception as exc: raise ToolError("Tool worker is unavailable") from exc
        job_id = str(uuid4()); now = _now(); owner_user_id = authentication.user_id or "public"
        with self._db().transaction() as session:
            session.execute(insert(_jobs).values(job_id=job_id, tool_id=tool_id, owner=owner, worker=contract.worker, external_id=None,
                job_values=_dump(valid), status=ToolJobStatus.PENDING.value, progress="0", result=None, failure=None,
                owner_user_id=owner_user_id, created_at=now, updated_at=now))
        try: submitted = provider.submit(tool_id, job_id, valid)
        except Exception as exc:
            self._set_failure(job_id, "Tool worker rejected the job")
            raise ToolError("Tool job submission failed safely") from exc
        if not _external_id(submitted.external_id) or submitted.status not in {ToolJobStatus.PENDING, ToolJobStatus.RUNNING}:
            self._set_failure(job_id, "Tool worker returned an invalid response"); raise ToolError("Tool job submission failed safely")
        with self._db().transaction() as session:
            session.execute(update(_jobs).where(_jobs.c.job_id == job_id).values(external_id=submitted.external_id, status=submitted.status.value, updated_at=_now()))
        return self._load(job_id)
    def status(self, owner: str, tool_id: str, job_id: str, authentication: AuthenticationContext) -> ToolJob:
        contract = self._contract(owner, tool_id); job, row = self._load_row(job_id)
        self._authorize(contract, authentication, job)
        if job.status in {ToolJobStatus.PENDING, ToolJobStatus.RUNNING} and row["external_id"]:
            provider = self._providers.get(str(row["worker"]))
            if provider is not None:
                try:
                    state = provider.state(str(row["external_id"])); _validate_worker_state(state)
                    with self._db().transaction() as session:
                        session.execute(update(_jobs).where(_jobs.c.job_id == job_id).values(status=state.status.value, progress=str(state.progress),
                            result=_dump(state.result) if state.result is not None else None, failure=state.failure, updated_at=_now()))
                except Exception: pass
        return self._load(job_id)
    def cancel(self, owner: str, tool_id: str, job_id: str, authentication: AuthenticationContext) -> bool:
        contract = self._contract(owner, tool_id); job, row = self._load_row(job_id); self._authorize(contract, authentication, job)
        if job.status not in {ToolJobStatus.PENDING, ToolJobStatus.RUNNING} or not row["external_id"]: return False
        provider = self._providers.get(str(row["worker"])); cancelled = bool(provider and provider.cancel(str(row["external_id"])))
        if cancelled:
            with self._db().transaction() as session: session.execute(update(_jobs).where(_jobs.c.job_id == job_id).values(status=ToolJobStatus.CANCELLED.value, updated_at=_now()))
        return cancelled
    def _contract(self, owner: str, tool_id: str) -> ToolContract:
        try: return self._contracts[(owner, tool_id)]
        except KeyError as exc: raise InvalidTool("Tool contract is unavailable") from exc
    def _authorize(self, contract: ToolContract, authentication: AuthenticationContext, job: ToolJob | None = None) -> None:
        if self._permissions is None: raise ToolError("Permission service is unavailable")
        self._permissions.require(contract.execute_permission, AuthorizationContext("execute", "plugin_tool", authentication,
            job.job_id if job else None, job.owner_user_id if job and job.owner_user_id != "public" else None, contract.public))
    def _load(self, job_id: str) -> ToolJob: return self._load_row(job_id)[0]
    def _load_row(self, job_id: str):
        try: identifier = str(UUID(job_id))
        except (ValueError, TypeError) as exc: raise InvalidTool("Tool job identifier is invalid") from exc
        with self._db().session() as session: row = session.execute(select(_jobs).where(_jobs.c.job_id == identifier)).mappings().first()
        if row is None: raise ToolError("Tool job was not found")
        return _job(row), row
    def _set_failure(self, job_id: str, message: str) -> None:
        with self._db().transaction() as session: session.execute(update(_jobs).where(_jobs.c.job_id == job_id).values(status=ToolJobStatus.FAILED.value, failure=message, updated_at=_now()))
    def _db(self) -> DatabaseEngine:
        if not self.ready or self._database is None: raise ToolError("Tool Engine is unavailable")
        return self._database


class PluginTools:
    def __init__(self, engine: ToolEngine, plugin_id: str) -> None: self._engine = engine; self.plugin_id = plugin_id
    def register(self, contract: ToolContract) -> None:
        if contract.owner != self.plugin_id: raise InvalidTool("Plugin cannot register another owner's Tool")
        self._engine.register(contract)
    def availability(self, tool_id: str) -> str: return self._engine.availability(self.plugin_id, tool_id)
    def submit(self, tool_id: str, values: Mapping[str, object], authentication: AuthenticationContext) -> ToolJob: return self._engine.submit(self.plugin_id, tool_id, values, authentication)
    def status(self, tool_id: str, job_id: str, authentication: AuthenticationContext) -> ToolJob: return self._engine.status(self.plugin_id, tool_id, job_id, authentication)
    def cancel(self, tool_id: str, job_id: str, authentication: AuthenticationContext) -> bool: return self._engine.cancel(self.plugin_id, tool_id, job_id, authentication)
    def unregister_all(self) -> None: self._engine.unregister_owner(self.plugin_id)


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl): return None


class HttpToolWorkerProvider:
    """Fixed operator-configured gateway; Plugin input can never choose the destination."""
    def __init__(self, base_url: str, token: str, timeout_seconds: int) -> None:
        parsed = urlsplit(base_url)
        if parsed.scheme not in {"http", "https"} or not parsed.hostname or parsed.username or parsed.password or parsed.query or parsed.fragment:
            raise InvalidTool("Tool worker URL is invalid")
        if not token or not 1 <= timeout_seconds <= 120: raise InvalidTool("Tool worker configuration is invalid")
        self._base = base_url.rstrip("/"); self._token = token; self._timeout = timeout_seconds; self._opener = build_opener(_NoRedirect)
    def healthcheck(self) -> bool:
        try: return self._request("GET", "/v1/health").get("status") == "healthy"
        except Exception: return False
    def submit(self, tool_id: str, job_id: str, values: Mapping[str, object]) -> ToolWorkerSubmission:
        value = self._request("POST", "/v1/jobs", {"tool_id": tool_id, "job_id": job_id, "input": dict(values)})
        return ToolWorkerSubmission(str(value.get("job_id", "")), ToolJobStatus(str(value.get("status", ""))))
    def state(self, external_id: str) -> ToolWorkerState:
        value = self._request("GET", f"/v1/jobs/{quote(external_id, safe='')}")
        result = value.get("result"); return ToolWorkerState(ToolJobStatus(str(value.get("status", ""))), int(value.get("progress", 0)),
            MappingProxyType(result) if isinstance(result, dict) else None, str(value["failure"])[:500] if value.get("failure") else None)
    def cancel(self, external_id: str) -> bool: return self._request("DELETE", f"/v1/jobs/{quote(external_id, safe='')}").get("cancelled") is True
    def _request(self, method: str, path: str, body: Mapping[str, object] | None = None) -> dict[str, object]:
        data = json.dumps(body, separators=(",", ":")).encode() if body is not None else None
        request = Request(self._base + path, data=data, method=method, headers={"authorization": f"Bearer {self._token}", "content-type": "application/json", "accept": "application/json"})
        try:
            with self._opener.open(request, timeout=self._timeout) as response:
                if response.status < 200 or response.status >= 300: raise ToolError("Tool worker request failed")
                raw = response.read(1_000_001)
        except (HTTPError, URLError, TimeoutError, OSError) as exc: raise ToolError("Tool worker request failed") from exc
        if len(raw) > 1_000_000: raise ToolError("Tool worker response is too large")
        try: value = json.loads(raw.decode("utf-8"))
        except (UnicodeError, json.JSONDecodeError) as exc: raise ToolError("Tool worker response is invalid") from exc
        if not isinstance(value, dict): raise ToolError("Tool worker response is invalid")
        return value


def _validate_input(contract: ToolContract, values: Mapping[str, object]) -> Mapping[str, object]:
    if not isinstance(values, Mapping) or set(values) - {field.field_id for field in contract.fields}: raise InvalidTool("Tool input contains unknown fields")
    output: dict[str, object] = {}
    for field in contract.fields:
        value = values.get(field.field_id)
        if value is None:
            if field.required: raise InvalidTool(f"Tool input is required: {field.field_id}")
            continue
        if field.kind in {ToolFieldKind.TEXT, ToolFieldKind.URL, ToolFieldKind.MEDIA, ToolFieldKind.SELECT}:
            if not isinstance(value, str): raise InvalidTool(f"Tool input has an invalid type: {field.field_id}")
            value = value.strip(); maximum = field.maximum_length or 2_000
            if not value or len(value) > maximum: raise InvalidTool(f"Tool input has an invalid length: {field.field_id}")
            if field.kind is ToolFieldKind.URL:
                parsed = urlsplit(value)
                if parsed.scheme not in {"http", "https"} or not parsed.hostname or parsed.username or parsed.password: raise InvalidTool("Tool URL input is invalid")
            elif field.kind is ToolFieldKind.MEDIA:
                try: value = str(UUID(value))
                except (ValueError, TypeError) as exc: raise InvalidTool("Tool Media input is invalid") from exc
            elif field.kind is ToolFieldKind.SELECT and value not in field.choices: raise InvalidTool("Tool selection is invalid")
        elif field.kind is ToolFieldKind.INTEGER:
            if not isinstance(value, int) or isinstance(value, bool): raise InvalidTool("Tool integer input is invalid")
        elif field.kind is ToolFieldKind.BOOLEAN:
            if not isinstance(value, bool): raise InvalidTool("Tool boolean input is invalid")
        output[field.field_id] = value
    return MappingProxyType(output)


def _validate_worker_state(state: ToolWorkerState) -> None:
    if not isinstance(state.status, ToolJobStatus) or not 0 <= state.progress <= 100 or (state.failure is not None and len(state.failure) > 500): raise ToolError("Tool worker state is invalid")
def _identifier(value: object) -> bool: return isinstance(value, str) and re.fullmatch(r"[a-z][a-z0-9_.-]{2,127}", value) is not None
def _external_id(value: object) -> bool: return isinstance(value, str) and re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.:-]{0,254}", value) is not None
def _dump(value: Mapping[str, object] | None) -> str: return json.dumps(dict(value or {}), ensure_ascii=False, separators=(",", ":"), sort_keys=True)
def _now() -> str: return datetime.now(timezone.utc).isoformat()
def _job(row: Mapping[str, object]) -> ToolJob:
    result = json.loads(str(row["result"])) if row["result"] is not None else None
    if result is not None and not isinstance(result, dict): raise ToolError("Stored Tool result is invalid")
    return ToolJob(str(row["job_id"]), str(row["tool_id"]), str(row["owner"]), ToolJobStatus(str(row["status"])), int(str(row["progress"])), MappingProxyType(result) if result else None, str(row["failure"]) if row["failure"] else None, str(row["owner_user_id"]), str(row["created_at"]), str(row["updated_at"]))
