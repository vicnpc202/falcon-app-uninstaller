@echo off
setlocal
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" (
  ".venv\Scripts\python.exe" gestor.py --demo
) else (
  python gestor.py --demo
)
if errorlevel 1 pause
