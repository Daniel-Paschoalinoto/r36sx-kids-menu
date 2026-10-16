@echo off
chcp 65001 >nul
cd /d "%~dp0"
where python >nul 2>nul
if errorlevel 1 (
  echo Python was not found. Install it from https://www.python.org/downloads/ ^(tick "Add python.exe to PATH"^).
  echo Python nao encontrado. Instale em https://www.python.org/downloads/ ^(marque "Add python.exe to PATH"^).
  pause & exit /b 1
)
python -c "import PIL, numpy, keystone" >nul 2>nul
if errorlevel 1 (
  echo Installing needed packages / Instalando pacotes necessarios...
  python -m pip install -r requirements.txt
  if errorlevel 1 ( echo Failed / Falhou & pause & exit /b 1 )
)
python build.py %*
echo.
pause
