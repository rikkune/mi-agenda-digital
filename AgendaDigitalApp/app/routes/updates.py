"""Comprobar e instalar versiones nuevas de la agenda."""

from __future__ import annotations

from flask import Blueprint, current_app, jsonify, request

from ..services.updater import UpdateError

bp = Blueprint("updates", __name__, url_prefix="/api")


def _updater():
    return current_app.extensions["updater"]


@bp.get("/update")
def check_update():
    updater = _updater()
    force = request.args.get("force") == "1"
    return jsonify(updater.public(updater.check(force=force)))


@bp.post("/update/install")
def install_update():
    try:
        return jsonify(_updater().install())
    except UpdateError as error:
        return jsonify({"error": str(error), "page": error.page}), 409
