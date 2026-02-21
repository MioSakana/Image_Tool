import os
import numpy as np
import cv2
import time
import json
from rq import get_current_job

# Import existing processing functions
from function_method.DocBleach import sauvola_threshold
from function_method.TextOrientationCorrection import eval_angle
from function_method.HandwritingDenoisingBeautifying import docscan_main, get_argument_parser
from function_method.DocShadowRemoval import removeShadow
from function_method.DocSharpening import doc_sharpening_pred, img_enh
from function_method.DocTrimmingEnhancement import doc_trimming_enhancement_pred
from function_method.document_image_dewarping.correct import dewarping_pred


RESULT_DIR = os.path.join('web', 'results')
os.makedirs(RESULT_DIR, exist_ok=True)

SUPPORTED_ACTIONS = (
    "bleach",
    "orientation",
    "sharpen",
    "denoise",
    "shadow",
    "dewarp",
    "trim",
)


def get_supported_actions():
    return list(SUPPORTED_ACTIONS)


def parse_actions(action: str):
    if not isinstance(action, str):
        raise ValueError("Action must be a string")
    raw = [a.strip().lower() for a in action.replace(",", "|").split("|")]
    steps = [a for a in raw if a]
    if not steps:
        raise ValueError("Action is required")
    invalid = [a for a in steps if a not in SUPPORTED_ACTIONS]
    if invalid:
        raise ValueError(f"Unknown action(s): {', '.join(invalid)}")
    return steps


def process_image_bytes(data: bytes, action: str) -> bytes:
    """Synchronous helper that returns JPEG bytes (used by /process)."""
    nparr = np.frombuffer(data, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_UNCHANGED)
    if img is None:
        raise ValueError('Invalid image')

    out = _dispatch_image(img, action)
    # encode to jpg bytes
    if len(out.shape) == 2:
        ok, buf = cv2.imencode('.jpg', out)
    else:
        ok, buf = cv2.imencode('.jpg', out[:, :, ::-1])
    if not ok:
        raise RuntimeError('Failed to encode image')
    return buf.tobytes()


def process_job(data: bytes, action: str):
    """Legacy RQ-compatible job (keeps behavior similar to BG job)."""
    # For compatibility, generate an id
    job_id = None
    nparr = np.frombuffer(data, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_UNCHANGED)
    if img is None:
        raise ValueError('Invalid image')

    out = _dispatch_image(img, action)

    # write JPEG to disk
    result_path = os.path.join(RESULT_DIR, f'{job_id or "unknown"}.jpg')
    if len(out.shape) == 2:
        cv2.imwrite(result_path, out)
    else:
        cv2.imwrite(result_path, out[:, :, ::-1])
    return {'result_path': result_path}


def _dispatch_image(img, action: str):
    out = img
    for step in parse_actions(action):
        out = _dispatch_single(out, step)
    return out


def _dispatch_single(img, action: str):
    # Reuse existing functions; ensure channels where needed.
    if action == "bleach":
        return sauvola_threshold(img)
    if action == "orientation":
        out, _ = eval_angle(img, [-30, 30])
        return out
    if action == "sharpen":
        out = doc_sharpening_pred(img)
        out = img_enh(out)
        return out
    if action == "denoise":
        return docscan_main(img, get_argument_parser().parse_args([]))
    if action == "shadow":
        return removeShadow(img)
    if action == "dewarp":
        return dewarping_pred(img)
    if action == "trim":
        if len(img.shape) == 2:
            img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
        if img.shape[2] == 4:
            img = img[:, :, :3]
        img = img[:, :, ::-1]
        return doc_trimming_enhancement_pred(img)
    raise ValueError(f"Unknown action: {action}")


def process_job_bg(job_id: str, data: bytes, action: str):
    """BackgroundTasks target: write status file, process and save result JPEG."""
    status_path = os.path.join(RESULT_DIR, f'{job_id}.status')
    result_path = os.path.join(RESULT_DIR, f'{job_id}.jpg')
    meta_path = os.path.join(RESULT_DIR, f'{job_id}.meta.json')
    t0 = time.perf_counter()

    def _write_meta(status: str, error: str = ""):
        elapsed_ms = int((time.perf_counter() - t0) * 1000)
        payload = {
            "id": job_id,
            "action": action,
            "status": status,
            "elapsed_ms": elapsed_ms,
        }
        if error:
            payload["error"] = error
        with open(meta_path, "w", encoding="utf-8") as mf:
            json.dump(payload, mf, ensure_ascii=False)

    try:
        with open(status_path, 'w', encoding='utf-8') as f:
            f.write('processing')
        _write_meta("processing")

        nparr = np.frombuffer(data, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_UNCHANGED)
        if img is None:
            with open(status_path, 'w', encoding='utf-8') as f:
                f.write('error')
            _write_meta("error", "Invalid image")
            return

        out = _dispatch_image(img, action)

        if len(out.shape) == 2:
            cv2.imwrite(result_path, out)
        else:
            cv2.imwrite(result_path, out[:, :, ::-1])

        with open(status_path, 'w', encoding='utf-8') as f:
            f.write('finished')
        _write_meta("finished")
    except Exception as e:
        with open(status_path, 'w', encoding='utf-8') as f:
            f.write('error')
        _write_meta("error", str(e))
