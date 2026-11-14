"""Datos de la pantalla de inicio."""

from __future__ import annotations

from datetime import date, timedelta

from flask import Blueprint, jsonify, request

from ..db import get_db
from ..services.calendar_utils import WEEKDAYS_ES, iso
from ..services.validation import query_date
from ..services.query_helpers import (
    dashboard_counts,
    fetch_calendar_items,
    fetch_holidays,
    fetch_schedule,
    fetch_subjects,
)

bp = Blueprint("dashboard", __name__, url_prefix="/api")

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


def _upcoming_item(item: dict, today_iso: str | None = None) -> dict:
    label = CATEGORY_LABELS.get(item["category"], item["category"])
    if item["kind"] == "task":
        label = CATEGORY_LABELS.get(item["category"], "Tarea")
    elif item["kind"] == "event":
        label = CATEGORY_LABELS.get(item["category"], "Evento")
    elif item["kind"] == "evaluation":
        label = "Evaluación"
    return {
        "kind": item["kind"],
        "id": item["id"],
        # Los eventos de varios días que ya han empezado se muestran desde hoy
        "date": max(item["date"], today_iso) if today_iso else item["date"],
        "end_date": item["end_date"],
        "title": item["title"],
        "subject_name": item["subject_name"],
        "subject_short": item["subject_short"],
        "subject_color": item["subject_color"],
        "color": item.get("color"),
        "category": item["category"],
        "label": label,
        "priority": item["priority"],
        "status": item["status"],
        "time": item["time"],
    }


@bp.get("/dashboard")
def dashboard():
    today = query_date(request.args.get("date"), "fecha", date.today())
    weekday = today.isoweekday()
    connection = get_db()

    holidays_today = fetch_holidays(connection, today, today)
    is_school_day = weekday <= 5 and not holidays_today

    schedule = fetch_schedule(connection)
    today_schedule = [
        slot for slot in schedule if slot["weekday"] == weekday
    ]

    stats = dashboard_counts(connection, today)
    subjects = [subject for subject in fetch_subjects(connection) if not subject["is_area"]]

    end = today + timedelta(days=7)
    items = fetch_calendar_items(connection, today, end)
    upcoming_items = [
        item
        for item in items
        if not (item["kind"] == "task" and item["status"] == "completada")
    ]
    holidays = fetch_holidays(connection, today, end)

    upcoming: list[dict] = [_upcoming_item(item, iso(today)) for item in upcoming_items]
    for holiday in holidays:
        upcoming.append(
            {
                "kind": "holiday",
                "id": holiday["id"],
                "date": max(holiday["start_date"], iso(today)),
                "end_date": holiday["end_date"],
                "title": holiday["name"],
                "subject_name": SCOPE_LABELS.get(holiday["scope"], "No lectivo"),
                "subject_short": "",
                "subject_color": "#E6D76E",
                "category": "festivo",
                "label": SCOPE_LABELS.get(holiday["scope"], "No lectivo"),
                "priority": None,
                "status": None,
                "time": None,
            }
        )

    upcoming.sort(key=lambda item: (item["date"], item["time"] or "99:99", item["title"]))
    upcoming = upcoming[:6]

    name_row = connection.execute("SELECT value FROM settings WHERE key = 'display_name'").fetchone()
    return jsonify(
        {
            "display_name": name_row["value"] if name_row else "",
            "date": iso(today),
            "weekday": weekday,
            "weekday_name": WEEKDAYS_ES[weekday - 1],
            "is_school_day": is_school_day,
            "holiday_today": holidays_today,
            "schedule": today_schedule,
            "stats": stats,
            "subjects": subjects,
            "upcoming": upcoming,
        }
    )
