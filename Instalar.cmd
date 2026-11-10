@echo off
setlocal
cd /d "%~dp0"
where python >nul 2>nul
if errorlevel 1 (
  echo Instala Python 3.10 o superior desde python.org y activa Add Python to PATH.
  pause
  exit /b 1
)
python -m venv .venv
if errorlevel 1 goto error
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 goto error
echo Instalacion completada. Abre Iniciar.cmd.
pause
exit /b 0
:error
echo No se pudo completar la instalacion. Revisa el mensaje anterior.
pause
exit /b 1
