from fastapi import FastAPI, File, UploadFile, Form, BackgroundTasks, Request
from fastapi.responses import Response, HTMLResponse, JSONResponse, FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
import numpy as np
import cv2
import os
import uuid
import io
import zipfile
import re
import json
import socket
import time
from urllib.parse import urlsplit, urlunsplit

from  web import tasks

app = FastAPI()
app.mount("/static", StaticFiles(directory="web/static"), name="static")

# results dir
RESULT_DIR = os.path.join('web', 'results')
os.makedirs(RESULT_DIR, exist_ok=True)
SHARE_DB_PATH = os.path.join(RESULT_DIR, "shares.json")


def _result_path_from_id(result_id: str):
    if not isinstance(result_id, str):
        return None
    if not re.fullmatch(r"[0-9a-fA-F]{32}", result_id):
        return None
    return os.path.join(RESULT_DIR, f"{result_id.lower()}.jpg")


def _meta_path_from_id(result_id: str):
    if not isinstance(result_id, str):
        return None
    if not re.fullmatch(r"[0-9a-fA-F]{32}", result_id):
        return None
    return os.path.join(RESULT_DIR, f"{result_id.lower()}.meta.json")


def _load_job_meta(job_id: str):
    p = _meta_path_from_id(job_id)
    if not p or not os.path.exists(p):
        return {}
    try:
        with open(p, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _load_share_db():
    if not os.path.exists(SHARE_DB_PATH):
        return {}
    try:
        with open(SHARE_DB_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _read_text_with_fallback(path: str):
    with open(path, "rb") as f:
        raw = f.read()
    for enc in ("utf-8", "gb18030"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    # Last resort: keep service available instead of crashing on bad bytes.
    return raw.decode("latin-1", errors="replace")


def _save_share_db(data: dict):
    with open(SHARE_DB_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _create_share_token(result_id: str):
    db = _load_share_db()
    token = uuid.uuid4().hex
    db[token] = result_id.lower()
    _save_share_db(db)
    return token


def _detect_lan_ip():
    """Best-effort LAN IP detection for share links."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]
    except Exception:
        return None
    finally:
        s.close()


def _build_share_base_url(request: Request):
    # Allow explicit override in deployment.
    env_base = os.getenv("SHARE_BASE_URL", "").strip()
    if env_base:
        return env_base.rstrip("/")

    base = str(request.base_url).rstrip("/")
    parts = urlsplit(base)
    host = parts.hostname or ""
    if host in {"127.0.0.1", "localhost", "::1"}:
        lan_ip = _detect_lan_ip()
        if lan_ip:
            netloc = f"{lan_ip}:{parts.port}" if parts.port else lan_ip
            return urlunsplit((parts.scheme, netloc, "", "", "")).rstrip("/")
    return base


@app.get("/", response_class=HTMLResponse)
async def index():
    return HTMLResponse(_read_text_with_fallback("web/static/index.html"))


@app.get("/actions")
async def list_actions():
    return JSONResponse(
        {
            "actions": tasks.get_supported_actions(),
            "pipeline_separator": "|",
            "examples": ["trim|orientation|bleach", "shadow|sharpen"],
        }
    )


@app.post("/process")
async def process(file: UploadFile = File(...), action: str = Form(...)):
    try:
        tasks.parse_actions(action)
    except Exception as e:
        return Response(content=f"Invalid action: {e}", status_code=400)

    t0 = time.perf_counter()
    data = await file.read()
    nparr = np.frombuffer(data, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_UNCHANGED)
    if img is None:
        return Response(content="Invalid image", status_code=400)

    # synchronous processing (keeps previous behavior)
    try:
        out = tasks.process_image_bytes(data, action)
    except Exception as e:
        return Response(content=f"Processing error: {e}", status_code=500)
    elapsed_ms = int((time.perf_counter() - t0) * 1000)

    # Save sync result so it can join current-session "download all".
    result_id = uuid.uuid4().hex
    result_path = _result_path_from_id(result_id)
    if result_path:
        with open(result_path, "wb") as f:
            f.write(out)

    # Return image bytes and id for client-side session tracking.
    return Response(
        content=out,
        media_type='image/jpeg',
        headers={"X-Result-Id": result_id, "X-Elapsed-Ms": str(elapsed_ms)},
    )


@app.post('/process_async')
async def process_async(background_tasks: BackgroundTasks, file: UploadFile = File(...), action: str = Form(...)):
    try:
        tasks.parse_actions(action)
    except Exception as e:
        return Response(content=f"Invalid action: {e}", status_code=400)

    data = await file.read()
    job_id = uuid.uuid4().hex
    # schedule background task
    background_tasks.add_task(tasks.process_job_bg, job_id, data, action)
    return JSONResponse({'job_id': job_id, 'status_url': f'/status/{job_id}', 'result_url': f'/result/{job_id}'} )


@app.post('/process_async_batch')
async def process_async_batch(
    background_tasks: BackgroundTasks,
    files: list[UploadFile] = File(...),
    action: str = Form(...),
):
    try:
        tasks.parse_actions(action)
    except Exception as e:
        return Response(content=f"Invalid action: {e}", status_code=400)

    jobs = []
    for up in files:
        data = await up.read()
        nparr = np.frombuffer(data, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_UNCHANGED)
        if img is None:
            jobs.append(
                {
                    "filename": up.filename or "unknown",
                    "status": "rejected",
                    "reason": "invalid image",
                }
            )
            continue

        job_id = uuid.uuid4().hex
        background_tasks.add_task(tasks.process_job_bg, job_id, data, action)
        jobs.append(
            {
                "filename": up.filename or "unknown",
                "job_id": job_id,
                "status": "queued",
                "status_url": f"/status/{job_id}",
                "result_url": f"/result/{job_id}",
            }
        )
    return JSONResponse({"action": action, "jobs": jobs})


@app.get('/status/{job_id}')
async def job_status(job_id: str):
    status_path = os.path.join(RESULT_DIR, f'{job_id}.status')
    result_path = os.path.join(RESULT_DIR, f'{job_id}.jpg')
    meta = _load_job_meta(job_id)
    if os.path.exists(result_path):
        out = {'id': job_id, 'status': 'finished'}
        if "elapsed_ms" in meta:
            out["elapsed_ms"] = meta.get("elapsed_ms")
        if "error" in meta:
            out["error"] = meta.get("error")
        return JSONResponse(out)
    if os.path.exists(status_path):
        with open(status_path, 'r', encoding='utf-8') as f:
            status = f.read().strip()
        out = {'id': job_id, 'status': status}
        if "elapsed_ms" in meta:
            out["elapsed_ms"] = meta.get("elapsed_ms")
        if "error" in meta:
            out["error"] = meta.get("error")
        return JSONResponse(out)
    return JSONResponse({'id': job_id, 'status': 'queued'})


@app.get('/result/{job_id}')
async def job_result(job_id: str):
    result_path = os.path.join(RESULT_DIR, f'{job_id}.jpg')
    if os.path.exists(result_path):
        # return as inline image
        return FileResponse(result_path, media_type='image/jpeg')
    else:
        return Response(content='Result not ready', status_code=404)


@app.get('/download/{job_id}')
async def download_result(job_id: str):
    """Download result as attachment for the given job_id."""
    result_path = os.path.join(RESULT_DIR, f'{job_id}.jpg')
    if os.path.exists(result_path):
        return FileResponse(result_path, media_type='application/octet-stream', filename=f'{job_id}.jpg')
    else:
        return Response(content='Result not ready', status_code=404)


@app.post('/share')
async def create_share_link(request: Request):
    try:
        payload = await request.json()
    except Exception:
        payload = {}

    result_id = payload.get("result_id", "") if isinstance(payload, dict) else ""
    result_path = _result_path_from_id(result_id)
    if not result_path or not os.path.exists(result_path):
        return Response(content="Result not found", status_code=404)

    token = _create_share_token(result_id)
    base = _build_share_base_url(request)
    share_url = f"{base}/share/{token}"
    return JSONResponse({"token": token, "share_url": share_url})


@app.get('/share/{token}')
async def shared_page(token: str):
    db = _load_share_db()
    result_id = db.get(token)
    if not result_id:
        return Response(content="Share link is invalid or expired", status_code=404)

    result_path = _result_path_from_id(result_id)
    if not result_path or not os.path.exists(result_path):
        return Response(content="Shared result not found", status_code=404)

    html = f"""<!doctype html>
<html lang="zh-CN">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width,initial-scale=1" />
    <title>共享结果</title>
    <style>
      body{{font-family:Arial,Helvetica,sans-serif;margin:20px;color:#222}}
      img{{max-width:100%;height:auto;border:1px solid #ddd;background:#fafafa}}
      .box{{max-width:1000px;margin:0 auto}}
    </style>
  </head>
  <body>
    <div class="box">
      <h2>文档处理结果</h2>
      <p>ID: {result_id}</p>
      <img src="/share/{token}/image" alt="shared-result" />
    </div>
  </body>
</html>"""
    return HTMLResponse(content=html)


@app.get('/share/{token}/image')
async def shared_image(token: str):
    db = _load_share_db()
    result_id = db.get(token)
    if not result_id:
        return Response(content="Share link is invalid or expired", status_code=404)

    result_path = _result_path_from_id(result_id)
    if not result_path or not os.path.exists(result_path):
        return Response(content="Shared result not found", status_code=404)

    return FileResponse(result_path, media_type='image/jpeg')


@app.post('/download_all')
async def download_all_results(request: Request):
    """Package only current-session result ids provided by client."""
    try:
        payload = await request.json()
    except Exception:
        payload = {}

    ids = payload.get("ids", []) if isinstance(payload, dict) else []
    picked = []
    seen = set()
    for rid in ids:
        if not isinstance(rid, str) or rid in seen:
            continue
        seen.add(rid)
        p = _result_path_from_id(rid)
        if p and os.path.exists(p):
            picked.append((rid, p))

    if not picked:
        return Response(content='No result files for this session', status_code=404)

    mem = io.BytesIO()
    with zipfile.ZipFile(mem, 'w', compression=zipfile.ZIP_DEFLATED) as zf:
        for rid, p in picked:
            zf.write(p, arcname=f'{rid}.jpg')
    mem.seek(0)

    headers = {'Content-Disposition': 'attachment; filename="results.zip"'}
    return StreamingResponse(mem, media_type='application/zip', headers=headers)


@app.post('/clear_results')
async def clear_results(request: Request):
    """Delete session result/status files provided by client ids."""
    try:
        payload = await request.json()
    except Exception:
        payload = {}

    ids = payload.get("ids", []) if isinstance(payload, dict) else []
    removed = 0
    seen = set()
    for rid in ids:
        if not isinstance(rid, str) or rid in seen:
            continue
        seen.add(rid)
        p = _result_path_from_id(rid)
        if p and os.path.exists(p):
            os.remove(p)
            removed += 1
        if re.fullmatch(r"[0-9a-fA-F]{32}", rid):
            status_path = os.path.join(RESULT_DIR, f'{rid.lower()}.status')
            if os.path.exists(status_path):
                os.remove(status_path)
                removed += 1
            meta_path = os.path.join(RESULT_DIR, f'{rid.lower()}.meta.json')
            if os.path.exists(meta_path):
                os.remove(meta_path)
                removed += 1

    # Remove share entries pointing to deleted results.
    db = _load_share_db()
    if db:
        deleted_ids = {rid.lower() for rid in ids if isinstance(rid, str)}
        filtered = {k: v for k, v in db.items() if v not in deleted_ids}
        if filtered != db:
            _save_share_db(filtered)

    return JSONResponse({'removed': removed})
