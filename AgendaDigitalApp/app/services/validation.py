"""Validación de los datos que llegan desde la interfaz."""

from __future__ import annotations

import re
from datetime import date, datetime, time


class ValidationError(ValueError):
    """Error de validación que se devuelve a la interfaz en español."""


DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
TIME_RE = re.compile(r"^\d{2}:\d{2}$")


def text(
    value,
    field: str,
    *,
    max_len: int = 500,
    required: bool = False,
    default: str = "",
) -> str:
    """Limpia un texto y comprueba su longitud."""
    if value is None:
        value = default
    if not isinstance(value, str):
        raise ValidationError(f"El campo «{field}» debe ser texto.")
    cleaned = value.strip()
    if required and not cleaned:
        raise ValidationError(f"El campo «{field}» es obligatorio.")
    if len(cleaned) > max_len:
        raise ValidationError(
            f"El campo «{field}» no puede superar los {max_len} caracteres."
        )
    return cleaned


def date_value(value, field: str, *, required: bool = False) -> str | None:
    """Valida una fecha ISO y la devuelve como YYYY-MM-DD."""
    if value in (None, ""):
        if required:
            raise ValidationError(f"El campo «{field}» es obligatorio.")
        return None
    if not isinstance(value, str) or not DATE_RE.match(value):
        raise ValidationError(f"El campo «{field}» debe tener el formato AAAA-MM-DD.")
    try:
        date.fromisoformat(value)
    except ValueError as exc:
        raise ValidationError(f"La fecha de «{field}» no es válida.") from exc
    return value


def time_value(value, field: str, *, required: bool = False) -> str | None:
    """Valida una hora HH:MM."""
    if value in (None, ""):
        if required:
            raise ValidationError(f"El campo «{field}» es obligatorio.")
        return None
    if not isinstance(value, str) or not TIME_RE.match(value):
        raise ValidationError(f"El campo «{field}» debe tener el formato HH:MM.")
    try:
        time.fromisoformat(value)
    except ValueError as exc:
        raise ValidationError(f"La hora de «{field}» no es válida.") from exc
    return value


def choice(value, field: str, allowed: dict | tuple | list, *, default=None):
    """Comprueba que un valor pertenece a una lista cerrada."""
    if value in (None, "") and default is not None:
        return default
    if value not in allowed:
        options = ", ".join(str(item) for item in allowed)
        raise ValidationError(f"El campo «{field}» debe ser uno de: {options}.")
    return value


def integer(value, field: str, *, required: bool = False, default=None) -> int | None:
    if value in (None, "") and not required:
        return default
    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise ValidationError(f"El campo «{field}» debe ser un número entero.") from exc


def boolean(value, field: str, *, default: int = 0) -> int:
    if value is None:
        return default
    if isinstance(value, bool):
        return 1 if value else 0
    if value in (0, 1, "0", "1"):
        return int(value)
    if isinstance(value, str) and value.lower() in ("true", "false"):
        return 1 if value.lower() == "true" else 0
    raise ValidationError(f"El campo «{field}» debe ser verdadero o falso.")


COLOR_RE = re.compile(r"^#[0-9a-fA-F]{6}$")
COLOR_KEYWORDS = ("gradient-pink-blue",)


def color_value(value, field: str = "color") -> str | None:
    """Valida un color #RRGGBB o uno de los degradados predefinidos."""
    if value in (None, ""):
        return None
    if isinstance(value, str) and (COLOR_RE.match(value) or value in COLOR_KEYWORDS):
        return value.upper() if value.startswith("#") else value
    raise ValidationError(f"El campo «{field}» no es un color válido.")


def ensure_range(start: str, end: str | None, field: str) -> None:
    """Comprueba que la fecha final no es anterior a la inicial."""
    if end and start and end < start:
        raise ValidationError(
            f"La fecha final de «{field}» no puede ser anterior a la inicial."
        )


def query_date(value, field: str, default: date) -> date:
    """Fecha opcional de la URL; devuelve un error 400 si no es válida."""
    if value in (None, ""):
        return default
    return date.fromisoformat(date_value(value, field))


def iso_now() -> str:
    return datetime.now().replace(microsecond=0).isoformat()


def today_iso() -> str:
    return date.today().isoformat()
