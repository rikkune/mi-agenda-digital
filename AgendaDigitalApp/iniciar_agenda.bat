@echo off
chcp 65001 >nul
cd /d "%~dp0"
title Mi Agenda Digital 2026-2027

echo.
echo   Mi Agenda Digital 2026-2027
echo   ---------------------------
echo.

set "PYTHON=py -3"
where py >nul 2>nul
if errorlevel 1 set "PYTHON=python"

%PYTHON% --version >nul 2>nul
if errorlevel 1 goto :no_python

if not exist ".venv\Scripts\python.exe" (
    echo   Preparando la agenda por primera vez...
    echo   Se va a crear un entorno privado dentro de esta carpeta.
    echo.
    %PYTHON% -m venv .venv
    if errorlevel 1 goto :venv_error
)

".venv\Scripts\python.exe" -c "import flask" >nul 2>nul
if errorlevel 1 (
    echo   Falta un componente necesario: Flask.
    echo.
    choice /C SN /M "  Quieres instalarlo ahora? (S = si, N = no)"
    if errorlevel 2 goto :no_install
    echo.
    echo   Instalando componentes. Esto puede tardar un poco...
    ".venv\Scripts\python.exe" -m pip install --upgrade pip
    ".venv\Scripts\python.exe" -m pip install -r requirements.txt
    if errorlevel 1 goto :install_error
    echo.
    echo   Instalacion terminada.
    echo.
)

echo   Abriendo la agenda en tu navegador...
echo   No cierres esta ventana mientras la estes usando.
echo.
".venv\Scripts\python.exe" run.py
echo.
echo   La agenda se ha cerrado.
pause
exit /b 0

:no_python
echo   No se ha encontrado Python en este ordenador.
echo.
echo   Instala Python 3 desde https://www.python.org/downloads/
echo   y marca la opcion "Add Python to PATH" durante la instalacion.
echo.
pause
exit /b 1

:venv_error
echo.
echo   No se ha podido preparar el entorno de la agenda.
echo   Comprueba que tienes espacio en disco y vuelve a intentarlo.
echo.
pause
exit /b 1

:no_install
echo.
echo   Sin Flask la agenda no puede arrancar.
echo   Vuelve a ejecutar este archivo cuando quieras instalarlo.
echo.
pause
exit /b 1

:install_error
echo.
echo   No se ha podido instalar Flask.
echo   Comprueba tu conexion a Internet y vuelve a intentarlo.
echo.
pause
exit /b 1