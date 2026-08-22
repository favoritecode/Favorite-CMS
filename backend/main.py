"""FastAPI transport adapter for the Core-owned Phase 7 request pipeline."""

from contextlib import asynccontextmanager

import json
import re
from uuid import uuid4
from collections.abc import Callable

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse, Response

from backend.bootstrap import build_kernel
from backend.core import Kernel
from backend.engines.api import APIEngine
from backend.engines.rendering import RenderingEngine
from backend.engines.routing import InvalidRoute, MethodNotAllowed, RouteNotFound, RouteType, RoutingEngine, RoutingFailure


def create_app(*, on_started: Callable[[Kernel], None] | None = None) -> FastAPI:
    """Create the application around the Phase 1 Core lifecycle."""
    kernel = build_kernel()

    @asynccontextmanager
    async def lifespan(application: FastAPI):
        kernel.bootstrap()
        if on_started is not None:
            on_started(kernel)
        application.state.kernel = kernel
        try:
            yield
        finally:
            kernel.shutdown()

    application = FastAPI(title="Favorite CMS", version="0.1.0", lifespan=lifespan,
                          docs_url=None, redoc_url=None, openapi_url=None)

    @application.api_route("/{request_path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"], include_in_schema=False)
    async def dispatch(request: Request, request_path: str) -> Response:
        active_kernel: Kernel = request.app.state.kernel
        routing = active_kernel.container.resolve("engine.routing", RoutingEngine)
        request_id = _request_id(request.headers.get("x-request-id"))
        path = "/" + request_path
        try:
            route = routing.resolve(request.method, path)
        except RouteNotFound:
            return JSONResponse({"success": False, "error": {"code": "route_not_found", "message": "Route was not found"}, "request_id": request_id}, 404)
        except MethodNotAllowed:
            return JSONResponse({"success": False, "error": {"code": "method_not_allowed", "message": "Request method is not supported"}, "request_id": request_id}, 405)
        except InvalidRoute:
            return JSONResponse({"success": False, "error": {"code": "invalid_route", "message": "Routing input is invalid"}, "request_id": request_id}, 400)
        except RoutingFailure:
            return JSONResponse({"success": False, "error": {"code": "routing_failure", "message": "The Route is unavailable"}, "request_id": request_id}, 503)
        credential = _bearer(request.headers.get("authorization"))
        if route.route_type is RouteType.API:
            api = active_kernel.container.resolve("engine.api", APIEngine)
            raw = await request.body()
            if len(raw) > 14_000_000:
                return JSONResponse({"success": False, "error": {"code": "payload_too_large", "message": "Request body is too large"}, "request_id": request_id}, 413)
            else:
                try: body = json.loads(raw) if raw else None
                except (UnicodeError, json.JSONDecodeError):
                    result = api.invalid_request("Request body is invalid", request_id=request_id)
                else:
                    query = {key: value for key, value in request.query_params.items()}
                    result = api.handle(route, query=query, body=body, headers=request.headers,
                                        credential=credential, request_id=request_id)
            if isinstance(result.body, bytes):
                return Response(result.body, result.status, headers=dict(result.headers), media_type=result.headers.get("content-type"))
            return JSONResponse(dict(result.body), result.status, headers=dict(result.headers))
        rendering = active_kernel.container.resolve("engine.rendering", RenderingEngine)
        rendered = rendering.render(route, request_id=request_id, credential=credential)
        return HTMLResponse(rendered.body, rendered.status, headers=dict(rendered.headers), media_type=rendered.content_type)

    return application

def _bearer(value: str | None) -> str | None:
    if value is None: return None
    scheme, separator, credential = value.partition(" ")
    if separator and scheme.lower() == "bearer" and credential and len(credential) <= 8192:
        return credential
    return None

def _request_id(value: str | None) -> str:
    if value is not None and re.fullmatch(r"[A-Za-z0-9._-]{1,128}", value): return value
    return str(uuid4())


app = create_app()
