@echo off
cd /d "%~dp0"
if exist "venv\Scripts\python.exe" (
    "venv\Scripts\python.exe" serve.py --reload
) else if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" serve.py --reload
) else (
    python serve.py --reload
)
