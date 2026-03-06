@echo off
setlocal EnableExtensions

echo --------------------------------------------------
echo Starting Doc-Image-Tool with conda env: dit
echo --------------------------------------------------

if not exist "web\logs" mkdir "web\logs"

for /f "usebackq tokens=*" %%i in (`powershell -NoProfile -Command "Get-Date -Format yyyyMMdd_HHmmss"`) do set "TS=%%i"
set "LOGFILE=web\logs\uvicorn_%TS%.log"
set "ERRFILE=web\logs\uvicorn_%TS%.err.log"
set "URL=http://127.0.0.1:8000/"
set "PYEXE="

echo Logfile: %LOGFILE%
echo ErrorLog: %ERRFILE%

if defined DIT_PYEXE set "PYEXE=%DIT_PYEXE%"
if not defined PYEXE if not "%~1"=="" set "PYEXE=%~1"
if not defined PYEXE if exist "D:\anaconda\envs\dit\python.exe" set "PYEXE=D:\anaconda\envs\dit\python.exe"
if not defined PYEXE if exist "%USERPROFILE%\anaconda3\envs\dit\python.exe" set "PYEXE=%USERPROFILE%\anaconda3\envs\dit\python.exe"
if not defined PYEXE if /I "%CONDA_DEFAULT_ENV%"=="dit" if exist "%CONDA_PREFIX%\python.exe" set "PYEXE=%CONDA_PREFIX%\python.exe"

if not defined PYEXE goto :NO_PY
if not exist "%PYEXE%" goto :NO_PY

powershell -NoProfile -ExecutionPolicy Bypass -Command "Get-NetTCPConnection -LocalPort 8000 -State Listen -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -Unique | ForEach-Object { Stop-Process -Id $_ -Force -ErrorAction SilentlyContinue }" >nul 2>nul
timeout /t 1 /nobreak >nul

powershell -NoProfile -ExecutionPolicy Bypass -Command "Start-Process -FilePath '%PYEXE%' -ArgumentList '-m uvicorn web.app:app --host 0.0.0.0 --port 8000 --log-level warning' -WorkingDirectory '%CD%' -WindowStyle Hidden -RedirectStandardOutput '%LOGFILE%' -RedirectStandardError '%ERRFILE%'"
if errorlevel 1 goto :START_FAIL

echo Server started in hidden background.
echo URL: %URL%
echo Logs: %LOGFILE%
echo Error Logs: %ERRFILE%

timeout /t 1 /nobreak >nul
start "" "%URL%"
echo Done.
endlocal
exit /b 0

:NO_PY
echo [ERROR] Could not resolve Python for conda env "dit".
echo [HINT] Set DIT_PYEXE or run:
echo        .\run-conda.bat D:\anaconda\envs\dit\python.exe
exit /b 1

:START_FAIL
echo [ERROR] Failed to launch python process.
echo [HINT] Check error log: %ERRFILE%
exit /b 1
