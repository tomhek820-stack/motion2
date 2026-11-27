import math
from PIL import Image, ImageDraw
from engine.project_config import load_project_config
from engine.typography import draw_masked_text
from engine.easing import ease_out_cubic, ease_in_out_cubic, spring_damped
from engine.shapes import draw_rounded_card, draw_accent_bar, draw_progress_meter, draw_badge_icon

_CFG = load_project_config()

def _apply_subtle_camera(frame_rgba: Image.Image, t: float, zoom_amount: float = 0.035) -> Image.Image:
    w, h = frame_rgba.size
    scale = 1.0 + zoom_amount * math.sin(t * math.pi)
    nw = max(w, int(round(w * scale)))
    nh = max(h, int(round(h * scale)))
    zoomed = frame_rgba.resize((nw, nh), Image.Resampling.BILINEAR)
    left = max(0, (nw - w) // 2)
    top = max(0, (nh - h) // 2)
    return zoomed.crop((left, top, left + w, top + h))

def render_scene_frame(scene_idx: int, t: float, width: int, height: int) -> Image.Image:
    theme = _CFG.get("theme", {})
    bg_color = tuple(theme.get("bg_color", [11, 15, 25]))
    primary_text = tuple(theme.get("primary_text", [248, 250, 252]))
    accent_color = tuple(theme.get("accent_color", [56, 189, 248]))
    secondary_accent = tuple(theme.get("secondary_accent", [16, 185, 129]))
    font_path = theme.get("font_path", "assets/fonts/Cairo-Bold.ttf")

    intro_cfg = _CFG.get("intro", {})
    outro_cfg = _CFG.get("outro", {})

    canvas = Image.new("RGBA", (width, height), (*bg_color, 255))
    cx, cy = width // 2, height // 2

    title_sz = max(34, int(height * 0.066))
    sub_sz = max(22, int(height * 0.036))
    body_sz = max(20, int(height * 0.032))

    draw_progress_meter(
        canvas,
        int(width * 0.10),
        int(height * 0.05),
        int(width * 0.80),
        max(5, int(height * 0.007)),
        progress=t,
        bg_rgba=(255, 255, 255, 22),
        fg_rgba=(*accent_color, 220),
    )

    if scene_idx == 0:
        p_card = ease_out_cubic((t - 0.05) / 0.30)
        cw, ch = int(width * 0.80), int(height * 0.58)
        draw_rounded_card(
            canvas,
            (cx - cw // 2, cy - ch // 2 + int(18 * (1 - p_card)), cx + cw // 2, cy + ch // 2 + int(18 * (1 - p_card))),
            radius=28,
            fill_rgba=(255, 255, 255, int(18 * p_card)),
            border_rgba=(255, 255, 255, int(36 * p_card)),
        )
        draw_masked_text(canvas, intro_cfg.get("title", "محرك موشن جرافيك برمجي احترافي"), font_path, title_sz, primary_text, cx, int(height * 0.35), ease_out_cubic((t - 0.10) / 0.30))
        draw_accent_bar(canvas, cx, int(height * 0.46), int(width * 0.32), max(4, int(height * 0.006)), (t - 0.22) / 0.28, (*accent_color, 255))
        draw_masked_text(canvas, intro_cfg.get("subtitle", "إنتاج متكامل 45-120 ثانية بالصوت والحركة والخط العربي"), font_path, sub_sz, accent_color, cx, int(height * 0.53), ease_out_cubic((t - 0.30) / 0.30))

    elif scene_idx == 1:
        draw_masked_text(canvas, "منظومة متكاملة بدون مفاتيح API", font_path, title_sz, primary_text, cx, int(height * 0.14), ease_out_cubic(t / 0.22))
        rows = [
            ("اختبار سريع مباشر داخل Termux", "bolt", 0.94, 0.14, accent_color),
            ("نصوص عربية متصلة واتجاه صحيح", "check", 1.00, 0.28, secondary_accent),
            ("تصيير سحابي عالي الدقة على GitHub", "play", 0.96, 0.42, accent_color),
        ]
        row_h = int(height * 0.16)
        start_y = int(height * 0.27)
        cw = int(width * 0.78)
        x0 = (width - cw) // 2
        x1 = x0 + cw

        for idx, (label, kind, ratio, st, col) in enumerate(rows):
            p = ease_out_cubic((t - st) / 0.32)
            y0 = start_y + idx * (row_h + int(height * 0.03)) + int(20 * (1 - p))
            y1 = y0 + row_h
            if p > 0:
                draw_rounded_card(canvas, (x0, y0, x1, y1), 20, (255, 255, 255, int(16 * p)), (255, 255, 255, int(30 * p)))
                draw_badge_icon(canvas, x1 - int(cw * 0.07), y0 + row_h // 2, max(18, int(row_h * 0.26)), kind, (*col, int(235 * p)), (*bg_color, int(255 * p)))
                draw_masked_text(canvas, label, font_path, body_sz, primary_text, x0 + int(cw * 0.58), y0 + int(row_h * 0.16), p)
                draw_progress_meter(canvas, x0 + int(cw * 0.26), y0 + int(row_h * 0.65), int(cw * 0.64), max(8, int(height * 0.010)), p * ratio, (255, 255, 255, int(28 * p)), (*col, int(255 * p)))

    elif scene_idx == 2:
        draw_masked_text(canvas, "معدلات الأداء والمرونة البرمجية", font_path, title_sz, primary_text, cx, int(height * 0.15), ease_out_cubic(t / 0.22))
        cards = [
            ("60 إطار في الثانية", "سلاسة حركة في التصيير النهائي", 0.15, accent_color),
            ("45 - 120 ثانية", "مدة مرنة للفيديوهات الكاملة", 0.30, secondary_accent),
            ("صوت وموسيقى", "دمج تلقائي ومؤثرات انتقال", 0.45, accent_color),
        ]
        gap = int(width * 0.03)
        total_w = int(width * 0.84)
        bw = (total_w - gap * 2) // 3
        bh = int(height * 0.44)
        by = int(height * 0.32)
        base_x = (width - total_w) // 2

        for i, (metric, desc, st, col) in enumerate(cards):
            p = spring_damped((t - st) / 0.45)
            bx = base_x + i * (bw + gap)
            by_anim = by + int(26 * (1 - p))
            if p > 0.01:
                draw_rounded_card(canvas, (bx, by_anim, bx + bw, by_anim + bh), 24, (255, 255, 255, int(18 * min(1.0, p))), (*col, int(90 * min(1.0, p))))
                draw_accent_bar(canvas, bx + bw // 2, by_anim + int(bh * 0.16), int(bw * 0.45), 5, min(1.0, p), (*col, 255))
                draw_masked_text(canvas, metric, font_path, sub_sz, col, bx + bw // 2, by_anim + int(bh * 0.34), min(1.0, p))
                draw_masked_text(canvas, desc, font_path, max(18, int(height * 0.026)), primary_text, bx + bw // 2, by_anim + int(bh * 0.58), min(1.0, p))

    elif scene_idx == 3:
        draw_masked_text(canvas, "خط إنتاج منظم من الكود إلى الفيديو", font_path, title_sz, primary_text, cx, int(height * 0.15), ease_out_cubic(t / 0.22))
        steps = [
            "1. ضبط السيناريو والسمات في config/project.json",
            "2. توليد الإطارات والرسوم والنصوص العربية",
            "3. دمج الانتقالات والصوت والموسيقى عبر FFmpeg",
            "4. تصيير النسخة النهائية ورفعها كـ Artifact",
        ]
        for i, s_txt in enumerate(steps):
            p = ease_out_cubic((t - (0.12 + i * 0.14)) / 0.28)
            sy = int(height * 0.30) + i * int(height * 0.125)
            draw_masked_text(canvas, s_txt, font_path, body_sz, primary_text if i < 3 else secondary_accent, cx, sy, p)

    elif scene_idx == 4:
        draw_masked_text(canvas, "دقة هندسية وتحكم كامل بكل إطار", font_path, title_sz, primary_text, cx, int(height * 0.15), ease_out_cubic(t / 0.22))
        pulse = 1.0 + 0.08 * math.sin(t * math.pi * 4.0)
        r_outer = int(min(width, height) * 0.15 * pulse)
        layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
        d = ImageDraw.Draw(layer)
        d.ellipse([cx - r_outer, cy + int(height * 0.03) - r_outer, cx + r_outer, cy + int(height * 0.03) + r_outer], outline=(*accent_color, 190), width=5)
        r_inner = int(r_outer * 0.65)
        d.ellipse([cx - r_inner, cy + int(height * 0.03) - r_inner, cx + r_inner, cy + int(height * 0.03) + r_inner], fill=(*secondary_accent, 75))
        canvas.alpha_composite(layer)
        draw_masked_text(canvas, "قابل للتوسع بإضافة مشاهد ومؤثرات جديدة بسهولة", font_path, sub_sz, primary_text, cx, int(height * 0.76), ease_in_out_cubic((t - 0.20) / 0.35))

    else:
        draw_masked_text(canvas, outro_cfg.get("title", "motion2 • محرك إنتاج مرئي متكامل"), font_path, title_sz, primary_text, cx, int(height * 0.36), ease_out_cubic((t - 0.10) / 0.30))
        draw_accent_bar(canvas, cx, int(height * 0.47), int(width * 0.30), max(4, int(height * 0.006)), (t - 0.22) / 0.28, (*secondary_accent, 255))
        draw_masked_text(canvas, outro_cfg.get("subtitle", "اختبار سريع في Termux وتصيير سحابي عبر GitHub Actions"), font_path, sub_sz, accent_color, cx, int(height * 0.53), ease_out_cubic((t - 0.30) / 0.30))

    return _apply_subtle_camera(canvas, t, zoom_amount=0.025).convert("RGB")
