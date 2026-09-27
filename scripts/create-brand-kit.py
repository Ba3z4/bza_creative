from pathlib import Path
import sys

from PIL import Image, ImageDraw, ImageFont, ImageFilter


INK = "#171717"
PAPER = "#F7F7F5"
GREEN = "#083D3A"
RED = "#D92E22"
MUTED = "#666660"


def font(size: int, bold: bool = False):
    name = "arialbd.ttf" if bold else "arial.ttf"
    return ImageFont.truetype(str(Path("C:/Windows/Fonts") / name), size)


def star(draw: ImageDraw.ImageDraw, cx: float, cy: float, radius: float, color: str, width: int):
    arm = radius * 0.72
    draw.line((cx, cy - radius, cx, cy + radius), fill=color, width=width)
    draw.line((cx - radius, cy, cx + radius, cy), fill=color, width=width)
    draw.line((cx - arm, cy - arm, cx + arm, cy + arm), fill=color, width=width)
    draw.line((cx - arm, cy + arm, cx + arm, cy - arm), fill=color, width=width)


def fit_cover(image: Image.Image, size: tuple[int, int]):
    iw, ih = image.size
    tw, th = size
    scale = max(tw / iw, th / ih)
    resized = image.resize((round(iw * scale), round(ih * scale)), Image.Resampling.LANCZOS)
    left = (resized.width - tw) // 2
    top = (resized.height - th) // 2
    return resized.crop((left, top, left + tw, top + th))


def make_avatar(out_dir: Path):
    size = 1080
    image = Image.new("RGB", (size, size), GREEN)
    draw = ImageDraw.Draw(image)
    for pos in range(90, size, 150):
        draw.line((pos, 0, pos, size), fill="#174C48", width=2)
        draw.line((0, pos, size, pos), fill="#174C48", width=2)
    star(draw, 540, 245, 104, RED, 26)
    title = font(260, True)
    box = draw.textbbox((0, 0), "BZA", font=title)
    draw.text(((size - (box[2] - box[0])) / 2, 395), "BZA", font=title, fill=PAPER)
    sub = font(64, False)
    sub_box = draw.textbbox((0, 0), "CREATIVE", font=sub)
    draw.text(((size - (sub_box[2] - sub_box[0])) / 2, 720), "CREATIVE", font=sub, fill=PAPER)
    draw.ellipse((515, 842, 565, 892), fill=RED)
    image.save(out_dir / "profile-avatar.png", quality=95)


def make_horizontal_logo(out_dir: Path):
    image = Image.new("RGBA", (1400, 360), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    star(draw, 170, 180, 130, RED, 22)
    draw.text((350, 76), "BZA", font=font(190, True), fill=GREEN)
    draw.text((745, 128), "creative", font=font(110), fill=INK)
    draw.ellipse((1240, 216, 1270, 246), fill=RED)
    image.save(out_dir / "logo-primary.png")


def make_cover(background: Image.Image, out_dir: Path):
    size = (1640, 624)
    image = fit_cover(background, size).convert("RGB")
    veil = Image.new("RGBA", size, (247, 247, 245, 0))
    vd = ImageDraw.Draw(veil)
    vd.rectangle((0, 0, 950, size[1]), fill=(247, 247, 245, 235))
    veil = veil.filter(ImageFilter.GaussianBlur(10))
    image = Image.alpha_composite(image.convert("RGBA"), veil)
    draw = ImageDraw.Draw(image)
    star(draw, 154, 150, 52, RED, 12)
    draw.text((238, 85), "BZA", font=font(98, True), fill=GREEN)
    draw.text((452, 105), "CREATIVE", font=font(54), fill=INK)
    draw.text((100, 275), "Diseño que conecta.", font=font(64, True), fill=INK)
    draw.text((100, 354), "Estrategia que convierte.", font=font(64, True), fill=GREEN)
    draw.line((100, 474, 800, 474), fill=RED, width=5)
    draw.text((100, 505), "DISEÑO WEB  ·  CONTENIDO  ·  PUBLICIDAD DIGITAL", font=font(25, True), fill=MUTED)
    image.convert("RGB").save(out_dir / "facebook-cover.png", quality=95)


def make_wide_banner(background: Image.Image, out_dir: Path):
    size = (1500, 500)
    image = fit_cover(background, size).convert("RGBA")
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((75, 75, 870, 425), radius=4, fill=(8, 61, 58, 242))
    star(draw, 165, 160, 45, RED, 10)
    draw.text((235, 112), "BZA CREATIVE", font=font(58, True), fill=PAPER)
    draw.text((135, 245), "Buen diseño. Mejores conexiones.", font=font(42), fill=PAPER)
    draw.text((135, 330), "WEB  ·  ADS  ·  CONTENIDO", font=font(24, True), fill="#D8DED8")
    image.convert("RGB").save(out_dir / "brand-banner-wide.png", quality=95)


def write_svgs(out_dir: Path):
    primary = f'''<svg xmlns="http://www.w3.org/2000/svg" width="1400" height="360" viewBox="0 0 1400 360" role="img" aria-labelledby="title desc">
  <title id="title">BZA Creative</title><desc id="desc">Logotipo de BZA Creative con estrella roja</desc>
  <g fill="none" stroke="{RED}" stroke-width="22" stroke-linecap="butt">
    <path d="M170 50v260M40 180h260M78 88l184 184M78 272 262 88"/>
  </g>
  <text x="350" y="230" fill="{GREEN}" font-family="Arial, Helvetica, sans-serif" font-size="190" font-weight="700" letter-spacing="-10">BZA</text>
  <text x="735" y="230" fill="{INK}" font-family="Arial, Helvetica, sans-serif" font-size="112" font-weight="400" letter-spacing="-5">creative</text>
  <circle cx="1245" cy="218" r="15" fill="{RED}"/>
</svg>'''
    mark = f'''<svg xmlns="http://www.w3.org/2000/svg" width="1080" height="1080" viewBox="0 0 1080 1080" role="img" aria-labelledby="title desc">
  <title id="title">Símbolo BZA Creative</title><desc id="desc">Monograma BZA sobre fondo verde con estrella roja</desc>
  <rect width="1080" height="1080" rx="120" fill="{GREEN}"/>
  <g fill="none" stroke="{RED}" stroke-width="27" stroke-linecap="butt">
    <path d="M540 120v220M430 230h220M462 152l156 156M462 308l156-156"/>
  </g>
  <text x="540" y="690" text-anchor="middle" fill="{PAPER}" font-family="Arial, Helvetica, sans-serif" font-size="300" font-weight="700" letter-spacing="-18">BZA</text>
  <text x="540" y="815" text-anchor="middle" fill="{PAPER}" font-family="Arial, Helvetica, sans-serif" font-size="72" letter-spacing="15">CREATIVE</text>
  <circle cx="540" cy="900" r="25" fill="{RED}"/>
</svg>'''
    (out_dir / "logo-primary.svg").write_text(primary, encoding="utf-8")
    (out_dir / "logo-mark.svg").write_text(mark, encoding="utf-8")


def main():
    if len(sys.argv) != 2:
        raise SystemExit("Usage: create-brand-kit.py BACKGROUND_IMAGE")
    background = Image.open(sys.argv[1]).convert("RGB")
    out_dir = Path(__file__).resolve().parents[1] / "dist" / "assets" / "brand-kit"
    out_dir.mkdir(parents=True, exist_ok=True)
    make_avatar(out_dir)
    make_horizontal_logo(out_dir)
    make_cover(background, out_dir)
    make_wide_banner(background, out_dir)
    write_svgs(out_dir)
    background.save(out_dir / "banner-background-generated.png", quality=95)
    print(f"Created brand kit in {out_dir}")


if __name__ == "__main__":
    main()
