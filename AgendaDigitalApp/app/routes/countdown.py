"""Cuenta atrás hasta el próximo descanso (festivo o vacaciones), para la barra superior."""

from __future__ import annotations

from datetime import date, timedelta

from flask import Blueprint, jsonify, request

from ..db import get_db
from ..services.validation import query_date

bp = Blueprint("countdown", __name__, url_prefix="/api")


def _periods(connection) -> list[tuple[date, date, str, str]]:
    rows = connection.execute(
        "SELECT start_date, end_date, name, scope FROM holidays ORDER BY start_date"
    ).fetchall()
    periods = []
    for row in rows:
        start = date.fromisoformat(row["start_date"])
        end = date.fromisoformat(row["end_date"]) if row["end_date"] else start
        periods.append((start, end, row["name"], row["scope"]))
    return periods


def _is_school_day(day: date, periods) -> bool:
    return day.isoweekday() <= 5 and not any(start <= day <= end for start, end, _, _ in periods)


@bp.get("/countdown")
def countdown():
    today = query_date(request.args.get("date"), "fecha", date.today())
    periods = _periods(get_db())

    for start, end, name, scope in periods:
        if start <= today <= end:
            back = end + timedelta(days=1)
            while not _is_school_day(back, periods) and back - end < timedelta(days=30):
                back += timedelta(days=1)
            return jsonify({"state": "now", "name": name, "scope": scope,
                            "end": end.isoformat(), "back": back.isoformat()})

    upcoming = next(((s, e, n, sc) for s, e, n, sc in periods if s > today), None)
    if upcoming is None:
        return jsonify({"state": "done"})
    start, end, name, scope = upcoming
    school_days = sum(
        1 for offset in range((start - today).days)
        if _is_school_day(today + timedelta(days=offset), periods)
    )
    return jsonify({"state": "upcoming", "name": name, "scope": scope, "start": start.isoformat(),
                    "end": end.isoformat(), "days": (start - today).days, "school_days": school_days})
