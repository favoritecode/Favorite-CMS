"""FastAPI transport for the separately deployed Favorite Tool Worker."""
from __future__ import annotations

from contextlib import asynccontextmanager
from hmac import compare_digest
from typing import Iterator

from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, ConfigDict, Field

from .engine import WorkerConfiguration, WorkerEngine, WorkerError


class JobRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    tool_id: str = Field(min_length=3, max_length=128)
    job_id: str = Field(min_length=36, max_length=36)
    input: dict[str, object]


def create_app(configuration: WorkerConfiguration | None = None, engine: WorkerEngine | None = None) -> FastAPI:
    configured = configuration or WorkerConfiguration.from_environment()
    worker = engine or WorkerEngine(configured)
    @asynccontextmanager
    async def lifespan(_: FastAPI) -> Iterator[None]:
        yield
        worker.shutdown()
    application = FastAPI(title="Favorite CMS Tool Worker", version="0.1.0", lifespan=lifespan)

    @application.get("/")
    def information():
        return {
            "service": "Favorite CMS Tool Worker",
            "status": "running",
            "authentication": "required for Worker operations",
            "health": "/v1/health",
        }

    def authorize(authorization: str | None = Header(default=None)) -> None:
        expected = f"Bearer {configured.token}"
        if authorization is None or not compare_digest(authorization, expected): raise HTTPException(401, "Worker authentication required")
    @application.get("/v1/health")
    def health(_: None = Depends(authorize)): return {"status": "healthy"}
    @application.post("/v1/jobs")
    def submit(request: JobRequest, _: None = Depends(authorize)):
        try: job = worker.submit(request.tool_id, request.job_id, request.input)
        except WorkerError as exc: raise HTTPException(422, str(exc)) from exc
        return {"job_id": job.job_id, "status": job.status}
    @application.get("/v1/jobs/{job_id}")
    def state(job_id: str, _: None = Depends(authorize)):
        try: job = worker.state(job_id)
        except WorkerError as exc: raise HTTPException(404, str(exc)) from exc
        return {"status": job.status, "progress": job.progress, "result": job.result, "failure": job.failure}
    @application.delete("/v1/jobs/{job_id}")
    def cancel(job_id: str, _: None = Depends(authorize)):
        try: return {"cancelled": worker.cancel(job_id)}
        except WorkerError as exc: raise HTTPException(404, str(exc)) from exc
    @application.get("/v1/artifacts/{artifact_id}")
    def artifact(artifact_id: str, _: None = Depends(authorize)):
        try: path, media_type, filename = worker.artifact(artifact_id)
        except WorkerError as exc: raise HTTPException(404, str(exc)) from exc
        return FileResponse(path, media_type=media_type, filename=filename)
    application.state.worker = worker
    return application
