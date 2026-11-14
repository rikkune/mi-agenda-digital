"""Sincronización con el Aula Virtual de MEDAC (Canvas LMS).

Flujo de acceso (sin navegador):
1. Login con formulario en https://instituto.medac.es/login (token CSRF).
2. https://medac.instructure.com/ redirige al proveedor SAML del instituto, que
   devuelve un formulario con SAMLResponse; se envía a Canvas.
3. Con las cookies de Canvas se consulta la API REST (/api/v1/...).

Qué se vuelca en la agenda:
- Cada tarea de Canvas con fecha de entrega -> tarea de tipo «entrega».
- Cada tarea con entregas sin corregir -> recordatorio «corregir» en la semana actual.

Las credenciales son las del inicio de sesión de la agenda (ver services/auth.py).
Nunca se guardan en la base de datos. Solo se usa la biblioteca estándar.
"""

from __future__ import annotations

import html
import json
import re
import sqlite3
import threading
import unicodedata
from datetime import date, datetime
from html.parser import HTMLParser
from http.cookiejar import CookieJar
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urljoin
from urllib.request import HTTPCookieProcessor, Request, build_opener

LOGIN_URL = "https://instituto.medac.es/login"
CANVAS_URL = "https://medac.instructure.com"
API = CANVAS_URL + "/api/v1"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) MiAgendaDigital/1.0"
TIMEOUT = 25

# Asignaturas de la agenda -> fragmentos (normalizados) del nombre del curso en Canvas.
COURSE_KEYWORDS = {
    "juego": ("juego infantil",),
    "habilidades": ("habilidades sociales",),
    "saac": ("sistemas aumentativos", "saac"),
    "mediacion": ("mediacion comunitaria",),
    "apoyo": ("apoyo a la intervencion",),
    "practicas": ("formacion en empresa", "ffe"),
}

EXTRA_COLORS = ("#5BB5B0", "#D9A441", "#7C8CD8", "#C46F6F", "#6FA35E")

_lock = threading.Lock()
_jar = CookieJar()  # La sesión de Canvas se mantiene solo en memoria.


class CanvasError(RuntimeError):
    """Error de sincronización con un mensaje apto para la interfaz."""


class CanvasAuthError(CanvasError):
    """MEDAC ha rechazado el usuario o la contraseña."""


# ---------------------------------------------------------------- HTTP


class _FormParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.forms: list[dict] = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "form":
            self.forms.append({"action": attrs.get("action"), "inputs": {}})
        elif tag == "input" and self.forms and attrs.get("name"):
            self.forms[-1]["inputs"][attrs["name"]] = attrs.get("value") or ""


def _forms(page: str) -> list[dict]:
    parser = _FormParser()
    parser.feed(page)
    return parser.forms


_opener = build_opener(HTTPCookieProcessor(_jar))


def _request(url: str, data: dict | None = None, accept: str = "text/html") -> tuple[str, str]:
    body = urlencode(data).encode() if data is not None else None
    request = Request(url, data=body, headers={"User-Agent": USER_AGENT, "Accept": accept})
    try:
        with _opener.open(request, timeout=TIMEOUT) as response:
            return response.geturl(), response.read().decode("utf-8", "replace")
    except HTTPError as error:
        if error.code in (401, 403):
            raise PermissionError(error.code) from error
        raise CanvasError(f"El Aula Virtual ha respondido con un error {error.code}.") from error
    except (URLError, TimeoutError, OSError) as error:
        raise CanvasError("No se ha podido conectar con el Aula Virtual. Comprueba tu conexión a Internet.") from error


def _login(credentials: tuple[str, str]) -> None:
    _jar.clear()
    user, password = credentials
    _, page = _request(LOGIN_URL)
    csrf = next((f["inputs"].get("_csrf_token") for f in _forms(page) if "_csrf_token" in f["inputs"]), None)
    if not csrf:
        raise CanvasError("No se ha podido leer el formulario de acceso de MEDAC.")
    url, _ = _request(LOGIN_URL, {"username": user, "password": password, "_csrf_token": csrf})
    if "/login" in url:
        raise CanvasAuthError("MEDAC ha rechazado el usuario o la contraseña.")

    url, page = _request(CANVAS_URL + "/")
    for _ in range(4):  # Formularios SAML que el navegador enviaría solo.
        form = next((f for f in _forms(page) if "SAMLResponse" in f["inputs"]), None)
        if not form:
            break
        url, page = _request(urljoin(url, form["action"] or url), form["inputs"])
    if not url.startswith(CANVAS_URL):
        raise CanvasError("No se ha podido completar el acceso al Aula Virtual.")


def _api_get(path: str, params: dict | None = None) -> list | dict:
    """GET a la API de Canvas siguiendo la paginación (cabecera Link)."""
    url = API + path + ("?" + urlencode(params, doseq=True) if params else "")
    results: list = []
    while url:
        request = Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
        try:
            with _opener.open(request, timeout=TIMEOUT) as response:
                link = response.headers.get("Link", "")
                text = response.read().decode("utf-8", "replace")
        except HTTPError as error:
            if error.code in (401, 403):
                raise PermissionError(error.code) from error
            raise CanvasError(f"La API del Aula Virtual ha respondido con un error {error.code}.") from error
        except (URLError, TimeoutError, OSError) as error:
            raise CanvasError("Se ha perdido la conexión con el Aula Virtual.") from error
        data = json.loads(text.removeprefix("while(1);"))
        if not isinstance(data, list):
            return data
        results.extend(data)
        match = re.search(r'<([^>]+)>;\s*rel="next"', link)
        url = match.group(1) if match else None
    return results


def _fetch(credentials: tuple[str, str], open_grading: set[str]) -> list[dict]:
    """Descarga cursos activos con sus tareas. Reintenta el login si la sesión caducó.

    Para las tareas con algo por corregir (o con un recordatorio de corrección aún
    abierto en la agenda) se descarga también el resumen de entregas.
    """
    for attempt in range(2):
        try:
            courses = _api_get("/courses", {"enrollment_state": "active", "per_page": 100})
            for course in courses:
                course["assignments"] = _api_get(
                    f"/courses/{course['id']}/assignments",
                    {"per_page": 100, "include[]": "submission"},
                )
                for assignment in course["assignments"]:
                    if assignment.get("needs_grading_count") or str(assignment["id"]) in open_grading:
                        assignment["summary"] = _api_get(
                            f"/courses/{course['id']}/assignments/{assignment['id']}/submission_summary"
                        )
            return courses
        except PermissionError:
            if attempt:
                raise CanvasError("El Aula Virtual no ha aceptado la sesión.")
            _login(credentials)
    return []


# ---------------------------------------------------------------- volcado a la agenda


def _norm(value: str) -> str:
    value = unicodedata.normalize("NFKD", value or "").encode("ascii", "ignore").decode()
    return re.sub(r"\s+", " ", value.lower()).strip()


_STOPWORDS = {"tarea", "de", "la", "el", "los", "las", "y", "a", "en", "del", "para", "con", "un", "una"}


def _words(value: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", _norm(value))) - _STOPWORDS


def _plain(html_text: str | None, limit: int = 1500) -> str:
    text = re.sub(r"<(br|/p|/li|/div)[^>]*>", "\n", html_text or "", flags=re.I)
    text = html.unescape(re.sub(r"<[^>]+>", "", text))
    text = re.sub(r"\n\s*\n+", "\n\n", text).strip()
    return text[:limit] + ("…" if len(text) > limit else "")


def week_monday(iso_day: str) -> str:
    day = date.fromisoformat(iso_day)
    return date.fromordinal(day.toordinal() - day.weekday()).isoformat()


def _local_due(value: str) -> tuple[str, str]:
    moment = datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone()
    return moment.date().isoformat(), moment.strftime("%H:%M")


def _link(conn, kind: str, canvas_id) -> sqlite3.Row | None:
    return conn.execute(
        "SELECT * FROM canvas_links WHERE kind = ? AND canvas_id = ?", (kind, str(canvas_id))
    ).fetchone()


def _save_link(conn, kind: str, canvas_id, local_id: int, meta: str = "") -> None:
    conn.execute(
        "INSERT INTO canvas_links (kind, canvas_id, local_id, meta) VALUES (?, ?, ?, ?) "
        "ON CONFLICT(kind, canvas_id) DO UPDATE SET local_id = excluded.local_id, meta = excluded.meta",
        (kind, str(canvas_id), local_id, meta),
    )


def _subject_for(conn, course: dict, has_items: bool) -> int | None:
    link = _link(conn, "course", course["id"])
    if link:
        if conn.execute("SELECT 1 FROM subjects WHERE id = ?", (link["local_id"],)).fetchone():
            return link["local_id"]
        return None  # La asignatura se borró en la agenda: el curso se ignora.

    name = _norm(course.get("name", ""))
    subjects = conn.execute("SELECT id, slug, name FROM subjects").fetchall()
    for row in subjects:
        keywords = COURSE_KEYWORDS.get(row["slug"], ()) + (_norm(row["name"]),)
        if any(keyword and keyword in name for keyword in keywords):
            _save_link(conn, "course", course["id"], row["id"])
            return row["id"]
    if not has_items:
        return None

    full = (course.get("name") or "Curso del Aula Virtual").strip()
    short = full.split(" - ")[0].strip()[:40]
    order = conn.execute("SELECT COALESCE(MAX(sort_order), 0) + 1 FROM subjects").fetchone()[0]
    cursor = conn.execute(
        "INSERT INTO subjects (slug, name, short_name, course, color, icon, is_area, sort_order) "
        "VALUES (?, ?, ?, ?, ?, '◇', 0, ?)",
        (f"canvas-{course['id']}", full, short, course.get("course_code") or "",
         EXTRA_COLORS[order % len(EXTRA_COLORS)], order),
    )
    _save_link(conn, "course", course["id"], cursor.lastrowid)
    return cursor.lastrowid


def _sync_assignment(conn, assignment: dict, subject_id: int, role: str, today: str, now: str, stats: dict) -> None:
    due_date, due_time = _local_due(assignment["due_at"])
    title = (assignment.get("name") or "Tarea del Aula Virtual").strip()[:200]
    description = _plain(assignment.get("description"))
    if assignment.get("html_url"):
        description = (description + "\n\n" if description else "") + "Aula Virtual: " + assignment["html_url"]

    link = _link(conn, "assignment", assignment["id"])
    if link:
        if not conn.execute("SELECT 1 FROM tasks WHERE id = ?", (link["local_id"],)).fetchone():
            return  # La borraste en la agenda: no se vuelve a crear.
        # Canvas manda en título y fechas. La descripción solo se sustituye si no la
        # has escrito tú (vacía o generada por la sincronización, con el enlace).
        current = conn.execute("SELECT description FROM tasks WHERE id = ?", (link["local_id"],)).fetchone()
        sql = "title = ?, due_date = ?, due_time = ?, subject_id = ?"
        args = [title, due_date, due_time, subject_id]
        if not current["description"].strip() or "Aula Virtual: " in current["description"]:
            sql += ", description = ?"
            args.append(description)
        fields = [part.split(" = ")[0] for part in sql.split(", ")]
        changed = conn.execute(
            f"UPDATE tasks SET {sql}, updated_at = ? WHERE id = ? AND ("
            + " OR ".join(f"{field} IS NOT ?" for field in fields) + ")",
            (*args, now, link["local_id"], *args),
        ).rowcount
        stats["updated"] += changed
        return

    # ¿Ya existe en la agenda (creada a mano o de una copia restaurada)? Se vincula sin duplicar.
    candidates = conn.execute(
        "SELECT id, title, due_time FROM tasks WHERE subject_id = ? AND due_date = ? "
        "AND id NOT IN (SELECT local_id FROM canvas_links WHERE kind = 'assignment')",
        (subject_id, due_date),
    ).fetchall()
    same = [row for row in candidates if _norm(row["title"]) == _norm(title)]
    if not same:
        words = _words(title)
        same = [row for row in candidates if row["due_time"] == due_time and words & _words(row["title"])]
        same = same if len(same) == 1 else []
    if same:
        _save_link(conn, "assignment", assignment["id"], same[0]["id"], "manual")
        stats["linked"] += 1
        return _sync_assignment(conn, assignment, subject_id, role, today, now, {**stats, "updated": 0})

    # Profesora: es la entrega de su alumnado. Alumna: es su propia entrega.
    target = "docente" if role == "student" else "alumno"
    submitted = (assignment.get("submission") or {}).get("workflow_state") in ("submitted", "graded")
    done = due_date < today or (role == "student" and submitted)
    cursor = conn.execute(
        "INSERT INTO tasks (title, description, subject_id, kind, target, priority, status, due_date, due_time, "
        "created_at, updated_at, completed_at) VALUES (?, ?, ?, 'entrega', ?, 'media', ?, ?, ?, ?, ?, ?)",
        (title, description, subject_id, target, "completada" if done else "pendiente",
         due_date, due_time, now, now, now if done else None),
    )
    _save_link(conn, "assignment", assignment["id"], cursor.lastrowid)
    stats["created"] += 1


def _sync_grading(conn, assignment: dict, subject_id: int, today: str, now: str, stats: dict) -> None:
    pending = int(assignment.get("needs_grading_count") or 0)
    link = _link(conn, "grading", assignment["id"])
    row = conn.execute("SELECT * FROM reminders WHERE id = ?", (link["local_id"],)).fetchone() if link else None
    if pending == 0 and (row is None or row["done"]):
        return  # Nada que corregir y nada abierto en la agenda: ni se consulta.

    summary = assignment.get("summary") or {}
    progress = json.dumps({key: int(summary.get(key) or 0) for key in ("graded", "ungraded", "not_submitted")})
    title = f"Corregir «{(assignment.get('name') or 'tarea').strip()}»"[:200]

    if pending == 0:
        conn.execute(
            "UPDATE reminders SET title = ?, progress = ?, done = 1, done_at = ?, updated_at = ? WHERE id = ?",
            (title, progress, now, now, row["id"]),
        )
        _save_link(conn, "grading", assignment["id"], row["id"], "0")
        stats["grading_done"] += 1
        return

    if row is None:
        cursor = conn.execute(
            "INSERT INTO reminders (title, body, subject_id, reminder_date, category, progress, created_at, updated_at) "
            "VALUES (?, ?, ?, ?, 'corregir', ?, ?, ?)",
            (title, "Aula Virtual: " + (assignment.get("html_url") or CANVAS_URL), subject_id, today, progress, now, now),
        )
        _save_link(conn, "grading", assignment["id"], cursor.lastrowid, str(pending))
        stats["grading"] += 1
        return

    previous = int(link["meta"] or 0)
    if row["done"] and pending <= previous:
        # Ya la diste por corregida y no han llegado entregas nuevas: solo se refrescan los números.
        conn.execute("UPDATE reminders SET progress = ? WHERE id = ? AND progress IS NOT ?", (progress, row["id"], progress))
        return
    # Sigue pendiente: se mantiene en la semana actual con los números al día.
    changed = conn.execute(
        "UPDATE reminders SET title = ?, progress = ?, reminder_date = ?, done = 0, done_at = NULL, updated_at = ? "
        "WHERE id = ? AND (title IS NOT ? OR progress IS NOT ? OR reminder_date < ? OR done = 1)",
        (title, progress, today, now, row["id"], title, progress, week_monday(today)),
    ).rowcount
    _save_link(conn, "grading", assignment["id"], row["id"], str(pending))
    stats["grading"] += changed


def _apply(conn: sqlite3.Connection, courses: list[dict]) -> dict:
    today = date.today().isoformat()
    now = datetime.now().replace(microsecond=0).isoformat()
    stats = {"courses": 0, "created": 0, "linked": 0, "updated": 0, "grading": 0, "grading_done": 0}
    for course in courses:
        roles = {e.get("type") for e in course.get("enrollments") or []}
        role = "teacher" if roles & {"teacher", "ta"} else "student"
        dated = [a for a in course.get("assignments", []) if a.get("due_at")]
        grading = [a for a in course.get("assignments", []) if role == "teacher" and "needs_grading_count" in a]
        subject_id = _subject_for(conn, course, bool(dated))
        if subject_id is None:
            continue
        stats["courses"] += 1
        for assignment in dated:
            _sync_assignment(conn, assignment, subject_id, role, today, now, stats)
        for assignment in grading:
            _sync_grading(conn, assignment, subject_id, today, now, stats)
    return stats


def _set_setting(conn, key: str, value: str) -> None:
    conn.execute(
        "INSERT INTO settings (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value = excluded.value",
        (key, value),
    )


def status(conn: sqlite3.Connection) -> dict:
    rows = dict(conn.execute("SELECT key, value FROM settings WHERE key LIKE 'canvas_%'").fetchall())
    return {
        "running": _lock.locked(),
        "last_sync": rows.get("canvas_last_sync"),
        "last_error": rows.get("canvas_last_error") or None,
        "last_result": json.loads(rows["canvas_last_result"]) if rows.get("canvas_last_result") else None,
    }


def _open_grading(database: str) -> set[str]:
    conn = sqlite3.connect(database, timeout=15)
    try:
        rows = conn.execute(
            "SELECT l.canvas_id FROM canvas_links l JOIN reminders r ON r.id = l.local_id "
            "WHERE l.kind = 'grading' AND r.done = 0"
        ).fetchall()
        return {row[0] for row in rows}
    finally:
        conn.close()


def verify_login(username: str, password: str) -> None:
    """Comprueba las credenciales contra MEDAC y deja abierta la sesión de Canvas.

    Lanza CanvasAuthError si las rechaza o CanvasError si no se puede conectar.
    """
    if not _lock.acquire(timeout=120):
        raise CanvasError("Hay una sincronización en curso. Espera un momento y vuelve a intentarlo.")
    try:
        _login((username, password))
    finally:
        _lock.release()


def sync(database: str, credentials: tuple[str, str]) -> dict:
    """Descarga el Aula Virtual y vuelca los datos. Devuelve un resumen."""
    if not _lock.acquire(blocking=False):
        return {"status": "busy"}
    try:
        try:
            courses = _fetch(credentials, _open_grading(database))
            error = None
            try:
                profile = _api_get("/users/self")
                display_name = (profile.get("short_name") or profile.get("name") or "").strip()
            except Exception:  # noqa: BLE001 - el saludo no es imprescindible
                display_name = ""
        except CanvasAuthError:
            raise
        except CanvasError as exc:
            courses, error = None, str(exc)

        conn = sqlite3.connect(database, timeout=15)
        conn.row_factory = sqlite3.Row
        try:
            conn.execute("PRAGMA foreign_keys = ON")
            now = datetime.now().replace(microsecond=0).isoformat()
            if error:
                _set_setting(conn, "canvas_last_error", error)
                conn.commit()
                raise CanvasError(error)
            with conn:
                result = _apply(conn, courses)
                _set_setting(conn, "canvas_last_sync", now)
                _set_setting(conn, "canvas_last_error", "")
                _set_setting(conn, "canvas_last_result", json.dumps(result))
                if display_name:
                    _set_setting(conn, "display_name", display_name[:60])
            return {"status": "ok", "synced_at": now, **result}
        finally:
            conn.close()
    finally:
        _lock.release()
