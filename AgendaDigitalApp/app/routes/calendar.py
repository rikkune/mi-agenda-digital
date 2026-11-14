"""Calendario escolar: vistas mensual, semanal y anual, y eventos."""

from __future__ import annotations

from datetime import date

from flask import Blueprint, abort, jsonify, request
import sqlite3

from ..db import get_db
from ..services.calendar_utils import (
    MONTHS_ES,
    SCHOOL_END,
    SCHOOL_START,
    WEEKDAYS_ES,
    WEEKDAYS_SHORT,
    clamp_date,
    date_range,
    days_in_month,
    iso,
    month_grid,
    month_title,
    parse_date,
    school_year_days,
    shift_month,
    shift_week,
    week_grid,
    year_bounds,
)
from ..services.query_helpers import (
    fetch_calendar_items,
    fetch_holidays,
    fetch_schedule,
    group_holidays_by_day,
    group_items_by_day,
)
from ..services.validation import (
    ValidationError,
    boolean,
    choice,
    color_value,
    date_value,
    ensure_range,
    integer,
    iso_now,
    query_date,
    text,
    time_value,
)

bp = Blueprint("calendar", __name__, url_prefix="/api")

EVENT_CATEGORIES = ("evento", "entrega", "reunion", "examen", "otro")
SCOPE_LABELS = {
    "nacional": "Festivo nacional",
    "autonomico": "Festivo autonómico",
    "local": "Festivo local",
    "vacaciones": "Vacaciones",
    "no_lectivo": "Día no lectivo",
}
CATEGORY_LABELS = {
    "tarea": "Tarea",
    "entrega": "Entrega",
    "examen": "Examen",
    "reunion": "Reunión",
    "otro": "Otro",
    "evento": "Evento",
    "comienzo": "Comienzo",
    "plazo": "Plazo",
    "entrega_notas": "Entrega de notas",
    "festivo": "Festivo",
    "no_lectivo": "No lectivo",
}
PRIORITY_RANK = {"alta": 0, "media": 1, "baja": 2}


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


def _week_title(start: date, end: date) -> str:
    if start.month == end.month:
        return (
            f"Del {start.day} al {end.day} de "
            f"{MONTHS_ES[start.month - 1].lower()} de {start.year}"
        )
    return (
        f"Del {start.day} de {MONTHS_ES[start.month - 1].lower()} "
        f"al {end.day} de {MONTHS_ES[end.month - 1].lower()} de {end.year}"
    )


def _month_metadata(year: int, month: int) -> dict:
    return {
        "year": year,
        "month": month,
        "label": MONTHS_ES[month - 1],
        "first_weekday": date(year, month, 1).isoweekday(),
        "days_in_month": days_in_month(year, month),
    }


def _year_months() -> list[dict]:
    months = []
    for index in range(12):
        month_index = (SCHOOL_START.month - 1) + index
        year = SCHOOL_START.year + month_index // 12
        month = month_index % 12 + 1
        months.append(_month_metadata(year, month))
    return months


def _sort_items(items: list[dict]) -> list[dict]:
    return sorted(
        items,
        key=lambda item: (
            0 if item["time"] else 1,
            item["time"] or "",
            0 if item["kind"] == "event" else 1,
            PRIORITY_RANK.get(item.get("priority") or "", 9),
            item["title"].lower(),
        ),
    )


def _class_notes_for_day(day: date, schedule: list[dict], notes: dict, subjects_by_id: dict, *, skip_classes: bool) -> list[dict]:
    """Una entrada por asignatura que se imparte ese día (en orden del horario),
    con su nota. Las notas de asignaturas que ya no están en el horario se
    conservan al final para no perderlas."""
    entries: dict[int, dict] = {}
    if not skip_classes:
        for slot in schedule:
            if slot["weekday"] != day.isoweekday() or slot["kind"] != "class" or not slot["subject_id"]:
                continue
            entry = entries.get(slot["subject_id"])
            if entry is None:
                entries[slot["subject_id"]] = {
                    "subject_id": slot["subject_id"],
                    "subject_name": slot["subject_name"] or "",
                    "subject_short": slot["subject_short"] or slot["subject_name"] or "",
                    "subject_color": slot["subject_color"],
                    "times": [f"{slot['start_time']}–{slot['end_time']}"],
                    "body": notes.get(slot["subject_id"], ""),
                }
            else:
                entry["times"].append(f"{slot['start_time']}–{slot['end_time']}")
    for subject_id, body in notes.items():
        if subject_id in entries or subject_id not in subjects_by_id:
            continue
        subject = subjects_by_id[subject_id]
        entries[subject_id] = {
            "subject_id": subject_id,
            "subject_name": subject["name"],
            "subject_short": subject["short_name"],
            "subject_color": subject["color"],
            "times": [],
            "body": body,
        }
    return list(entries.values())


@bp.get("/calendar")
def calendar():
    view = choice(request.args.get("view"), "vista", ("month", "week", "year"), default="month")
    anchor = clamp_date(query_date(request.args.get("anchor"), "fecha", date.today()))

    if view == "month":
        days = month_grid(anchor.year, anchor.month)
        start, end = days[0], days[-1]
        title = month_title(anchor.year, anchor.month)
        months = [_month_metadata(anchor.year, anchor.month)]
        in_month = lambda day: day.year == anchor.year and day.month == anchor.month
        can_prev = date(anchor.year, anchor.month, 1) > SCHOOL_START
        can_next = date(anchor.year, anchor.month, days_in_month(anchor.year, anchor.month)) < SCHOOL_END
        prev_anchor = iso(shift_month(anchor, -1)) if can_prev else None
        next_anchor = iso(shift_month(anchor, 1)) if can_next else None
    elif view == "week":
        days = week_grid(anchor)
        start, end = days[0], days[-1]
        title = _week_title(start, end)
        months = []
        in_month = lambda day: True
        can_prev = start > SCHOOL_START
        can_next = end < SCHOOL_END
        prev_anchor = iso(shift_week(anchor, -1)) if can_prev else None
        next_anchor = iso(shift_week(anchor, 1)) if can_next else None
    else:
        days = school_year_days()
        start, end = year_bounds()
        title = "Curso 2026–2027"
        months = _year_months()
        in_month = lambda day: True
        can_prev = False
        can_next = False
        prev_anchor = None
        next_anchor = None

    connection = get_db()
    holidays = fetch_holidays(connection, start, end)
    holidays_by_day = group_holidays_by_day(holidays, start, end)
    items = fetch_calendar_items(connection, start, end)
    items_by_day = group_items_by_day(items, start, end)
    day_notes = {
        row["note_date"]: row["body"]
        for row in connection.execute(
            "SELECT note_date, body FROM day_notes WHERE note_date BETWEEN ? AND ?",
            (iso(start), iso(end)),
        ).fetchall()
    }
    schedule = fetch_schedule(connection)
    class_notes: dict[str, dict[int, str]] = {}
    for row in connection.execute(
        "SELECT note_date, subject_id, body FROM class_notes WHERE note_date BETWEEN ? AND ?",
        (iso(start), iso(end)),
    ).fetchall():
        class_notes.setdefault(row["note_date"], {})[row["subject_id"]] = row["body"]
    note_states: dict[str, dict[int, str]] = {}
    for row in connection.execute(
        "SELECT note_date, subject_id, state FROM class_note_state WHERE note_date BETWEEN ? AND ?",
        (iso(start), iso(end)),
    ).fetchall():
        note_states.setdefault(row["note_date"], {})[row["subject_id"]] = row["state"]
    subjects_by_id = {
        row["id"]: row
        for row in connection.execute("SELECT id, name, short_name, color FROM subjects").fetchall()
    }

    payload_days = []
    for day in days:
        day_key = iso(day)
        day_holidays = [
            {**holiday, "scope_label": SCOPE_LABELS.get(holiday["scope"], "No lectivo")}
            for holiday in holidays_by_day.get(day_key, [])
        ]
        day_items = [
            {**item, "category_label": CATEGORY_LABELS.get(item["category"], item["category"])}
            for item in _sort_items(items_by_day.get(day_key, []))
        ]
        day_states = note_states.get(day_key, {})
        day_class_notes = _class_notes_for_day(
            day,
            schedule,
            class_notes.get(day_key, {}),
            subjects_by_id,
            skip_classes=bool(day_holidays),
        )
        # Cada nota de clase trae su estado guardado (si lo hay): abierta,
        # minimizada o cerrada.
        # Se guarda también su posición para recolocarla al volver a mostrarla.
        for order, entry in enumerate(day_class_notes):
            entry["state"] = day_states.get(entry["subject_id"])
            entry["order"] = order
        payload_days.append(
            {
                "date": day_key,
                "day": day.day,
                "month": day.month,
                "year": day.year,
                "weekday": day.isoweekday(),
                "weekday_name": WEEKDAYS_ES[day.isoweekday() - 1],
                "in_month": bool(in_month(day)),
                "weekend": day.isoweekday() >= 6,
                "holidays": day_holidays,
                "items": day_items,
                "day_note": day_notes.get(day_key, ""),
                "class_notes": [
                    entry for entry in day_class_notes if entry["state"] != "hidden"
                ],
                "hidden_notes": [
                    entry for entry in day_class_notes if entry["state"] == "hidden"
                ],
            }
        )

    return jsonify(
        {
            "view": view,
            "title": title,
            "anchor": iso(anchor),
            "range_start": iso(start),
            "range_end": iso(end),
            "today": iso(date.today()),
            "days": payload_days,
            "months": months,
            "weekdays": WEEKDAYS_ES,
            "weekdays_short": WEEKDAYS_SHORT,
            "can_prev": can_prev,
            "can_next": can_next,
            "prev_anchor": prev_anchor,
            "next_anchor": next_anchor,
            "schedule": schedule if view == "week" else [],
        }
    )


def _event_query(connection, event_id: int):
    return connection.execute(
        """
        SELECT e.*, s.name AS subject_name, s.short_name AS subject_short,
               s.color AS subject_color, s.course AS subject_course
        FROM events e
        LEFT JOIN subjects s ON s.id = e.subject_id
        WHERE e.id = ?
        """,
        (event_id,),
    ).fetchone()


def _event_dict(row) -> dict:
    return {
        "id": row["id"],
        "title": row["title"],
        "description": row["description"],
        "start_date": row["start_date"],
        "end_date": row["end_date"] or row["start_date"],
        "start_time": row["start_time"],
        "end_time": row["end_time"],
        "all_day": row["all_day"],
        "subject_id": row["subject_id"],
        "subject_name": row["subject_name"] or "",
        "subject_short": row["subject_short"] or "",
        "subject_color": row["subject_color"] or "#8C929B",
        "subject_course": row["subject_course"] or "",
        "category": row["category"],
        "category_label": CATEGORY_LABELS.get(row["category"], row["category"]),
        "color": row["color"],
    }


@bp.get("/events")
def list_events():
    connection = get_db()
    start = date_value(request.args.get("from"), "desde")
    end = date_value(request.args.get("to"), "hasta")
    clauses = []
    args: list = []
    ensure_range(start, end, "hasta")
    # Eventos que se solapan con el intervalo [desde, hasta]
    if start:
        clauses.append("COALESCE(e.end_date, e.start_date) >= ?")
        args.append(start)
    if end:
        clauses.append("e.start_date <= ?")
        args.append(end)
    subject = request.args.get("subject", "").strip()
    if subject:
        clauses.append("s.slug = ?")
        args.append(subject)
    where = " WHERE " + " AND ".join(clauses) if clauses else ""
    rows = connection.execute(
        f"""
        SELECT e.*, s.name AS subject_name, s.short_name AS subject_short,
               s.color AS subject_color, s.course AS subject_course
        FROM events e
        LEFT JOIN subjects s ON s.id = e.subject_id
        {where}
        ORDER BY e.start_date, e.start_time
        LIMIT 500
        """,
        tuple(args),
    ).fetchall()
    return jsonify({"events": [_event_dict(row) for row in rows]})


@bp.post("/events")
def create_event():
    data = _body()
    connection = get_db()
    title = text(data.get("title"), "título", max_len=200, required=True)
    description = text(data.get("description"), "descripción", max_len=5000)
    start_date = date_value(data.get("start_date"), "fecha de inicio", required=True)
    end_date = date_value(data.get("end_date"), "fecha de fin")
    ensure_range(start_date, end_date, "fecha de fin")
    start_time = time_value(data.get("start_time"), "hora de inicio")
    end_time = time_value(data.get("end_time"), "hora de fin")
    all_day = boolean(data.get("all_day"), "todo el día", default=1)
    subject_id = _subject_id(connection, data.get("subject_id"))
    category = choice(data.get("category"), "categoría", EVENT_CATEGORIES, default="evento")
    color = color_value(data.get("color"))
    now = iso_now()
    try:
        cursor = connection.execute(
            """
            INSERT INTO events
                (title, description, start_date, end_date, start_time, end_time,
                 all_day, subject_id, category, color, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                title,
                description,
                start_date,
                end_date,
                start_time,
                end_time,
                all_day,
                subject_id,
                category,
                color,
                now,
                now,
            ),
        )
        connection.commit()
    except sqlite3.IntegrityError:
        raise ValidationError("Ya existe un evento igual (mismo título, fecha, asignatura y categoría).")
    return jsonify({"event": _event_dict(_event_query(connection, cursor.lastrowid))}), 201


@bp.put("/events/<int:event_id>")
def update_event(event_id: int):
    data = _body()
    connection = get_db()
    current = _event_query(connection, event_id)
    if current is None:
        abort(404, description="El evento no existe.")
    title = text(data.get("title", current["title"]), "título", max_len=200, required=True)
    description = text(
        data.get("description", current["description"]), "descripción", max_len=5000
    )
    start_date = date_value(
        data.get("start_date", current["start_date"]), "fecha de inicio", required=True
    )
    end_date = date_value(
        data.get("end_date", current["end_date"]), "fecha de fin"
    )
    ensure_range(start_date, end_date, "fecha de fin")
    start_time = time_value(
        data.get("start_time", current["start_time"]), "hora de inicio"
    )
    end_time = time_value(data.get("end_time", current["end_time"]), "hora de fin")
    all_day = boolean(
        data.get("all_day", current["all_day"]), "todo el día", default=current["all_day"]
    )
    subject_id = _subject_id(
        connection, data.get("subject_id", current["subject_id"])
    )
    category = choice(
        data.get("category", current["category"]), "categoría", EVENT_CATEGORIES, default="evento"
    )
    color = color_value(data.get("color", current["color"]))
    try:
        connection.execute(
            """
            UPDATE events SET
                title = ?, description = ?, start_date = ?, end_date = ?,
                start_time = ?, end_time = ?, all_day = ?, subject_id = ?,
                category = ?, color = ?, updated_at = ?
            WHERE id = ?
            """,
            (
                title,
                description,
                start_date,
                end_date,
                start_time,
                end_time,
                all_day,
                subject_id,
                category,
                color,
                iso_now(),
                event_id,
            ),
        )
        connection.commit()
    except sqlite3.IntegrityError:
        raise ValidationError("Ya existe un evento igual (mismo título, fecha, asignatura y categoría).")
    return jsonify({"event": _event_dict(_event_query(connection, event_id))})


@bp.delete("/events/<int:event_id>")
def delete_event(event_id: int):
    connection = get_db()
    cursor = connection.execute("DELETE FROM events WHERE id = ?", (event_id,))
    connection.commit()
    if cursor.rowcount == 0:
        abort(404, description="El evento no existe.")
    return jsonify({"ok": True})


@bp.post("/events/deduplicate")
def deduplicate_events():
    """Elimina eventos duplicados manteniendo el más reciente."""
    connection = get_db()
    # Encuentra duplicados por (title, start_date, subject_id, category)
    # y elimina todos menos el de mayor id (más reciente)
    cursor = connection.execute("""
        DELETE FROM events
        WHERE id NOT IN (
            SELECT MAX(id)
            FROM events
            GROUP BY title, start_date, subject_id, category
        )
    """)
    connection.commit()
    deleted = cursor.rowcount
    message = (
        f"Se eliminaron {deleted} eventos duplicados."
        if deleted
        else "No hay eventos duplicados que limpiar."
    )
    return jsonify({"deleted": deleted, "message": message})


@bp.put("/day-notes/<note_date>")
def save_day_note(note_date: str):
    """Guarda (o borra, si llega vacía) la nota libre de un día."""
    day = date_value(note_date, "fecha", required=True)
    body = text(_body().get("body"), "nota", max_len=5000)
    connection = get_db()
    if body:
        connection.execute(
            """
            INSERT INTO day_notes (note_date, body, updated_at) VALUES (?, ?, ?)
            ON CONFLICT(note_date) DO UPDATE SET body = excluded.body, updated_at = excluded.updated_at
            """,
            (day, body, iso_now()),
        )
    else:
        connection.execute("DELETE FROM day_notes WHERE note_date = ?", (day,))
    connection.commit()
    return jsonify({"date": day, "body": body})


@bp.put("/class-notes/<note_date>/<int:subject_id>")
def save_class_note(note_date: str, subject_id: int):
    """Guarda (o borra, si llega vacía) lo que se hace un día en una asignatura."""
    day = date_value(note_date, "fecha", required=True)
    body = text(_body().get("body"), "nota", max_len=5000)
    connection = get_db()
    subject_id = _subject_id(connection, subject_id)
    if body:
        connection.execute(
            """
            INSERT INTO class_notes (note_date, subject_id, body, updated_at) VALUES (?, ?, ?, ?)
            ON CONFLICT(note_date, subject_id) DO UPDATE SET
                body = excluded.body, updated_at = excluded.updated_at
            """,
            (day, subject_id, body, iso_now()),
        )
    else:
        connection.execute(
            "DELETE FROM class_notes WHERE note_date = ? AND subject_id = ?", (day, subject_id)
        )
    connection.commit()
    return jsonify({"date": day, "subject_id": subject_id, "body": body})


@bp.put("/class-notes/<note_date>/<int:subject_id>/state")
def set_class_note_state(note_date: str, subject_id: int):
    """Cambia el estado de la nota de una asignatura en un día.

    Estados: 'open' (abierta), 'collapsed' (minimizada) o 'hidden' (cerrada).
    """
    day = date_value(note_date, "fecha", required=True)
    state = choice(
        _body().get("state"), "estado", ("open", "collapsed", "hidden"), default="open"
    )
    connection = get_db()
    subject_id = _subject_id(connection, subject_id)
    connection.execute(
        """
        INSERT INTO class_note_state (note_date, subject_id, state, updated_at)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(note_date, subject_id) DO UPDATE SET
            state = excluded.state, updated_at = excluded.updated_at
        """,
        (day, subject_id, state, iso_now()),
    )
    connection.commit()
    return jsonify({"date": day, "subject_id": subject_id, "state": state})


@bp.get("/holidays")
def list_holidays():
    start = query_date(request.args.get("from"), "desde", SCHOOL_START)
    end = query_date(request.args.get("to"), "hasta", SCHOOL_END)
    holidays = fetch_holidays(get_db(), start, end)
    return jsonify(
        {
            "holidays": [
                {**holiday, "scope_label": SCOPE_LABELS.get(holiday["scope"], "No lectivo")}
                for holiday in holidays
            ]
        }
    )
