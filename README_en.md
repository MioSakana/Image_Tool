# Doc-Image-Tool

[中文](README.md)

## Overview
Doc-Image-Tool is an offline document image processing tool with a web UI for enhancement and batch workflows.

## Current Features
- Bleach (`bleach`)
- Text orientation correction (`orientation`)
- Sharpen (`sharpen`)
- Handwriting denoise/beautify (`denoise`)
- Shadow removal (`shadow`)
- Dewarp (`dewarp`)
- Trim enhancement (`trim`)

## Web Enhancements
- Multi-file batch submit (sync / async)
- Action pipeline support (for example: `trim|orientation|bleach`)
- One-click pipeline templates
- Task filtering, statistics, and selected download
- Failed task retry (single / batch)
- Task elapsed-time display and sorting
- Share link generation for single result

## Requirements
- Windows
- Anaconda (recommended)
- Existing conda environment: `dit`
- Model files under `weights/`

## Quick Start (Recommended)
Run in project root (PowerShell):

```bat
.\run-conda.bat
```

Notes:
- `run-conda.bat` starts the server as a hidden background process (no extra terminal window).
- It automatically opens the browser to `http://127.0.0.1:8000/` after the server is ready.

Then open:
- `http://127.0.0.1:8000/`

Logs are written to:
- `web/logs/`

## Manual Start
```powershell
D:\anaconda\envs\dit\python.exe -m uvicorn web.app:app --host 127.0.0.1 --port 8000
```

## Stop Server (Port 8000 only)
```bat
.\stop-server.bat
```

## Core Structure
```text
web/
  app.py                # FastAPI entry
  static/index.html     # Frontend page
  tasks.py              # Task dispatch / processing
function_method/        # Algorithm implementations
weights/                # Model weights
```

## Common Issues
1. Unicode decode error on `/`
- Keep `web/static/index.html` in UTF-8.

2. Port already in use (`10048`)
- Change port, or release the occupied port first.

3. `conda run` encoding issues on Windows
- Prefer direct Python path:
  `D:\anaconda\envs\dit\python.exe ...`

## Support
If this project helps you, feel free to open an Issue or PR.
