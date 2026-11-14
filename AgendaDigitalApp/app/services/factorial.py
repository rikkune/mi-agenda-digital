"""Fichaje en Factorial (app.factorialhr.com) con tu cuenta de Microsoft (Entra ID).

Cómo funciona:
1. Factorial entra con Microsoft (SSO + MFA), así que el inicio de sesión necesita
   un navegador de verdad. «Conectar con Factorial» abre Microsoft Edge con un
   perfil propio de la agenda (data/factorial-profile). Inicias sesión como siempre
   y, en cuanto Factorial carga, la ventana se cierra sola.
2. La agenda se queda con las cookies de Factorial, cifradas con DPAPI en
   data/factorial.json, y ficha con peticiones HTTP normales (sin navegador).
3. Si la sesión de Factorial caduca, se renueva sin mostrar nada: Edge se abre en
   segundo plano con el mismo perfil y Microsoft reconoce tu sesión. Solo cuando
   Microsoft vuelve a pedir contraseña o MFA hay que pulsar «Conectar» otra vez.
4. Después de cada fichaje se vuelve a leer el estado en Factorial para confirmar
   que ha quedado registrado de verdad.

Las cookies y el perfil de Edge nunca van a la base de datos ni a las copias.
"""

from __future__ import annotations

import base64
import json
import os
import shutil
import socket
import subprocess
import threading
import time
from datetime import date, datetime
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlparse
from urllib.request import ProxyHandler, Request, build_opener, urlopen

from .auth import decrypt_text, encrypt_text

APP_URL = "https://app.factorialhr.com/"
API = "https://api.factorialhr.com"
API_VERSION = "2026-10-01"
RESOURCES = f"{API}/api/{API_VERSION}/resources"
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/130.0 Safari/537.36 Edg/130.0"
)
TIMEOUT = 20
LOGIN_TIMEOUT = 300   # Tiempo para completar el inicio de sesión en la ventana de Edge.
SILENT_TIMEOUT = 45   # Renovación en segundo plano.
SILENT_RETRY = 300    # Tras un intento fallido, no se reintenta en 5 minutos.

# Acción -> (ruta en la API, texto para la interfaz).
ACTIONS = {
    "clock_in": ("attendance/shifts/clock_in", "Entrada"),
    "break_start": ("attendance/shifts/break_start", "Inicio de descanso"),
    "break_end": ("attendance/shifts/break_end", "Fin de descanso"),
    "clock_out": ("attendance/shifts/clock_out", "Salida"),
}
# Estado actual -> acciones que tienen sentido.
ALLOWED = {
    "out": ("clock_in",),
    "working": ("break_start", "clock_out"),
    "break": ("break_end",),
}
# Estado que debe quedar tras cada acción (para confirmar el fichaje).
EXPECTED = {"clock_in": "working", "break_start": "break", "break_end": "working", "clock_out": "out"}


class FactorialError(RuntimeError):
    """Error con un mensaje apto para la interfaz."""


class FactorialAuthError(FactorialError):
    """La sesión de Factorial no es válida y no se ha podido renovar."""


# ---------------------------------------------------------------- navegador


def _is_app_page(url: str) -> bool:
    """¿Es una página de Factorial ya dentro de la sesión (no de inicio de sesión)?"""
    parsed = urlparse(url or "")
    if parsed.hostname != "app.factorialhr.com":
        return False
    path = parsed.path.lower()
    return not any(word in path for word in ("sign_in", "login", "saml", "sso", "oauth", "two_factor"))


_LOCAL = build_opener(ProxyHandler({}))  # El puerto de depuración es local: sin proxy.


def _edge_path() -> str:
    for variable in ("PROGRAMFILES(X86)", "PROGRAMFILES", "LOCALAPPDATA"):
        base = os.environ.get(variable)
        if base:
            candidate = Path(base) / "Microsoft" / "Edge" / "Application" / "msedge.exe"
            if candidate.exists():
                return str(candidate)
    found = shutil.which("msedge")
    if found:
        return found
    raise FactorialError("No se ha encontrado Microsoft Edge en este equipo.")


def _free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def _devtools(port: int, path: str):
    with _LOCAL.open(f"http://127.0.0.1:{port}{path}", timeout=2) as response:
        return json.load(response)


def launch_edge(profile_dir: Path, hidden: bool) -> tuple[subprocess.Popen, int]:
    """Abre un Edge normal (sin automatización) con el perfil de la agenda.

    Cloudflare bloquea los navegadores automatizados, así que Edge se abre como lo
    abrirías tú; la agenda solo consulta por el puerto de depuración qué página
    hay abierta, sin intervenir en ella.
    """
    profile_dir.mkdir(parents=True, exist_ok=True)
    port = _free_port()
    args = [
        _edge_path(),
        f"--remote-debugging-port={port}",
        f"--user-data-dir={profile_dir}",
        "--no-first-run",
        "--no-default-browser-check",
        "--new-window",
    ]
    if hidden:
        # Renovación silenciosa: la ventana existe, pero fuera de la pantalla.
        args += ["--window-position=-32000,-32000", "--window-size=1024,768"]
    args.append(APP_URL)
    process = subprocess.Popen(args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    deadline = time.monotonic() + 20
    while time.monotonic() < deadline:
        if process.poll() is not None:
            break
        try:
            _devtools(port, "/json/version")
            return process, port
        except (URLError, OSError, ValueError):
            time.sleep(0.3)
    process.kill()
    raise FactorialError(
        "No se ha podido abrir Microsoft Edge. Si ya hay una ventana de Factorial "
        "abierta por la agenda, ciérrala y vuelve a intentarlo."
    )


def page_urls(port: int) -> list[str] | None:
    """URLs de las pestañas abiertas, o None si Edge se ha cerrado."""
    try:
        return [t.get("url", "") for t in _devtools(port, "/json/list") if t.get("type") == "page"]
    except (URLError, OSError, ValueError):
        return None


def wait_for_session(process: subprocess.Popen, port: int, timeout: int) -> bool:
    """Espera a que alguna pestaña esté dentro de Factorial (sesión iniciada)."""
    deadline = time.monotonic() + timeout
    stable_since = None
    while time.monotonic() < deadline:
        urls = page_urls(port)
        if urls is None or process.poll() is not None:
            return False  # Ventana cerrada.
        if any(_is_app_page(url) for url in urls):
            stable_since = stable_since or time.monotonic()
            # Sin sesión, la aplicación redirige al acceso en un momento.
            if time.monotonic() - stable_since >= 3:
                return True
        else:
            stable_since = None
        time.sleep(0.5)
    return False


def _cookie_header_for(cookies: list[dict], host: str) -> str:
    now = time.time()
    pairs = []
    for cookie in cookies:
        domain = cookie.get("domain", "").lstrip(".")
        expires = cookie.get("expires", -1)
        if (host == domain or host.endswith("." + domain)) and (expires in (-1, None) or expires > now):
            pairs.append(f"{cookie['name']}={cookie['value']}")
    return "; ".join(pairs)


def _session_works(cookies: list[dict], user_agent: str) -> bool:
    """¿Aceptan estas cookies la API de Factorial? (sin sesión responde 401)."""
    today = date.today()
    url = f"{API}/attendance/periods?" + urlencode({"year": today.year, "month": today.month})
    headers = {
        "Accept": "application/json",
        "Cookie": _cookie_header_for(cookies, "api.factorialhr.com"),
        "Origin": "https://app.factorialhr.com",
        "Referer": APP_URL,
        "User-Agent": user_agent,
    }
    try:
        with urlopen(Request(url, headers=headers), timeout=TIMEOUT) as response:
            return response.status == 200 and "json" in response.headers.get("Content-Type", "")
    except (HTTPError, URLError, TimeoutError, OSError):
        return False


class _CDP:
    """Cliente mínimo del protocolo DevTools de Edge (WebSocket, solo librería estándar).

    La agenda solo necesita dos órdenes —leer las cookies y cerrar el navegador—,
    así que no hace falta Playwright.
    """

    def __init__(self, ws_url: str, timeout: float = 10):
        parsed = urlparse(ws_url)
        self._sock = socket.create_connection((parsed.hostname, parsed.port or 80), timeout=timeout)
        key = base64.b64encode(os.urandom(16)).decode()
        handshake = (
            f"GET {parsed.path} HTTP/1.1\r\nHost: {parsed.hostname}:{parsed.port}\r\n"
            "Upgrade: websocket\r\nConnection: Upgrade\r\n"
            f"Sec-WebSocket-Key: {key}\r\nSec-WebSocket-Version: 13\r\n\r\n"
        )
        self._sock.sendall(handshake.encode())
        response = b""
        while b"\r\n\r\n" not in response:
            chunk = self._sock.recv(4096)
            if not chunk:
                raise OSError("Edge ha cerrado la conexión de depuración.")
            response += chunk
        head, self._buffer = response.split(b"\r\n\r\n", 1)
        if b" 101 " not in head.split(b"\r\n", 1)[0]:
            raise OSError("Edge no ha aceptado la conexión de depuración.")
        self._next_id = 0

    def _recv_exact(self, size: int) -> bytes:
        while len(self._buffer) < size:
            chunk = self._sock.recv(65536)
            if not chunk:
                raise OSError("Edge ha cerrado la conexión de depuración.")
            self._buffer += chunk
        data, self._buffer = self._buffer[:size], self._buffer[size:]
        return data

    def _send_text(self, text: str) -> None:
        payload = text.encode("utf-8")
        header = bytearray([0x81])  # FIN + texto
        length = len(payload)
        if length < 126:
            header.append(0x80 | length)
        elif length < 1 << 16:
            header.append(0x80 | 126)
            header += length.to_bytes(2, "big")
        else:
            header.append(0x80 | 127)
            header += length.to_bytes(8, "big")
        mask = os.urandom(4)
        masked = bytes(b ^ mask[i % 4] for i, b in enumerate(payload))
        self._sock.sendall(bytes(header) + mask + masked)

    def _recv_message(self) -> str:
        parts = []
        while True:
            first, second = self._recv_exact(2)
            length = second & 0x7F
            if length == 126:
                length = int.from_bytes(self._recv_exact(2), "big")
            elif length == 127:
                length = int.from_bytes(self._recv_exact(8), "big")
            mask = self._recv_exact(4) if second & 0x80 else None
            payload = self._recv_exact(length)
            if mask:
                payload = bytes(b ^ mask[i % 4] for i, b in enumerate(payload))
            opcode = first & 0x0F
            if opcode == 0x8:
                raise OSError("Edge ha cerrado la conexión de depuración.")
            if opcode in (0x9, 0xA):  # ping/pong: no llevan datos de la agenda
                continue
            parts.append(payload)
            if first & 0x80:
                return b"".join(parts).decode("utf-8")

    def call(self, method: str, params: dict | None = None, wait: bool = True) -> dict:
        self._next_id += 1
        message_id = self._next_id
        self._send_text(json.dumps({"id": message_id, "method": method, "params": params or {}}))
        if not wait:
            return {}
        while True:
            message = json.loads(self._recv_message())
            if message.get("id") == message_id:
                if "error" in message:
                    raise OSError(message["error"].get("message", "Error de Edge"))
                return message.get("result", {})

    def close(self) -> None:
        try:
            self._sock.close()
        except OSError:
            pass


def _browser_login(profile_dir: Path, hidden: bool, timeout: int) -> tuple[list[dict], str] | None:
    """Abre Edge, espera a que entres en Factorial y devuelve (cookies, user-agent).

    Devuelve None si no se llega a Factorial con la sesión iniciada (tiempo
    agotado, ventana cerrada o Microsoft pide volver a identificarse).
    """
    process, port = launch_edge(profile_dir, hidden)
    deadline = time.monotonic() + timeout
    try:
        version = _devtools(port, "/json/version")
        user_agent = version.get("User-Agent", USER_AGENT)
        while True:
            remaining = int(deadline - time.monotonic())
            if remaining <= 0 or not wait_for_session(process, port, remaining):
                return None
            # Solo ahora (ya dentro de Factorial) se conecta la agenda al navegador.
            cdp = _CDP(version["webSocketDebuggerUrl"])
            try:
                cookies = [
                    cookie for cookie in cdp.call("Storage.getCookies").get("cookies", [])
                    if cookie.get("domain", "").lstrip(".").endswith("factorialhr.com")
                ]
                if cookies and _session_works(cookies, user_agent):
                    try:
                        # Cierre ordenado: Edge guarda el perfil (y tu sesión de Microsoft).
                        cdp.call("Browser.close", wait=False)
                    except OSError:
                        pass
                    return cookies, user_agent
            finally:
                cdp.close()
            time.sleep(2)  # Aún no hay sesión válida: se sigue esperando.
    except FactorialError:
        raise
    except Exception:  # noqa: BLE001 - Edge cerrado a mitad
        return None
    finally:
        close_edge(process)


def close_edge(process: subprocess.Popen) -> None:
    """Tras Browser.close, Edge termina solo; si no (tiempo agotado), se fuerza."""
    if process.poll() is None:
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()


# ---------------------------------------------------------------- utilidades


def _parse_time(value, day: str | None) -> datetime | None:
    """Acepta «2026-11-12T08:01:00+01:00» o «08:01» (junto con la fecha del turno)."""
    if not value:
        return None
    text = str(value)
    try:
        if "T" in text:
            moment = datetime.fromisoformat(text.replace("Z", "+00:00"))
            return moment.astimezone().replace(tzinfo=None)
        if day:
            return datetime.fromisoformat(f"{day}T{text[:5]}")
    except ValueError:
        return None
    return None


def _items(payload) -> list[dict]:
    if isinstance(payload, dict):
        payload = payload.get("data", payload.get("shifts", []))
    return [item for item in payload or [] if isinstance(item, dict)]


# ---------------------------------------------------------------- cliente


class Factorial:
    """Sesión de Factorial de la persona usuaria (aplicación de un solo usuario)."""

    def __init__(self, data_dir: Path):
        self.path = data_dir / "factorial.json"
        self.profile_dir = data_dir / "factorial-profile"
        self._lock = threading.Lock()          # Cookies y fichero.
        self._browser_lock = threading.Lock()  # Un solo Edge a la vez con el perfil.
        self._cookies: list[dict] = []
        self._user_agent = USER_AGENT
        self._employee_id: int | None = None
        self._connected_at: str | None = None
        self._login = {"state": "idle", "error": None}
        self._silent_failed_at = 0.0
        self._load()

    # -- fichero

    def _load(self) -> None:
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
            cookies = json.loads(decrypt_text(payload["scheme"], payload["secret"]))
        except (OSError, ValueError, KeyError):
            return
        self._cookies = cookies
        self._user_agent = payload.get("user_agent") or USER_AGENT
        self._employee_id = payload.get("employee_id")
        self._connected_at = payload.get("connected_at")

    def _save(self) -> None:
        if not self._cookies:
            self.path.unlink(missing_ok=True)
            return
        scheme, secret = encrypt_text(json.dumps(self._cookies))
        payload = {
            "scheme": scheme,
            "secret": secret,
            "employee_id": self._employee_id,
            "connected_at": self._connected_at,
            "user_agent": self._user_agent,
        }
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        try:
            os.chmod(tmp, 0o600)
        except OSError:
            pass
        os.replace(tmp, self.path)

    def _store_cookies(self, session: tuple[list[dict], str], fresh_login: bool) -> None:
        with self._lock:
            self._cookies, self._user_agent = session
            if fresh_login or not self._connected_at:
                self._connected_at = datetime.now().isoformat(timespec="seconds")
            self._save()

    # -- HTTP

    def _cookie_header(self, host: str) -> str:
        return _cookie_header_for(self._cookies, host)

    def _request(self, method: str, url: str, params: dict | None = None, body: dict | None = None):
        if params:
            url += "?" + urlencode(params, doseq=True)
        cookie = self._cookie_header(urlparse(url).hostname or "")
        if not cookie:
            raise FactorialAuthError("No hay sesión de Factorial.")
        headers = {
            "Accept": "application/json",
            "Cookie": cookie,
            "Origin": "https://app.factorialhr.com",
            "Referer": APP_URL,
            "User-Agent": self._user_agent,
        }
        data = None
        if body is not None:
            data = json.dumps(body).encode("utf-8")
            headers["Content-Type"] = "application/json"
        try:
            with urlopen(Request(url, data=data, headers=headers, method=method), timeout=TIMEOUT) as response:
                final_url = response.geturl()
                raw = response.read()
                kind = response.headers.get("Content-Type", "")
        except HTTPError as error:
            if error.code == 401:
                raise FactorialAuthError("La sesión de Factorial ha caducado.") from error
            detail = ""
            try:
                payload = json.loads(error.read() or b"{}")
                detail = payload.get("error") or payload.get("message") or ""
                if isinstance(detail, dict):
                    detail = detail.get("message", "")
            except ValueError:
                pass
            raise FactorialError(
                f"Factorial ha respondido con un error ({error.code})" + (f": {detail}" if detail else ".")
            ) from error
        except (URLError, TimeoutError, OSError) as error:
            raise FactorialError("No se ha podido conectar con Factorial. Revisa tu conexión a Internet.") from error
        if "sign_in" in final_url or "json" not in kind:
            # Redirigido a la página de acceso: la cookie ya no vale.
            raise FactorialAuthError("La sesión de Factorial ha caducado.")
        return json.loads(raw or b"null")

    def _call(self, method: str, url: str, params: dict | None = None, body: dict | None = None):
        """Petición con renovación silenciosa de la sesión si ha caducado."""
        try:
            return self._request(method, url, params, body)
        except FactorialAuthError:
            if not self._silent_renew():
                with self._lock:
                    self._cookies = []
                    self._save()
                raise FactorialAuthError(
                    "La sesión de Factorial ha caducado. Pulsa «Conectar con Factorial» "
                    "para volver a iniciar sesión con Microsoft."
                )
            return self._request(method, url, params, body)

    def _silent_renew(self) -> bool:
        if time.monotonic() - self._silent_failed_at < SILENT_RETRY or not self.profile_dir.exists():
            return False
        if not self._browser_lock.acquire(timeout=SILENT_TIMEOUT + 15):
            return False
        try:
            cookies = _browser_login(self.profile_dir, hidden=True, timeout=SILENT_TIMEOUT)
        except FactorialError:
            cookies = None
        finally:
            self._browser_lock.release()
        if not cookies:
            self._silent_failed_at = time.monotonic()
            return False
        self._store_cookies(cookies, fresh_login=False)
        return True

    # -- inicio de sesión

    def start_login(self) -> None:
        """Abre la ventana de Edge para iniciar sesión (en segundo plano)."""
        with self._lock:
            if self._login["state"] == "waiting":
                return
            self._login = {"state": "waiting", "error": None}
        threading.Thread(target=self._login_worker, name="factorial-login", daemon=True).start()

    def _login_worker(self) -> None:
        error = None
        try:
            with self._browser_lock:
                cookies = _browser_login(self.profile_dir, hidden=False, timeout=LOGIN_TIMEOUT)
            if cookies:
                self._store_cookies(cookies, fresh_login=True)
                self._silent_failed_at = 0.0
                self._employee()  # Comprueba que la sesión sirve para la API.
            else:
                error = "No se ha completado el inicio de sesión en Factorial."
        except FactorialError as exc:
            error = str(exc)
        except Exception as exc:  # noqa: BLE001 - nunca dejar la tarjeta «esperando».
            error = f"Error inesperado al conectar con Factorial: {exc}"
        with self._lock:
            self._login = {"state": "error" if error else "idle", "error": error}

    def disconnect(self) -> None:
        """Olvida la sesión de Factorial y borra el perfil de Edge de la agenda."""
        with self._browser_lock, self._lock:
            self._cookies, self._employee_id, self._connected_at = [], None, None
            self._save()
            shutil.rmtree(self.profile_dir, ignore_errors=True)

    # -- datos

    def _employee(self) -> int:
        if self._employee_id:
            return self._employee_id
        today = date.today()
        employee_id = None
        # 1) API clásica de la web: los periodos de asistencia llevan tu employee_id.
        try:
            periods = self._call("GET", f"{API}/attendance/periods", {"year": today.year, "month": today.month})
            for period in _items(periods):
                if period.get("employee_id"):
                    employee_id = int(period["employee_id"])
                    break
        except FactorialAuthError:
            raise
        except FactorialError:
            pass
        # 2) API pública: credenciales de la sesión actual.
        if not employee_id:
            try:
                credentials = self._call("GET", f"{RESOURCES}/api_public/credentials")
                for item in _items(credentials):
                    if item.get("employee_id"):
                        employee_id = int(item["employee_id"])
                        break
            except FactorialAuthError:
                raise
            except FactorialError:
                pass
        if not employee_id:
            raise FactorialError("No se ha podido identificar tu ficha de empleado en Factorial.")
        with self._lock:
            self._employee_id = employee_id
            self._save()
        return employee_id

    def _today_shifts(self) -> list[dict]:
        employee_id = self._employee()
        today = date.today().isoformat()
        payload = self._call(
            "GET",
            f"{RESOURCES}/attendance/shifts",
            {"employee_ids[]": employee_id, "start_on": today, "end_on": today},
        )
        shifts = []
        for item in _items(payload):
            day = item.get("date") or item.get("reference_date") or today
            if day != today:
                continue
            start = _parse_time(item.get("clock_in"), day)
            if not start:
                continue
            shifts.append({
                "start": start,
                "end": _parse_time(item.get("clock_out"), day),
                "workable": item.get("workable", True) is not False,
            })
        shifts.sort(key=lambda shift: shift["start"])
        return shifts

    def clock(self) -> dict:
        """Estado del fichaje de hoy leído de Factorial."""
        shifts = self._today_shifts()
        now = datetime.now().replace(microsecond=0)
        state, since = "out", None
        worked = 0
        for shift in shifts:
            end = shift["end"] or now
            if shift["workable"]:
                worked += max(0, int((end - shift["start"]).total_seconds()))
            if shift["end"] is None:
                state, since = ("working" if shift["workable"] else "break"), shift["start"]
        return {
            "state": state,
            "since": since.isoformat() if since else None,
            "worked_seconds": worked,
            "first_in": shifts[0]["start"].isoformat() if shifts else None,
            "actions": list(ALLOWED[state]),
            "checked_at": now.isoformat(),
        }

    def status(self) -> dict:
        with self._lock:
            login = dict(self._login)
            connected = bool(self._cookies)
            connected_at = self._connected_at
        result = {"connected": connected, "login": login, "connected_at": connected_at, "clock": None, "error": None}
        if connected and login["state"] != "waiting":
            try:
                result["clock"] = self.clock()
            except FactorialAuthError as error:
                result.update(connected=False, error=str(error))
            except FactorialError as error:
                result["error"] = str(error)
        return result

    def act(self, action: str) -> dict:
        """Ficha (entrada, descanso o salida) y confirma el resultado en Factorial."""
        if action not in ACTIONS:
            raise FactorialError("Acción de fichaje desconocida.")
        path, label = ACTIONS[action]
        current = self.clock()
        if action not in current["actions"]:
            raise FactorialError(f"Ahora mismo no se puede fichar «{label}»: el estado en Factorial ha cambiado.")
        now = datetime.now().astimezone().replace(microsecond=0).isoformat()
        self._call("POST", f"{RESOURCES}/{path}", body={"employee_id": self._employee(), "now": now})
        after = self.clock()
        if after["state"] != EXPECTED[action]:
            raise FactorialError(
                f"Factorial no ha confirmado «{label}». Revisa tu fichaje en app.factorialhr.com."
            )
        return {"label": label, "clock": after}
