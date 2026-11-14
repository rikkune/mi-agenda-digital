"""Fichaje de jornada en Factorial."""

from __future__ import annotations

from flask import Blueprint, current_app, jsonify

from ..services.factorial import ACTIONS, FactorialAuthError, FactorialError

bp = Blueprint("factorial", __name__, url_prefix="/api/factorial")


def _client():
    return current_app.extensions["factorial"]


@bp.get("/status")
def status():
    return jsonify(_client().status())


@bp.post("/connect")
def connect():
    _client().start_login()
    return jsonify(_client().status()), 202


@bp.post("/disconnect")
def disconnect():
    _client().disconnect()
    return jsonify({"ok": True})


@bp.post("/clock/<action>")
def clock(action: str):
    if action not in ACTIONS:
        return jsonify({"error": "Acción de fichaje desconocida."}), 404
    try:
        return jsonify(_client().act(action))
    except FactorialAuthError as error:
        return jsonify({"error": str(error), "factorial_login": True}), 401
    except FactorialError as error:
        return jsonify({"error": str(error)}), 502
