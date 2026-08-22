# Favorite CMS Tool Worker

This separately deployed service executes only two fixed operations: OCR and allowlisted direct-media retrieval. It is not a Plugin runtime and never imports Plugin code.

Install with `pip install ".[tool-worker]"`, configure from `.env.worker.example`, then run:

```text
uvicorn favorite_worker.app:create_app --factory --host 127.0.0.1 --port 8060
```

The CMS uses the private Worker URL/token through `FAVORITE_TOOL_WORKER_URL` and `FAVORITE_TOOL_WORKER_TOKEN`. Put both services on a private network. Install Tesseract separately and configure its fixed executable path. Bengali OCR also requires Tesseract's `ben` trained data.

Downloader scope is deliberately limited to direct HTTPS media files on the operator allowlist. It does not extract protected streams, bypass a platform, resolve YouTube pages, or download DRM/copyright-restricted content. Artifacts require Worker authentication; a public CMS artifact-delivery contract is not yet implemented.
