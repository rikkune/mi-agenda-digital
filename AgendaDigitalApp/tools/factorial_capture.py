"""Captura las peticiones que hace la web de Factorial (solo para calibrar la agenda).

Uso (desde la carpeta AgendaDigitalApp, sin la ventana de Factorial de la agenda abierta):
    .venv\\Scripts\\python.exe tools\\factorial_capture.py

Se abre un Microsoft Edge normal con el perfil de la agenda (data/factorial-profile):
1. Inicia sesión en Factorial con Microsoft (si no lo estabas ya).
2. Cuando estés dentro, la captura empieza sola: ve a la pantalla de fichaje y
   ficha como siempre (entrada, descanso o salida).
3. Cierra la ventana de Edge.

Se guarda en data/factorial-capture.jsonl: método, URL, estado, cabeceras y cuerpos
JSON (recortados). Los valores de cookies y tokens se ocultan.
"""

from __future__ import annotations

import json
import sys
import time
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from playwright.sync_api import sync_playwright  # noqa: E402

from app.services.factorial import close_edge, launch_edge, page_urls, wait_for_session  # noqa: E402

BASE = Path(__file__).resolve().parent.parent / "data"
PROFILE = BASE / "factorial-profile"
OUTPUT = BASE / "factorial-capture.jsonl"
SECRET_HEADERS = ("cookie", "authorization", "x-csrf-token", "x-xsrf-token", "x-api-key")
MAX_BODY = 4000


def _headers(headers: dict) -> dict:
    return {k: ("<oculto>" if k.lower() in SECRET_HEADERS else v) for k, v in headers.items()}


def main() -> int:
    process, port = launch_edge(PROFILE, hidden=False)
    print("Edge abierto. Inicia sesión en Factorial (tienes 10 minutos)...")
    if not wait_for_session(process, port, timeout=600):
        print("No se ha llegado a Factorial con la sesión iniciada.")
        close_edge(process)
        return 1
    print("Sesión detectada. Captura en marcha: ficha como siempre y cierra Edge al terminar.")

    out = OUTPUT.open("a", encoding="utf-8")

    def on_response(response):
        request = response.request
        if request.resource_type not in ("xhr", "fetch"):
            return
        if not request.url.split("/")[2].endswith("factorialhr.com"):
            return
        body = None
        try:
            if "json" in (response.headers.get("content-type") or ""):
                body = response.text()[:MAX_BODY]
        except Exception:  # noqa: BLE001 - algunas respuestas no tienen cuerpo legible
            pass
        entry = {
            "at": datetime.now().isoformat(timespec="seconds"),
            "method": request.method,
            "url": request.url,
            "status": response.status,
            "request_headers": _headers(request.headers),
            "request_body": (request.post_data or "")[:MAX_BODY] or None,
            "response_body": body,
        }
        out.write(json.dumps(entry, ensure_ascii=False) + "\n")
        out.flush()
        if request.method != "GET":
            print(f"  {request.method} {request.url} -> {response.status}")

    with sync_playwright() as playwright:
        browser = playwright.chromium.connect_over_cdp(f"http://127.0.0.1:{port}")
        for context in browser.contexts:
            context.on("response", on_response)
        while process.poll() is None and page_urls(port) is not None:
            time.sleep(1)
    out.close()
    close_edge(process)
    print(f"Captura guardada en {OUTPUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
