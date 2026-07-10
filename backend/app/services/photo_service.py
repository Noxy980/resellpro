"""AI Photo Studio — enhancement + background cleanup."""

from __future__ import annotations

import io
import uuid
from pathlib import Path

from PIL import Image, ImageEnhance, ImageFilter, ImageOps

OUTPUT_DIR = Path(__file__).resolve().parent.parent.parent.parent / "data" / "enhanced_photos"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def _remove_background_simple(img: Image.Image) -> Image.Image:
    """Light background cleanup — replace near-white/dark edges with clean white."""
    img = img.convert("RGBA")
    pixels = img.load()
    w, h = img.size

    # Sample corners for background color
    corners = [pixels[0, 0], pixels[w - 1, 0], pixels[0, h - 1], pixels[w - 1, h - 1]]
    bg_r = sum(c[0] for c in corners) // 4
    bg_g = sum(c[1] for c in corners) // 4
    bg_b = sum(c[2] for c in corners) // 4

    threshold = 40
    for y in range(h):
        for x in range(w):
            r, g, b, a = pixels[x, y]
            dist = abs(r - bg_r) + abs(g - bg_g) + abs(b - bg_b)
            if dist < threshold:
                pixels[x, y] = (255, 255, 255, 255)

    return img.convert("RGB")


def _try_rembg(img: Image.Image) -> Image.Image | None:
    try:
        from rembg import remove
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        result = remove(buf.getvalue())
        return Image.open(io.BytesIO(result)).convert("RGB")
    except Exception:
        return None


def enhance_photo(
    image_bytes: bytes,
    *,
    brightness: float = 1.1,
    contrast: float = 1.15,
    sharpness: float = 1.4,
    saturation: float = 1.05,
    remove_bg: bool = False,
    auto_level: bool = True,
) -> tuple[str, bytes]:
    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")

    if remove_bg:
        rembg_result = _try_rembg(img)
        if rembg_result:
            img = rembg_result
        else:
            img = _remove_background_simple(img)

    if auto_level:
        img = ImageOps.autocontrast(img, cutoff=1)

    img = ImageEnhance.Brightness(img).enhance(brightness)
    img = ImageEnhance.Contrast(img).enhance(contrast)
    img = ImageEnhance.Color(img).enhance(saturation)
    img = ImageEnhance.Sharpness(img).enhance(sharpness)
    img = img.filter(ImageFilter.MedianFilter(size=3))
    img = ImageEnhance.Sharpness(img).enhance(1.2)

    filename = f"{uuid.uuid4().hex}.jpg"
    out_path = OUTPUT_DIR / filename
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=93, optimize=True)
    result_bytes = buf.getvalue()
    out_path.write_bytes(result_bytes)
    return str(out_path), result_bytes
