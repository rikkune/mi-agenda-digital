"""Horario semanal editable (franjas horarias y clases de cada persona)."""

from __future__ import annotations

import json

from flask import Blueprint, jsonify, request

from ..db import get_db
from ..seed import TIME_ROWS
from ..services.calendar_utils import WEEKDAYS_ES
from ..services.query_helpers import fetch_schedule
from ..services.validation import (
    ValidationError,
    choice,
    integer,
    text,
    time_value,
)

bp = Blueprint("schedule", __name__, url_prefix="/api")

SLOT_KINDS = ("class", "break", "free")
TIMES_KEY = "schedule_times"
MAX_ROWS = 14


def _body() -> dict:
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        raise ValidationError("No se han recibido datos válidos.")
    return data


def _subject_id(connection, value):
    if value in (None, ""):
        return None
    subject_id = integer(value, "asignatura")
    row = connection.execute(
        "SELECT id FROM subjects WHERE id = ?", (subject_id,)
    ).fetchone()
    if not row:
        raise ValidationError("La asignatura seleccionada no existe.")
    return subject_id


def load_times(connection) -> list[tuple[str, str]]:
    """Franjas de esta persona; si no las ha cambiado, las del centro."""
    row = connection.execute("SELECT value FROM settings WHERE key = ?", (TIMES_KEY,)).fetchone()
    if row and row["value"]:
        try:
            return [(item["start"], item["end"]) for item in json.loads(row["value"])]
        except (ValueError, KeyError, TypeError):
            pass
    return list(TIME_ROWS)


def _validate_times(raw) -> list[tuple[str, str]]:
    if not isinstance(raw, list) or not raw:
        raise ValidationError("El horario necesita al menos una franja horaria.")
    if len(raw) > MAX_ROWS:
        raise ValidationError(f"El horario admite como máximo {MAX_ROWS} franjas.")
    times = []
    for index, item in enumerate(raw, start=1):
        if not isinstance(item, dict):
            raise ValidationError(f"La franja {index} no es válida.")
        start = time_value(item.get("start"), f"inicio de la franja {index}", required=True)
        end = time_value(item.get("end"), f"fin de la franja {index}", required=True)
        if start >= end:
            raise ValidationError(f"En la franja {index}, la hora de fin debe ser posterior a la de inicio.")
        times.append((start, end))
    times.sort()
    for (_, previous_end), (start, _) in zip(times, times[1:]):
        if start < previous_end:
            raise ValidationError(f"Las franjas se solapan: revisa la que empieza a las {start}.")
    return times


@bp.get("/schedule")
def get_schedule():
    connection = get_db()
    return jsonify(
        {
            "times": [{"start": start, "end": end} for start, end in load_times(connection)],
            "weekdays": WEEKDAYS_ES,
            "slots": fetch_schedule(connection),
        }
    )


@bp.put("/schedule")
def save_schedule():
    data = _body()
    slots = data.get("slots")
    if not isinstance(slots, list):
        raise ValidationError("El horario debe enviarse como una lista de clases.")
    if len(slots) > 5 * MAX_ROWS:
        raise ValidationError("El horario contiene demasiadas filas.")

    connection = get_db()
    times = _validate_times(data["times"]) if "times" in data else load_times(connection)
    ends = dict(times)

    prepared = []
    seen = set()
    for index, slot in enumerate(slots, start=1):
        if not isinstance(slot, dict):
            raise ValidationError(f"La fila {index} del horario no es válida.")
        weekday = integer(slot.get("weekday"), "día de la semana", required=True)
        if weekday not in (1, 2, 3, 4, 5):
            raise ValidationError("El día de la semana debe estar entre lunes y viernes.")
        start_time = time_value(slot.get("start_time"), "hora de inicio", required=True)
        if start_time not in ends:
            continue  # La franja se ha eliminado: su celda desaparece con ella.
        end_time = ends[start_time]
        kind = choice(slot.get("kind"), "tipo de celda", SLOT_KINDS, default="class")
        subject_id = _subject_id(connection, slot.get("subject_id"))
        label = text(slot.get("label"), "etiqueta", max_len=60)
        if kind == "class" and not subject_id:
            raise ValidationError("Cada clase debe tener una asignatura.")
        if kind != "class":
            subject_id = None
            if not label:
                label = "Descanso" if kind == "break" else "Libre"
        key = (weekday, start_time)
        if key in seen:
            raise ValidationError("Hay dos clases a la misma hora el mismo día.")
        seen.add(key)
        prepared.append((weekday, start_time, end_time, subject_id, label, kind))

    with connection:
        connection.execute("DELETE FROM schedule_slots")
        connection.executemany(
            """
            INSERT INTO schedule_slots
                (weekday, start_time, end_time, subject_id, label, kind)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            prepared,
        )
        connection.execute(
            "INSERT INTO settings (key, value) VALUES (?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
            (TIMES_KEY, json.dumps([{"start": s, "end": e} for s, e in times])),
        )

    return jsonify(
        {
            "ok": True,
            "times": [{"start": start, "end": end} for start, end in times],
            "slots": fetch_schedule(connection),
        }
    )
