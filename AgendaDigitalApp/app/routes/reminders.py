"""Recordatorios semanales: pendientes, cosas por corregir, notas que revisar..."""

from __future__ import annotations

import json
from datetime import date, timedelta

from flask import Blueprint, abort, jsonify, request

from ..db import get_db
from ..services.validation import (
    ValidationError,
    boolean,
    choice,
    date_value,
    integer,
    iso_now,
    text,
    today_iso,
)

bp = Blueprint("reminders", __name__, url_prefix="/api")

REMINDER_CATEGORIES = ("pendiente", "corregir", "revisar", "otro")


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


def week_start(iso_date: str) -> str:
    """Lunes de la semana a la que pertenece la fecha."""
    day = date.fromisoformat(iso_date)
    return (day - timedelta(days=day.weekday())).isoformat()


_SELECT = """
    SELECT r.*, s.name AS subject_name, s.short_name AS subject_short,
           s.slug AS subject_slug, s.color AS subject_color
    FROM reminders r
    LEFT JOIN subjects s ON s.id = r.subject_id
"""


def _query(connection, reminder_id: int):
    return connection.execute(_SELECT + " WHERE r.id = ?", (reminder_id,)).fetchone()


def _progress(value: str | None) -> dict | None:
    """Progreso de corrección que trae la sincronización con el Aula Virtual."""
    if not value:
        return None
    try:
        data = json.loads(value)
        graded, ungraded, missing = (int(data.get(key) or 0) for key in ("graded", "ungraded", "not_submitted"))
    except (ValueError, TypeError, AttributeError):
        return None
    submitted = graded + ungraded
    return {
        "graded": graded,
        "ungraded": ungraded,
        "not_submitted": missing,
        "submitted": submitted,
        "total": submitted + missing,
        "percent": round(graded * 100 / submitted) if submitted else 0,
    }


def _dict(row) -> dict:
    return {
        "id": row["id"],
        "title": row["title"],
        "body": row["body"],
        "subject_id": row["subject_id"],
        "subject_name": row["subject_name"] or "",
        "subject_short": row["subject_short"] or "",
        "subject_slug": row["subject_slug"] or "",
        "subject_color": row["subject_color"] or "#8C929B",
        "reminder_date": row["reminder_date"],
        "week_start": week_start(row["reminder_date"]),
        "category": row["category"],
        "done": row["done"],
        "done_at": row["done_at"],
        "progress": _progress(row["progress"]),
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


@bp.get("/reminders")
def list_reminders():
    connection = get_db()
    subject = request.args.get("subject", "").strip()
    clauses = []
    args: list = []
    if subject:
        clauses.append("s.slug = ?")
        args.append(subject)
    where = " WHERE " + " AND ".join(clauses) if clauses else ""
    rows = connection.execute(
        _SELECT + where + " ORDER BY r.reminder_date, r.done, r.created_at",
        tuple(args),
    ).fetchall()
    reminders = [_dict(row) for row in rows]
    today = today_iso()
    return jsonify(
        {
            "reminders": reminders,
            "today": today,
            "current_week": week_start(today),
            "counts": {
                "pending": sum(1 for item in reminders if not item["done"]),
                "done": sum(1 for item in reminders if item["done"]),
            },
        }
    )


def _done_at(done: int, previous_done: int | None, previous_at: str | None):
    if not done:
        return None
    if previous_done:
        return previous_at
    return iso_now()


@bp.post("/reminders")
def create_reminder():
    data = _body()
    connection = get_db()
    title = text(data.get("title"), "recordatorio", max_len=300, required=True)
    body = text(data.get("body"), "detalle", max_len=5000)
    subject_id = _subject_id(connection, data.get("subject_id"))
    reminder_date = date_value(data.get("reminder_date"), "fecha") or today_iso()
    category = choice(
        data.get("category"), "tipo", REMINDER_CATEGORIES, default="pendiente"
    )
    done = boolean(data.get("done"), "hecho", default=0)
    now = iso_now()
    cursor = connection.execute(
        """
        INSERT INTO reminders
            (title, body, subject_id, reminder_date, category, done, done_at,
             created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            title, body, subject_id, reminder_date, category, done,
            _done_at(done, None, None), now, now,
        ),
    )
    connection.commit()
    return jsonify({"reminder": _dict(_query(connection, cursor.lastrowid))}), 201


@bp.put("/reminders/<int:reminder_id>")
def update_reminder(reminder_id: int):
    data = _body()
    connection = get_db()
    current = _query(connection, reminder_id)
    if current is None:
        abort(404, description="El recordatorio no existe.")
    title = text(
        data.get("title", current["title"]), "recordatorio", max_len=300, required=True
    )
    body = text(data.get("body", current["body"]), "detalle", max_len=5000)
    subject_id = _subject_id(connection, data.get("subject_id", current["subject_id"]))
    reminder_date = (
        date_value(data.get("reminder_date", current["reminder_date"]), "fecha")
        or current["reminder_date"]
    )
    category = choice(
        data.get("category", current["category"]),
        "tipo",
        REMINDER_CATEGORIES,
        default=current["category"],
    )
    done = boolean(data.get("done", current["done"]), "hecho", default=current["done"])
    connection.execute(
        """
        UPDATE reminders SET
            title = ?, body = ?, subject_id = ?, reminder_date = ?, category = ?,
            done = ?, done_at = ?, updated_at = ?
        WHERE id = ?
        """,
        (
            title, body, subject_id, reminder_date, category, done,
            _done_at(done, current["done"], current["done_at"]),
            iso_now(), reminder_id,
        ),
    )
    connection.commit()
    return jsonify({"reminder": _dict(_query(connection, reminder_id))})


@bp.delete("/reminders/<int:reminder_id>")
def delete_reminder(reminder_id: int):
    connection = get_db()
    cursor = connection.execute("DELETE FROM reminders WHERE id = ?", (reminder_id,))
    connection.commit()
    if cursor.rowcount == 0:
        abort(404, description="El recordatorio no existe.")
    return jsonify({"ok": True})


@bp.post("/notes/<int:note_id>/to-reminder")
def note_to_reminder(note_id: int):
    """Convierte una nota en recordatorio (y elimina la nota original)."""
    connection = get_db()
    note = connection.execute("SELECT * FROM notes WHERE id = ?", (note_id,)).fetchone()
    if note is None:
        abort(404, description="La nota no existe.")
    now = iso_now()
    with connection:
        cursor = connection.execute(
            """
            INSERT INTO reminders
                (title, body, subject_id, reminder_date, category, done, done_at,
                 created_at, updated_at)
            VALUES (?, ?, ?, ?, 'pendiente', 0, NULL, ?, ?)
            """,
            (
                note["title"], note["body"], note["subject_id"],
                note["note_date"] or today_iso(), now, now,
            ),
        )
        connection.execute("DELETE FROM notes WHERE id = ?", (note_id,))
    return jsonify({"reminder": _dict(_query(connection, cursor.lastrowid))}), 201
