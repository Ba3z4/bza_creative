from pathlib import Path
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


def base(color=PAPER):
    image = Image.new("RGB", (1080, 1350), color)
    draw = ImageDraw.Draw(image)
    for x in range(0, 1081, 135):
        draw.line((x, 0, x, 1350), fill="#E6E6E0" if color == PAPER else "#174C48", width=2)
    for y in range(0, 1351, 135):
        draw.line((0, y, 1080, y), fill="#E6E6E0" if color == PAPER else "#174C48", width=2)
    return image, draw


def brand_header(draw, dark=False):
    fg = PAPER if dark else GREEN
    star(draw, 105, 105, 48)
    draw.text((180, 57), "BZA CREATIVE", font=font(46, True), fill=fg)
    draw.line((72, 185, 1008, 185), fill=RED, width=5)


def slide_one(out):
    image, draw = base()
    brand_header(draw)
    draw.text((72, 330), "Tu marca", font=font(112, True), fill=INK)
    draw.text((72, 455), "merece claridad.", font=font(112, True), fill=GREEN)
    draw.text((75, 655), "Diseñamos experiencias digitales que\nexplican, conectan y convierten.", font=font(48), fill=MUTED, spacing=18)
    draw.rounded_rectangle((72, 1030, 650, 1150), radius=5, fill=RED)
    draw.text((115, 1064), "CONOCE BZA CREATIVE", font=font(31, True), fill=PAPER)
    draw.text((72, 1240), "01 / 03", font=font(25, True), fill=MUTED)
    image.save(out / "intro-01.png", quality=95)


def slide_two(out):
    image, draw = base(GREEN)
    brand_header(draw, dark=True)
    draw.text((72, 290), "Lo que hacemos", font=font(92, True), fill=PAPER)
    services = [
        ("01", "Diseño y desarrollo web"),
        ("02", "Publicidad digital"),
        ("03", "Contenido y creatividad"),
    ]
    y = 505
    for number, label in services:
        draw.text((75, y), number, font=font(30, True), fill=RED)
        draw.text((175, y-12), label, font=font(50, True), fill=PAPER)
        draw.line((75, y+92, 1005, y+92), fill="#48716E", width=2)
        y += 210
    draw.text((72, 1240), "02 / 03", font=font(25, True), fill="#AFC1BF")
    image.save(out / "intro-02.png", quality=95)


def slide_three(out):
    image, draw = base()
    brand_header(draw)
    star(draw, 540, 410, 130, width=28)
    draw.text((128, 625), "Empecemos con un", font=font(78, True), fill=INK)
    draw.text((175, 720), "diagnóstico inicial.", font=font(78, True), fill=GREEN)
    draw.text((215, 875), "Cuéntanos qué quieres lograr y te\npropondremos el siguiente paso.", font=font(41), fill=MUTED, spacing=15, align="center")
    draw.rounded_rectangle((235, 1060, 845, 1180), radius=5, fill=RED)
    draw.text((302, 1094), "ESCRÍBENOS: INICIO", font=font(32, True), fill=PAPER)
    draw.text((72, 1240), "03 / 03", font=font(25, True), fill=MUTED)
    image.save(out / "intro-03.png", quality=95)


def main():
    out = Path(__file__).resolve().parents[1] / "dist" / "assets" / "brand-kit" / "profile-carousel"
    out.mkdir(parents=True, exist_ok=True)
    slide_one(out)
    slide_two(out)
    slide_three(out)
    print(f"Created carousel in {out}")


if __name__ == "__main__":
    main()
