"""Evaluaciones y plazos importados del PDF de la agenda escolar."""

from __future__ import annotations

from flask import Blueprint, jsonify, request

from ..db import get_db
from ..services.validation import ValidationError, choice

bp = Blueprint("evaluations", __name__, url_prefix="/api")

COURSES = {
    "1LFP": "1.º LFP",
    "2LFP": "2.º LFP-LOGSE",
}
KIND_LABELS = {
    "comienzo": "Comienzo",
    "plazo": "Plazo máximo",
    "entrega_notas": "Entrega de notas",
    "no_lectivo": "No lectivo",
    "festivo": "Festivo",
    "otro": "Otro",
}


@bp.get("/evaluations")
def list_evaluations():
    course = request.args.get("course", "1LFP").strip()
    if course not in COURSES:
        raise ValidationError("El curso debe ser 1LFP o 2LFP.")
    connection = get_db()
    rows = connection.execute(
        """
        SELECT * FROM evaluations
        WHERE course = ?
        ORDER BY start_date, title
        """,
        (course,),
    ).fetchall()
    items = [
        {
            "id": row["id"],
            "course": row["course"],
            "course_label": COURSES[row["course"]],
            "start_date": row["start_date"],
            "end_date": row["end_date"] or row["start_date"],
            "title": row["title"],
            "kind": row["kind"],
            "kind_label": KIND_LABELS.get(row["kind"], row["kind"]),
            "source_page": row["source_page"],
            "notes": row["notes"],
        }
        for row in rows
    ]
    return jsonify(
        {
            "course": course,
            "course_label": COURSES[course],
            "courses": [{"code": code, "label": label} for code, label in COURSES.items()],
            "items": items,
            "source_note": (
                "Fechas importadas del PDF. Cuando el listado «Fechas marcadas» "
                "y el calendario coloreado no coinciden, prevalece el listado."
            ),
        }
    )
