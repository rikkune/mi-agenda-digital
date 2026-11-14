"""Sincronización con el Aula Virtual de MEDAC."""

from __future__ import annotations

from flask import Blueprint, current_app, jsonify

from ..db import get_db
from ..services import backups, canvas

bp = Blueprint("canvas", __name__, url_prefix="/api/canvas")


@bp.get("/status")
def sync_status():
    return jsonify(canvas.status(get_db()))


@bp.post("/sync")
def run_sync():
    store = current_app.extensions["auth"]
    credentials = store.credentials()
    if not credentials:
        return jsonify({"error": "Inicia sesión para sincronizar con el Aula Virtual."}), 401
    if not canvas.status(get_db())["last_sync"]:
        # Primera vez que se vuelca el Aula Virtual: copia de seguridad por si acaso.
        backups.create_backup("antes-de-aula-virtual")
    try:
        result = canvas.sync(current_app.config["DATABASE"], credentials)
    except canvas.CanvasAuthError:
        # La contraseña ha cambiado en MEDAC: la guardada ya no sirve.
        store.sign_out()
        return jsonify({
            "error": "MEDAC ya no acepta tu contraseña guardada. Vuelve a iniciar sesión.",
            "login_required": True,
        }), 401
    except canvas.CanvasError as error:
        return jsonify({"error": str(error)}), 502
    if result.get("status") == "busy":
        return jsonify({"error": "Ya hay una sincronización en curso."}), 409
    return jsonify(result)
