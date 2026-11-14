"""Inicio de sesión de la agenda con las credenciales del Aula Virtual de MEDAC.

- El usuario y la contraseña son los de MEDAC: se comprueban contra el Aula
  Virtual al iniciar sesión y son los que luego usa la sincronización.
- Con «Mantener la sesión iniciada», la contraseña se guarda cifrada en
  data/credentials.json con DPAPI de Windows (solo tu usuario de Windows en este
  equipo puede descifrarla) y la cookie de sesión no caduca hasta que pulses
  «Cerrar sesión». Sin esa opción, la contraseña vive solo en memoria y la
  sesión termina al cerrar el navegador o la agenda.
- Cerrar sesión borra la contraseña guardada e invalida todas las cookies.
- Las credenciales nunca se guardan en la base de datos (ni en sus copias).
"""

from __future__ import annotations

import base64
import json
import os
import secrets
import sys
import threading
from pathlib import Path

_ENTROPY = b"MiAgendaDigital/credenciales-medac"


# ---------------------------------------------------------------- cifrado


def _dpapi(data: bytes, protect: bool) -> bytes:
    """Cifra o descifra con DPAPI (ligado al usuario de Windows actual)."""
    import ctypes
    from ctypes import wintypes

    class Blob(ctypes.Structure):
        _fields_ = [("cbData", wintypes.DWORD), ("pbData", ctypes.POINTER(ctypes.c_char))]

    def blob(raw: bytes) -> tuple[Blob, ctypes.Array]:
        buffer = ctypes.create_string_buffer(raw, len(raw))
        return Blob(len(raw), ctypes.cast(buffer, ctypes.POINTER(ctypes.c_char))), buffer

    crypt32 = ctypes.WinDLL("crypt32", use_last_error=True)
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.LocalFree.argtypes = [ctypes.c_void_p]
    function = crypt32.CryptProtectData if protect else crypt32.CryptUnprotectData
    function.argtypes = [
        ctypes.POINTER(Blob), ctypes.c_wchar_p, ctypes.POINTER(Blob),
        ctypes.c_void_p, ctypes.c_void_p, wintypes.DWORD, ctypes.POINTER(Blob),
    ]
    function.restype = wintypes.BOOL

    data_in, _keep_data = blob(data)
    entropy, _keep_entropy = blob(_ENTROPY)
    data_out = Blob()
    ui_forbidden = 0x01
    ok = function(ctypes.byref(data_in), "Mi Agenda Digital" if protect else None,
                  ctypes.byref(entropy), None, None, ui_forbidden, ctypes.byref(data_out))
    if not ok:
        raise OSError(ctypes.get_last_error(), "DPAPI no ha podido procesar la contraseña.")
    try:
        return ctypes.string_at(data_out.pbData, data_out.cbData)
    finally:
        kernel32.LocalFree(data_out.pbData)


def _encrypt(password: str) -> tuple[str, str]:
    raw = password.encode("utf-8")
    if sys.platform == "win32":
        return "dpapi", base64.b64encode(_dpapi(raw, protect=True)).decode()
    # Fuera de Windows no hay DPAPI: el fichero queda solo legible por tu usuario.
    return "plain", base64.b64encode(raw).decode()


def _decrypt(scheme: str, value: str) -> str:
    raw = base64.b64decode(value)
    if scheme == "dpapi":
        raw = _dpapi(raw, protect=False)
    return raw.decode("utf-8")


# Uso desde otros servicios (p. ej. las cookies de Factorial).
encrypt_text = _encrypt
decrypt_text = _decrypt


# ---------------------------------------------------------------- almacén


class AuthStore:
    """Credenciales de la persona que ha iniciado sesión (aplicación de un solo usuario)."""

    def __init__(self, data_dir: Path):
        self.path = data_dir / "credentials.json"
        self._lock = threading.Lock()
        self._username: str | None = None
        self._password: str | None = None
        self._token: str | None = None
        self._last_username = ""
        self._load()

    # -- fichero

    def _read_file(self) -> dict:
        try:
            return json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return {}

    def _write_file(self, payload: dict) -> None:
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        try:
            os.chmod(tmp, 0o600)
        except OSError:
            pass
        os.replace(tmp, self.path)

    def _load(self) -> None:
        payload = self._read_file()
        self._last_username = payload.get("last_username", "")
        if not (payload.get("username") and payload.get("secret") and payload.get("token")):
            return
        try:
            password = _decrypt(payload.get("scheme", ""), payload["secret"])
        except (OSError, ValueError):
            # Fichero copiado de otro equipo/usuario: hay que volver a iniciar sesión.
            return
        self._username, self._password, self._token = payload["username"], password, payload["token"]

    # -- API

    @property
    def last_username(self) -> str:
        return self._last_username

    def is_valid(self, token: str | None) -> bool:
        return bool(token and self._token and self._password and secrets.compare_digest(token, self._token))

    def username(self) -> str | None:
        return self._username

    def credentials(self) -> tuple[str, str] | None:
        if self._username and self._password:
            return self._username, self._password
        return None

    def sign_in(self, username: str, password: str, persistent: bool) -> str:
        """Guarda las credenciales ya comprobadas y devuelve el token de la nueva sesión."""
        token = secrets.token_urlsafe(32)
        with self._lock:
            payload = {"last_username": username}
            if persistent:
                scheme, secret = _encrypt(password)
                payload.update(username=username, scheme=scheme, secret=secret, token=token)
            self._write_file(payload)
            self._username, self._password, self._token = username, password, token
            self._last_username = username
        return token

    def sign_out(self) -> None:
        """Borra la contraseña guardada e invalida cualquier sesión abierta."""
        with self._lock:
            self._username = self._password = self._token = None
            self._write_file({"last_username": self._last_username})


def secret_key(data_dir: Path) -> bytes:
    """Clave para firmar las cookies; se crea una vez y se reutiliza entre arranques."""
    path = data_dir / "secret_key"
    try:
        key = path.read_bytes()
        if len(key) >= 32:
            return key
    except OSError:
        pass
    key = secrets.token_bytes(48)
    path.write_bytes(key)
    try:
        os.chmod(path, 0o600)
    except OSError:
        pass
    return key
