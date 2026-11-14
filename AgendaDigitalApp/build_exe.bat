@echo off
chcp 65001 >nul
cd /d "%~dp0"
rem Genera dist\MiAgendaDigital.exe (solo lo necesita quien desarrolla la agenda).

if not exist ".venv\Scripts\python.exe" (
    py -3 -m venv .venv || python -m venv .venv || goto :error
)
".venv\Scripts\python.exe" -m pip install -q -r requirements-build.txt || goto :error
".venv\Scripts\python.exe" -m PyInstaller --noconfirm --clean MiAgendaDigital.spec || goto :error

echo.
echo   Listo: dist\MiAgendaDigital.exe
echo.
pause
exit /b 0

:error
echo.
echo   No se ha podido generar el ejecutable.
pause
exit /b 1
