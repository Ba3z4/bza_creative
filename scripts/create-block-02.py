"""Genera las piezas del bloque 2 de contenido (26 oct – 21 nov 2026).

Salida: dist/assets/brand-kit/bloque-02/ (imágenes 1080×1350 y Reels 1080×1920).
Uso: python scripts/create-block-02.py
"""
from pathlib import Path
import shutil
import subprocess

from PIL import Image, ImageDraw, ImageFont, ImageOps

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "dist" / "assets"
OUT = ASSETS / "brand-kit" / "bloque-02"

PAPER = "#F7F7F5"
INK = "#171717"
GREEN = "#083D3A"
RED = "#D92E22"
MUTED = "#666660"
SOFT = "#B9CBC9"
W, H = 1080, 1350

FONT_CANDIDATES = {
    False: ["C:/Windows/Fonts/arial.ttf", "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
            "/Library/Fonts/Arial.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"],
    True: ["C:/Windows/Fonts/arialbd.ttf", "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
           "/Library/Fonts/Arial Bold.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"],
}


def font(size, bold=False):
    for candidate in FONT_CANDIDATES[bold]:
        if Path(candidate).exists():
            return ImageFont.truetype(candidate, size)
    raise FileNotFoundError("No se encontró Arial ni Liberation Sans")


def wrap(draw, text, face, max_width):
    lines, current = [], ""
    for word in text.split():
        candidate = f"{current} {word}".strip()
        if draw.textbbox((0, 0), candidate, font=face)[2] <= max_width:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def star(draw, cx, cy, radius, color=RED, width=14):
    arm = radius * .72
    draw.line((cx, cy - radius, cx, cy + radius), fill=color, width=width)
    draw.line((cx - radius, cy, cx + radius, cy), fill=color, width=width)
    draw.line((cx - arm, cy - arm, cx + arm, cy + arm), fill=color, width=width)
    draw.line((cx - arm, cy + arm, cx + arm, cy - arm), fill=color, width=width)


def base(dark=False):
    image = Image.new("RGB", (W, H), GREEN if dark else PAPER)
    draw = ImageDraw.Draw(image)
    color = "#174C48" if dark else "#E5E5DF"
    for x in range(0, W + 1, 135):
        draw.line((x, 0, x, H), fill=color, width=2)
    for y in range(0, H + 1, 135):
        draw.line((0, y, W, y), fill=color, width=2)
    star(draw, 104, 104, 47)
    draw.text((178, 57), "BZA CREATIVE", font=font(46, True), fill=PAPER if dark else GREEN)
    draw.line((72, 185, 1008, 185), fill=RED, width=5)
    return image, draw


def title(draw, lines, y, dark=False, size=78, accent_last=True):
    face = font(size, True)
    for index, line in enumerate(lines):
        last = index == len(lines) - 1
        color = RED if (accent_last and last) else (PAPER if dark else INK)
        for part in wrap(draw, line, face, 936):
            draw.text((72, y), part, font=face, fill=color)
            y += int(size * 1.18)
    return y


def cta(draw, keyword, dark=False, label="ESCRÍBENOS POR MENSAJE"):
    draw.text((72, 1214), label, font=font(26, True), fill=SOFT if dark else MUTED)
    face = font(40, True)
    box = draw.textbbox((0, 0), keyword, font=face)
    width = box[2] - box[0]
    draw.rounded_rectangle((72, 1252, 72 + width + 56, 1316), radius=32, fill=RED)
    draw.text((100, 1262), keyword, font=face, fill=PAPER)
    draw.text((1008 - draw.textbbox((0, 0), "bzacreative.com", font=font(26, True))[2], 1272),
              "bzacreative.com", font=font(26, True), fill=SOFT if dark else MUTED)


def bullets(draw, items, y, dark=False, size=46, check=True, gap=52):
    face = font(size)
    for item in items:
        if check:
            draw.rounded_rectangle((72, y + 4, 126, y + 58), radius=10, outline=RED, width=5)
            draw.line((85, y + 31, 98, y + 44, 115, y + 16), fill=RED, width=6)
        else:
            draw.ellipse((84, y + 20, 106, y + 42), fill=RED)
        lines = wrap(draw, item, face, 820)
        for index, line in enumerate(lines):
            draw.text((150, y + index * int(size * 1.3)), line, font=face, fill=PAPER if dark else INK)
        y += max(60, len(lines) * int(size * 1.3)) + gap
    return y


def steps(draw, items, y, dark=False):
    for index, (heading, detail) in enumerate(items, start=1):
        draw.ellipse((72, y, 142, y + 70), outline=RED, width=5)
        draw.text((90, y + 17), f"{index:02d}", font=font(25, True), fill=PAPER if dark else INK)
        draw.text((180, y - 3), heading, font=font(48, True), fill=PAPER if dark else INK)
        draw.text((180, y + 56), detail, font=font(30), fill=SOFT if dark else MUTED)
        if index != len(items):
            draw.line((107, y + 78, 107, y + 168), fill="#48716E" if dark else "#CFCFC8", width=4)
        y += 190
    return y


def card_list(name, lines, items, keyword, dark=False, check=True, kicker=None):
    image, draw = base(dark)
    y = 250
    if kicker:
        draw.text((72, y), kicker.upper(), font=font(28, True), fill=RED)
        y += 60
    y = title(draw, lines, y, dark)
    bullets(draw, items, y + 90, dark, check=check)
    cta(draw, keyword, dark)
    image.save(OUT / f"{name}.png", optimize=True)


def card_steps(name, lines, items, keyword, dark=True, kicker=None):
    image, draw = base(dark)
    y = 250
    if kicker:
        draw.text((72, y), kicker.upper(), font=font(28, True), fill=RED)
        y += 60
    y = title(draw, lines, y, dark)
    steps(draw, items, y + 70, dark)
    cta(draw, keyword, dark)
    image.save(OUT / f"{name}.png", optimize=True)


def card_statement(name, lines, detail, keyword, dark=False, kicker=None, size=96):
    image, draw = base(dark)
    y = 300
    if kicker:
        draw.text((72, y), kicker.upper(), font=font(28, True), fill=RED)
        y += 70
    y = title(draw, lines, y, dark, size=size)
    face = font(40)
    y += 50
    for line in wrap(draw, detail, face, 900):
        draw.text((72, y), line, font=face, fill=SOFT if dark else MUTED)
        y += 54
    cta(draw, keyword, dark)
    image.save(OUT / f"{name}.png", optimize=True)


def card_compare(name, lines, left, right, keyword):
    image, draw = base(False)
    y = title(draw, lines, 250, size=70)
    top = y + 50
    columns = [(72, left, "#FFFFFF", INK, MUTED), (552, right, GREEN, PAPER, SOFT)]
    for x, (heading, items), fill, ink, muted in columns:
        draw.rectangle((x, top, x + 456, 1150), fill=fill, outline="#DEDBD2", width=2)
        draw.text((x + 32, top + 30), heading.upper(), font=font(30, True), fill=RED)
        yy = top + 100
        for item in items:
            for index, line in enumerate(wrap(draw, item, font(36, True), 392)):
                draw.text((x + 32, yy + index * 46), line, font=font(36, True), fill=ink)
            yy += len(wrap(draw, item, font(36, True), 392)) * 46 + 50
    cta(draw, keyword)
    image.save(OUT / f"{name}.png", optimize=True)


def card_search(name, query, lines, items, keyword):
    image, draw = base(True)
    draw.rounded_rectangle((72, 260, 1008, 360), radius=50, fill=PAPER)
    draw.ellipse((112, 290, 152, 330), outline=GREEN, width=6)
    draw.line((146, 324, 166, 344), fill=GREEN, width=7)
    draw.text((190, 288), query, font=font(40), fill=INK)
    y = title(draw, lines, 440, dark=True, size=70)
    bullets(draw, items, y + 50, dark=True, check=False)
    cta(draw, keyword, dark=True)
    image.save(OUT / f"{name}.png", optimize=True)


def card_funnel(name, lines, stages, keyword):
    image, draw = base(False)
    y = title(draw, lines, 250, size=84)
    y += 50
    widths = [936, 800, 664, 528]
    for index, (label, color) in enumerate(stages):
        width = widths[index]
        x = 72 + (936 - width) // 2
        draw.rectangle((x, y, x + width, y + 120), fill=color)
        face = font(40, True)
        text_width = draw.textbbox((0, 0), label, font=face)[2]
        draw.text((540 - text_width // 2, y + 38), label, font=face, fill=INK if color in (PAPER, "#DEDBD2") else PAPER)
        y += 140
    cta(draw, keyword)
    image.save(OUT / f"{name}.png", optimize=True)


def carousel_cover(name, kicker, lines, detail, total, dark=False):
    image, draw = base(dark)
    draw.text((72, 300), kicker.upper(), font=font(30, True), fill=RED)
    y = title(draw, lines, 370, dark, size=104)
    face = font(42)
    y += 40
    for line in wrap(draw, detail, face, 900):
        draw.text((72, y), line, font=face, fill=SOFT if dark else MUTED)
        y += 56
    draw.text((72, 1262), f"DESLIZA  →   1 / {total}", font=font(30, True), fill=RED)
    image.save(OUT / f"{name}.png", optimize=True)


def carousel_slide(name, number, total, lines, items, dark=False, keyword=None, check=False, size=78):
    image, draw = base(dark)
    y = title(draw, lines, 290, dark, size=size)
    bullets(draw, items, y + 90, dark, check=check)
    if keyword:
        cta(draw, keyword, dark)
    else:
        draw.text((72, 1262), f"{number} / {total}", font=font(30, True), fill=RED)
    image.save(OUT / f"{name}.png", optimize=True)


# Reels -------------------------------------------------------------------
RW, RH = 1080, 1920
IVORY = "#f4f1e9"


def reel_text(kicker, heading, details, number, dark=False):
    bg, fg = (GREEN, IVORY) if dark else (IVORY, INK)
    image = Image.new("RGB", (RW, RH), bg)
    draw = ImageDraw.Draw(image)
    draw.rectangle((0, 0, 28, RH), fill=RED)
    draw.ellipse((840, -100, 1160, 220), fill=RED)
    draw.text((90, 110), "BZA CREATIVE", font=font(34, True), fill=RED)
    draw.text((90, 245), kicker.upper(), font=font(30, True), fill=RED)
    y = 390
    face = font(84, True)
    for line in wrap(draw, heading, face, 890):
        draw.text((90, y), line, font=face, fill=fg)
        y += 102
    y += 55
    face = font(42)
    for detail in details:
        draw.ellipse((94, y + 18, 110, y + 34), fill=RED)
        lines = wrap(draw, detail, face, 820)
        for index, line in enumerate(lines):
            draw.text((135, y + index * 56), line, font=face, fill=fg)
        y += max(84, len(lines) * 56 + 30)
    draw.text((90, 1760), f"{number} / 04", font=font(28, True), fill=RED)
    return image


def reel_image(source, headline, number):
    picture = ImageOps.fit(Image.open(source).convert("RGB"), (RW, RH), method=Image.Resampling.LANCZOS)
    overlay = Image.new("RGBA", (RW, RH), (0, 0, 0, 0))
    layer = ImageDraw.Draw(overlay)
    layer.rectangle((0, 0, RW, RH), fill=(4, 45, 40, 105))
    layer.rectangle((0, 1250, RW, RH), fill=(4, 45, 40, 225))
    result = Image.alpha_composite(picture.convert("RGBA"), overlay).convert("RGB")
    draw = ImageDraw.Draw(result)
    draw.text((75, 105), "BZA CREATIVE", font=font(34, True), fill=IVORY)
    y = 1340
    face = font(72, True)
    for line in wrap(draw, headline, face, 930):
        draw.text((75, y), line, font=face, fill=IVORY)
        y += 88
    draw.text((75, 1760), f"{number} / 04", font=font(28, True), fill=RED)
    return result


def ffmpeg_path():
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except ImportError:
        found = shutil.which("ffmpeg")
        if not found:
            raise SystemExit("Se necesita ffmpeg o imageio-ffmpeg para crear los Reels")
        return found


def reel(name, slides, image_source, headline):
    files = []
    for index, (kicker, heading, details, dark) in enumerate(slides, start=1):
        path = OUT / f"{name}-{index}.png"
        reel_text(kicker, heading, details, index, dark).save(path, optimize=True)
        files.append(path)
    path = OUT / f"{name}-4.png"
    reel_image(image_source, headline, 4).save(path, optimize=True)
    files.append(path)
    args = [ffmpeg_path(), "-y"]
    for path in files:
        args += ["-loop", "1", "-framerate", "30", "-t", "2.7", "-i", str(path)]
    chains = [f"[{i}:v]fps=30,scale={RW}:{RH},format=yuv420p[v{i}]" for i in range(4)]
    chains.append("[v0][v1][v2][v3]concat=n=4:v=1:a=0,fade=t=in:st=0:d=0.25,fade=t=out:st=10.3:d=0.45[out]")
    args += ["-filter_complex", ";".join(chains), "-map", "[out]", "-t", "10.8", "-c:v", "libx264",
             "-preset", "medium", "-crf", "21", "-pix_fmt", "yuv420p", "-movflags", "+faststart",
             str(OUT / f"{name}.mp4")]
    subprocess.run(args, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def main():
    OUT.mkdir(parents=True, exist_ok=True)

    # b2-01 · carrusel Google o Facebook
    carousel_cover("b2-01-1", "Antes de invertir", ["¿Google", "o Facebook?"],
                   "Dónde conviene anunciar primero un negocio de servicios.", 3)
    carousel_slide("b2-01-2", 2, 3, ["Google", "captura demanda."],
                   ["La persona ya busca lo que vendes", "Llega con un proyecto en mente",
                    "Necesita una página que convierta"], dark=True)
    carousel_slide("b2-01-3", 3, 3, ["Facebook e Instagram", "crean demanda."],
                   ["Llegas a quien aún no te busca", "Construyes confianza y recordación",
                    "Vuelves a encontrar a quien ya te visitó"], keyword="GOOGLE")

    # b2-02 · después del clic
    card_list("b2-02", ["El anuncio trae la visita.", "La página decide si te escriben."],
              ["Una promesa clara", "Pruebas de que sabes hacerlo", "Un siguiente paso evidente"], "LANDING")

    # b2-03 · medir conversaciones
    card_funnel("b2-03", ["Los me gusta", "no pagan la renta."],
                [("Mensajes", "#DEDBD2"), ("Conversaciones calificadas", GREEN), ("Propuestas", "#48716E"),
                 ("Clientes", RED)], "MEDIR")

    # b2-04 · Reel Google vs Facebook
    reel("b2-04-reel-google-facebook", [
        ("Pregunta", "¿Dónde anuncio primero?", [], False),
        ("Si ya te buscan", "Google.", ["Búsquedas con intención", "Pagas por clic", "Necesita una buena landing"], True),
        ("Si aún no te conocen", "Facebook e Instagram.", ["Alcance local", "Confianza", "Retargeting"], False),
    ], ASSETS / "creative-loop.png", "Escribe EMPEZAR y te decimos por dónde iniciar.")

    # b2-05 · carrusel señales del sitio
    carousel_cover("b2-05-1", "Revisión rápida", ["5 señales de que", "tu sitio pierde", "clientes."],
                   "Si marcas dos o más, hay oportunidades claras.", 3, dark=True)
    carousel_slide("b2-05-2", 2, 3, ["Señales 1 a 3"],
                   ["No se entiende qué haces en cinco segundos", "El contacto está escondido",
                    "En el celular se ve mal o tarda en cargar"], check=True)
    carousel_slide("b2-05-3", 3, 3, ["Señales 4 y 5"],
                   ["No hay pruebas de tu trabajo", "No sabes cuántas personas te escriben desde ahí"],
                   dark=True, keyword="REVISAR", check=True)

    # b2-06 · presupuesto inicial
    card_steps("b2-06", ["¿Cuánto invertir", "al empezar?"],
               [("Un canal", "No dividas poco presupuesto en cinco"),
                ("Cuatro semanas", "Tiempo mínimo antes de juzgar"),
                ("Costo por conversación", "La métrica que decide, no el clic")], "PRESUPUESTO")

    # b2-07 · búsqueda local
    card_search("b2-07", "remodelaciones cerca de mí", ["Cuando te buscan en", "tu ciudad, ¿te encuentran?"],
                ["Una página que diga qué haces y dónde", "Información consistente en Google",
                 "Anuncios de búsqueda bien segmentados"], "LOCAL")

    # b2-08 · Buen Fin
    card_list("b2-08", ["Buen Fin:", "no improvises tus anuncios."],
              ["Prepara la página antes de pagar", "Oferta clara y fecha límite real",
               "Etiqueta cada enlace para medir"], "BUENFIN", dark=True)

    # b2-09 · retargeting
    card_statement("b2-09", ["Casi nadie te escribe", "en la primera visita."],
                   "El retargeting vuelve a mostrar tu marca a quien ya visitó tu sitio o interactuó con tus redes.",
                   "VOLVER", kicker="Retargeting")

    # b2-10 · ordenar una oferta
    card_compare("b2-10", ["Una oferta clara", "decide más que un buen diseño."],
                 ("Antes", ["“Hacemos de todo”", "“Precios a consultar”", "“Contáctanos”"]),
                 ("Después", ["El problema que resuelves", "Rangos de inversión claros", "Un siguiente paso concreto"]),
                 "OFERTA")

    # b2-11 · Reel errores de landing
    reel("b2-11-reel-errores-landing", [
        ("3 errores", "Tu anuncio recibe clics, pero nadie escribe.", [], True),
        ("Errores 1 y 2", "Así se pierde la visita.", ["Enviar el anuncio a la portada",
                                                      "Pedir demasiados datos antes de conversar"], False),
        ("Error 3", "No saber qué anuncio trajo cada mensaje.", ["Sin etiquetas UTM no hay aprendizaje"], True),
    ], ASSETS / "app-development-hero.png", "Escribe ERRORES y revisamos tu página.")

    # b2-12 · apps
    card_statement("b2-12", ["Si tu operación vive en", "chats y hojas de cálculo,", "una app puede ordenarla."],
                   "Diseñamos y desarrollamos aplicaciones para Android, Windows y macOS.", "OPERAR",
                   dark=True, size=74)

    # b2-13 · planear 2027
    card_steps("b2-13", ["Enero se gana", "en noviembre."],
               [("Noviembre", "Diagnóstico y plan"), ("Diciembre", "Diseño, contenido y medición"),
                ("Enero", "Lanzamiento con todo listo")], "2027", dark=False)

    # b2-14 · diagnóstico de cierre
    card_list("b2-14", ["Diagnóstico de", "cierre de año."],
              ["Tu oferta", "Tu sitio", "Tu contenido", "Cómo mides los contactos"], "CIERRE", dark=True,
              kicker="Llamada de 30 minutos")

    for path in sorted(OUT.iterdir()):
        print(f"Created {path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
