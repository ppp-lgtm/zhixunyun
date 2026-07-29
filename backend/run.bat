@echo off
REM ============================================================
REM  Zhixunyun Backend Launcher - STUPID SIMPLE EDITION
REM  NO CHINESE / NO UTF-8 / NO BOM / ASCII ONLY / CRLF
REM ============================================================
REM  Usage:
REM    run.bat                       default 127.0.0.1:8000
REM    run.bat 8001                  set port
REM    run.bat --port 8001           same
REM    run.bat --host 0.0.0.0        all interfaces
REM    run.bat --reload              dev reload
REM    run.bat --help, -h            show serve.py help
REM ============================================================
setlocal
cd /d "%~dp0"

REM --- locate venv python.exe ---
set "PYEXE="
if exist ".venv\Scripts\python.exe" set "PYEXE=%~dp0.venv\Scripts\python.exe"
if exist "venv\Scripts\python.exe"   set "PYEXE=%~dp0venv\Scripts\python.exe"
if "%PYEXE%"=="" (
    echo [ERROR] venv python.exe not found. Expected:
    echo         .\venv\Scripts\python.exe OR .\.venv\Scripts\python.exe
    echo.
    echo Please run:
    echo   python -m venv venv
    echo   venv\Scripts\pip install -r requirements.txt
    echo.
    pause
    exit /b 1
)

if NOT exist "serve.py" (
    echo [ERROR] serve.py missing in "%CD%"
    pause
    exit /b 1
)

REM --- pass all args directly to serve.py. No bat-side parsing ever. ---
"%PYEXE%" "%~dp0serve.py" %*
set "EXIT_CODE=%ERRORLEVEL%"

echo.
if "%EXIT_CODE%"=="0" (
    echo [EXIT] Clean exit ^(code 0^).
) else if "%EXIT_CODE%"=="2" (
    echo [EXIT] Port occupied ^(code 2^).
    echo        Change port: run.bat 8001
) else (
    echo [EXIT] code=%EXIT_CODE%
)
echo.
pause
exit /b %EXIT_CODE%
