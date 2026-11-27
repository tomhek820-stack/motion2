import arabic_reshaper
from bidi.algorithm import get_display
from PIL import Image, ImageDraw, ImageFont

_RESHAPER = arabic_reshaper.ArabicReshaper(
    configuration={
        "delete_harakat": False,
        "support_ligatures": True,
        "shift_harakat_position": False,
    }
)

def shape_ar(text: str) -> str:
    reshaped = _RESHAPER.reshape(text)
    try:
        return get_display(reshaped, upper_is_rtl=False, base_dir="R")
    except TypeError:
        return get_display(reshaped)

def draw_masked_text(
    canvas: Image.Image,
    text: str,
    font_path: str,
    font_size: int,
    fill: tuple,
    center_x: int,
    target_y: int,
    progress: float,
    slide_px: int = 28,
):
    progress = max(0.0, min(1.0, progress))
    font = ImageFont.truetype(font_path, font_size)
    shaped = shape_ar(text)

    layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)

    bbox = draw.textbbox((0, 0), shaped, font=font)
    w = bbox[2] - bbox[0]
    h = bbox[3] - bbox[1]

    x = center_x - w // 2
    y = target_y + int(slide_px * (1.0 - progress))

    draw.text((x - bbox[0], y - bbox[1]), shaped, font=font, fill=(*fill, 255))

    mask = Image.new("L", canvas.size, 0)
    mdraw = ImageDraw.Draw(mask)
    visible_h = int(h * progress) + 18
    mdraw.rectangle(
        [x - 40, target_y + h - visible_h, x + w + 40, target_y + h + 40],
        fill=255,
    )

    layer.putalpha(mask)
    canvas.alpha_composite(layer)
