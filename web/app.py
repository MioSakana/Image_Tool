from fastapi import FastAPI, File, UploadFile, Form, BackgroundTasks
from fastapi.responses import Response, HTMLResponse, JSONResponse, FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
import numpy as np
import cv2
import os
import uuid

from  web import tasks

app = FastAPI()
app.mount("/static", StaticFiles(directory="web/static"), name="static")

# results dir
RESULT_DIR = os.path.join('web', 'results')
os.makedirs(RESULT_DIR, exist_ok=True)


@app.get("/", response_class=HTMLResponse)
async def index():
    with open("web/static/index.html", "r", encoding="utf-8") as f:
        return HTMLResponse(f.read())


@app.post("/process")
async def process(file: UploadFile = File(...), action: str = Form(...)):
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

    # Encode to JPEG bytes (already done in task), return
    return Response(content=out, media_type='image/jpeg')


@app.post('/process_async')
async def process_async(background_tasks: BackgroundTasks, file: UploadFile = File(...), action: str = Form(...)):
    data = await file.read()
    job_id = uuid.uuid4().hex
    # schedule background task
    background_tasks.add_task(tasks.process_job_bg, job_id, data, action)
    return JSONResponse({'job_id': job_id, 'status_url': f'/status/{job_id}', 'result_url': f'/result/{job_id}'} )


@app.get('/status/{job_id}')
async def job_status(job_id: str):
    status_path = os.path.join(RESULT_DIR, f'{job_id}.status')
    result_path = os.path.join(RESULT_DIR, f'{job_id}.jpg')
    if os.path.exists(result_path):
        return JSONResponse({'id': job_id, 'status': 'finished'})
    if os.path.exists(status_path):
        with open(status_path, 'r', encoding='utf-8') as f:
            status = f.read().strip()
        return JSONResponse({'id': job_id, 'status': status})
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


@app.get('/download_all')
async def download_all_results():
    """Package all results in web/results into a zip and return as a streaming attachment.

    This builds the ZIP in-memory and streams it back to avoid temporary-file locking
    and to be friendly to browser fetch/download flows.
    """
    import io, zipfile, time

    files = [f for f in os.listdir(RESULT_DIR) if f.endswith('.jpg')]
    if not files:
        return Response(content='No result files', status_code=404)

    mem = io.BytesIO()
    with zipfile.ZipFile(mem, 'w', compression=zipfile.ZIP_DEFLATED) as zf:
        for fn in files:
            zf.write(os.path.join(RESULT_DIR, fn), arcname=fn)
    mem.seek(0)

    headers = {'Content-Disposition': 'attachment; filename="results.zip"'}
    return StreamingResponse(mem, media_type='application/zip', headers=headers)
