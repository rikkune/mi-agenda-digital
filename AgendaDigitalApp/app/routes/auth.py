"""Inicio y cierre de sesión con las credenciales del Aula Virtual."""

from __future__ import annotations

from flask import (
    Blueprint,
    current_app,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

from ..services import canvas

bp = Blueprint("auth", __name__)

# Rutas accesibles sin haber iniciado sesión.
PUBLIC_ENDPOINTS = {"auth.login_page", "auth.login", "static", "ping"}


def _store():
    return current_app.extensions["auth"]


def is_authenticated() -> bool:
    return _store().is_valid(session.get("token"))


def require_login():
    """before_request: todo lo que no sea público exige sesión iniciada."""
    if request.endpoint in PUBLIC_ENDPOINTS or is_authenticated():
        return None
    session.clear()
    if request.path.startswith("/api/"):
        return jsonify({"error": "Tu sesión ha terminado. Vuelve a iniciar sesión.", "login_required": True}), 401
    return redirect(url_for("auth.login_page"))


def _render_login(error: str = "", username: str | None = None, remember: bool = True, status: int = 200):
    return (
        render_template(
            "login.html",
            error=error,
            username=_store().last_username if username is None else username,
            remember=remember,
        ),
        status,
    )


@bp.get("/login")
def login_page():
    if is_authenticated():
        return redirect(url_for("index"))
    return _render_login()


@bp.post("/login")
def login():
    username = (request.form.get("username") or "").strip()
    password = request.form.get("password") or ""
    remember = request.form.get("remember") == "1"
    if not username or not password:
        return _render_login("Escribe tu usuario y tu contraseña de MEDAC.", username, remember, 400)
    try:
        canvas.verify_login(username, password)
    except canvas.CanvasAuthError:
        return _render_login("MEDAC no reconoce ese usuario o esa contraseña.", username, remember, 401)
    except canvas.CanvasError as error:
        return _render_login(str(error), username, remember, 502)

    token = _store().sign_in(username, password, persistent=remember)
    session.clear()
    session.permanent = remember
    session["token"] = token
    return redirect(url_for("index"))


@bp.post("/api/auth/logout")
def logout():
    _store().sign_out()
    session.clear()
    return jsonify({"ok": True})


@bp.get("/api/auth/me")
def me():
    return jsonify({"username": _store().username()})
