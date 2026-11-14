"""Utilidades de fechas para el calendario escolar."""

from __future__ import annotations

from datetime import date, timedelta

SCHOOL_START = date(2026, 9, 1)
SCHOOL_END = date(2027, 8, 31)

MONTHS_ES = [
    "Enero",
    "Febrero",
    "Marzo",
    "Abril",
    "Mayo",
    "Junio",
    "Julio",
    "Agosto",
    "Septiembre",
    "Octubre",
    "Noviembre",
    "Diciembre",
]

WEEKDAYS_ES = [
    "Lunes",
    "Martes",
    "Miércoles",
    "Jueves",
    "Viernes",
    "Sábado",
    "Domingo",
]

WEEKDAYS_SHORT = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]


def iso(value: date) -> str:
    return value.isoformat()


def parse_date(value: str | None, default: date | None = None) -> date:
    if not value:
        if default is None:
            raise ValueError("Fecha vacía")
        return default
    return date.fromisoformat(value)


def month_title(year: int, month: int) -> str:
    return f"{MONTHS_ES[month - 1]} {year}"


def month_first_weekday(year: int, month: int) -> int:
    """Día de la semana del día 1, con lunes = 1 y domingo = 7."""
    return date(year, month, 1).isoweekday()


def days_in_month(year: int, month: int) -> int:
    if month == 12:
        return 31
    return (date(year, month + 1, 1) - date(year, month, 1)).days


def month_grid(year: int, month: int, weeks: int = 6) -> list[date]:
    """Cuadrícula de 6 semanas que empieza en lunes."""
    first = date(year, month, 1)
    start = first - timedelta(days=first.isoweekday() - 1)
    return [start + timedelta(days=index) for index in range(weeks * 7)]


def week_grid(anchor: date) -> list[date]:
    start = anchor - timedelta(days=anchor.isoweekday() - 1)
    return [start + timedelta(days=index) for index in range(7)]


def school_year_days() -> list[date]:
    total = (SCHOOL_END - SCHOOL_START).days + 1
    return [SCHOOL_START + timedelta(days=index) for index in range(total)]


def clamp_date(value: date) -> date:
    if value < SCHOOL_START:
        return SCHOOL_START
    if value > SCHOOL_END:
        return SCHOOL_END
    return value


def shift_month(value: date, delta: int) -> date:
    month = value.month - 1 + delta
    year = value.year + month // 12
    month = month % 12 + 1
    day = min(value.day, days_in_month(year, month))
    return clamp_date(date(year, month, day))


def shift_week(value: date, delta: int) -> date:
    return clamp_date(value + timedelta(days=7 * delta))


def date_range(start: date, end: date):
    current = start
    while current <= end:
        yield current
        current += timedelta(days=1)


def month_bounds(year: int, month: int) -> tuple[date, date]:
    first = date(year, month, 1)
    last = date(year, month, days_in_month(year, month))
    return first, last


def year_bounds() -> tuple[date, date]:
    return SCHOOL_START, SCHOOL_END
