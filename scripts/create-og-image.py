"""Genera la imagen para compartir enlaces (Open Graph), 1200×630.

Uso: python scripts/create-og-image.py
"""
from pathlib import Path
import importlib.util

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("block", ROOT / "scripts" / "create-block-02.py")
block = importlib.util.module_from_spec(spec)
spec.loader.exec_module(block)

W, H = 1200, 630
image = Image.new("RGB", (W, H), block.GREEN)
draw = ImageDraw.Draw(image)
for x in range(0, W + 1, 105):
    draw.line((x, 0, x, H), fill="#174C48", width=2)
for y in range(0, H + 1, 105):
    draw.line((0, y, W, y), fill="#174C48", width=2)
block.star(draw, 110, 112, 46)
draw.text((186, 66), "BZA CREATIVE", font=block.font(46, True), fill=block.PAPER)
draw.line((72, 190, 1128, 190), fill=block.RED, width=5)
draw.text((72, 250), "Diseño web, aplicaciones", font=block.font(68, True), fill=block.PAPER)
draw.text((72, 334), "y publicidad digital.", font=block.font(68, True), fill=block.RED)
draw.text((72, 452), "Sitios y campañas que convierten búsquedas en conversaciones.", font=block.font(32), fill=block.SOFT)
draw.text((72, 548), "GUADALAJARA · MÉXICO", font=block.font(26, True), fill=block.SOFT)
label = "bzacreative.com"
width = draw.textbbox((0, 0), label, font=block.font(30, True))[2]
draw.text((W - 72 - width, 544), label, font=block.font(30, True), fill=block.PAPER)
out = ROOT / "dist" / "assets" / "og-bza-creative.png"
image.save(out, optimize=True)
print(f"Created {out.relative_to(ROOT)}")
