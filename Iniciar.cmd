@echo off
setlocal
cd /d "%~dp0"
if exist ".venv\Scripts\pythonw.exe" (
  start "" ".venv\Scripts\pythonw.exe" "%~dp0GestorFalcon.pyw"
) else (
  python gestor.py
  if errorlevel 1 pause
)
