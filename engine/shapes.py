from PIL import Image, ImageDraw
from .easing import ease_out_cubic

def draw_rounded_card(
    canvas: Image.Image,
    box: tuple[int, int, int, int],
    radius: int,
    fill_rgba: tuple[int, int, int, int],
    border_rgba: tuple[int, int, int, int] | None = None,
    border_width: int = 2,
):
    x0, y0, x1, y1 = box
    if x1 <= x0 or y1 <= y0:
        return
    layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    draw.rounded_rectangle([x0, y0, x1, y1], radius=radius, fill=fill_rgba, outline=border_rgba, width=border_width)
    canvas.alpha_composite(layer)

def draw_accent_bar(
    canvas: Image.Image,
    center_x: int,
    y: int,
    max_width: int,
    height: int,
    progress: float,
    color_rgba: tuple[int, int, int, int],
):
    p = ease_out_cubic(progress)
    w = int(max_width * p)
    if w <= 2:
        return
    layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    x0 = center_x - w // 2
    x1 = center_x + w // 2
    draw.rounded_rectangle([x0, y, x1, y + height], radius=max(2, height // 2), fill=color_rgba)
    canvas.alpha_composite(layer)

def draw_progress_meter(
    canvas: Image.Image,
    x: int,
    y: int,
    width: int,
    height: int,
    progress: float,
    bg_rgba: tuple[int, int, int, int],
    fg_rgba: tuple[int, int, int, int],
):
    p = ease_out_cubic(progress)
    layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    r = max(3, height // 2)
    draw.rounded_rectangle([x, y, x + width, y + height], radius=r, fill=bg_rgba)
    fill_w = max(r * 2, int(width * p)) if p > 0.01 else 0
    if fill_w > 0:
        draw.rounded_rectangle([x, y, min(x + width, x + fill_w), y + height], radius=r, fill=fg_rgba)
    canvas.alpha_composite(layer)

def draw_badge_icon(
    canvas: Image.Image,
    cx: int,
    cy: int,
    radius: int,
    kind: str,
    circle_rgba: tuple[int, int, int, int],
    icon_rgba: tuple[int, int, int, int],
):
    layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    draw.ellipse([cx - radius, cy - radius, cx + radius, cy + radius], fill=circle_rgba)

    s = max(6, radius // 2)
    if kind == "bolt":
        pts = [
            (cx + s // 3, cy - s),
            (cx - s // 2, cy + s // 8),
            (cx + s // 8, cy + s // 8),
            (cx - s // 3, cy + s),
            (cx + s // 2, cy - s // 8),
            (cx - s // 8, cy - s // 8),
        ]
        draw.polygon(pts, fill=icon_rgba)
    elif kind == "check":
        draw.line([(cx - s // 2, cy), (cx - s // 8, cy + s // 2)], fill=icon_rgba, width=max(3, radius // 6))
        draw.line([(cx - s // 8, cy + s // 2), (cx + s // 2, cy - s // 2)], fill=icon_rgba, width=max(3, radius // 6))
    else:
        draw.polygon([(cx - s // 2, cy - s // 2), (cx + s // 2, cy), (cx - s // 2, cy + s // 2)], fill=icon_rgba)

    canvas.alpha_composite(layer)
