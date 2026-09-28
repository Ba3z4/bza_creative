from pathlib import Path
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / ".tools"))
import imageio_ffmpeg
from PIL import Image, ImageDraw, ImageFont, ImageOps

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "dist" / "assets"
OUT = ASSETS / "brand-kit" / "reels"
OUT.mkdir(parents=True, exist_ok=True)

W, H = 1080, 1920
IVORY = "#f4f1e9"
GREEN = "#073f39"
RED = "#df3023"
INK = "#151515"
FONT_BOLD = Path(r"C:\Windows\Fonts\arialbd.ttf")
FONT_REGULAR = Path(r"C:\Windows\Fonts\arial.ttf")


def font(size, bold=False):
    return ImageFont.truetype(str(FONT_BOLD if bold else FONT_REGULAR), size)


def wrap(draw, text, face, max_width):
    words = text.split()
    lines, current = [], ""
    for word in words:
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


def text_slide(kicker, title, details, number, dark=False):
    bg = GREEN if dark else IVORY
    fg = IVORY if dark else INK
    im = Image.new("RGB", (W, H), bg)
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, 28, H), fill=RED)
    d.ellipse((840, -100, 1160, 220), fill=RED)
    d.text((90, 110), "BZA CREATIVE", font=font(34, True), fill=RED)
    d.text((90, 245), kicker.upper(), font=font(30, True), fill=RED)
    y = 390
    title_face = font(84, True)
    for line in wrap(d, title, title_face, 890):
        d.text((90, y), line, font=title_face, fill=fg)
        y += 102
    y += 55
    detail_face = font(42)
    for detail in details:
        d.ellipse((94, y + 18, 110, y + 34), fill=RED)
        lines = wrap(d, detail, detail_face, 820)
        for idx, line in enumerate(lines):
            d.text((135, y + idx * 56), line, font=detail_face, fill=fg)
        y += max(84, len(lines) * 56 + 30)
    d.text((90, 1760), f"{number} / 04", font=font(28, True), fill=RED)
    return im


def image_slide(source, headline, number):
    base = Image.open(source).convert("RGB")
    base = ImageOps.fit(base, (W, H), method=Image.Resampling.LANCZOS)
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    od.rectangle((0, 0, W, H), fill=(4, 45, 40, 105))
    od.rectangle((0, 1250, W, H), fill=(4, 45, 40, 225))
    result = Image.alpha_composite(base.convert("RGBA"), overlay).convert("RGB")
    d = ImageDraw.Draw(result)
    d.text((75, 105), "BZA CREATIVE", font=font(34, True), fill=IVORY)
    y = 1340
    title_face = font(72, True)
    for line in wrap(d, headline, title_face, 930):
        d.text((75, y), line, font=title_face, fill=IVORY)
        y += 88
    d.text((75, 1760), f"{number} / 04", font=font(28, True), fill=RED)
    return result


REELS = [
    {
        "name": "reel-operacion-digital",
        "image": ASSETS / "app-development-hero.png",
        "slides": [
            ("Pregunta", "¿Tu negocio sigue dependiendo de hojas, chats y tareas manuales?", [], False),
            ("Oportunidad", "Una aplicación puede ordenar la operación.", ["Menos pasos repetidos", "Información disponible", "Procesos conectados"], True),
            ("Producto", "Android. Windows. macOS.", ["La plataforma se elige según usuarios, procesos e integraciones."], False),
        ],
        "image_headline": "Escribe SISTEMA y cuéntanos qué quieres mejorar.",
    },
    {
        "name": "reel-sitio-corporativo",
        "image": ASSETS / "creative-web-v2.png",
        "slides": [
            ("Primera impresión", "Tu sitio tiene cinco segundos.", [], True),
            ("Debe responder", "¿Qué haces? ¿Para quién? ¿Por qué confiar?", [], False),
            ("Diseño estratégico", "Claridad antes que decoración.", ["Mensaje", "Jerarquía", "Siguiente paso"], True),
        ],
        "image_headline": "Escribe CLARIDAD y revisamos la primera pantalla.",
    },
    {
        "name": "reel-proyecto-grande",
        "image": ASSETS / "creative-studio-v2.png",
        "slides": [
            ("Proyectos grandes", "La claridad viene antes que la velocidad.", [], False),
            ("Descubrimiento", "Primero entendemos el problema.", ["Usuarios", "Operación", "Integraciones", "Resultado esperado"], True),
            ("Ejecución", "Estrategia. UX/UI. Ingeniería.", ["Etapas visibles y decisiones revisables."], False),
        ],
        "image_headline": "Escribe MAPA y definimos el punto de partida.",
    },
]


ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
for reel in REELS:
    slide_files = []
    for index, (kicker, title, details, dark) in enumerate(reel["slides"], start=1):
        slide = text_slide(kicker, title, details, index, dark)
        path = OUT / f"{reel['name']}-{index}.png"
        slide.save(path, optimize=True)
        slide_files.append(path)
    final_slide = image_slide(reel["image"], reel["image_headline"], 4)
    final_path = OUT / f"{reel['name']}-4.png"
    final_slide.save(final_path, optimize=True)
    slide_files.append(final_path)

    args = [ffmpeg, "-y"]
    for path in slide_files:
        args += ["-loop", "1", "-framerate", "30", "-t", "2.7", "-i", str(path)]
    chains = [f"[{i}:v]fps=30,scale={W}:{H},format=yuv420p[v{i}]" for i in range(4)]
    chains.append("[v0][v1][v2][v3]concat=n=4:v=1:a=0,fade=t=in:st=0:d=0.25,fade=t=out:st=10.3:d=0.45[out]")
    output = OUT / f"{reel['name']}.mp4"
    args += ["-filter_complex", ";".join(chains), "-map", "[out]", "-t", "10.8", "-c:v", "libx264", "-preset", "medium", "-crf", "21", "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(output)]
    subprocess.run(args, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print(f"Created {output.relative_to(ROOT)}")
