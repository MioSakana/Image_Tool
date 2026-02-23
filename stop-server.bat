@echo off
setlocal EnableExtensions

REM stop-server.bat - stop listener on port 8000 only

for /f "tokens=5" %%p in ('netstat -ano ^| findstr /R /C:":8000 .*LISTENING"') do (
    echo Stopping PID %%p on port 8000...
    taskkill /PID %%p /F >nul 2>nul
)

for /f "tokens=5" %%p in ('netstat -ano ^| findstr /R /C:":8000 .*LISTENING"') do (
    echo [ERROR] Port 8000 is still in use by PID %%p
    endlocal
    exit /b 1
)

echo Port 8000 released.
endlocal
