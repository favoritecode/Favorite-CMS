"""Fixed-operation OCR/direct-media worker with bounded network and process use."""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from hashlib import sha256
from http.client import HTTPSConnection
from ipaddress import ip_address
import json
import mimetypes
import os
from pathlib import Path
import re
import socket
import ssl
import subprocess
from threading import Lock
from typing import Mapping
from urllib.parse import urlsplit
from uuid import uuid4


class WorkerError(ValueError): pass


@dataclass(frozen=True)
class WorkerConfiguration:
    token: str
    allowed_hosts: frozenset[str]
    spool: Path
    tesseract_command: str = "tesseract"
    maximum_download_bytes: int = 25 * 1024 * 1024
    timeout_seconds: int = 20
    concurrency: int = 2

    @classmethod
    def from_environment(cls) -> "WorkerConfiguration":
        token = os.environ.get("FAVORITE_WORKER_TOKEN", "")
        hosts = frozenset(item.strip().casefold() for item in os.environ.get("FAVORITE_WORKER_ALLOWED_HOSTS", "").split(",") if item.strip())
        spool = Path(os.environ.get("FAVORITE_WORKER_SPOOL", "worker-storage")).resolve()
        if len(token) < 32: raise WorkerError("Worker token is not configured")
        if not hosts: raise WorkerError("Worker source host allowlist is not configured")
        return cls(token, hosts, spool,
            os.environ.get("FAVORITE_WORKER_TESSERACT", "tesseract"),
            _bounded_int("FAVORITE_WORKER_MAX_DOWNLOAD_BYTES", 25 * 1024 * 1024, 1_024, 100 * 1024 * 1024),
            _bounded_int("FAVORITE_WORKER_TIMEOUT_SECONDS", 20, 1, 120),
            _bounded_int("FAVORITE_WORKER_CONCURRENCY", 2, 1, 8))


@dataclass
class WorkerJob:
    job_id: str
    tool_id: str
    status: str = "pending"
    progress: int = 0
    result: dict[str, object] | None = None
    failure: str | None = None
    cancelled: bool = False


@dataclass
class WorkerEngine:
    configuration: WorkerConfiguration
    _jobs: dict[str, WorkerJob] = field(default_factory=dict)
    _lock: Lock = field(default_factory=Lock)
    _executor: ThreadPoolExecutor = field(init=False)

    def __post_init__(self) -> None:
        self.configuration.spool.mkdir(parents=True, exist_ok=True)
        self._executor = ThreadPoolExecutor(max_workers=self.configuration.concurrency, thread_name_prefix="favorite-tool")

    def shutdown(self) -> None: self._executor.shutdown(wait=False, cancel_futures=True)
    def submit(self, tool_id: str, job_id: str, values: Mapping[str, object]) -> WorkerJob:
        if tool_id not in {"favorite.tool.ocr", "favorite.tool.direct-media-download"}: raise WorkerError("Tool is not supported by this Worker")
        if not re.fullmatch(r"[0-9a-f-]{36}", job_id) or job_id in self._jobs: raise WorkerError("Job identifier is invalid")
        job = WorkerJob(job_id, tool_id)
        with self._lock: self._jobs[job_id] = job
        self._executor.submit(self._execute, job, dict(values))
        return job
    def state(self, job_id: str) -> WorkerJob:
        with self._lock:
            try: return self._jobs[job_id]
            except KeyError as exc: raise WorkerError("Job was not found") from exc
    def cancel(self, job_id: str) -> bool:
        job = self.state(job_id)
        with self._lock:
            if job.status not in {"pending", "running"}: return False
            job.cancelled = True; job.status = "cancelled"; job.progress = 0
        return True
    def artifact(self, artifact_id: str) -> tuple[Path, str, str]:
        if not re.fullmatch(r"[0-9a-f]{32}", artifact_id): raise WorkerError("Artifact identifier is invalid")
        metadata = self.configuration.spool / f"{artifact_id}.json"; payload = self.configuration.spool / f"{artifact_id}.bin"
        if not metadata.is_file() or not payload.is_file(): raise WorkerError("Artifact was not found")
        value = json.loads(metadata.read_text(encoding="utf-8"))
        return payload, str(value["media_type"]), str(value["filename"])
    def _execute(self, job: WorkerJob, values: dict[str, object]) -> None:
        try:
            with self._lock:
                if job.cancelled: return
                job.status = "running"; job.progress = 5
            result = self._ocr(values, job) if job.tool_id == "favorite.tool.ocr" else self._download(values, job)
            with self._lock:
                if job.cancelled: return
                job.result = result; job.progress = 100; job.status = "completed"
        except Exception as exc:
            with self._lock:
                if not job.cancelled:
                    job.status = "failed"; job.failure = _safe_failure(exc); job.progress = 0
    def _download(self, values: Mapping[str, object], job: WorkerJob) -> dict[str, object]:
        url = _required_url(values); data, media_type, filename = _fetch(url, self.configuration)
        if not media_type.startswith(("image/", "video/", "audio/")) and media_type != "application/pdf":
            raise WorkerError("Source is not an allowed media type")
        artifact_id = uuid4().hex; payload = self.configuration.spool / f"{artifact_id}.bin"
        payload.write_bytes(data)
        (self.configuration.spool / f"{artifact_id}.json").write_text(json.dumps({"media_type": media_type, "filename": filename}), encoding="utf-8")
        return {"artifact_id": artifact_id, "filename": filename, "media_type": media_type, "size": len(data), "sha256": sha256(data).hexdigest()}
    def _ocr(self, values: Mapping[str, object], job: WorkerJob) -> dict[str, object]:
        url = _required_url(values); language = str(values.get("language", "eng"))
        if language not in {"eng", "ben", "eng+ben"}: raise WorkerError("OCR language is not supported")
        data, media_type, _ = _fetch(url, self.configuration)
        if media_type not in {"image/png", "image/jpeg", "image/webp", "image/tiff", "image/bmp"}: raise WorkerError("OCR source is not a supported image")
        input_path = self.configuration.spool / f"ocr-{job.job_id}.input"; output_base = self.configuration.spool / f"ocr-{job.job_id}"
        try:
            input_path.write_bytes(data)
            command = [self.configuration.tesseract_command, str(input_path), str(output_base), "-l", language, "--psm", "3"]
            completed = subprocess.run(command, shell=False, capture_output=True, timeout=self.configuration.timeout_seconds, check=False)
            if completed.returncode != 0: raise WorkerError("OCR engine could not process the image")
            output = output_base.with_suffix(".txt")
            text = output.read_text(encoding="utf-8").strip()
            if len(text) > 500_000: raise WorkerError("OCR result exceeds the text limit")
            return {"text": text, "language": language, "characters": len(text)}
        except (OSError, subprocess.SubprocessError, UnicodeError) as exc: raise WorkerError("OCR engine is unavailable") from exc
        finally:
            input_path.unlink(missing_ok=True); output_base.with_suffix(".txt").unlink(missing_ok=True)


class _PinnedHTTPSConnection(HTTPSConnection):
    """Connect to one validated address while verifying TLS for the allowlisted host."""
    def __init__(self, host: str, address: str, timeout: int) -> None:
        super().__init__(host, 443, timeout=timeout, context=ssl.create_default_context())
        self._validated_address = address

    def connect(self) -> None:
        self.sock = socket.create_connection((self._validated_address, 443), self.timeout, self.source_address)
        self.sock = self._context.wrap_socket(self.sock, server_hostname=self.host)


def _fetch(url: str, configuration: WorkerConfiguration) -> tuple[bytes, str, str]:
    parsed = urlsplit(url)
    host = (parsed.hostname or "").casefold()
    if (parsed.scheme != "https" or not host or host not in configuration.allowed_hosts or parsed.port not in {None, 443}
            or parsed.username or parsed.password or parsed.fragment):
        raise WorkerError("Source URL is not allowed")
    address = _public_addresses(host)[0]
    target = parsed.path or "/"
    if parsed.query: target += f"?{parsed.query}"
    connection = _PinnedHTTPSConnection(host, address, configuration.timeout_seconds)
    try:
        connection.request("GET", target, headers={"user-agent": "Favorite-CMS-Tool-Worker/0.1", "accept": "image/*,video/*,audio/*,application/pdf"})
        response = connection.getresponse()
        if not 200 <= response.status < 300: raise WorkerError("Source download failed safely")
        declared_media_type = response.headers.get_content_type().casefold()
        length = response.getheader("content-length")
        if length and int(length) > configuration.maximum_download_bytes: raise WorkerError("Source exceeds the download limit")
        data = response.read(configuration.maximum_download_bytes + 1)
        media_type = _sniff_media_type(data)
        if media_type is None or (declared_media_type != "application/octet-stream" and
                declared_media_type.split("/", 1)[0] != media_type.split("/", 1)[0]):
            raise WorkerError("Source media signature is not allowed")
        filename = _safe_filename(Path(parsed.path).name, media_type)
    except WorkerError: raise
    except (TimeoutError, OSError, ValueError, ssl.SSLError) as exc: raise WorkerError("Source download failed safely") from exc
    finally: connection.close()
    if len(data) > configuration.maximum_download_bytes: raise WorkerError("Source exceeds the download limit")
    return data, media_type, filename


def _public_addresses(host: str) -> tuple[str, ...]:
    try: addresses = {item[4][0] for item in socket.getaddrinfo(host, 443, type=socket.SOCK_STREAM)}
    except OSError as exc: raise WorkerError("Source host could not be resolved") from exc
    for value in addresses:
        address = ip_address(value)
        if not address.is_global: raise WorkerError("Private or local source hosts are prohibited")
    if not addresses: raise WorkerError("Source host could not be resolved")
    return tuple(sorted(addresses))


def _required_url(values: Mapping[str, object]) -> str:
    if set(values) - {"url", "language"} or not isinstance(values.get("url"), str): raise WorkerError("Tool input is invalid")
    return str(values["url"])
def _safe_filename(value: str, media_type: str) -> str:
    name = re.sub(r"[^A-Za-z0-9._-]", "_", value)[:120].strip("._")
    extension = mimetypes.guess_extension(media_type) or ".bin"
    stem = name.rsplit(".", 1)[0].strip("._") if name else "download"
    stem = stem or "download"
    return stem if stem.casefold().endswith(extension.casefold()) else f"{stem}{extension}"
def _sniff_media_type(data: bytes) -> str | None:
    if data.startswith(b"\x89PNG\r\n\x1a\n"): return "image/png"
    if data.startswith(b"\xff\xd8\xff"): return "image/jpeg"
    if data.startswith((b"II*\x00", b"MM\x00*")): return "image/tiff"
    if data.startswith(b"BM"): return "image/bmp"
    if len(data) >= 12 and data.startswith(b"RIFF") and data[8:12] == b"WEBP": return "image/webp"
    if data.startswith(b"%PDF-"): return "application/pdf"
    if len(data) >= 12 and data[4:8] == b"ftyp": return "video/mp4"
    if data.startswith(b"\x1aE\xdf\xa3"): return "video/webm"
    if data.startswith(b"OggS"): return "audio/ogg"
    if len(data) >= 12 and data.startswith(b"RIFF") and data[8:12] == b"WAVE": return "audio/wav"
    if data.startswith(b"ID3") or data.startswith((b"\xff\xfb", b"\xff\xf3", b"\xff\xf2")): return "audio/mpeg"
    return None
def _safe_failure(exc: Exception) -> str:
    return str(exc)[:300] if isinstance(exc, WorkerError) else "Worker operation failed safely"
def _bounded_int(name: str, default: int, minimum: int, maximum: int) -> int:
    try: value = int(os.environ.get(name, str(default)))
    except ValueError as exc: raise WorkerError(f"{name} is invalid") from exc
    if not minimum <= value <= maximum: raise WorkerError(f"{name} is invalid")
    return value
