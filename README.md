# Doc-Image-Tool 文档图像处理工具

[English](README_en.md)

## 项目简介
Doc-Image-Tool 是一个离线文档图像处理工具，提供 Web 界面进行图片增强与批量处理。

## 当前功能
- 漂白（`bleach`）
- 文字方向矫正（`orientation`）
- 清晰增强（`sharpen`）
- 手写去噪美化（`denoise`）
- 去阴影（`shadow`）
- 扭曲矫正（`dewarp`）
- 切边增强（`trim`）

## Web 端增强功能
- 多文件批量提交（同步 / 异步）
- 动作流水线（例如：`trim|orientation|bleach`）
- 流水线模板一键套用
- 任务列表筛选、统计、勾选下载
- 失败任务重试（单条 / 批量）
- 任务耗时显示与排序
- 单图分享链接生成

## 环境要求
- Windows
- Anaconda（推荐）
- 已创建 conda 环境：`dit`
- 模型文件放置在 `weights/` 目录

## 启动方式（推荐）
在项目根目录执行（PowerShell）：

```bat
.\run-conda.bat
```

说明：
- `run-conda.bat` 会以隐藏后台进程启动服务，不会弹出额外终端窗口。
- 检测到服务就绪后会自动打开浏览器访问首页（`http://127.0.0.1:8000/`）。

启动后访问：
- `http://127.0.0.1:8000/`

日志输出目录：
- `web/logs/`

## 手动启动
```powershell
D:\anaconda\envs\dit\python.exe -m uvicorn web.app:app --host 127.0.0.1 --port 8000
```

## 停止服务
如需释放端口：

```powershell
# 释放 8000
$conn = Get-NetTCPConnection -LocalPort 8000 -State Listen -ErrorAction SilentlyContinue | Select-Object -First 1
if ($conn) { Stop-Process -Id $conn.OwningProcess -Force }
```

## 项目结构（核心）
```text
web/
  app.py                # FastAPI 入口
  static/index.html     # 前端页面
  tasks.py              # 图像处理任务分发
function_method/        # 各功能算法实现
weights/                # 模型权重
```

## 常见问题
1. 首页报编码错误
- 已支持编码回退读取；建议保持 `web/static/index.html` 为 UTF-8。

2. 端口被占用（10048）
- 换端口启动，或先释放占用端口。

3. conda run 出现编码异常
- 优先使用 `D:\anaconda\envs\dit\python.exe` 直接启动。

## 致谢
如果这个项目对你有帮助，欢迎提交 Issue 或 PR。

## 一键停止（仅 8000）
```bat
.\stop-server.bat
```
