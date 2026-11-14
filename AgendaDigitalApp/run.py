"""Arranque de Mi Agenda Digital.

Uso:
    python run.py              (desde el código fuente)
    MiAgendaDigital.exe        (versión empaquetada)

La aplicación escucha solo en 127.0.0.1 (tu ordenador); no se publica en
Internet. Se abre en una ventana propia de Microsoft Edge (modo aplicación, sin
pestañas ni barra de direcciones) y, al cerrar esa ventana, la agenda se cierra.

Si la agenda ya está abierta, volver a ejecutarla solo abre otra ventana.

Variables de entorno opcionales:
    AGENDA_PORT=5000         puerto local
    AGENDA_NO_BROWSER=1      no abrir ventana (el servidor sigue hasta Ctrl+C)
    AGENDA_DATA_DIR=...      carpeta de datos (ver app/paths.py)
"""

from __future__ import annotations

import json
import logging
import os
import shutil
import socket
import subprocess
import sys
import threading
import time
import webbrowser
from logging.handlers import RotatingFileHandler
from pathlib import Path
from urllib.request import ProxyHandler, build_opener

from app.paths import FROZEN, app_home, data_dir
from app.version import APP_VERSION

HOST = "127.0.0.1"
PORT = int(os.environ.get("AGENDA_PORT", "5000"))
URL = f"http://{HOST}:{PORT}/"
TITLE = "Mi Agenda Digital"

_LOCAL = build_opener(ProxyHandler({}))


# ---------------------------------------------------------------- avisos


def _message(text: str, error: bool = False) -> None:
    """Aviso visible: en el .exe no hay consola, así que se usa un cuadro de Windows."""
    if FROZEN and sys.platform == "win32":
        import ctypes

        flags = 0x10 if error else 0x40  # MB_ICONERROR / MB_ICONINFORMATION
        ctypes.windll.user32.MessageBoxW(None, text, TITLE, flags | 0x10000)  # MB_SETFOREGROUND
    else:
        print(f"\n  {text}\n")


def _setup_logging(folder: Path) -> None:
    folder.mkdir(parents=True, exist_ok=True)
    handlers: list[logging.Handler] = [
        RotatingFileHandler(folder / "agenda.log", maxBytes=1_000_000, backupCount=2, encoding="utf-8")
    ]
    if not FROZEN:
        handlers.append(logging.StreamHandler())
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s",
                        handlers=handlers)
    logging.getLogger("werkzeug").setLevel(logging.WARNING)


# ---------------------------------------------------------------- datos


def _migrate_portable_data(target: Path) -> None:
    """Primera vez con el .exe: si hay una carpeta data/ junto al ejecutable
    (la de la versión anterior con iniciar_agenda.bat), se copian sus datos."""
    if not FROZEN or (target / "agenda.db").exists():
        return
    legacy = Path(sys.executable).resolve().parent / "data"
    if not (legacy / "agenda.db").exists():
        return
    logging.info("Copiando datos de %s a %s", legacy, target)
    shutil.copytree(legacy, target, dirs_exist_ok=True)


# ---------------------------------------------------------------- ventana


def _already_running() -> bool:
    try:
        with _LOCAL.open(URL + "api/ping", timeout=2) as response:
            return json.load(response).get("app") == "MiAgendaDigital"
    except Exception:  # noqa: BLE001 - nada escuchando, u otra cosa en el puerto
        return False


def _window_profile() -> Path:
    return app_home() / "ventana"


def _window_alive() -> bool:
    """¿Sigue abierta alguna ventana de la agenda?

    No basta con esperar al proceso lanzado: al abrirse desde el Explorador,
    Edge se relanza a sí mismo y el primer proceso termina enseguida. Lo fiable
    es el «lockfile» del perfil, que Edge mantiene bloqueado mientras funciona.
    """
    lock = _window_profile() / "lockfile"
    try:
        with open(lock, "rb"):
            return False  # Fichero huérfano de un cierre anterior.
    except FileNotFoundError:
        return False
    except OSError:
        return True  # Bloqueado: Edge lo está usando.


def _wait_window_closed(stop: threading.Event) -> bool:
    """Espera a que se cierre la ventana (o a que una actualización pida
    reiniciar). False si la ventana nunca llegó a abrirse."""
    deadline = time.monotonic() + 30
    while not _window_alive():
        if stop.is_set():
            return True
        if time.monotonic() > deadline:
            return False
        time.sleep(0.5)
    misses = 0
    while misses < 3:  # Varios segundos libres seguidos: cerrada de verdad.
        if stop.wait(1):
            return True
        misses = 0 if _window_alive() else misses + 1
    return True


def _open_window() -> subprocess.Popen | None:
    """Abre la agenda en una ventana de Edge en modo aplicación, con un perfil
    propio (separado del Edge personal) donde se conserva la sesión de la agenda."""
    from app.services.factorial import FactorialError, _edge_path

    try:
        edge = _edge_path()
    except FactorialError:
        return None
    profile = _window_profile()
    profile.mkdir(parents=True, exist_ok=True)
    return subprocess.Popen(
        [
            edge,
            f"--app={URL}",
            f"--user-data-dir={profile}",
            "--no-first-run",
            "--no-default-browser-check",
            "--disable-background-mode",
            "--window-size=1400,900",
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def _browser_fallback() -> None:
    """Sin Edge: se abre el navegador predeterminado y un aviso hace de botón de cierre."""
    webbrowser.open(URL)
    _message("La agenda está abierta en tu navegador.\n\nPulsa Aceptar cuando termines para cerrarla.")


# ---------------------------------------------------------------- arranque


def _port_free() -> bool:
    with socket.socket() as probe:
        try:
            probe.bind((HOST, PORT))
            return True
        except OSError:
            return False


def _bind_server(app, retry_seconds: float):
    """Abre el puerto; tras una actualización espera a que lo suelte la versión anterior.

    Se comprueba antes de crear el servidor porque werkzeug, si el puerto está
    ocupado, no lanza una excepción: imprime el error y termina el programa.
    """
    from werkzeug.serving import make_server

    deadline = time.monotonic() + retry_seconds
    while not _port_free():
        if time.monotonic() > deadline:
            raise OSError(f"El puerto {PORT} está en uso.")
        time.sleep(0.5)
    try:
        return make_server(HOST, PORT, app, threaded=True)
    except SystemExit:
        raise OSError(f"El puerto {PORT} está en uso.") from None


def main() -> int:
    folder = data_dir()
    _setup_logging(folder)
    no_window = os.environ.get("AGENDA_NO_BROWSER", "").strip().lower() in ("1", "true", "si", "sí")
    after_update = os.environ.pop("AGENDA_AFTER_UPDATE", "") == "1"

    if not after_update and _already_running():
        if not no_window and _open_window() is None:
            webbrowser.open(URL)
        return 0

    try:
        from app.services.updater import cleanup_old_versions

        cleanup_old_versions()
        # Tras actualizar, el .exe anterior sigue en uso unos segundos: se reintenta luego.
        cleaner = threading.Timer(20, cleanup_old_versions)
        cleaner.daemon = True
        cleaner.start()
        _migrate_portable_data(folder)
        from app import create_app

        app = create_app()
        server = _bind_server(app, retry_seconds=20 if after_update else 0)
    except OSError as error:
        logging.exception("No se ha podido iniciar el servidor")
        _message(
            f"No se ha podido iniciar la agenda: el puerto {PORT} está ocupado por otro programa.\n\n"
            f"Detalle: {error}",
            error=True,
        )
        return 1
    except Exception as error:  # noqa: BLE001
        logging.exception("Error al arrancar")
        _message(f"No se ha podido iniciar la agenda.\n\nDetalle: {error}\n\nRegistro: {folder / 'agenda.log'}",
                 error=True)
        return 1

    logging.info("Agenda %s iniciada en %s (datos en %s)", APP_VERSION, URL, folder)
    stop = app.extensions["updater"].restart_requested
    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()

    try:
        if no_window:
            print(f"\n  Mi Agenda Digital {APP_VERSION} en {URL}\n  Para cerrarla: Ctrl+C\n")
            while not stop.wait(0.5):
                pass
        elif after_update and _window_alive():
            # La ventana de antes sigue abierta y se recarga sola con la versión nueva.
            _wait_window_closed(stop)
        elif _open_window() is None or not _wait_window_closed(stop):
            _browser_fallback()
    except KeyboardInterrupt:
        pass
    finally:
        server.shutdown()
        logging.info("Agenda cerrada%s", " para actualizarse" if stop.is_set() else "")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
