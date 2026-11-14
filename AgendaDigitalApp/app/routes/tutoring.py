"""Seguimiento de prácticas y tutoría."""

from __future__ import annotations

from flask import Blueprint, abort, jsonify, request

from ..db import get_db
from ..services.validation import (
    ValidationError,
    choice,
    date_value,
    integer,
    iso_now,
    text,
    time_value,
)

bp = Blueprint("tutoring", __name__, url_prefix="/api")

KINDS = ("seguimiento", "visita", "reunion")
STATUSES = ("pendiente", "realizado", "cancelado")
KIND_LABELS = {
    "seguimiento": "Seguimiento",
    "visita": "Visita",
    "reunion": "Reunión",
}


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


def _query(connection, item_id: int):
    return connection.execute(
        """
        SELECT t.*, s.name AS subject_name, s.color AS subject_color
        FROM tutoring t
        LEFT JOIN subjects s ON s.id = t.subject_id
        WHERE t.id = ?
        """,
        (item_id,),
    ).fetchone()


def _dict(row) -> dict:
    return {
        "id": row["id"],
        "kind": row["kind"],
        "kind_label": KIND_LABELS.get(row["kind"], row["kind"]),
        "student": row["student"],
        "start_date": row["start_date"],
        "start_time": row["start_time"],
        "subject_id": row["subject_id"],
        "subject_name": row["subject_name"] or "",
        "subject_color": row["subject_color"] or "#8C929B",
        "status": row["status"],
        "notes": row["notes"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


@bp.get("/tutoring")
def list_tutoring():
    connection = get_db()
    rows = connection.execute(
        """
        SELECT t.*, s.name AS subject_name, s.color AS subject_color
        FROM tutoring t
        LEFT JOIN subjects s ON s.id = t.subject_id
        ORDER BY
            CASE t.status WHEN 'pendiente' THEN 0 WHEN 'realizado' THEN 1 ELSE 2 END,
            t.start_date,
            COALESCE(t.start_time, '99:99')
        """
    ).fetchall()
    items = [_dict(row) for row in rows]
    return jsonify(
        {
            "items": items,
            "counts": {
                "total": len(items),
                "pendiente": sum(1 for item in items if item["status"] == "pendiente"),
                "realizado": sum(1 for item in items if item["status"] == "realizado"),
            },
        }
    )


@bp.post("/tutoring")
def create_tutoring():
    data = _body()
    connection = get_db()
    kind = choice(data.get("kind"), "tipo", KINDS, default="seguimiento")
    student = text(data.get("student"), "alumno o grupo", max_len=160, required=True)
    start_date = date_value(data.get("start_date"), "fecha", required=True)
    start_time = time_value(data.get("start_time"), "hora")
    subject_id = _subject_id(connection, data.get("subject_id"))
    status = choice(data.get("status"), "estado", STATUSES, default="pendiente")
    notes = text(data.get("notes"), "notas", max_len=5000)
    now = iso_now()
    cursor = connection.execute(
        """
        INSERT INTO tutoring
            (kind, student, start_date, start_time, subject_id, status, notes,
             created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (kind, student, start_date, start_time, subject_id, status, notes, now, now),
    )
    connection.commit()
    return jsonify({"item": _dict(_query(connection, cursor.lastrowid))}), 201


@bp.put("/tutoring/<int:item_id>")
def update_tutoring(item_id: int):
    data = _body()
    connection = get_db()
    current = _query(connection, item_id)
    if current is None:
        abort(404, description="El seguimiento no existe.")
    kind = choice(data.get("kind", current["kind"]), "tipo", KINDS, default="seguimiento")
    student = text(
        data.get("student", current["student"]), "alumno o grupo", max_len=160, required=True
    )
    start_date = date_value(
        data.get("start_date", current["start_date"]), "fecha", required=True
    )
    start_time = time_value(data.get("start_time", current["start_time"]), "hora")
    subject_id = _subject_id(
        connection, data.get("subject_id", current["subject_id"])
    )
    status = choice(
        data.get("status", current["status"]), "estado", STATUSES, default="pendiente"
    )
    notes = text(data.get("notes", current["notes"]), "notas", max_len=5000)
    connection.execute(
        """
        UPDATE tutoring SET
            kind = ?, student = ?, start_date = ?, start_time = ?, subject_id = ?,
            status = ?, notes = ?, updated_at = ?
        WHERE id = ?
        """,
        (
            kind,
            student,
            start_date,
            start_time,
            subject_id,
            status,
            notes,
            iso_now(),
            item_id,
        ),
    )
    connection.commit()
    return jsonify({"item": _dict(_query(connection, item_id))})


@bp.delete("/tutoring/<int:item_id>")
def delete_tutoring(item_id: int):
    connection = get_db()
    cursor = connection.execute("DELETE FROM tutoring WHERE id = ?", (item_id,))
    connection.commit()
    if cursor.rowcount == 0:
        abort(404, description="El seguimiento no existe.")
    return jsonify({"ok": True})
