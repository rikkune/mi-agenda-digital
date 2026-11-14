"""Copias de seguridad, exportación e importación de datos."""

from __future__ import annotations

import json
import os
import re
import sqlite3
from datetime import datetime
from pathlib import Path

from flask import current_app, g

from .query_helpers import rows_to_dicts

APP_ID = "mi-agenda-digital"
APP_VERSION = "1.0.0"

TABLES = [
    "settings",
    "subjects",
    "schedule_slots",
    "tasks",
    "events",
    "holidays",
    "evaluations",
    "tutoring",
    "notes",
    "reminders",
    "day_notes",
    "class_notes",
    "class_note_state",
    "materials",
    "lesson_plans",
    "canvas_links",
]

CHILD_FIRST = [
    "canvas_links",
    "class_notes",
    "class_note_state",
    "day_notes",
    "lesson_plans",
    "materials",
    "reminders",
    "notes",
    "tutoring",
    "evaluations",
    "holidays",
    "events",
    "tasks",
    "schedule_slots",
    "subjects",
    "settings",
]


def database_path() -> Path:
    return Path(current_app.config["DATABASE"])


def backup_dir() -> Path:
    path = Path(current_app.config["BACKUP_DIR"])
    path.mkdir(parents=True, exist_ok=True)
    return path


def _stamp() -> str:
    return datetime.now().strftime("%Y%m%d-%H%M%S")


def _safe_reason(reason: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9_-]+", "-", reason).strip("-").lower()
    return cleaned[:30] or "copia"


def create_backup(reason: str = "manual") -> dict:
    """Crea una copia consistente con la API de SQLite."""
    source_path = database_path()
    if not source_path.exists():
        raise FileNotFoundError("Todavía no existe la base de datos.")

    filename = f"agenda-{_stamp()}-{_safe_reason(reason)}.db"
    target_path = backup_dir() / filename
    source = sqlite3.connect(source_path)
    target = sqlite3.connect(target_path)
    try:
        source.backup(target)
        check = target.execute("PRAGMA integrity_check").fetchone()
        if not check or check[0] != "ok":
            raise RuntimeError("La copia de seguridad no ha pasado la comprobación de integridad.")
    finally:
        source.close()
        target.close()

    stat = target_path.stat()
    return {
        "name": filename,
        "size": stat.st_size,
        "created_at": datetime.fromtimestamp(stat.st_mtime).isoformat(timespec="seconds"),
        "reason": reason,
    }


def list_backups() -> list[dict]:
    result = []
    for path in sorted(backup_dir().glob("*.db"), key=lambda item: item.stat().st_mtime, reverse=True):
        stat = path.stat()
        result.append(
            {
                "name": path.name,
                "size": stat.st_size,
                "created_at": datetime.fromtimestamp(stat.st_mtime).isoformat(timespec="seconds"),
            }
        )
    return result


def _resolve_backup(filename: str) -> Path:
    if not filename or Path(filename).name != filename or not filename.endswith(".db"):
        raise ValueError("El nombre de la copia no es válido.")
    path = (backup_dir() / filename).resolve()
    if backup_dir().resolve() not in path.parents or not path.exists():
        raise ValueError("La copia de seguridad no existe.")
    return path


def restore_backup(filename: str) -> dict:
    """Restaura una copia. Antes guarda el estado actual."""
    path = _resolve_backup(filename)
    safety = create_backup("antes-de-restaurar")

    if "db" in g:
        g.db.close()
        del g.db

    source = sqlite3.connect(path)
    target = sqlite3.connect(database_path())
    try:
        check = source.execute("PRAGMA integrity_check").fetchone()
        if not check or check[0] != "ok":
            raise RuntimeError("La copia está dañada y no se puede restaurar.")
        source.backup(target)
    finally:
        source.close()
        target.close()

    return {"restored": filename, "safety_backup": safety["name"]}


def export_data() -> dict:
    connection = sqlite3.connect(database_path())
    connection.row_factory = sqlite3.Row
    try:
        tables = {}
        for table in TABLES:
            tables[table] = rows_to_dicts(connection.execute(f"SELECT * FROM {table}").fetchall())
        version_row = connection.execute(
            "SELECT value FROM settings WHERE key = 'schema_version'"
        ).fetchone()
    finally:
        connection.close()

    return {
        "app": APP_ID,
        "version": APP_VERSION,
        "schema_version": version_row["value"] if version_row else "1",
        "exported_at": datetime.now().isoformat(timespec="seconds"),
        "tables": tables,
    }


def _table_columns(connection: sqlite3.Connection, table: str) -> list[str]:
    rows = connection.execute(f"PRAGMA table_info({table})").fetchall()
    return [row[1] for row in rows]


def import_data(payload: dict) -> dict:
    """Sustituye todos los datos por los de un JSON exportado."""
    if not isinstance(payload, dict):
        raise ValueError("El archivo no contiene un objeto JSON válido.")
    if payload.get("app") != APP_ID:
        raise ValueError("El archivo no es una exportación de Mi Agenda Digital.")
    tables = payload.get("tables")
    if not isinstance(tables, dict):
        raise ValueError("El archivo no contiene la sección «tables».")
    if not isinstance(tables.get("subjects"), list) or not tables["subjects"]:
        raise ValueError("El archivo no contiene asignaturas.")

    safety = create_backup("antes-de-importar")
    connection = sqlite3.connect(database_path())
    connection.row_factory = sqlite3.Row
    try:
        connection.execute("PRAGMA foreign_keys = ON")
        with connection:
            for table in CHILD_FIRST:
                connection.execute(f"DELETE FROM {table}")
            for table in TABLES:
                rows = tables.get(table, [])
                if not isinstance(rows, list):
                    raise ValueError(f"La tabla «{table}» no es válida.")
                columns = _table_columns(connection, table)
                for row in rows:
                    if not isinstance(row, dict):
                        continue
                    values = {key: row[key] for key in columns if key in row}
                    if not values:
                        continue
                    names = ", ".join(values.keys())
                    marks = ", ".join("?" for _ in values)
                    connection.execute(
                        f"INSERT OR REPLACE INTO {table} ({names}) VALUES ({marks})",
                        tuple(values.values()),
                    )
            connection.execute(
                "INSERT INTO settings (key, value) VALUES ('seeded', '1') "
                "ON CONFLICT(key) DO UPDATE SET value = '1'"
            )
    finally:
        connection.close()

    return {"imported": True, "safety_backup": safety["name"]}


def write_json_export(path: Path) -> None:
    """Escribe una exportación en disco (para pruebas o copias manuales)."""
    path.write_text(
        json.dumps(export_data(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def human_size(size: int) -> str:
    if size < 1024:
        return f"{size} B"
    if size < 1024 * 1024:
        return f"{size / 1024:.1f} KB"
    return f"{size / (1024 * 1024):.1f} MB"
