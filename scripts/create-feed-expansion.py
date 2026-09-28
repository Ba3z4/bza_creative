from pathlib import Path
import shutil

from PIL import Image, ImageDraw, ImageFont


PAPER = "#F7F7F5"
INK = "#171717"
GREEN = "#083D3A"
RED = "#D92E22"
MUTED = "#666660"


def font(size: int, bold: bool = False):
    filename = "arialbd.ttf" if bold else "arial.ttf"
    return ImageFont.truetype(str(Path("C:/Windows/Fonts") / filename), size)


def star(draw, cx, cy, radius, color=RED, width=14):
    arm = radius * .72
    draw.line((cx, cy-radius, cx, cy+radius), fill=color, width=width)
    draw.line((cx-radius, cy, cx+radius, cy), fill=color, width=width)
    draw.line((cx-arm, cy-arm, cx+arm, cy+arm), fill=color, width=width)
    draw.line((cx-arm, cy+arm, cx+arm, cy-arm), fill=color, width=width)


def grid(draw, dark=False):
    color = "#174C48" if dark else "#E5E5DF"
    for x in range(0, 1081, 135):
        draw.line((x, 0, x, 1350), fill=color, width=2)
    for y in range(0, 1351, 135):
        draw.line((0, y, 1080, y), fill=color, width=2)


def header(draw, dark=False):
    star(draw, 104, 104, 47)
    draw.text((178, 57), "BZA CREATIVE", font=font(46, True), fill=PAPER if dark else GREEN)
    draw.line((72, 185, 1008, 185), fill=RED, width=5)


def process_card(out):
    image = Image.new("RGB", (1080, 1350), GREEN)
    draw = ImageDraw.Draw(image)
    grid(draw, dark=True)
    header(draw, dark=True)
    draw.text((72, 275), "Un proceso claro.", font=font(84, True), fill=PAPER)
    draw.text((72, 375), "Mejores decisiones.", font=font(84, True), fill=RED)
    steps = [
        ("01", "Descubrir", "Objetivos, público y contexto"),
        ("02", "Diseñar", "Mensaje, experiencia y piezas"),
        ("03", "Activar", "Publicar, medir y mejorar"),
    ]
    y = 575
    for number, title, detail in steps:
        draw.ellipse((72, y, 142, y+70), outline=RED, width=5)
        draw.text((88, y+17), number, font=font(25, True), fill=PAPER)
        draw.text((180, y-3), title, font=font(50, True), fill=PAPER)
        draw.text((180, y+58), detail, font=font(30), fill="#B9CBC9")
        if number != "03":
            draw.line((107, y+78, 107, y+177), fill="#48716E", width=4)
        y += 210
    draw.text((72, 1240), "ENFOQUE BZA  ·  2026", font=font(24, True), fill="#AFC1BF")
    image.save(out / "feed-process.png", quality=95)


def audit_card(out):
    image = Image.new("RGB", (1080, 1350), PAPER)
    draw = ImageDraw.Draw(image)
    grid(draw)
    header(draw)
    draw.text((72, 290), "¿Tu presencia digital", font=font(76, True), fill=INK)
    draw.text((72, 382), "está lista para crecer?", font=font(76, True), fill=GREEN)
    checks = [
        "Tu oferta se entiende en segundos",
        "El sitio guía hacia el contacto",
        "El contenido sigue una estrategia",
        "Puedes medir las conversaciones",
    ]
    y = 570
    for item in checks:
        draw.rectangle((76, y+6, 120, y+50), outline=RED, width=5)
        draw.line((87, y+29, 99, y+41), fill=RED, width=5)
        draw.line((99, y+41, 116, y+17), fill=RED, width=5)
        draw.text((160, y), item, font=font(36, True), fill=INK)
        draw.line((72, y+92, 1008, y+92), fill="#D3D3CD", width=2)
        y += 145
    draw.rounded_rectangle((72, 1112, 780, 1228), radius=5, fill=RED)
    draw.text((111, 1145), "ENVÍANOS DIAGNÓSTICO", font=font(32, True), fill=PAPER)
    image.save(out / "feed-diagnostic.png", quality=95)


def main():
    root = Path(__file__).resolve().parents[1]
    assets = root / "dist" / "assets"
    out = assets / "brand-kit" / "feed"
    out.mkdir(parents=True, exist_ok=True)
    source_map = {
        "creative-studio-v2.png": "feed-identity.png",
        "creative-web-v2.png": "feed-web-example.png",
        "creative-social-v2.png": "feed-content-example.png",
    }
    for source, target in source_map.items():
        shutil.copy2(assets / source, out / target)
    process_card(out)
    audit_card(out)
    print(f"Created feed expansion in {out}")


if __name__ == "__main__":
    main()
