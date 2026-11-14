"""Consultas y serialización compartidas por las rutas de la API."""

from __future__ import annotations

import sqlite3
from datetime import date, timedelta

from .calendar_utils import date_range, iso, parse_date


def rows_to_dicts(rows) -> list[dict]:
    return [{key: row[key] for key in row.keys()} for row in rows]


def subject_dict(row) -> dict:
    return {
        "id": row["id"],
        "slug": row["slug"],
        "name": row["name"],
        "short_name": row["short_name"],
        "course": row["course"] or "",
        "color": row["color"],
        "icon": row["icon"],
        "is_area": row["is_area"],
        "sort_order": row["sort_order"],
    }


def fetch_subjects(conn: sqlite3.Connection) -> list[dict]:
    rows = conn.execute(
        """
        SELECT s.*,
               COALESCE(SUM(CASE WHEN t.status <> 'completada' THEN 1 ELSE 0 END), 0) AS open_tasks,
               COUNT(t.id) AS total_tasks
        FROM subjects s
        LEFT JOIN tasks t ON t.subject_id = s.id
        GROUP BY s.id
        ORDER BY s.sort_order, s.name
        """
    ).fetchall()
    result = []
    for row in rows:
        item = subject_dict(row)
        item["open_tasks"] = row["open_tasks"]
        item["total_tasks"] = row["total_tasks"]
        result.append(item)
    return result


def subject_by_slug(conn: sqlite3.Connection, slug: str):
    return conn.execute("SELECT * FROM subjects WHERE slug = ?", (slug,)).fetchone()


def fetch_schedule(conn: sqlite3.Connection) -> list[dict]:
    rows = conn.execute(
        """
        SELECT ss.*, s.name AS subject_name, s.short_name AS subject_short,
               s.color AS subject_color, s.course AS subject_course
        FROM schedule_slots ss
        LEFT JOIN subjects s ON s.id = ss.subject_id
        ORDER BY ss.weekday, ss.start_time
        """
    ).fetchall()
    return [
        {
            "id": row["id"],
            "weekday": row["weekday"],
            "start_time": row["start_time"],
            "end_time": row["end_time"],
            "subject_id": row["subject_id"],
            "subject_name": row["subject_name"],
            "subject_short": row["subject_short"],
            "subject_color": row["subject_color"] or "#8C929B",
            "subject_course": row["subject_course"] or "",
            "label": row["label"],
            "kind": row["kind"],
            "notes": row["notes"],
        }
        for row in rows
    ]


def holiday_dict(row) -> dict:
    return {
        "id": row["id"],
        "start_date": row["start_date"],
        "end_date": row["end_date"] or row["start_date"],
        "name": row["name"],
        "scope": row["scope"],
        "verified": row["verified"],
        "source": row["source"],
        "notes": row["notes"],
    }


def fetch_holidays(conn: sqlite3.Connection, start: date, end: date) -> list[dict]:
    rows = conn.execute(
        """
        SELECT * FROM holidays
        WHERE start_date <= ? AND COALESCE(end_date, start_date) >= ?
        ORDER BY start_date, name
        """,
        (iso(end), iso(start)),
    ).fetchall()
    return [holiday_dict(row) for row in rows]


def fetch_calendar_items(conn: sqlite3.Connection, start: date, end: date) -> list[dict]:
    items: list[dict] = []

    task_rows = conn.execute(
        """
        SELECT t.*, s.name AS subject_name, s.short_name AS subject_short,
               s.color AS subject_color, s.course AS subject_course
        FROM tasks t
        LEFT JOIN subjects s ON s.id = t.subject_id
        WHERE t.due_date BETWEEN ? AND ?
        ORDER BY t.due_date, t.priority
        """,
        (iso(start), iso(end)),
    ).fetchall()
    for row in task_rows:
        items.append(
            {
                "kind": "task",
                "id": row["id"],
                "date": row["due_date"],
                "end_date": row["due_date"],
                "title": row["title"],
                "description": row["description"],
                "subject_id": row["subject_id"],
                "subject_name": row["subject_name"] or "",
                "subject_short": row["subject_short"] or "",
                "subject_color": row["subject_color"] or "#8C929B",
                "subject_course": row["subject_course"] or "",
                "category": row["kind"],
                "target": row["target"],
                "priority": row["priority"],
                "status": row["status"],
                "time": row["due_time"],
                "all_day": 0 if row["due_time"] else 1,
                "source": None,
                "color": row["color"],
                "marked": row["marked"],
            }
        )

    event_rows = conn.execute(
        """
        SELECT e.*, s.name AS subject_name, s.short_name AS subject_short,
               s.color AS subject_color, s.course AS subject_course
        FROM events e
        LEFT JOIN subjects s ON s.id = e.subject_id
        WHERE e.start_date <= ? AND COALESCE(e.end_date, e.start_date) >= ?
        ORDER BY e.start_date, e.start_time
        """,
        (iso(end), iso(start)),
    ).fetchall()
    for row in event_rows:
        items.append(
            {
                "kind": "event",
                "id": row["id"],
                "date": row["start_date"],
                "end_date": row["end_date"] or row["start_date"],
                "title": row["title"],
                "description": row["description"],
                "subject_id": row["subject_id"],
                "subject_name": row["subject_name"] or "",
                "subject_short": row["subject_short"] or "",
                "subject_color": row["subject_color"] or "#8C929B",
                "subject_course": row["subject_course"] or "",
                "category": row["category"],
                "color": row["color"],
                "priority": None,
                "status": None,
                "time": row["start_time"],
                "end_time": row["end_time"],
                "all_day": row["all_day"],
                "source": None,
            }
        )

    evaluation_rows = conn.execute(
        """
        SELECT * FROM evaluations
        WHERE start_date <= ? AND COALESCE(end_date, start_date) >= ?
          AND kind NOT IN ('no_lectivo', 'festivo')
        ORDER BY start_date
        """,
        (iso(end), iso(start)),
    ).fetchall()
    for row in evaluation_rows:
        items.append(
            {
                "kind": "evaluation",
                "id": row["id"],
                "date": row["start_date"],
                "end_date": row["end_date"] or row["start_date"],
                "title": row["title"],
                "description": row["notes"] or "",
                "subject_id": None,
                "subject_name": "Evaluaciones " + ("1.º LFP" if row["course"] == "1LFP" else "2.º LFP-LOGSE"),
                "subject_short": "Evaluación",
                "subject_color": "#8973ad",
                "subject_course": row["course"],
                "category": row["kind"],
                "priority": None,
                "status": None,
                "time": None,
                "all_day": 1,
                "source": row["source_page"],
            }
        )

    return items


def group_holidays_by_day(holidays: list[dict], start: date, end: date) -> dict[str, list[dict]]:
    result: dict[str, list[dict]] = {}
    for holiday in holidays:
        first = max(parse_date(holiday["start_date"]), start)
        last = min(parse_date(holiday["end_date"]), end)
        for day in date_range(first, last):
            result.setdefault(iso(day), []).append(holiday)
    return result


def group_items_by_day(items: list[dict], start: date, end: date) -> dict[str, list[dict]]:
    result: dict[str, list[dict]] = {}
    for item in items:
        first = max(parse_date(item["date"]), start)
        last = min(parse_date(item["end_date"] or item["date"]), end)
        for day in date_range(first, last):
            result.setdefault(iso(day), []).append(item)
    return result


def fetch_task_counts(conn: sqlite3.Connection) -> dict[str, int]:
    rows = conn.execute(
        "SELECT status, COUNT(*) AS total FROM tasks GROUP BY status"
    ).fetchall()
    counts = {"todas": 0, "pendiente": 0, "en_curso": 0, "completada": 0}
    for row in rows:
        counts[row["status"]] = row["total"]
        counts["todas"] += row["total"]
    return counts


def dashboard_counts(conn: sqlite3.Connection, today: date) -> dict[str, int]:
    pending = conn.execute(
        "SELECT COUNT(*) AS total FROM tasks WHERE status <> 'completada'"
    ).fetchone()["total"]
    due_soon_end = today + timedelta(days=3)
    due_soon = conn.execute(
        """
        SELECT COUNT(*) AS total FROM tasks
        WHERE status <> 'completada' AND due_date BETWEEN ? AND ?
        """,
        (iso(today), iso(due_soon_end)),
    ).fetchone()["total"]
    upcoming_end = today + timedelta(days=7)
    upcoming = conn.execute(
        """
        SELECT COUNT(*) AS total FROM tasks
        WHERE status <> 'completada'
          AND kind IN ('entrega', 'examen')
          AND due_date BETWEEN ? AND ?
        """,
        (iso(today), iso(upcoming_end)),
    ).fetchone()["total"]
    classes = conn.execute(
        "SELECT COUNT(*) AS total FROM schedule_slots WHERE kind = 'class'"
    ).fetchone()["total"]
    subjects = conn.execute(
        "SELECT COUNT(*) AS total FROM subjects WHERE is_area = 0"
    ).fetchone()["total"]
    return {
        "pending": pending,
        "due_soon": due_soon,
        "upcoming": upcoming,
        "classes_week": classes,
        "subjects": subjects,
    }
