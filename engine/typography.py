import numpy as np
from PIL import Image, ImageDraw, ImageFont
import arabic_reshaper
from bidi.algorithm import get_display

_RESHAPER = arabic_reshaper.ArabicReshaper(
    configuration={
        "delete_harakat": False,
        "support_ligatures": False,
        "shift_harakat_position": False,
    }
)

def _has_arabic(text: str) -> bool:
    return any(0x0600 <= ord(ch) <= 0x08FF or 0xFB50 <= ord(ch) <= 0xFEFF for ch in text)

def _format_text(text: str, use_raqm: bool) -> str:
    has_ar = _has_arabic(text)
    if has_ar and use_raqm:
        return text
    reshaped = _RESHAPER.reshape(text) if has_ar else text
    return get_display(reshaped, base_dir="R") if has_ar else reshaped

def _draw_single_line(
    canvas: Image.Image,
    line_text: str,
    font: ImageFont.FreeTypeFont,
    use_raqm: bool,
    fill: tuple,
    center_x: int,
    target_y: int,
    progress: float,
    slide_px: int,
    font_size: int,
):
    rendered_str = _format_text(line_text, use_raqm)
    pad = max(12, font_size // 2)
    probe = Image.new("RGBA", (10, 10), (0, 0, 0, 0))
    pdraw = ImageDraw.Draw(probe)

    draw_kwargs = {"font": font, "fill": (*fill, 255)}
    bbox_kwargs = {"font": font}
    if use_raqm:
        draw_kwargs["direction"] = "rtl"
        draw_kwargs["language"] = "ar"
        bbox_kwargs["direction"] = "rtl"
        bbox_kwargs["language"] = "ar"

    bbox = pdraw.textbbox((0, 0), rendered_str, **bbox_kwargs)
    tw = max(1, bbox[2] - bbox[0])
    th = max(1, bbox[3] - bbox[1])

    layer = Image.new("RGBA", (tw + pad * 2, th + pad * 2), (0, 0, 0, 0))
    ldraw = ImageDraw.Draw(layer)
    ldraw.text((pad - bbox[0], pad - bbox[1]), rendered_str, **draw_kwargs)

    arr = np.array(layer, dtype=np.uint8)
    lh = arr.shape[0]
    visible_h = max(1, int(lh * progress))
    if visible_h < lh:
        arr[: lh - visible_h, :, 3] = 0

    masked = Image.fromarray(arr, mode="RGBA")
    x = center_x - (masked.width // 2)
    y = target_y + int(slide_px * (1.0 - progress)) - pad
    canvas.alpha_composite(masked, dest=(x, y))

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
    line_spacing: float = 1.25,
):
    progress = max(0.0, min(1.0, progress))
    if progress <= 0.0 or not text:
        return

    lines = [ln for ln in text.splitlines() if ln.strip()] or [text]
    has_ar = any(_has_arabic(ln) for ln in lines)
    use_raqm = bool(has_ar and hasattr(ImageFont, "Layout") and hasattr(ImageFont.Layout, "RAQM"))
    font = ImageFont.truetype(font_path, font_size, layout_engine=ImageFont.Layout.RAQM if use_raqm else None)

    step_y = int(font_size * line_spacing)
    for idx, line in enumerate(lines):
        _draw_single_line(
            canvas=canvas,
            line_text=line,
            font=font,
            use_raqm=use_raqm,
            fill=fill,
            center_x=center_x,
            target_y=target_y + idx * step_y,
            progress=progress,
            slide_px=slide_px,
            font_size=font_size,
        )
