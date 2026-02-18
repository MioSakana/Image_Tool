@echo off
REM run-conda.bat - 启动 Doc-Image-Tool 的 Windows 脚本 (使用 conda env: dit)
REM 使用方式：在项目根目录双击或在命令行运行此脚本。

echo --------------------------------------------------
echo Starting Doc-Image-Tool with conda environment: dit
echo --------------------------------------------------

REM Ensure logs folder exists
if not exist "web\logs" (
    mkdir "web\logs"
)

REM Build a timestamp for the logfile using PowerShell (yyyyMMdd_HHmmss)
for /f "usebackq tokens=*" %%i in (`powershell -NoProfile -Command "Get-Date -Format yyyyMMdd_HHmmss"`) do set TS=%%i
set LOGFILE=web\logs\uvicorn_%TS%.log

echo Logfile: %LOGFILE%

rem Try to activate the conda env; if activation isn't available, fall back to conda run.
call conda activate dit 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo Could not activate 'dit' in this shell; using 'conda run -n dit' and launching in new window.
    start "Doc-Image-Tool" cmd /c "conda run -n dit python -m uvicorn web.app:app --host 127.0.0.1 --port 8000 --log-level info > %LOGFILE% 2>&1"
    echo Server started (background). Logs are written to %LOGFILE%
    goto :end
)

rem Activation succeeded; start server in new window and redirect logs
start "Doc-Image-Tool" cmd /c "python -m uvicorn web.app:app --host 127.0.0.1 --port 8000 --log-level info > %LOGFILE% 2>&1"
echo Server started (background). Logs are written to %LOGFILE%

:end
echo Done.

