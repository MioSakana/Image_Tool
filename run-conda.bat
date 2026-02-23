@echo off
setlocal EnableExtensions

REM run-conda.bat - Use conda env "dit" to start Doc-Image-Tool (Windows, hidden background process)

echo --------------------------------------------------
echo Starting Doc-Image-Tool with conda env: dit
echo --------------------------------------------------

if not exist "web\logs" (
    mkdir "web\logs"
)

for /f "usebackq tokens=*" %%i in (`powershell -NoProfile -Command "Get-Date -Format yyyyMMdd_HHmmss"`) do set TS=%%i
set LOGFILE=web\logs\uvicorn_%TS%.log
set PYEXE=D:\anaconda\envs\dit\python.exe
set URL=http://127.0.0.1:8000/

echo Logfile: %LOGFILE%

if not exist "%PYEXE%" (
    echo [ERROR] Python not found in env dit: %PYEXE%
    echo Please check your Anaconda install path or env name.
    pause
    exit /b 1
)

REM If port 8000 is occupied, stop the listener first.
for /f "tokens=5" %%p in ('netstat -ano ^| findstr /R /C:":8000 .*LISTENING"') do (
    echo Port 8000 is occupied by PID %%p, stopping it...
    taskkill /PID %%p /F >nul 2>nul
)

REM Start hidden and redirect logs (no extra terminal window).
powershell -NoProfile -ExecutionPolicy Bypass -Command "$py='%PYEXE%'; $args='-m uvicorn web.app:app --host 127.0.0.1 --port 8000 --log-level info'; Start-Process -FilePath $py -ArgumentList $args -WorkingDirectory '%CD%' -WindowStyle Hidden -RedirectStandardOutput '%LOGFILE%' -RedirectStandardError '%LOGFILE%'"

echo Server started in hidden background.
echo URL: %URL%
echo Logs: %LOGFILE%

REM Wait until port 8000 is listening (max 15s), then open browser.
powershell -NoProfile -ExecutionPolicy Bypass -Command "$deadline=(Get-Date).AddSeconds(15); do { $ready = Get-NetTCPConnection -LocalPort 8000 -State Listen -ErrorAction SilentlyContinue; if ($ready) { Start-Process '%URL%'; break }; Start-Sleep -Milliseconds 300 } while ((Get-Date) -lt $deadline)"

echo Done.
endlocal
