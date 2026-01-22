# services/fetcher-worker/app/server.py
import os
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from .contracts import FetchRequest
from .util import decode_pubsub_data, utc_now_iso_z
from .fetch import fetch_url_streaming, sha256_bytes
from .clean import clean_html_to_text
from .gcs import GcsEvidenceWriter

    
def create_app() -> FastAPI:
    app = FastAPI(title="fetcher-worker", version="phase4")

    @app.get("/")
    def root():
        return {"ok": True, "service": "fetcher-worker"}

    @app.get("/healthz") #this does not work
    @app.get("/healthz/") # this works
    def healthz():
        return {"ok": True, "service": "fetcher-worker"}
    
    @app.post("/pubsub/push")
    async def pubsub_push(req: Request):

        bucket_name = os.environ.get("EVIDENCE_BUCKET")
        if not bucket_name:
            raise RuntimeError("EVIDENCE_BUCKET env var is required")


        writer = GcsEvidenceWriter(bucket_name)

        body = await req.json()
        msg = body.get("message", {})
        payload = decode_pubsub_data(msg["data"])
        fr = FetchRequest.from_dict(payload)

        prefix = writer.build_prefix(fr.fetch_timestamp, fr.request_id)

        fetch = fetch_url_streaming(
            fr.url,
            max_bytes=fr.options.max_bytes,
            timeout_ms=fr.options.timeout_ms,
        )

        html = fetch.raw_bytes.decode("utf-8", errors="replace")
        clean = clean_html_to_text(html)

        writer.write_bytes(prefix + "raw.html", fetch.raw_bytes, "text/html")
        writer.write_text(prefix + "clean.txt", clean)

        meta = {
            "request_id": fr.request_id,
            "url": fr.url,
            "final_url": fetch.final_url,
            "fetched_at": utc_now_iso_z(),
            "http_status": fetch.status,
            "truncated": fetch.truncated,
            "hash_raw": sha256_bytes(fetch.raw_bytes),
            "clean_chars": len(clean),
        }

        writer.write_json(prefix + "meta.json", meta)
        writer.write_json(prefix + "done.json", {"ok": True})

        return {"ok": True}

    return app
app = create_app()
