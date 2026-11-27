"""Rebuild every UniWay brand image from the single source logo, including the 1200x630 Open Graph preview card.

    python scripts/build_brand_assets.py

Reads ``static/assets/brand/uniway-logo.webp`` (the logo on a transparent background) and writes, next to it:

* ``uniway-mark.webp``   square, transparent, shown wherever the brand mark appears in the page;
* ``favicon.ico`` / ``favicon-16.png`` / ``favicon-32.png``   transparent tab icons;
* ``apple-touch-icon.png``   180px square on white for iOS home screens;
* ``og-image.png``   1200x630 Open Graph / Twitter Card social share preview banner.
"""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

BRAND_DIR = Path(__file__).resolve().parents[1] / "src" / "exchange_info" / "static" / "assets" / "brand"
SOURCE = BRAND_DIR / "uniway-logo.webp"

FONT_CANDIDATES_BOLD = (
    "C:/Windows/Fonts/msjhbd.ttc",
    "C:/Windows/Fonts/NotoSansTC-VF.ttf",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
    "/usr/share/fonts/truetype/noto/NotoSansCJK-Bold.ttc",
)
FONT_CANDIDATES_REG = (
    "C:/Windows/Fonts/msjh.ttc",
    "C:/Windows/Fonts/NotoSansTC-VF.ttf",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
)


def _load_font(candidates: tuple[str, ...], size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for fp in candidates:
        if Path(fp).is_file():
            try:
                return ImageFont.truetype(fp, size=size)
            except OSError:
                continue
    return ImageFont.load_default()


def mark_box(image: Image.Image, threshold: int = 8) -> tuple[int, int, int, int]:
    """Bounding box of everything visible; faint anti-aliasing below ``threshold`` is ignored."""
    box = image.getchannel("A").point(lambda value: 255 if value > threshold else 0).getbbox()
    if box is None:
        raise SystemExit("The source logo is fully transparent; there is nothing to crop around.")
    return box


def framed(image: Image.Image, box: tuple[int, int, int, int], margin: float) -> Image.Image:
    """The mark centred on a transparent square ``margin`` times its larger side (1.0 = touching the edges)."""
    mark = image.crop(box)
    side = round(max(mark.width, mark.height) * margin)
    canvas = Image.new("RGBA", (side, side), (0, 0, 0, 0))
    canvas.paste(mark, ((side - mark.width) // 2, (side - mark.height) // 2))
    return canvas


def resized(tile: Image.Image, size: int) -> Image.Image:
    return tile.resize((size, size), Image.Resampling.LANCZOS)


def on_white(tile: Image.Image) -> Image.Image:
    background = Image.new("RGBA", tile.size, (255, 255, 255, 255))
    background.alpha_composite(tile)
    return background.convert("RGB")


def build_og_image(logo: Image.Image, box: tuple[int, int, int, int]) -> Image.Image:
    """Render a clean, brand-aligned 1200x630 social share preview card."""
    w, h = 1200, 630
    canvas = Image.new("RGBA", (w, h), (242, 247, 253, 255))
    draw = ImageDraw.Draw(canvas)

    # Subtle soft sky gradient bands & decorative soft circles matching UniWay's glass-blue palette
    for y in range(h):
        t = y / (h - 1)
        r = round(238 + (248 - 238) * t)
        g = round(245 + (251 - 245) * t)
        b = round(254 + (255 - 254) * t)
        draw.line([(0, y), (w, y)], fill=(r, g, b, 255))

    accent = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    adraw = ImageDraw.Draw(accent)
    adraw.ellipse((760, -140, 1340, 440), fill=(208, 230, 252, 135))
    adraw.ellipse((-120, 360, 380, 820), fill=(216, 235, 253, 120))
    canvas.alpha_composite(accent)

    # Main elevated white card container
    card_rect = (56, 52, w - 56, h - 52)
    draw = ImageDraw.Draw(canvas)
    draw.rounded_rectangle(card_rect, radius=36, fill=(255, 255, 255, 248), outline=(211, 226, 240, 255), width=2)

    # Left text & badge column
    f_eyebrow = _load_font(FONT_CANDIDATES_BOLD, 22)
    f_brand = _load_font(FONT_CANDIDATES_BOLD, 64)
    f_sub = _load_font(FONT_CANDIDATES_BOLD, 34)
    f_desc = _load_font(FONT_CANDIDATES_REG, 23)
    f_pill = _load_font(FONT_CANDIDATES_BOLD, 20)
    f_url = _load_font(FONT_CANDIDATES_BOLD, 21)

    x_left = 104
    eyebrow_txt = "台灣大學生出國交換規劃平台"
    eb = draw.textbbox((0, 0), eyebrow_txt, font=f_eyebrow)
    ew = (eb[2] - eb[0]) + 40
    draw.rounded_rectangle((x_left, 102, x_left + ew, 148), radius=23, fill=(229, 241, 253, 255))
    draw.text((x_left + 20, 110), eyebrow_txt, font=f_eyebrow, fill=(24, 92, 148, 255))

    draw.text((x_left, 168), "UniWay", font=f_brand, fill=(16, 40, 55, 255))
    draw.text((x_left, 256), "全台 71 校合作名單・申請時程", font=f_sub, fill=(16, 40, 55, 255))
    draw.text((x_left, 306), "免登入換算工具與公開數據庫", font=f_sub, fill=(24, 92, 148, 255))

    draw.text((x_left, 372), "依母校查詢海外姊妹校門檻、名額狀態、預算與官方來源", font=f_desc, fill=(75, 99, 114, 255))

    pills = ("GPA／ECTS 學分換算", "語言門檻選校比對", "預算匯率與獎學金")
    px = x_left
    py = 434
    for text in pills:
        bbox = draw.textbbox((0, 0), text, font=f_pill)
        pw = (bbox[2] - bbox[0]) + 34
        draw.rounded_rectangle((px, py, px + pw, py + 44), radius=22, fill=(242, 247, 252, 255), outline=(206, 222, 237, 255), width=2)
        draw.text((px + 17, py + 9), text, font=f_pill, fill=(22, 56, 76, 255))
        px += pw + 14

    draw.text((x_left, 512), "app.uniway-tw.com  ｜  公開資料免登入・以各校最新官方公告為準", font=f_url, fill=(92, 115, 130, 255))

    # Right brand logo tile
    rx1, rx2 = 816, 1096
    rw = rx2 - rx1
    tile_box = (rx1, 126, rx2, 390)
    draw.rounded_rectangle(tile_box, radius=52, fill=(235, 245, 255, 255), outline=(204, 225, 246, 255), width=2)
    mark_img = resized(framed(logo, box, 1.12), 208)
    canvas.alpha_composite(mark_img, (rx1 + (rw - 208) // 2, 126 + (264 - 208) // 2))

    # Compact stat badge below logo tile
    stat_box = (rx1, 412, rx2, 480)
    draw.rounded_rectangle(stat_box, radius=20, fill=(16, 40, 55, 255))
    stat_txt = "71 所母校 · 4,000+ 合作校"
    sb = draw.textbbox((0, 0), stat_txt, font=f_pill)
    draw.text((rx1 + (rw - (sb[2] - sb[0])) // 2, 433), stat_txt, font=f_pill, fill=(255, 255, 255, 255))

    return canvas.convert("RGB")


def main() -> None:
    logo = Image.open(SOURCE).convert("RGBA")
    box = mark_box(logo)

    mark = resized(framed(logo, box, 1.04), 160)
    mark.save(BRAND_DIR / "uniway-mark.webp", quality=92, alpha_quality=100, method=6)

    icon = framed(logo, box, 1.08)
    resized(icon, 16).save(BRAND_DIR / "favicon-16.png", optimize=True)
    resized(icon, 32).save(BRAND_DIR / "favicon-32.png", optimize=True)
    resized(icon, 256).save(BRAND_DIR / "favicon.ico", sizes=[(16, 16), (32, 32), (48, 48), (64, 64)])
    on_white(resized(framed(logo, box, 1.5), 180)).save(BRAND_DIR / "apple-touch-icon.png", optimize=True)
    build_og_image(logo, box).save(BRAND_DIR / "og-image.png", optimize=True)

    for name in ("uniway-mark.webp", "favicon.ico", "favicon-16.png", "favicon-32.png", "apple-touch-icon.png", "og-image.png"):
        print(f"{name:22} {(BRAND_DIR / name).stat().st_size:>7} bytes")


if __name__ == "__main__":
    main()
