# Web 原型

运行前请激活 `py311` 环境，并安装依赖：

```powershell
python -m pip install fastapi uvicorn python-multipart aiofiles redis rq
```

启动开发服务器：

```powershell
uvicorn web.app:app --host 127.0.0.1 --port 8000
```

异步处理说明（BackgroundTasks，无需 Redis）：

- 本原型使用 FastAPI 的 `BackgroundTasks` 实现异步任务，结果会保存到 `web/results/{job_id}.jpg`。
- 调用 `/process_async` 上传图片并指定 `action`，接口返回 `job_id`。
- 使用 `/status/{job_id}` 查询任务状态（返回 `queued`、`processing`、`finished` 或 `error`）。任务完成后 `/result/{job_id}` 返回处理后的图片。

打开浏览器访问 `http://127.0.0.1:8000/` 即可使用前端上传与同步处理（POST `/process`）或异步队列（POST `/process_async`）。
