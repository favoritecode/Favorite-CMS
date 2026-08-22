"""Generic API and safe shortcode presentation for registered Tool contracts."""
from __future__ import annotations

from html import escape
import re
from typing import Mapping

from backend.core.container import ServiceContainer
from backend.engines.api import APIEngine, APIOperation, APIRequest, APIValidationError
from backend.engines.rendering import PresentationDecorator, RenderingEngine
from backend.engines.routing import RouteDefinition, RouteType
from backend.engines.tools import ToolContract, ToolEngine, ToolFieldKind, ToolJob


OWNER = "application.tools"
_SHORTCODE = re.compile(r"\[favorite-tool\s+id=(?:\"|&quot;)([a-z][a-z0-9_.-]{2,127})(?:\"|&quot;)\s*\]")


class ToolPlatformEngine:
    engine_id = "tool_platform"
    dependencies = ("tools", "api", "rendering")
    def __init__(self) -> None: self._container: ServiceContainer | None = None; self.ready = False
    def initialize(self, container: ServiceContainer) -> None: self._container = container; container.register("application.tools", self)
    def start(self) -> None:
        api = self._service("engine.api", APIEngine)
        api.register(RouteDefinition("platform.tools.submit", OWNER, RouteType.API, "/api/tools/{tool_id}/jobs", ("POST",), "platform.tools.submit"),
            APIOperation("platform.tools.submit", OWNER, _mapping, self._submit, lambda value: value, success_status=202))
        api.register(RouteDefinition("platform.tools.job", OWNER, RouteType.API, "/api/tools/{tool_id}/jobs/{job_id}", ("GET", "DELETE"), "platform.tools.job"),
            APIOperation("platform.tools.job", OWNER, _job_input, self._job, lambda value: value))
        self._service("engine.rendering", RenderingEngine).register_decorator(PresentationDecorator(
            "platform.tools.shortcodes", OWNER, self._decorate, 40))
        self.ready = True
    def shutdown(self) -> None: self.ready = False
    def _submit(self, request: APIRequest, data: object) -> object:
        assert isinstance(data, Mapping)
        return _job_value(self._service("engine.tools", ToolEngine).submit_registered(request.route.parameters["tool_id"], data, request.authentication))
    def _job(self, request: APIRequest, data: object) -> object:
        tools = self._service("engine.tools", ToolEngine); tool_id = request.route.parameters["tool_id"]; job_id = request.route.parameters["job_id"]
        if request.route.method == "DELETE": return {"cancelled": tools.cancel_registered(tool_id, job_id, request.authentication)}
        return _job_value(tools.status_registered(tool_id, job_id, request.authentication))
    def _decorate(self, body: str, route, model: object) -> str:
        matched = False; tools = self._service("engine.tools", ToolEngine)
        def replace(found: re.Match[str]) -> str:
            nonlocal matched; matched = True
            try: contract = tools.contract(found.group(1))
            except Exception: return '<div class="tool-unavailable" role="status">This tool is currently unavailable.</div>'
            if not contract.public: return '<div class="tool-unavailable" role="status">Sign in with permission to use this tool.</div>'
            return _tool_form(contract, tools.availability(contract.owner, contract.tool_id))
        rendered = _SHORTCODE.sub(replace, body)
        return rendered + (_TOOL_SCRIPT if matched else "")
    def _service(self, name: str, expected):
        if self._container is None: raise RuntimeError("Tool platform is unavailable")
        return self._container.resolve(name, expected)


def _mapping(query: Mapping[str, str], body: object) -> object:
    if query or not isinstance(body, dict) or len(body) > 50: raise APIValidationError("Tool job request is invalid")
    return body
def _job_input(query: Mapping[str, str], body: object) -> object:
    if query or body not in (None, {}, ""): raise APIValidationError("Tool job request is invalid")
    return {}
def _job_value(job: ToolJob) -> dict[str, object]: return {"id": job.job_id, "tool_id": job.tool_id, "status": job.status.value, "progress": job.progress, "result": dict(job.result) if job.result else None, "failure": job.failure, "created_at": job.created_at, "updated_at": job.updated_at}


def _tool_form(contract: ToolContract, availability: str) -> str:
    title = escape(contract.label); description = escape(contract.description)
    if availability != "available": return f'<section class="favorite-tool" data-tool-id="{escape(contract.tool_id, quote=True)}"><h2>{title}</h2><p>{description}</p><p role="status">Tool worker: {escape(availability.replace("_", " "))}.</p></section>'
    fields = "".join(_field(item) for item in contract.fields)
    return (f'<section class="favorite-tool" data-tool-id="{escape(contract.tool_id, quote=True)}"><h2>{title}</h2><p>{description}</p>'
            f'<form data-tool-form>{fields}<button type="submit">Run tool</button><p role="status" data-tool-status></p></form></section>')


def _field(field) -> str:
    identifier = escape(field.field_id, quote=True); label = escape(field.field_id.replace("_", " ").title())
    required = " required" if field.required else ""; maximum = f' maxlength="{field.maximum_length}"' if field.maximum_length else ""
    if field.kind is ToolFieldKind.SELECT:
        choices = "".join(f'<option value="{escape(item, quote=True)}">{escape(item)}</option>' for item in field.choices)
        control = f'<select name="{identifier}"{required}>{choices}</select>'
    elif field.kind is ToolFieldKind.BOOLEAN: control = f'<input name="{identifier}" type="checkbox">'
    elif field.kind is ToolFieldKind.INTEGER: control = f'<input name="{identifier}" type="number" step="1"{required}>'
    else:
        input_type = "url" if field.kind is ToolFieldKind.URL else "text"
        control = f'<input name="{identifier}" type="{input_type}"{required}{maximum}>'
    return f'<label>{label}{control}</label>'


_TOOL_SCRIPT = '''<script>(function(){document.querySelectorAll("form[data-tool-form]").forEach(function(form){if(form.dataset.bound)return;form.dataset.bound="1";form.addEventListener("submit",async function(event){event.preventDefault();const section=form.closest("[data-tool-id]"),status=form.querySelector("[data-tool-status]"),input={};new FormData(form).forEach(function(value,key){input[key]=value});form.querySelectorAll('input[type="checkbox"]').forEach(function(item){input[item.name]=item.checked});status.textContent="Submitting…";try{const response=await fetch("/api/tools/"+encodeURIComponent(section.dataset.toolId)+"/jobs",{method:"POST",headers:{"content-type":"application/json"},body:JSON.stringify(input)}),payload=await response.json();status.textContent=response.ok?"Job submitted: "+payload.data.id:((payload.error&&payload.error.message)||"Tool request failed.")}catch(_){status.textContent="Tool request failed."}})})})();</script>'''
