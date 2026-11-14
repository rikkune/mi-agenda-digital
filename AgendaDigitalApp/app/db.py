"""Conexión y creación de la base de datos SQLite."""

from __future__ import annotations

import sqlite3
from pathlib import Path

from flask import current_app, g

from . import seed


def get_db() -> sqlite3.Connection:
    """Devuelve la conexión de la petición actual."""
    if "db" not in g:
        connection = sqlite3.connect(
            current_app.config["DATABASE"],
            timeout=15,
        )
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA journal_mode = WAL")
        connection.execute("PRAGMA busy_timeout = 5000")
        g.db = connection
    return g.db


def close_db(_error: BaseException | None = None) -> None:
    """Cierra la conexión al terminar la petición."""
    connection = g.pop("db", None)
    if connection is not None:
        connection.close()


def query_db(query: str, args: tuple = (), one: bool = False):
    """Consulta de solo lectura con parámetros."""
    cursor = get_db().execute(query, args)
    rows = cursor.fetchall()
    cursor.close()
    if one:
        return rows[0] if rows else None
    return rows


def execute_db(query: str, args: tuple = ()) -> int:
    """Ejecuta una escritura y confirma."""
    connection = get_db()
    cursor = connection.execute(query, args)
    connection.commit()
    last_id = cursor.lastrowid
    cursor.close()
    return int(last_id)


def row_to_dict(row: sqlite3.Row | None) -> dict | None:
    if row is None:
        return None
    return {key: row[key] for key in row.keys()}


def init_db() -> None:
    """Crea el esquema si falta y carga los datos iniciales una sola vez."""
    database = Path(current_app.config["DATABASE"])
    database.parent.mkdir(parents=True, exist_ok=True)
    Path(current_app.config["BACKUP_DIR"]).mkdir(parents=True, exist_ok=True)

    schema_path = Path(__file__).with_name("schema.sql")
    with open(schema_path, "r", encoding="utf-8") as schema_file:
        schema = schema_file.read()

    connection = sqlite3.connect(database)
    connection.row_factory = sqlite3.Row
    try:
        connection.execute("PRAGMA foreign_keys = ON")
        connection.executescript(schema)

        # Migración: añadir due_time a tareas si no existe
        cols = connection.execute("PRAGMA table_info(tasks)").fetchall()
        col_names = [c["name"] for c in cols]
        if "due_time" not in col_names:
            connection.execute("ALTER TABLE tasks ADD COLUMN due_time TEXT")
        if "target" not in col_names:
            connection.execute("ALTER TABLE tasks ADD COLUMN target TEXT NOT NULL DEFAULT 'docente' CHECK (target IN ('docente', 'alumno'))")
        if "color" not in col_names:
            connection.execute("ALTER TABLE tasks ADD COLUMN color TEXT")
        if "marked" not in col_names:
            connection.execute("ALTER TABLE tasks ADD COLUMN marked INTEGER NOT NULL DEFAULT 0 CHECK (marked IN (0, 1))")

        # Migración: progreso de corrección (Aula Virtual) en los recordatorios
        reminder_cols = [c["name"] for c in connection.execute("PRAGMA table_info(reminders)").fetchall()]
        if "progress" not in reminder_cols:
            connection.execute("ALTER TABLE reminders ADD COLUMN progress TEXT")

        # Migración: añadir color a eventos si no existe
        event_cols = connection.execute("PRAGMA table_info(events)").fetchall()
        event_col_names = [c["name"] for c in event_cols]
        if "color" not in event_col_names:
            connection.execute("ALTER TABLE events ADD COLUMN color TEXT")

        # Migración: añadir índice único para evitar duplicados en eventos
        indexes = connection.execute("PRAGMA index_list(events)").fetchall()
        has_unique = any(idx["name"] == "uq_events_title_date_subject_category" for idx in indexes)
        if not has_unique:
            # Las bases antiguas pueden tener duplicados: sin limpiarlos, crear
            # el índice único falla y la agenda no arranca.
            connection.execute("""
                DELETE FROM events
                WHERE id NOT IN (
                    SELECT MAX(id) FROM events
                    GROUP BY title, start_date, COALESCE(subject_id, -id), category
                )
            """)
            connection.execute("""
                CREATE UNIQUE INDEX IF NOT EXISTS uq_events_title_date_subject_category
                ON events (title, start_date, subject_id, category)
            """)

        connection.execute("PRAGMA user_version = 2")

        seeded = connection.execute(
            "SELECT value FROM settings WHERE key = 'seeded'"
        ).fetchone()
        if not seeded:
            seed.seed_all(connection)
            connection.execute(
                "INSERT INTO settings (key, value) VALUES ('seeded', '1') "
                "ON CONFLICT(key) DO UPDATE SET value = '1'"
            )
        connection.commit()
    finally:
        connection.close()


def init_app(app) -> None:
    """Registra el cierre de conexiones en la aplicación Flask."""
    app.teardown_appcontext(close_db)
