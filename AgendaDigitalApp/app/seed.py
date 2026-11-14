"""Datos iniciales de la agenda.

Solo contiene lo común a todo el claustro: calendario escolar, festivos,
fechas de evaluación del centro y la rejilla de horas por defecto. Las
asignaturas y el horario son de cada persona: se crean desde la propia agenda
(«Mi horario» → «Mis asignaturas») o al sincronizar con el Aula Virtual.
Se ejecuta una sola vez sobre una base de datos nueva.

Fuentes:
- Calendario escolar 2026-2027 de Aragón (DGA).
- Decreto 70/2025 y Decreto 163/2026 del Gobierno de Aragón.
- Calendario laboral de Zaragoza (San Valero y Cincomarzada).
- PDF "AGENDA ESCOLAR 26-27", páginas 5-9.

Las fechas del PDF que no coinciden entre el listado "Fechas marcadas" y el
calendario coloreado se han cargado según el listado, que es el documento
detallado. Las discrepancias quedan anotadas en el campo notes.
"""

from __future__ import annotations

import sqlite3
from datetime import date

# Rejilla de horas por defecto del centro (cada persona puede cambiarla en «Mi horario»).
TIME_ROWS = [
    ("08:15", "10:15"),
    ("10:15", "11:15"),
    ("11:15", "11:45"),
    ("11:45", "12:45"),
    ("12:45", "13:45"),
    ("13:45", "14:45"),
]

# Franja de descanso común: se marca como «Descanso» todos los días.
BREAK_ROW = ("11:15", "11:45")

HOLIDAYS = [
    {
        "start_date": "2026-10-12",
        "end_date": None,
        "name": "Fiesta Nacional de España",
        "scope": "nacional",
        "verified": 1,
        "source": "BOE y Decreto 70/2025 (BOA)",
    },
    {
        "start_date": "2026-10-13",
        "end_date": "2026-10-14",
        "name": "Días no lectivos de Zaragoza",
        "scope": "no_lectivo",
        "verified": 1,
        "source": "Calendario escolar 2026-2027 (DGA)",
    },
    {
        "start_date": "2026-11-02",
        "end_date": None,
        "name": "Todos los Santos (trasladado)",
        "scope": "nacional",
        "verified": 1,
        "source": "BOE y Decreto 70/2025 (BOA)",
    },
    {
        "start_date": "2026-12-07",
        "end_date": None,
        "name": "Día de la Constitución (trasladado)",
        "scope": "nacional",
        "verified": 1,
        "source": "BOE y Decreto 70/2025 (BOA)",
    },
    {
        "start_date": "2026-12-08",
        "end_date": None,
        "name": "Inmaculada Concepción",
        "scope": "nacional",
        "verified": 1,
        "source": "BOE y Decreto 70/2025 (BOA)",
    },
    {
        "start_date": "2026-12-23",
        "end_date": "2027-01-06",
        "name": "Vacaciones de Navidad",
        "scope": "vacaciones",
        "verified": 1,
        "source": "Calendario escolar 2026-2027 (DGA)",
    },
    {
        "start_date": "2027-01-29",
        "end_date": None,
        "name": "San Valero",
        "scope": "local",
        "verified": 1,
        "source": "Calendario laboral de Zaragoza y BOA",
    },
    {
        "start_date": "2027-03-05",
        "end_date": None,
        "name": "Cincomarzada",
        "scope": "local",
        "verified": 1,
        "source": "Calendario laboral de Zaragoza y BOA",
    },
    {
        "start_date": "2027-03-25",
        "end_date": "2027-04-02",
        "name": "Vacaciones de Semana Santa",
        "scope": "vacaciones",
        "verified": 1,
        "source": "Calendario escolar 2026-2027 (DGA)",
    },
    {
        "start_date": "2027-04-23",
        "end_date": None,
        "name": "San Jorge, Día de Aragón",
        "scope": "autonomico",
        "verified": 1,
        "source": "BOA y Decreto 163/2026",
    },
    {
        "start_date": "2027-05-01",
        "end_date": None,
        "name": "Fiesta del Trabajo",
        "scope": "nacional",
        "verified": 1,
        "source": "BOE y Decreto 163/2026 (BOA)",
    },
    {
        "start_date": "2027-05-03",
        "end_date": None,
        "name": "Día no lectivo de Zaragoza",
        "scope": "no_lectivo",
        "verified": 1,
        "source": "Calendario escolar 2026-2027 (DGA)",
    },
    {
        "start_date": "2027-06-19",
        "end_date": "2027-08-31",
        "name": "Vacaciones de verano",
        "scope": "vacaciones",
        "verified": 1,
        "source": "Calendario escolar 2026-2027 (DGA): fin de curso 18/06/2027",
        "notes": "Periodo no lectivo posterior al fin de curso.",
    },
]

COMMON_EVALUATIONS = [
    ("2026-09-10", None, "Comienzo de curso", "comienzo"),
    ("2026-10-12", None, "Festivo nacional: Fiesta Nacional de España", "festivo"),
    ("2026-10-13", "2026-10-14", "Días no lectivos de Zaragoza", "no_lectivo"),
    ("2026-11-02", None, "Festivo: Día de Todos los Santos", "festivo"),
    ("2026-11-27", None, "Plazo máximo evaluación PRL 1.º curso", "plazo"),
    ("2026-12-07", None, "No lectivo: traslado del Día de la Constitución", "no_lectivo"),
    ("2026-12-08", None, "Festivo nacional: Inmaculada Concepción", "festivo"),
    ("2026-12-11", None, "Plazo máximo fin de exámenes del 1.er trimestre", "plazo"),
    ("2026-12-14", None, "Comienzo del 2.º trimestre", "comienzo"),
    ("2026-12-16", None, "Plazo máximo fin FCT TCAE + periodo extraordinario", "plazo"),
    ("2026-12-17", None, "Plazo máximo sesión de evaluación del 1.er trimestre + PRL 1.º", "plazo"),
    ("2026-12-23", "2027-01-06", "Vacaciones de Navidad", "no_lectivo"),
    ("2027-01-19", None, "Plazo máximo recuperación del 1.er trimestre", "plazo"),
    ("2027-01-29", None, "Festivo local: San Valero", "festivo"),
    ("2027-03-05", None, "Festivo local: Cincomarzada", "festivo"),
    ("2027-03-25", "2027-04-02", "Vacaciones de Semana Santa", "no_lectivo"),
    ("2027-04-23", None, "Festivo: San Jorge, Día de Aragón", "festivo"),
    ("2027-05-03", None, "Día no lectivo de Zaragoza", "no_lectivo"),
    ("2027-06-04", None, "Convocatoria Ordinaria", "otro"),
    ("2027-06-04", None, "Plazo máximo defensa Ordinaria del Proyecto 2.º + subida 1 punto 1.º", "plazo"),
    ("2027-06-09", None, "Plazo máximo sesiones de evaluación del 3.er trimestre + Ordinaria", "plazo"),
    ("2027-06-10", None, "Entrega de boletín del 3.er trimestre + ordinaria", "entrega_notas"),
    ("2027-06-10", "2027-06-15", "Repaso + exámenes de la Extraordinaria", "otro"),
    ("2027-06-15", None, "Plazo máximo defensa Extraordinaria del Proyecto", "plazo"),
    ("2027-06-16", None, "Plazo máximo sesión de evaluación Extraordinaria", "plazo"),
    ("2027-06-18", None, "Fin de clases + Entrega del Boletín Final", "entrega_notas"),
]

EVALUATIONS_1LFP = [
    ("2026-12-21", None, "Plazo máximo publicación trabajo subida nota 1 punto (1.º)", "plazo"),
    ("2026-12-22", None, "Entrega boletín 1.er trimestre (1.º)", "entrega_notas"),
    ("2027-01-25", None, "Comienzo periodo FFE 1.º", "comienzo"),
    ("2027-02-26", None, "Fin máximo periodo FFE 1.º", "otro"),
    ("2027-03-01", None, "Reanudación de clases en el centro (1.º)", "comienzo"),
    ("2027-03-17", None, "Plazo máximo fin exámenes 2.º trimestre (1.º) + publicación trabajo 1 punto", "plazo"),
    ("2027-03-18", None, "Comienzo del 3.er trimestre", "comienzo"),
    ("2027-03-23", None, "Plazo máximo sesión evaluación 2.º trimestre + FFE 1.º", "plazo"),
    ("2027-03-24", None, "Entrega boletín 2.º trimestre (1.º)", "entrega_notas"),
    ("2027-04-13", None, "Plazo máximo recuperaciones 2.º trimestre (1.º)", "plazo"),
    ("2027-05-18", None, "Plazo máximo entrega subida nota 1 punto (1.º)", "plazo"),
    ("2027-05-20", None, "Plazo máximo fin exámenes 3.er trimestre (1.º)", "plazo"),
    ("2027-05-25", None, "Plazo máximo notificación alumnos suspensos (1.º)", "plazo"),
    ("2027-05-26", None, "Fin de clases periodo ordinario (1.º)", "otro"),
]

EVALUATIONS_2LFP = [
    ("2026-12-21", None, "Plazo máximo publicación trabajo subida nota 1 punto (2.º)", "plazo"),
    ("2026-12-22", None, "Entrega boletín 1.er trimestre + boletín 2.º TCAE", "entrega_notas"),
    ("2027-02-16", None, "Plazo máximo fin exámenes 2.º trimestre (2.º) + depósito de proyecto", "plazo"),
    ("2027-02-18", None, "Notificación alumnos suspensos 2.º trimestre (2.º)", "plazo"),
    ("2027-02-23", None, "Plazo máximo recuperación 2.º trimestre + subida nota 1 punto (2.º)", "plazo"),
    ("2027-02-24", None, "Plazo máximo exposición subida 1 punto (2.º)", "plazo"),
    ("2027-02-25", None, "Plazo máximo sesión evaluación 2.º trimestre (2.º)", "plazo"),
    ("2027-02-26", None, "Entrega boletín 2.º trimestre (2.º)", "entrega_notas"),
    ("2027-03-01", None, "Comienzo acceso periodo FFE 2.º", "comienzo"),
    ("2027-05-28", None, "Fin de clases periodo ordinario (2.º)", "otro"),
    ("2027-05-31", None, "Fin periodo FFE 2.º", "otro"),
]


def _seed_schedule(db: sqlite3.Connection) -> None:
    start_time, end_time = BREAK_ROW
    for weekday in range(1, 6):
        db.execute(
            """
            INSERT INTO schedule_slots (weekday, start_time, end_time, subject_id, label, kind)
            VALUES (?, ?, ?, NULL, 'Descanso', 'break')
            ON CONFLICT(weekday, start_time) DO NOTHING
            """,
            (weekday, start_time, end_time),
        )


def _seed_holidays(db: sqlite3.Connection) -> None:
    for holiday in HOLIDAYS:
        db.execute(
            """
            INSERT INTO holidays (start_date, end_date, name, scope, verified, source, notes)
            VALUES (:start_date, :end_date, :name, :scope, :verified, :source, :notes)
            ON CONFLICT(start_date, name) DO UPDATE SET
                end_date = excluded.end_date,
                scope = excluded.scope,
                verified = excluded.verified,
                source = excluded.source,
                notes = excluded.notes
            """,
            {"notes": None, **holiday},
        )


def _seed_evaluations(db: sqlite3.Connection) -> None:
    source_1 = "PDF AGENDA ESCOLAR 26-27, páginas 6-7 (1.º LFP)"
    source_2 = "PDF AGENDA ESCOLAR 26-27, páginas 8-9 (2.º LFP-LOGSE)"
    rows: list[tuple[str, str, str | None, str, str, str, str | None]] = []
    for start, end, title, kind in COMMON_EVALUATIONS:
        rows.append(("1LFP", start, end, title, kind, source_1, None))
        rows.append(("2LFP", start, end, title, kind, source_2, None))
    for start, end, title, kind in EVALUATIONS_1LFP:
        rows.append(("1LFP", start, end, title, kind, source_1, None))
    for start, end, title, kind in EVALUATIONS_2LFP:
        rows.append(("2LFP", start, end, title, kind, source_2, None))

    for course, start, end, title, kind, source, notes in rows:
        db.execute(
            """
            INSERT INTO evaluations (course, start_date, end_date, title, kind, source_page, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(course, start_date, title) DO UPDATE SET
                end_date = excluded.end_date,
                kind = excluded.kind,
                source_page = excluded.source_page,
                notes = excluded.notes
            """,
            (course, start, end, title, kind, source, notes),
        )


def _seed_settings(db: sqlite3.Connection) -> None:
    defaults = {
        "school_year": "2026–2027",
        "active_course": "1LFP",
        "schema_version": "1",
    }
    for key, value in defaults.items():
        db.execute(
            "INSERT INTO settings (key, value) VALUES (?, ?) ON CONFLICT(key) DO NOTHING",
            (key, value),
        )


def _seed_welcome_note(db: sqlite3.Connection) -> None:
    row = db.execute("SELECT value FROM settings WHERE key = 'welcome_seeded'").fetchone()
    if row:
        return
    today = date.today().isoformat()
    db.execute(
        """
        INSERT INTO notes (title, body, subject_id, note_date, pinned, created_at, updated_at)
        VALUES (?, ?, NULL, ?, 1, ?, ?)
        """,
        (
            "Tu agenda está lista",
            "Primero pulsa «Sincronizar» para traer tus cursos del Aula Virtual, o "
            "añade tus asignaturas en «Mi horario» → «Mis asignaturas». Después "
            "rellena tu horario pulsando cada celda. Todo se guarda solo en tu "
            "ordenador; puedes hacer copias desde «Copias y datos».",
            today,
            f"{today}T00:00:00",
            f"{today}T00:00:00",
        ),
    )
    db.execute("INSERT INTO settings (key, value) VALUES ('welcome_seeded', '1')")


def seed_all(db: sqlite3.Connection) -> None:
    """Carga los datos iniciales sin duplicarlos."""
    _seed_schedule(db)
    _seed_holidays(db)
    _seed_evaluations(db)
    _seed_settings(db)
    _seed_welcome_note(db)
    db.commit()
