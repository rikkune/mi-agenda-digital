"""Notas generales o asociadas a una asignatura y una fecha."""

from __future__ import annotations

from flask import Blueprint, abort, jsonify, request

from ..db import get_db
from ..services.validation import (
    ValidationError,
    boolean,
    date_value,
    integer,
    iso_now,
    text,
)

bp = Blueprint("notes", __name__, url_prefix="/api")


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


def _query(connection, note_id: int):
    return connection.execute(
        """
        SELECT n.*, s.name AS subject_name, s.color AS subject_color
        FROM notes n
        LEFT JOIN subjects s ON s.id = n.subject_id
        WHERE n.id = ?
        """,
        (note_id,),
    ).fetchone()


def _dict(row) -> dict:
    return {
        "id": row["id"],
        "title": row["title"],
        "body": row["body"],
        "subject_id": row["subject_id"],
        "subject_name": row["subject_name"] or "",
        "subject_color": row["subject_color"] or "#8C929B",
        "note_date": row["note_date"],
        "pinned": row["pinned"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


@bp.get("/notes")
def list_notes():
    connection = get_db()
    subject = request.args.get("subject", "").strip()
    search = request.args.get("q", "").strip()
    clauses = []
    args: list = []
    if subject:
        clauses.append("s.slug = ?")
        args.append(subject)
    if search:
        clauses.append("(n.title LIKE ? OR n.body LIKE ?)")
        args.extend([f"%{search}%", f"%{search}%"])
    where = " WHERE " + " AND ".join(clauses) if clauses else ""
    rows = connection.execute(
        f"""
        SELECT n.*, s.name AS subject_name, s.color AS subject_color
        FROM notes n
        LEFT JOIN subjects s ON s.id = n.subject_id
        {where}
        ORDER BY n.pinned DESC, COALESCE(n.note_date, n.updated_at) DESC
        """,
        tuple(args),
    ).fetchall()
    return jsonify({"notes": [_dict(row) for row in rows]})


@bp.post("/notes")
def create_note():
    data = _body()
    connection = get_db()
    title = text(data.get("title"), "título", max_len=200, required=True)
    body = text(data.get("body"), "contenido", max_len=10000)
    subject_id = _subject_id(connection, data.get("subject_id"))
    note_date = date_value(data.get("note_date"), "fecha")
    pinned = boolean(data.get("pinned"), "fijada", default=0)
    now = iso_now()
    cursor = connection.execute(
        """
        INSERT INTO notes
            (title, body, subject_id, note_date, pinned, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (title, body, subject_id, note_date, pinned, now, now),
    )
    connection.commit()
    return jsonify({"note": _dict(_query(connection, cursor.lastrowid))}), 201


@bp.put("/notes/<int:note_id>")
def update_note(note_id: int):
    data = _body()
    connection = get_db()
    current = _query(connection, note_id)
    if current is None:
        abort(404, description="La nota no existe.")
    title = text(data.get("title", current["title"]), "título", max_len=200, required=True)
    body = text(data.get("body", current["body"]), "contenido", max_len=10000)
    subject_id = _subject_id(
        connection, data.get("subject_id", current["subject_id"])
    )
    note_date = date_value(data.get("note_date", current["note_date"]), "fecha")
    pinned = boolean(
        data.get("pinned", current["pinned"]), "fijada", default=current["pinned"]
    )
    connection.execute(
        """
        UPDATE notes SET
            title = ?, body = ?, subject_id = ?, note_date = ?, pinned = ?,
            updated_at = ?
        WHERE id = ?
        """,
        (title, body, subject_id, note_date, pinned, iso_now(), note_id),
    )
    connection.commit()
    return jsonify({"note": _dict(_query(connection, note_id))})


@bp.delete("/notes/<int:note_id>")
def delete_note(note_id: int):
    connection = get_db()
    cursor = connection.execute("DELETE FROM notes WHERE id = ?", (note_id,))
    connection.commit()
    if cursor.rowcount == 0:
        abort(404, description="La nota no existe.")
    return jsonify({"ok": True})
