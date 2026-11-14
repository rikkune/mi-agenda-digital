"""Exportación, importación y copias de seguridad."""

from __future__ import annotations

import json
import sqlite3
from datetime import date
from pathlib import Path

from flask import Blueprint, current_app, jsonify, request

from ..db import get_db
from ..services.backups import (
    create_backup,
    export_data,
    import_data,
    list_backups,
    restore_backup,
)
from ..services.validation import ValidationError, text

bp = Blueprint("backups", __name__, url_prefix="/api")


def _body() -> dict:
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        raise ValidationError("No se han recibido datos válidos.")
    return data


@bp.get("/export")
def export_json():
    payload = export_data()
    body = json.dumps(payload, ensure_ascii=False, indent=2)
    response = current_app.response_class(body, mimetype="application/json")
    response.headers["Content-Disposition"] = (
        f'attachment; filename="mi-agenda-{date.today().isoformat()}.json"'
    )
    return response


@bp.post("/import")
def import_json():
    data = _body()
    if data.get("confirm") is not True:
        raise ValidationError("Debes confirmar la importación.")
    try:
        result = import_data(data.get("data"))
    except sqlite3.IntegrityError as exc:
        raise ValidationError(
            "El archivo contiene datos incoherentes y no se ha importado. "
            "Tus datos actuales no se han modificado."
        ) from exc
    except (ValueError, RuntimeError, FileNotFoundError) as exc:
        raise ValidationError(str(exc)) from exc
    return jsonify({"ok": True, **result})


@bp.post("/backup")
def create_backup_route():
    data = request.get_json(silent=True) or {}
    reason = text(data.get("reason", "manual"), "motivo", max_len=40, default="manual")
    try:
        backup = create_backup(reason)
    except (RuntimeError, FileNotFoundError) as exc:
        raise ValidationError(str(exc)) from exc
    return jsonify({"ok": True, "backup": backup})


@bp.get("/backups")
def list_backups_route():
    database = Path(current_app.config["DATABASE"])
    size = database.stat().st_size if database.exists() else 0
    return jsonify(
        {
            "database": str(database),
            "database_size": size,
            "backups_dir": str(current_app.config["BACKUP_DIR"]),
            "backups": list_backups(),
        }
    )


@bp.post("/restore")
def restore_route():
    data = _body()
    if data.get("confirm") is not True:
        raise ValidationError("Debes confirmar la restauración.")
    filename = text(data.get("file"), "copia de seguridad", max_len=200, required=True)
    try:
        result = restore_backup(filename)
    except (ValueError, RuntimeError, FileNotFoundError, sqlite3.DatabaseError) as exc:
        raise ValidationError(str(exc)) from exc
    # La conexión de la petición se ha cerrado; se abre una nueva al terminar.
    return jsonify({"ok": True, **result})


@bp.get("/data-info")
def data_info():
    connection = get_db()
    counts = {}
    for table in ("tasks", "events", "notes", "tutoring", "materials", "lesson_plans"):
        counts[table] = connection.execute(
            f"SELECT COUNT(*) AS total FROM {table}"
        ).fetchone()["total"]
    database = Path(current_app.config["DATABASE"])
    size = database.stat().st_size if database.exists() else 0
    return jsonify(
        {
            "database": str(database),
            "database_size": size,
            "backups_dir": str(current_app.config["BACKUP_DIR"]),
            "counts": counts,
            "backups": list_backups(),
        }
    )
