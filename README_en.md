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

## Web Enhancements（中文界面说明）
- 多文件批量提交（自动分流：单图实时预览，多图后台队列）
- 动作流水线（例如：`trim|orientation|bleach`）
- 流水线模板一键套用
- 任务列表筛选、统计、勾选下载
- 失败任务重试（单条 / 批量）
- 任务耗时显示与排序
- 单图分享链接生成
- 多图任务支持点击缩略图进入原图/结果对比预览
- 批量任务点击预览后自动高亮当前行

## 界面处理逻辑
- 已取消“同步/异步”手动切换按钮。
- 仅选择 1 张图片时：自动走实时处理，并直接显示对比预览。
- 选择多张图片时：自动走后台队列处理；完成后可点击任务行缩略图查看对比预览。

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
- The server listens on `0.0.0.0:8000` to allow LAN access and sharing.
- It automatically opens the browser to `http://127.0.0.1:8000/` after the server is ready.
- The script prints a LAN URL for other devices on the same network.

Then open:
- Local: `http://127.0.0.1:8000/`
- LAN: use the printed LAN URL (for example `http://192.168.1.10:8000/`)

Logs are written to:
- `web/logs/`

## Manual Start
```powershell
D:\anaconda\envs\dit\python.exe -m uvicorn web.app:app --host 0.0.0.0 --port 8000
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

4. Share link not accessible on other devices
- Ensure the server listens on `0.0.0.0`.
- Allow port 8000 in Windows Firewall (Admin PowerShell):
```bat
netsh advfirewall firewall add rule name="Doc-Image-Tool 8000" dir=in action=allow protocol=TCP localport=8000 profile=any
```

## Support
If this project helps you, feel free to open an Issue or PR.
