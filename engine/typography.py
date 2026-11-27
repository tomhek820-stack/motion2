import arabic_reshaper
from PIL import Image, ImageDraw, ImageFont

_RESHAPER = arabic_reshaper.ArabicReshaper(
    configuration={
        "delete_harakat": False,
        "support_ligatures": False,
        "shift_harakat_position": False,
    }
)

def _is_arabic_char(ch: str) -> bool:
    code = ord(ch)
    return (
        (0x0600 <= code <= 0x06FF)
        or (0x0750 <= code <= 0x077F)
        or (0x08A0 <= code <= 0x08FF)
        or (0xFB50 <= code <= 0xFDFF)
        or (0xFE70 <= code <= 0xFEFF)
    )

def shape_ar(text: str) -> str:
    reshaped = _RESHAPER.reshape(text)
    words = reshaped.split(" ")
    out_words = []
    for w in words:
        if any(_is_arabic_char(c) for c in w):
            # عكس أحرف الكلمة العربية لتظهر من اليمين لليسار عند رسمها LTR في Pillow
            out_words.append(w[::-1])
        else:
            out_words.append(w)
    # عكس ترتيب الكلمات لتبدأ الجملة العربية من اليمين
    return " ".join(reversed(out_words))

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
