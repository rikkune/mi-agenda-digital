"""Tareas, entregas y exámenes."""

from __future__ import annotations

from flask import Blueprint, abort, jsonify, request

from ..db import get_db
from ..services.query_helpers import fetch_task_counts
from ..services.validation import (
    ValidationError,
    boolean,
    choice,
    color_value,
    date_value,
    integer,
    iso_now,
    text,
    time_value,
)

bp = Blueprint("tasks", __name__, url_prefix="/api")

TASK_KINDS = ("tarea", "entrega", "examen", "reunion", "otro")
TASK_PRIORITIES = ("alta", "media", "baja")
TASK_STATUSES = ("pendiente", "en_curso", "completada")


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


def _task_query(connection, task_id: int):
    row = connection.execute(
        """
        SELECT t.*, s.name AS subject_name, s.short_name AS subject_short,
               s.color AS subject_color, s.course AS subject_course, s.slug AS subject_slug
        FROM tasks t
        LEFT JOIN subjects s ON s.id = t.subject_id
        WHERE t.id = ?
        """,
        (task_id,),
    ).fetchone()
    return row


def _task_dict(row) -> dict:
    return {
        "id": row["id"],
        "title": row["title"],
        "description": row["description"],
        "subject_id": row["subject_id"],
        "subject_name": row["subject_name"] or "",
        "subject_short": row["subject_short"] or "",
        "subject_color": row["subject_color"] or "#8C929B",
        "subject_course": row["subject_course"] or "",
        "subject_slug": row["subject_slug"] or "",
        "kind": row["kind"],
        "target": row["target"],
        "priority": row["priority"],
        "status": row["status"],
        "due_date": row["due_date"],
        "due_time": row["due_time"],
        "color": row["color"],
        "marked": row["marked"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
        "completed_at": row["completed_at"],
    }


@bp.get("/tasks")
def list_tasks():
    connection = get_db()
    status = request.args.get("status", "").strip()
    subject = request.args.get("subject", "").strip()
    priority = request.args.get("priority", "").strip()
    search = request.args.get("q", "").strip()

    clauses = []
    args: list = []
    if status and status != "todas":
        if status not in TASK_STATUSES:
            raise ValidationError("El filtro de estado no es válido.")
        clauses.append("t.status = ?")
        args.append(status)
    if subject:
        clauses.append("s.slug = ?")
        args.append(subject)
    if priority:
        if priority not in TASK_PRIORITIES:
            raise ValidationError("El filtro de prioridad no es válido.")
        clauses.append("t.priority = ?")
        args.append(priority)
    if search:
        clauses.append("(t.title LIKE ? OR t.description LIKE ?)")
        args.extend([f"%{search}%", f"%{search}%"])

    where = " WHERE " + " AND ".join(clauses) if clauses else ""
    rows = connection.execute(
        f"""
        SELECT t.*, s.name AS subject_name, s.short_name AS subject_short,
               s.color AS subject_color, s.course AS subject_course, s.slug AS subject_slug
        FROM tasks t
        LEFT JOIN subjects s ON s.id = t.subject_id
        {where}
        ORDER BY
            CASE t.status WHEN 'pendiente' THEN 0 WHEN 'en_curso' THEN 1 ELSE 2 END,
            CASE WHEN t.due_date IS NULL THEN 1 ELSE 0 END,
            t.due_date,
            CASE t.priority WHEN 'alta' THEN 0 WHEN 'media' THEN 1 ELSE 2 END,
            t.created_at DESC
        """,
        tuple(args),
    ).fetchall()

    return jsonify(
        {
            "tasks": [_task_dict(row) for row in rows],
            "counts": fetch_task_counts(connection),
        }
    )


@bp.post("/tasks")
def create_task():
    data = _body()
    connection = get_db()
    title = text(data.get("title"), "título", max_len=200, required=True)
    description = text(data.get("description"), "descripción", max_len=5000)
    subject_id = _subject_id(connection, data.get("subject_id"))
    kind = choice(data.get("kind"), "tipo", TASK_KINDS, default="entrega")
    # Las tareas son entregas del alumnado (lo de la docente va en las notas del día)
    target = choice(data.get("target"), "destinatario", ('docente', 'alumno'), default='alumno')
    priority = choice(data.get("priority"), "prioridad", TASK_PRIORITIES, default="media")
    status = choice(data.get("status"), "estado", TASK_STATUSES, default="pendiente")
    due_date = date_value(data.get("due_date"), "fecha de vencimiento")
    due_time = time_value(data.get("due_time"), "hora de vencimiento")
    color = color_value(data.get("color"))
    marked = boolean(data.get("marked"), "marca", default=0)
    now = iso_now()
    completed_at = now if status == "completada" else None

    cursor = connection.execute(
        """
        INSERT INTO tasks
            (title, description, subject_id, kind, target, priority, status, due_date, due_time, color,
             marked, created_at, updated_at, completed_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            title,
            description,
            subject_id,
            kind,
            target,
            priority,
            status,
            due_date,
            due_time,
            color,
            marked,
            now,
            now,
            completed_at,
        ),
    )
    connection.commit()
    row = _task_query(connection, cursor.lastrowid)
    return jsonify({"task": _task_dict(row)}), 201


@bp.put("/tasks/<int:task_id>")
def update_task(task_id: int):
    data = _body()
    connection = get_db()
    current = _task_query(connection, task_id)
    if current is None:
        abort(404, description="La tarea no existe.")

    title = text(data.get("title", current["title"]), "título", max_len=200, required=True)
    description = text(
        data.get("description", current["description"]), "descripción", max_len=5000
    )
    subject_id = _subject_id(connection, data.get("subject_id", current["subject_id"]))
    kind = choice(data.get("kind", current["kind"]), "tipo", TASK_KINDS, default="tarea")
    target = choice(data.get("target", current["target"]), "destinatario", ('docente', 'alumno'), default='docente')
    priority = choice(
        data.get("priority", current["priority"]), "prioridad", TASK_PRIORITIES, default="media"
    )
    status = choice(
        data.get("status", current["status"]), "estado", TASK_STATUSES, default="pendiente"
    )
    due_date = date_value(data.get("due_date", current["due_date"]), "fecha de vencimiento")
    due_time = time_value(data.get("due_time", current["due_time"]), "hora de vencimiento")
    color = color_value(data.get("color", current["color"]))
    marked = boolean(data.get("marked"), "marca", default=current["marked"])
    now = iso_now()
    completed_at = current["completed_at"]
    if status == "completada" and current["status"] != "completada":
        completed_at = now
    elif status != "completada":
        completed_at = None

    connection.execute(
        """
        UPDATE tasks SET
            title = ?, description = ?, subject_id = ?, kind = ?, target = ?, priority = ?,
            status = ?, due_date = ?, due_time = ?, color = ?, marked = ?, updated_at = ?, completed_at = ?
        WHERE id = ?
        """,
        (
            title,
            description,
            subject_id,
            kind,
            target,
            priority,
            status,
            due_date,
            due_time,
            color,
            marked,
            now,
            completed_at,
            task_id,
        ),
    )
    connection.commit()
    row = _task_query(connection, task_id)
    return jsonify({"task": _task_dict(row)})


@bp.patch("/tasks/<int:task_id>/status")
def update_task_status(task_id: int):
    data = _body()
    connection = get_db()
    current = _task_query(connection, task_id)
    if current is None:
        abort(404, description="La tarea no existe.")
    status = choice(data.get("status"), "estado", TASK_STATUSES)
    now = iso_now()
    completed_at = now if status == "completada" else None
    connection.execute(
        "UPDATE tasks SET status = ?, completed_at = ?, updated_at = ? WHERE id = ?",
        (status, completed_at, now, task_id),
    )
    connection.commit()
    return jsonify({"task": _task_dict(_task_query(connection, task_id))})


@bp.delete("/tasks/<int:task_id>")
def delete_task(task_id: int):
    connection = get_db()
    cursor = connection.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    connection.commit()
    if cursor.rowcount == 0:
        abort(404, description="La tarea no existe.")
    return jsonify({"ok": True})
