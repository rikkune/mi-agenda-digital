"""Dónde están los recursos de la aplicación y dónde se guardan los datos.

- Recursos (plantillas, estáticos, schema.sql): junto al código, o dentro del
  ejecutable cuando se empaqueta con PyInstaller (sys._MEIPASS).
- Datos (base de datos, copias, sesión): en el ejecutable, en
  %LOCALAPPDATA%\\MiAgendaDigital\\data, para que cada usuario de Windows tenga
  los suyos y actualizar el .exe no los toque. Al ejecutar desde el código
  fuente se sigue usando la carpeta data/ del proyecto. La variable de entorno
  AGENDA_DATA_DIR permite elegir otra carpeta.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

APP_NAME = "MiAgendaDigital"
FROZEN = bool(getattr(sys, "frozen", False))


def resource_dir() -> Path:
    if FROZEN:
        return Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent))
    return Path(__file__).resolve().parent.parent


def app_home() -> Path:
    """Carpeta propia de la aplicación para este usuario de Windows."""
    base = os.environ.get("LOCALAPPDATA") or str(Path.home() / "AppData" / "Local")
    return Path(base) / APP_NAME


def data_dir() -> Path:
    custom = os.environ.get("AGENDA_DATA_DIR", "").strip()
    if custom:
        return Path(custom)
    if FROZEN:
        return app_home() / "data"
    return resource_dir() / "data"
