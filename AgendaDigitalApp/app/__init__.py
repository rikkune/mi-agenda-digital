"""Aplicación local Mi Agenda Digital 2026-2027."""

from __future__ import annotations

from datetime import timedelta
from pathlib import Path

from flask import Flask, jsonify, render_template, request
from werkzeug.exceptions import HTTPException

from . import db
from .version import APP_VERSION
from .paths import data_dir as _data_dir
from .paths import resource_dir
from .services.auth import AuthStore, secret_key
from .services.factorial import Factorial
from .services.updater import Updater
from .services.validation import ValidationError



def create_app() -> Flask:
    base_dir = resource_dir()
    data_dir = _data_dir()
    backup_dir = data_dir / "backups"
    data_dir.mkdir(parents=True, exist_ok=True)
    backup_dir.mkdir(parents=True, exist_ok=True)

    app = Flask(
        __name__,
        template_folder=str(base_dir / "templates"),
        static_folder=str(base_dir / "static"),
    )
    app.config.update(
        DATABASE=str(data_dir / "agenda.db"),
        BACKUP_DIR=str(backup_dir),
        MAX_CONTENT_LENGTH=16 * 1024 * 1024,
        JSON_SORT_KEYS=False,
        SECRET_KEY=secret_key(data_dir),
        SESSION_COOKIE_NAME="agenda_session",
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        # «Mantener la sesión iniciada»: la cookie se renueva en cada visita y
        # solo se pierde al pulsar «Cerrar sesión» (400 días es el máximo de Chrome).
        PERMANENT_SESSION_LIFETIME=timedelta(days=400),
        SESSION_REFRESH_EACH_REQUEST=True,
    )
    app.extensions["auth"] = AuthStore(data_dir)
    app.extensions["factorial"] = Factorial(data_dir)
    app.extensions["updater"] = Updater()
    app.json.ensure_ascii = False
    app.json.sort_keys = False

    db.init_app(app)

    from .routes import (
        auth,
        backups,
        calendar,
        canvas,
        dashboard,
        evaluations,
        factorial,
        notes,
        reminders,
        schedule,
        subjects,
        tasks,
        tutoring,
        updates,
    )

    app.before_request(auth.require_login)

    for blueprint in (
        auth.bp,
        dashboard.bp,
        tasks.bp,
        calendar.bp,
        schedule.bp,
        subjects.bp,
        tutoring.bp,
        notes.bp,
        reminders.bp,
        evaluations.bp,
        backups.bp,
        canvas.bp,
        factorial.bp,
        updates.bp,
    ):
        app.register_blueprint(blueprint)

    with app.app_context():
        db.init_db()

    @app.get("/")
    def index():
        return render_template("index.html", username=app.extensions["auth"].username())

    @app.get("/api/ping")
    def ping():
        # Público: el lanzador lo usa para saber si la agenda ya está abierta.
        return jsonify({"app": "MiAgendaDigital", "version": APP_VERSION})

    @app.get("/api/health")
    def health():
        connection = db.get_db()
        connection.execute("SELECT 1").fetchone()
        database = Path(app.config["DATABASE"])
        return jsonify(
            {
                "ok": True,
                "version": APP_VERSION,
                "database": str(database),
                "database_exists": database.exists(),
                "database_size": database.stat().st_size if database.exists() else 0,
            }
        )

    @app.errorhandler(ValidationError)
    def handle_validation_error(error: ValidationError):
        return jsonify({"error": str(error)}), 400

    @app.errorhandler(413)
    def handle_too_large(_error):
        return jsonify({"error": "El archivo es demasiado grande (máximo 16 MB)."}), 413

    @app.errorhandler(404)
    def handle_not_found(error):
        message = getattr(error, "description", "No se ha encontrado el recurso.")
        if request.path.startswith("/api/"):
            return jsonify({"error": message}), 404
        return jsonify({"error": message}), 404

    @app.errorhandler(HTTPException)
    def handle_http_error(error: HTTPException):
        if request.path.startswith("/api/"):
            return jsonify({"error": error.description}), error.code
        return jsonify({"error": error.description}), error.code

    @app.errorhandler(Exception)
    def handle_unexpected_error(error: Exception):
        app.logger.exception("Error inesperado: %s", error)
        return (
            jsonify(
                {
                    "error": (
                        "Ha ocurrido un error inesperado. El detalle queda en el "
                        "registro de la agenda (agenda.log)."
                    )
                }
            ),
            500,
        )

    @app.after_request
    def security_headers(response):
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("Referrer-Policy", "no-referrer")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault(
            "Content-Security-Policy",
            "default-src 'self'; style-src 'self' 'unsafe-inline'; "
            "script-src 'self'; img-src 'self' data:; font-src 'self'; "
            "connect-src 'self'; base-uri 'none'; form-action 'self'; "
            "frame-ancestors 'none'",
        )
        if request.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store"
        return response

    return app
