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
set ERRFILE=web\logs\uvicorn_%TS%.err.log
set PYEXE=
set URL=http://127.0.0.1:8000/

echo Logfile: %LOGFILE%
echo ErrorLog: %ERRFILE%

REM Resolve python path for env "dit"
if defined DIT_PYEXE set "PYEXE=%DIT_PYEXE%"
if not defined PYEXE if "%~1" NEQ "" set "PYEXE=%~1"
if not defined PYEXE if /I "%CONDA_DEFAULT_ENV%"=="dit" if exist "%CONDA_PREFIX%\python.exe" set "PYEXE=%CONDA_PREFIX%\python.exe"
if not defined PYEXE if exist "D:\anaconda\envs\dit\python.exe" set "PYEXE=D:\anaconda\envs\dit\python.exe"
if not defined PYEXE if exist "%USERPROFILE%\anaconda3\envs\dit\python.exe" set "PYEXE=%USERPROFILE%\anaconda3\envs\dit\python.exe"

if not defined PYEXE (
    for /f "usebackq tokens=*" %%p in (`powershell -NoProfile -Command "$p=(conda env list 2^>^$null ^| Select-String '^\s*dit\s' ^| ForEach-Object { ($_ -split '\s+')[-1] } ^| Select-Object -First 1); if($p){Write-Output ($p + '\python.exe')}"`) do set "PYEXE=%%p"
)

if not defined PYEXE (
    echo [ERROR] Could not resolve Python for conda env "dit".
    echo [HINT] Set DIT_PYEXE or pass python path as first arg:
    echo        .\run-conda.bat D:\anaconda\envs\dit\python.exe
    pause
    exit /b 1
)

if not exist "%PYEXE%" (
    echo [ERROR] Python not found: %PYEXE%
    echo [HINT] Ensure env "dit" exists or set DIT_PYEXE explicitly.
    pause
    exit /b 1
)

REM If port 8000 is occupied, stop the listener first.
for /f "tokens=5" %%p in ('netstat -ano ^| findstr /R /C:":8000 .*LISTENING"') do (
    echo Port 8000 is occupied by PID %%p, stopping it...
    taskkill /PID %%p /F >nul 2>nul
)

REM Start hidden and redirect logs (no extra terminal window).
powershell -NoProfile -ExecutionPolicy Bypass -Command "$py='%PYEXE%'; $args='-m uvicorn web.app:app --host 127.0.0.1 --port 8000 --log-level warning'; Start-Process -FilePath $py -ArgumentList $args -WorkingDirectory '%CD%' -WindowStyle Hidden -RedirectStandardOutput '%LOGFILE%' -RedirectStandardError '%ERRFILE%'"
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Failed to launch python process.
    echo [HINT] Check error log: %ERRFILE%
    exit /b 1
)

echo Server started in hidden background.
echo URL: %URL%
echo Logs: %LOGFILE%
echo Error Logs: %ERRFILE%

REM Wait until port 8000 is listening (max 15s), then open browser.
powershell -NoProfile -ExecutionPolicy Bypass -Command "$opened=$false; $deadline=(Get-Date).AddSeconds(15); do { $ready = Get-NetTCPConnection -LocalPort 8000 -State Listen -ErrorAction SilentlyContinue; if ($ready) { Start-Process '%URL%'; $opened=$true; break }; Start-Sleep -Milliseconds 300 } while ((Get-Date) -lt $deadline); if(-not $opened){ exit 2 }"
if %ERRORLEVEL% EQU 2 (
    echo [ERROR] Server did not become ready within 15 seconds.
    echo [HINT] Check logs:
    echo        %LOGFILE%
    echo        %ERRFILE%
    exit /b 2
)

echo Done.
endlocal
