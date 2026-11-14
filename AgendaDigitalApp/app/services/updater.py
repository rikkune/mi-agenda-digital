"""Actualizaciones automáticas desde las «Releases» de GitHub.

Cómo funciona:
1. La agenda consulta la última release publicada del repositorio
   (api.github.com/repos/<repo>/releases/latest) y compara su etiqueta (vX.Y.Z)
   con APP_VERSION.
2. Si hay una versión nueva y la persona acepta, se descarga MiAgendaDigital.exe
   de esa release junto al ejecutable actual, se comprueba (huella SHA-256 que
   publica GitHub y cabecera de ejecutable de Windows) y se intercambia:
   Windows permite renombrar un .exe en uso, así que el actual pasa a «.old» y
   el nuevo ocupa su lugar.
3. Se arranca el nuevo ejecutable y el actual se cierra; la ventana abierta se
   recarga sola cuando la versión nueva responde. El «.old» se borra en el
   siguiente arranque.

Solo funciona en el .exe publicado por GitHub Actions, que lleva grabado de qué
repositorio sale (app/_build_info.py). La variable AGENDA_UPDATE_REPO=usuario/repo
permite probarlo con otro repositorio.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import re
import subprocess
import sys
import threading
import time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from ..paths import FROZEN
from ..version import APP_VERSION

try:
    from .._build_info import UPDATE_REPO  # Generado al compilar en GitHub Actions.
except ImportError:  # Ejecución desde el código o .exe compilado en local.
    UPDATE_REPO = ""

ASSET_NAME = "MiAgendaDigital.exe"
CHECK_TTL = 6 * 3600       # Se consulta GitHub como mucho cada 6 horas…
ERROR_TTL = 10 * 60        # …o cada 10 minutos si la última consulta falló.
MAX_SIZE = 200 * 1024 * 1024
USER_AGENT = f"MiAgendaDigital/{APP_VERSION} (actualizador)"

log = logging.getLogger(__name__)


class UpdateError(RuntimeError):
    """Error con un mensaje apto para la interfaz."""

    def __init__(self, message: str, page: str = ""):
        super().__init__(message)
        self.page = page


def _version(value: str) -> tuple[int, ...] | None:
    match = re.fullmatch(r"v?(\d+)\.(\d+)\.(\d+)", (value or "").strip())
    return tuple(int(part) for part in match.groups()) if match else None


def executable() -> Path:
    return Path(sys.executable).resolve()


def cleanup_old_versions() -> None:
    """Borra los ejecutables «.old» que dejó la última actualización."""
    if not FROZEN:
        return
    exe = executable()
    for leftover in exe.parent.glob(exe.name + ".old*"):
        try:
            leftover.unlink()
        except OSError:
            pass  # Aún en uso: se intentará en el próximo arranque.
    new = exe.with_name(exe.name + ".new")
    if new.exists():
        try:
            new.unlink()
        except OSError:
            pass


class Updater:
    def __init__(self) -> None:
        self.repo = os.environ.get("AGENDA_UPDATE_REPO", "").strip() or UPDATE_REPO
        self.restart_requested = threading.Event()
        self._lock = threading.Lock()
        self._cache: tuple[float, dict] | None = None
        self._installing = False

    @property
    def enabled(self) -> bool:
        return FROZEN and bool(self.repo)

    # ------------------------------------------------------------ consulta

    def _fetch(self) -> dict:
        info = {"current": APP_VERSION, "enabled": True, "available": False}
        request = Request(
            f"https://api.github.com/repos/{self.repo}/releases/latest",
            headers={"Accept": "application/vnd.github+json", "User-Agent": USER_AGENT},
        )
        try:
            with urlopen(request, timeout=15) as response:
                release = json.load(response)
        except (HTTPError, URLError, TimeoutError, OSError, ValueError) as error:
            log.info("No se ha podido consultar las actualizaciones: %s", error)
            return {**info, "error": "No se ha podido comprobar si hay versiones nuevas."}

        latest = _version(release.get("tag_name", ""))
        asset = next((a for a in release.get("assets") or [] if a.get("name") == ASSET_NAME), None)
        info.update(
            latest=".".join(map(str, latest)) if latest else None,
            notes=(release.get("body") or "").strip()[:4000],
            page=release.get("html_url", ""),
        )
        if latest and asset and latest > _version(APP_VERSION) and not release.get("draft"):
            info.update(
                available=True,
                _url=asset.get("browser_download_url", ""),
                _digest=asset.get("digest") or "",
                _size=int(asset.get("size") or 0),
            )
        return info

    def check(self, force: bool = False) -> dict:
        if not self.enabled:
            return {"current": APP_VERSION, "enabled": False, "available": False}
        with self._lock:
            now = time.monotonic()
            if self._cache and not force:
                stamp, info = self._cache
                if now - stamp < (ERROR_TTL if "error" in info else CHECK_TTL):
                    return info
            info = self._fetch()
            self._cache = (now, info)
            return info

    @staticmethod
    def public(info: dict) -> dict:
        return {key: value for key, value in info.items() if not key.startswith("_")}

    # ------------------------------------------------------------ instalación

    def _download(self, info: dict, target: Path) -> None:
        url = info["_url"]
        if not url.startswith("https://github.com/") and not url.startswith("https://objects.githubusercontent.com/"):
            raise UpdateError("La dirección de descarga no es de GitHub.", info.get("page", ""))
        digest = hashlib.sha256()
        size = 0
        request = Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/octet-stream"})
        try:
            with urlopen(request, timeout=60) as response, open(target, "wb") as output:
                while chunk := response.read(256 * 1024):
                    size += len(chunk)
                    if size > MAX_SIZE:
                        raise UpdateError("La descarga es demasiado grande.", info.get("page", ""))
                    digest.update(chunk)
                    output.write(chunk)
        except (HTTPError, URLError, TimeoutError, OSError) as error:
            raise UpdateError(f"No se ha podido descargar la versión nueva ({error}).", info.get("page", "")) from error

        with open(target, "rb") as check:
            is_exe = check.read(2) == b"MZ"
        expected = info.get("_digest", "")
        if not is_exe or (info.get("_size") and size != info["_size"]):
            raise UpdateError("La descarga está incompleta o dañada. Inténtalo de nuevo.", info.get("page", ""))
        if expected.startswith("sha256:") and expected[7:].lower() != digest.hexdigest():
            raise UpdateError("La descarga no coincide con la publicada. Inténtalo de nuevo.", info.get("page", ""))

    def install(self) -> dict:
        if not self.enabled:
            raise UpdateError("Las actualizaciones solo funcionan en la versión instalada (.exe).")
        with self._lock:
            if self._installing:
                raise UpdateError("Ya se está instalando la actualización.")
            self._installing = True
        try:
            info = self.check(force=True)
            if not info.get("available"):
                raise UpdateError(info.get("error") or "Ya tienes la última versión.")

            exe = executable()
            new = exe.with_name(exe.name + ".new")
            old = exe.with_name(exe.name + f".old{int(time.time())}")
            try:
                self._download(info, new)
                os.replace(exe, old)
            except PermissionError as error:
                new.unlink(missing_ok=True)
                raise UpdateError(
                    "No se puede escribir en la carpeta de la agenda. Descarga la versión "
                    "nueva desde la página de la actualización y sustituye el archivo.",
                    info.get("page", ""),
                ) from error
            except UpdateError:
                new.unlink(missing_ok=True)
                raise
            try:
                os.replace(new, exe)
                self._launch(exe)
            except OSError as error:
                # Se deja todo como estaba.
                try:
                    if exe.exists():
                        exe.unlink()
                    os.replace(old, exe)
                except OSError:
                    log.exception("No se ha podido restaurar el ejecutable anterior")
                raise UpdateError(f"No se ha podido instalar la actualización ({error}).", info.get("page", "")) from error

            log.info("Actualización a %s instalada; reiniciando", info["latest"])
            # Se responde a la ventana antes de cerrar este proceso.
            threading.Timer(1.0, self.restart_requested.set).start()
            return {"ok": True, "version": info["latest"]}
        finally:
            with self._lock:
                self._installing = False

    @staticmethod
    def _launch(exe: Path) -> None:
        env = os.environ.copy()
        env["PYINSTALLER_RESET_ENVIRONMENT"] = "1"  # Arranque independiente de este proceso.
        env["AGENDA_AFTER_UPDATE"] = "1"
        flags = 0
        if sys.platform == "win32":
            flags = subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP
        subprocess.Popen([str(exe)], cwd=str(exe.parent), env=env, creationflags=flags, close_fds=True)
