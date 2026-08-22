from __future__ import annotations

from pathlib import Path
import subprocess
from time import sleep
from uuid import uuid4

from fastapi.testclient import TestClient
import pytest

from favorite_worker.app import create_app
from favorite_worker.engine import WorkerConfiguration, WorkerEngine, WorkerError, _fetch, _safe_filename


@pytest.fixture
def worker(tmp_path: Path):
    configuration = WorkerConfiguration("worker-test-token-that-is-at-least-thirty-two-bytes", frozenset({"media.example.test"}), tmp_path)
    engine = WorkerEngine(configuration)
    try: yield configuration, engine
    finally: engine.shutdown()


def test_worker_transport_requires_bearer_and_supports_only_fixed_tools(worker, monkeypatch: pytest.MonkeyPatch) -> None:
    configuration, engine = worker
    monkeypatch.setattr("favorite_worker.engine._fetch", lambda url, config: (b"image", "image/png", "sample.png"))
    client = TestClient(create_app(configuration, engine)); headers = {"authorization": f"Bearer {configuration.token}"}
    assert client.get("/v1/health").status_code == 401
    assert client.get("/v1/health", headers=headers).json() == {"status": "healthy"}
    unknown = client.post("/v1/jobs", headers=headers, json={"tool_id": "favorite.tool.unknown", "job_id": str(uuid4()), "input": {"url": "https://media.example.test/x"}})
    assert unknown.status_code == 422
    accepted = client.post("/v1/jobs", headers=headers, json={"tool_id": "favorite.tool.direct-media-download", "job_id": str(uuid4()), "input": {"url": "https://media.example.test/x"}})
    assert accepted.status_code == 200 and accepted.json()["status"] in {"pending", "running", "completed"}
    job_id = accepted.json()["job_id"]
    for _ in range(50):
        state = client.get(f"/v1/jobs/{job_id}", headers=headers).json()
        if state["status"] == "completed": break
    assert state["result"]["media_type"] == "image/png" and "artifact_id" in state["result"]
    artifact = client.get(f'/v1/artifacts/{state["result"]["artifact_id"]}', headers=headers)
    assert artifact.status_code == 200 and artifact.content == b"image"


def test_ocr_uses_fixed_command_without_shell_and_bounds_result(worker, monkeypatch: pytest.MonkeyPatch) -> None:
    configuration, engine = worker
    monkeypatch.setattr("favorite_worker.engine._fetch", lambda url, config: (b"image", "image/png", "sample.png"))
    observed = {}
    def run(command, **kwargs):
        observed.update({"command": command, **kwargs})
        Path(str(command[2]) + ".txt").write_text("বাংলা OCR text", encoding="utf-8")
        return subprocess.CompletedProcess(command, 0, b"", b"")
    monkeypatch.setattr("favorite_worker.engine.subprocess.run", run)
    job = engine.submit("favorite.tool.ocr", str(uuid4()), {"url": "https://media.example.test/x.png", "language": "ben"})
    for _ in range(50):
        job = engine.state(job.job_id)
        if job.status == "completed": break
        sleep(0.01)
    assert job.result == {"text": "বাংলা OCR text", "language": "ben", "characters": 14}
    assert observed["shell"] is False and observed["command"][0] == configuration.tesseract_command


def test_fetch_rejects_non_https_unlisted_private_and_oversized_sources(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    configuration = WorkerConfiguration("worker-test-token-that-is-at-least-thirty-two-bytes", frozenset({"media.example.test"}), tmp_path, maximum_download_bytes=8)
    with pytest.raises(WorkerError, match="not allowed"): _fetch("http://media.example.test/a.png", configuration)
    with pytest.raises(WorkerError, match="not allowed"): _fetch("https://other.example.test/a.png", configuration)
    monkeypatch.setattr("favorite_worker.engine.socket.getaddrinfo", lambda *args, **kwargs: [(None, None, None, None, ("127.0.0.1", 443))])
    with pytest.raises(WorkerError, match="Private"): _fetch("https://media.example.test/a.png", configuration)


def test_fetch_pins_the_validated_address_and_filename_matches_detected_media(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    configuration = WorkerConfiguration("worker-test-token-that-is-at-least-thirty-two-bytes", frozenset({"media.example.test"}), tmp_path)
    resolutions = []
    monkeypatch.setattr("favorite_worker.engine.socket.getaddrinfo", lambda *args, **kwargs: resolutions.append(args) or [(None, None, None, None, ("93.184.216.34", 443))])

    class Headers:
        def get_content_type(self): return "image/png"
    class Response:
        status = 200; headers = Headers()
        def getheader(self, name): return None
        def read(self, limit): return b"\x89PNG\r\n\x1a\nimage"
    class Connection:
        def __init__(self, host, address, timeout):
            assert (host, address) == ("media.example.test", "93.184.216.34")
        def request(self, method, target, headers): assert method == "GET" and target == "/payload.exe"
        def getresponse(self): return Response()
        def close(self): pass

    monkeypatch.setattr("favorite_worker.engine._PinnedHTTPSConnection", Connection)
    _, media_type, filename = _fetch("https://media.example.test/payload.exe", configuration)
    assert len(resolutions) == 1 and media_type == "image/png" and filename == "payload.png"
    assert _safe_filename("archive.pdf.exe", "application/pdf") == "archive.pdf"
