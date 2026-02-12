import os
import numpy as np
import cv2
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
    # reuse existing functions; ensure channels where needed
    if action == "bleach":
        return sauvola_threshold(img)
    elif action == "orientation":
        out, _ = eval_angle(img, [-30, 30])
        return out
    elif action == "sharpen":
        out = doc_sharpening_pred(img)
        out = img_enh(out)
        return out
    elif action == "denoise":
        return docscan_main(img, get_argument_parser().parse_args([]))
    elif action == "shadow":
        return removeShadow(img)
    elif action == "dewarp":
        return dewarping_pred(img)
    elif action == "trim":
        if len(img.shape) == 2:
            img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
        if img.shape[2] == 4:
            img = img[:, :, :3]
        img = img[:, :, ::-1]
        return doc_trimming_enhancement_pred(img)
    else:
        raise ValueError('Unknown action')


def process_job_bg(job_id: str, data: bytes, action: str):
    """BackgroundTasks target: write status file, process and save result JPEG."""
    status_path = os.path.join(RESULT_DIR, f'{job_id}.status')
    result_path = os.path.join(RESULT_DIR, f'{job_id}.jpg')
    try:
        with open(status_path, 'w', encoding='utf-8') as f:
            f.write('processing')

        nparr = np.frombuffer(data, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_UNCHANGED)
        if img is None:
            with open(status_path, 'w', encoding='utf-8') as f:
                f.write('error')
            return

        out = _dispatch_image(img, action)

        if len(out.shape) == 2:
            cv2.imwrite(result_path, out)
        else:
            cv2.imwrite(result_path, out[:, :, ::-1])

        with open(status_path, 'w', encoding='utf-8') as f:
            f.write('finished')
    except Exception:
        with open(status_path, 'w', encoding='utf-8') as f:
            f.write('error')
