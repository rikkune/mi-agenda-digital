"""Página de cada asignatura."""

from __future__ import annotations

import re
import unicodedata
from datetime import date

from flask import Blueprint, abort, jsonify, request

from ..db import get_db
from ..services.calendar_utils import iso
from ..services.query_helpers import (
    fetch_subjects,
    rows_to_dicts,
    subject_by_slug,
    subject_dict,
)
from ..services.validation import (
    ValidationError,
    boolean,
    color_value,
    date_value,
    iso_now,
    text,
)

bp = Blueprint("subjects", __name__, url_prefix="/api")


def _body() -> dict:
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        raise ValidationError("No se han recibido datos válidos.")
    return data


def _require_subject(connection, slug: str):
    row = subject_by_slug(connection, slug)
    if row is None:
        abort(404, description="La asignatura no existe.")
    return row


def _task_rows(connection, subject_id: int, status: str | None = None):
    clauses = ["t.subject_id = ?"]
    args: list = [subject_id]
    if status:
        clauses.append("t.status = ?")
        args.append(status)
    return connection.execute(
        f"""
        SELECT t.*, s.name AS subject_name, s.short_name AS subject_short,
               s.color AS subject_color, s.course AS subject_course
        FROM tasks t
        LEFT JOIN subjects s ON s.id = t.subject_id
        WHERE {' AND '.join(clauses)}
        ORDER BY
            CASE WHEN t.due_date IS NULL THEN 1 ELSE 0 END,
            t.due_date,
            CASE t.priority WHEN 'alta' THEN 0 WHEN 'media' THEN 1 ELSE 2 END,
            t.created_at DESC
        """,
        tuple(args),
    ).fetchall()


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
        "kind": row["kind"],
        "target": row["target"],
        "priority": row["priority"],
        "status": row["status"],
        "due_date": row["due_date"],
        "due_time": row["due_time"],
        "color": row["color"],
        "marked": row["marked"],
        "created_at": row["created_at"],
        "completed_at": row["completed_at"],
    }


def _event_rows(connection, subject_id: int):
    return connection.execute(
        """
        SELECT * FROM events
        WHERE subject_id = ?
        ORDER BY start_date DESC, start_time DESC
        """,
        (subject_id,),
    ).fetchall()


def _note_rows(connection, subject_id: int):
    return connection.execute(
        """
        SELECT n.*, s.name AS subject_name, s.color AS subject_color
        FROM notes n
        LEFT JOIN subjects s ON s.id = n.subject_id
        WHERE n.subject_id = ?
        ORDER BY n.pinned DESC, COALESCE(n.note_date, n.updated_at) DESC
        """,
        (subject_id,),
    ).fetchall()


def _material_rows(connection, subject_id: int):
    return connection.execute(
        "SELECT * FROM materials WHERE subject_id = ? ORDER BY created_at DESC",
        (subject_id,),
    ).fetchall()


def _plan_rows(connection, subject_id: int):
    return connection.execute(
        """
        SELECT * FROM lesson_plans
        WHERE subject_id = ?
        ORDER BY COALESCE(plan_date, created_at) DESC
        """,
        (subject_id,),
    ).fetchall()


def _note_dict(row) -> dict:
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


@bp.get("/subjects")
def list_subjects():
    return jsonify({"subjects": fetch_subjects(get_db())})


# ---------------------------------------------------------------- gestionar asignaturas

DEFAULT_SUBJECT_COLOR = "#7C8CD8"


def _slugify(name: str) -> str:
    value = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "-", value).strip("-")[:40] or "asignatura"


def _unique_slug(connection, name: str) -> str:
    base = _slugify(name)
    slug, counter = base, 2
    while connection.execute("SELECT 1 FROM subjects WHERE slug = ?", (slug,)).fetchone():
        slug, counter = f"{base}-{counter}", counter + 1
    return slug


def _subject_fields(data: dict, current=None) -> dict:
    def pick(key, default=""):
        return data[key] if key in data else (current[key] if current is not None else default)

    name = text(pick("name"), "nombre", required=True, max_len=120)
    short_name = text(pick("short_name"), "nombre corto", max_len=40) or name[:40]
    course = text(pick("course"), "curso", max_len=40) or ""
    color = color_value(pick("color", DEFAULT_SUBJECT_COLOR), "color") or DEFAULT_SUBJECT_COLOR
    if not color.startswith("#"):
        raise ValidationError("Elige un color sólido para la asignatura.")
    icon = text(pick("icon", "◇"), "icono", max_len=4) or "◇"
    is_area = boolean(pick("is_area", 0), "área")
    return {"name": name, "short_name": short_name, "course": course, "color": color,
            "icon": icon, "is_area": is_area}


@bp.post("/subjects")
def create_subject():
    connection = get_db()
    fields = _subject_fields(_body())
    fields["slug"] = _unique_slug(connection, fields["name"])
    fields["sort_order"] = connection.execute(
        "SELECT COALESCE(MAX(sort_order), 0) + 1 FROM subjects"
    ).fetchone()[0]
    with connection:
        cursor = connection.execute(
            "INSERT INTO subjects (slug, name, short_name, course, color, icon, is_area, sort_order) "
            "VALUES (:slug, :name, :short_name, :course, :color, :icon, :is_area, :sort_order)",
            fields,
        )
    row = connection.execute("SELECT * FROM subjects WHERE id = ?", (cursor.lastrowid,)).fetchone()
    return jsonify({"subject": subject_dict(row)}), 201


@bp.put("/subjects/<slug>")
def update_subject(slug: str):
    connection = get_db()
    current = _require_subject(connection, slug)
    fields = _subject_fields(_body(), current)
    with connection:
        connection.execute(
            "UPDATE subjects SET name = :name, short_name = :short_name, course = :course, "
            "color = :color, icon = :icon, is_area = :is_area WHERE id = :id",
            {**fields, "id": current["id"]},
        )
    row = connection.execute("SELECT * FROM subjects WHERE id = ?", (current["id"],)).fetchone()
    return jsonify({"subject": subject_dict(row)})


@bp.delete("/subjects/<slug>")
def delete_subject(slug: str):
    """Borra la asignatura. Tareas, eventos y notas se conservan sin asignatura;
    materiales, planificaciones y notas de clase de la asignatura se borran."""
    connection = get_db()
    current = _require_subject(connection, slug)
    with connection:
        # Las clases del horario pasan a «Libre» (una clase sin asignatura no es válida).
        connection.execute(
            "UPDATE schedule_slots SET kind = 'free', label = 'Libre', subject_id = NULL WHERE subject_id = ?",
            (current["id"],),
        )
        connection.execute("DELETE FROM subjects WHERE id = ?", (current["id"],))
    return jsonify({"ok": True})


@bp.get("/subjects/<slug>")
def subject_detail(slug: str):
    connection = get_db()
    row = _require_subject(connection, slug)
    subject_id = row["id"]
    tasks = [_task_dict(task) for task in _task_rows(connection, subject_id)]
    open_tasks = [task for task in tasks if task["status"] != "completada"]
    completed_tasks = [task for task in tasks if task["status"] == "completada"]
    events = rows_to_dicts(_event_rows(connection, subject_id))
    # Los exámenes pueden crearse como tarea (kind) o como evento del calendario (category)
    exams = [{**task, "source": "task"} for task in tasks if task["kind"] == "examen"]
    exams.extend(
        {
            **event,
            "source": "event",
            "subject_color": row["color"],
            "due_date": event["start_date"],
            "due_time": event["start_time"],
        }
        for event in events
        if event["category"] == "examen"
    )
    exams.sort(key=lambda item: (item["due_date"] or "9999-12-31", item["due_time"] or ""))
    notes = [_note_dict(note) for note in _note_rows(connection, subject_id)]
    materials = rows_to_dicts(_material_rows(connection, subject_id))
    plans = rows_to_dicts(_plan_rows(connection, subject_id))

    today = date.today()
    history = [
        {
            "kind": "task",
            "id": task["id"],
            "title": task["title"],
            "date": task["completed_at"] or task["due_date"],
            "detail": "Tarea completada",
        }
        for task in completed_tasks
    ]
    history.extend(
        {
            "kind": "event",
            "id": event["id"],
            "title": event["title"],
            "date": event["end_date"] or event["start_date"],
            "detail": "Evento pasado",
        }
        for event in events
        if (event["end_date"] or event["start_date"]) < iso(today)
    )
    history.sort(key=lambda item: item["date"] or "", reverse=True)

    return jsonify(
        {
            "subject": subject_dict(row),
            "tasks": tasks,
            "open_tasks": open_tasks,
            "completed_tasks": completed_tasks,
            "exams": exams,
            "events": events,
            "notes": notes,
            "materials": materials,
            "plans": plans,
            "history": history[:40],
            "stats": {
                "open": len(open_tasks),
                "completed": len(completed_tasks),
                "exams": len(exams),
                "notes": len(notes),
                "materials": len(materials),
                "plans": len(plans),
            },
        }
    )


@bp.post("/subjects/<slug>/materials")
def create_material(slug: str):
    data = _body()
    connection = get_db()
    subject = _require_subject(connection, slug)
    title = text(data.get("title"), "título", max_len=200, required=True)
    kind = text(data.get("kind"), "tipo", max_len=60)
    link = text(data.get("link"), "enlace", max_len=500)
    notes = text(data.get("notes"), "notas", max_len=5000)
    cursor = connection.execute(
        """
        INSERT INTO materials (subject_id, title, kind, link, notes, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (subject["id"], title, kind, link, notes, iso_now()),
    )
    connection.commit()
    row = connection.execute(
        "SELECT * FROM materials WHERE id = ?", (cursor.lastrowid,)
    ).fetchone()
    return jsonify({"material": {key: row[key] for key in row.keys()}}), 201


@bp.put("/materials/<int:material_id>")
def update_material(material_id: int):
    data = _body()
    connection = get_db()
    current = connection.execute(
        "SELECT * FROM materials WHERE id = ?", (material_id,)
    ).fetchone()
    if current is None:
        abort(404, description="El material no existe.")
    title = text(data.get("title", current["title"]), "título", max_len=200, required=True)
    kind = text(data.get("kind", current["kind"]), "tipo", max_len=60)
    link = text(data.get("link", current["link"]), "enlace", max_len=500)
    notes = text(data.get("notes", current["notes"]), "notas", max_len=5000)
    connection.execute(
        "UPDATE materials SET title = ?, kind = ?, link = ?, notes = ? WHERE id = ?",
        (title, kind, link, notes, material_id),
    )
    connection.commit()
    row = connection.execute(
        "SELECT * FROM materials WHERE id = ?", (material_id,)
    ).fetchone()
    return jsonify({"material": {key: row[key] for key in row.keys()}})


@bp.delete("/materials/<int:material_id>")
def delete_material(material_id: int):
    connection = get_db()
    cursor = connection.execute("DELETE FROM materials WHERE id = ?", (material_id,))
    connection.commit()
    if cursor.rowcount == 0:
        abort(404, description="El material no existe.")
    return jsonify({"ok": True})


@bp.post("/subjects/<slug>/plans")
def create_plan(slug: str):
    data = _body()
    connection = get_db()
    subject = _require_subject(connection, slug)
    title = text(data.get("title"), "título", max_len=200, required=True)
    plan_date = date_value(data.get("plan_date"), "fecha")
    objectives = text(data.get("objectives"), "objetivos", max_len=5000)
    activities = text(data.get("activities"), "actividades", max_len=5000)
    resources = text(data.get("resources"), "recursos", max_len=5000)
    now = iso_now()
    cursor = connection.execute(
        """
        INSERT INTO lesson_plans
            (subject_id, plan_date, title, objectives, activities, resources, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (subject["id"], plan_date, title, objectives, activities, resources, now, now),
    )
    connection.commit()
    row = connection.execute(
        "SELECT * FROM lesson_plans WHERE id = ?", (cursor.lastrowid,)
    ).fetchone()
    return jsonify({"plan": {key: row[key] for key in row.keys()}}), 201


@bp.put("/plans/<int:plan_id>")
def update_plan(plan_id: int):
    data = _body()
    connection = get_db()
    current = connection.execute(
        "SELECT * FROM lesson_plans WHERE id = ?", (plan_id,)
    ).fetchone()
    if current is None:
        abort(404, description="La planificación no existe.")
    title = text(data.get("title", current["title"]), "título", max_len=200, required=True)
    plan_date = date_value(data.get("plan_date", current["plan_date"]), "fecha")
    objectives = text(
        data.get("objectives", current["objectives"]), "objetivos", max_len=5000
    )
    activities = text(
        data.get("activities", current["activities"]), "actividades", max_len=5000
    )
    resources = text(
        data.get("resources", current["resources"]), "recursos", max_len=5000
    )
    connection.execute(
        """
        UPDATE lesson_plans SET
            plan_date = ?, title = ?, objectives = ?, activities = ?,
            resources = ?, updated_at = ?
        WHERE id = ?
        """,
        (plan_date, title, objectives, activities, resources, iso_now(), plan_id),
    )
    connection.commit()
    row = connection.execute(
        "SELECT * FROM lesson_plans WHERE id = ?", (plan_id,)
    ).fetchone()
    return jsonify({"plan": {key: row[key] for key in row.keys()}})


@bp.delete("/plans/<int:plan_id>")
def delete_plan(plan_id: int):
    connection = get_db()
    cursor = connection.execute("DELETE FROM lesson_plans WHERE id = ?", (plan_id,))
    connection.commit()
    if cursor.rowcount == 0:
        abort(404, description="La planificación no existe.")
    return jsonify({"ok": True})
