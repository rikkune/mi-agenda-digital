"""Genera los iconos de la agenda (ventana, acceso directo y ejecutable).

Uso (solo hace falta al cambiar el diseño):
    .venv\\Scripts\\python.exe tools\\make_icons.py

Necesita Pillow (requirements-build.txt). Dibuja la «M» del logo sobre el mismo
degradado coral → rosa → lila que usa la interfaz.
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "static" / "img" / "icons"
STOPS = [(0.0, (0xFF, 0x7F, 0x7F)), (0.5, (0xE9, 0x89, 0xB4)), (1.0, (0xA7, 0x7A, 0xD8))]


def _color(t: float) -> tuple[int, int, int]:
    for (t0, c0), (t1, c1) in zip(STOPS, STOPS[1:]):
        if t <= t1:
            k = (t - t0) / (t1 - t0)
            return tuple(round(a + (b - a) * k) for a, b in zip(c0, c1))
    return STOPS[-1][1]


def _font(size: int) -> ImageFont.FreeTypeFont:
    for name in ("seguibl.ttf", "arialbd.ttf", "segoeuib.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default(size)


def draw(size: int, padding: float = 0.0) -> Image.Image:
    scale = 4  # Se dibuja grande y se reduce: bordes suaves.
    big = size * scale
    gradient = Image.new("RGB", (big, big))
    pixels = gradient.load()
    for y in range(big):
        for x in range(big):
            pixels[x, y] = _color((x + y) / (2 * (big - 1)))
    inset = round(big * padding)
    mask = Image.new("L", (big, big), 0)
    ImageDraw.Draw(mask).rounded_rectangle(
        (inset, inset, big - inset - 1, big - inset - 1), radius=round((big - 2 * inset) * 0.24), fill=255
    )
    image = Image.new("RGBA", (big, big), (0, 0, 0, 0))
    image.paste(gradient, mask=mask)
    text = ImageDraw.Draw(image)
    font = _font(round((big - 2 * inset) * 0.62))
    box = text.textbbox((0, 0), "M", font=font)
    x = (big - (box[2] - box[0])) / 2 - box[0]
    y = (big - (box[3] - box[1])) / 2 - box[1]
    text.text((x, y), "M", font=font, fill="white")
    return image.resize((size, size), Image.LANCZOS)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for size in (192, 512):
        draw(size).save(OUT / f"icon-{size}.png")
    draw(512, padding=0.1).save(OUT / "icon-maskable-512.png")
    draw(32).save(OUT / "favicon-32.png")
    draw(256).save(OUT / "agenda.ico", sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
    print(f"Iconos generados en {OUT}")


if __name__ == "__main__":
    main()
