# -*- mode: python ; coding: utf-8 -*-
# Empaquetado con PyInstaller: un único MiAgendaDigital.exe sin consola.
# Se genera con build_exe.bat (o: python -m PyInstaller MiAgendaDigital.spec).
#
# - La versión sale de app/version.py.
# - En GitHub Actions (variable GITHUB_REPOSITORY) se graba de qué repositorio
#   sale el .exe, para que busque ahí las actualizaciones. Un .exe compilado en
#   local no busca actualizaciones.

import os
import re
from pathlib import Path

ROOT = Path(SPECPATH)
VERSION = re.search(r'APP_VERSION = "([\d.]+)"', (ROOT / "app" / "version.py").read_text(encoding="utf-8")).group(1)
NUMBERS = tuple(int(n) for n in VERSION.split(".")) + (0,)

repo = os.environ.get("GITHUB_REPOSITORY", "") if os.environ.get("GITHUB_ACTIONS") == "true" else ""
(ROOT / "app" / "_build_info.py").write_text(
    '"""Generado al compilar (MiAgendaDigital.spec). No editar."""\n\n'
    f"UPDATE_REPO = {repo!r}\n",
    encoding="utf-8",
)

(ROOT / "build").mkdir(exist_ok=True)
VERSION_FILE = ROOT / "build" / "version_info.txt"
VERSION_FILE.write_text(f"""VSVersionInfo(
  ffi=FixedFileInfo(filevers={NUMBERS}, prodvers={NUMBERS}),
  kids=[
    StringFileInfo([
      StringTable('0C0A04B0', [
        StringStruct('FileDescription', 'Mi Agenda Digital'),
        StringStruct('ProductName', 'Mi Agenda Digital'),
        StringStruct('FileVersion', '{VERSION}'),
        StringStruct('ProductVersion', '{VERSION}'),
        StringStruct('OriginalFilename', 'MiAgendaDigital.exe'),
      ])
    ]),
    VarFileInfo([VarStruct('Translation', [0x0C0A, 1200])])
  ]
)
""", encoding="utf-8")

a = Analysis(
    ["run.py"],
    pathex=[],
    binaries=[],
    datas=[
        ("templates", "templates"),
        ("static", "static"),
        ("app/schema.sql", "app"),
    ],
    hiddenimports=["app._build_info"],
    hookspath=[],
    runtime_hooks=[],
    excludes=["playwright", "PIL", "tkinter", "unittest", "pydoc", "test"],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="MiAgendaDigital",
    icon="static/img/icons/agenda.ico",
    version=str(VERSION_FILE),
    console=False,
    upx=False,
    debug=False,
    strip=False,
    runtime_tmpdir=None,
)
