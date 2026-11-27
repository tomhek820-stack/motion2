import math
from PIL import Image, ImageDraw
from engine.theme import BG_COLOR, PRIMARY_TEXT, ACCENT_COLOR, FONT_PATH
from engine.typography import draw_masked_text
from engine.easing import ease_out_cubic, ease_in_out_cubic, spring_damped
from engine.shapes import draw_rounded_card, draw_accent_bar, draw_progress_meter, draw_badge_icon

def render_scene_frame(scene_idx: int, t: float, width: int, height: int) -> Image.Image:
    canvas = Image.new("RGBA", (width, height), (*BG_COLOR, 255))
    cx, cy = width // 2, height // 2

    title_sz = max(34, int(height * 0.066))
    sub_sz = max(22, int(height * 0.036))
    body_sz = max(20, int(height * 0.032))

    # شريط علوي لمؤشر تقدم المشهد
    draw_progress_meter(
        canvas,
        int(width * 0.10),
        int(height * 0.05),
        int(width * 0.80),
        max(5, int(height * 0.007)),
        progress=t,
        bg_rgba=(255, 255, 255, 22),
        fg_rgba=(*ACCENT_COLOR, 220),
    )

    if scene_idx == 0:
        # المشهد 1: الافتتاحية
        p_card = ease_out_cubic((t - 0.05) / 0.30)
        cw, ch = int(width * 0.80), int(height * 0.58)
        draw_rounded_card(
            canvas,
            (cx - cw // 2, cy - ch // 2 + int(18 * (1 - p_card)), cx + cw // 2, cy + ch // 2 + int(18 * (1 - p_card))),
            radius=28,
            fill_rgba=(255, 255, 255, int(18 * p_card)),
            border_rgba=(255, 255, 255, int(36 * p_card)),
        )
        draw_masked_text(canvas, "محرك موشن جرافيك برمجي متكامل", FONT_PATH, title_sz, PRIMARY_TEXT, cx, int(height * 0.35), ease_out_cubic((t - 0.10) / 0.30))
        draw_accent_bar(canvas, cx, int(height * 0.46), int(width * 0.32), max(4, int(height * 0.006)), (t - 0.22) / 0.28, (*ACCENT_COLOR, 255))
        draw_masked_text(canvas, "إنتاج أفلام كاملة 45-120 ثانية مع صوت وموسيقى", FONT_PATH, sub_sz, ACCENT_COLOR, cx, int(height * 0.53), ease_out_cubic((t - 0.30) / 0.30))

    elif scene_idx == 1:
        # المشهد 2: القدرات الأساسية
        draw_masked_text(canvas, "منظومة متكاملة بدون مفاتيح API", FONT_PATH, title_sz, PRIMARY_TEXT, cx, int(height * 0.14), ease_out_cubic(t / 0.22))
        rows = [
            ("اختبار سريع مباشر داخل Termux", "bolt", 0.94, 0.14),
            ("نصوص عربية متصلة واتجاه صحيح", "check", 1.00, 0.28),
            ("تصيير سحابي عالي الدقة على GitHub", "play", 0.96, 0.42),
        ]
        row_h = int(height * 0.16)
        start_y = int(height * 0.27)
        cw = int(width * 0.78)
        x0 = (width - cw) // 2
        x1 = x0 + cw

        for idx, (label, kind, ratio, st) in enumerate(rows):
            p = ease_out_cubic((t - st) / 0.32)
            y0 = start_y + idx * (row_h + int(height * 0.03)) + int(20 * (1 - p))
            y1 = y0 + row_h
            if p > 0:
                draw_rounded_card(canvas, (x0, y0, x1, y1), 20, (255, 255, 255, int(16 * p)), (255, 255, 255, int(30 * p)))
                draw_badge_icon(canvas, x1 - int(cw * 0.07), y0 + row_h // 2, max(18, int(row_h * 0.26)), kind, (*ACCENT_COLOR, int(235 * p)), (*BG_COLOR, int(255 * p)))
                draw_masked_text(canvas, label, FONT_PATH, body_sz, PRIMARY_TEXT, x0 + int(cw * 0.58), y0 + int(row_h * 0.16), p)
                draw_progress_meter(canvas, x0 + int(cw * 0.26), y0 + int(row_h * 0.65), int(cw * 0.64), max(8, int(height * 0.010)), p * ratio, (255, 255, 255, int(28 * p)), (*ACCENT_COLOR, int(255 * p)))

    elif scene_idx == 2:
        # المشهد 3: الأداء والمعدلات المتحركة
        draw_masked_text(canvas, "معدلات الأداء والمرونة البرمجية", FONT_PATH, title_sz, PRIMARY_TEXT, cx, int(height * 0.15), ease_out_cubic(t / 0.22))
        cards = [
            ("60 إطار في الثانية", "سلاسة حركة في التصيير النهائي", 0.15),
            ("45 - 120 ثانية", "مدة مرنة للفيديوهات الكاملة", 0.30),
            ("صوت وموسيقى", "دمج تلقائي ومؤثرات انتقال", 0.45),
        ]
        gap = int(width * 0.03)
        total_w = int(width * 0.84)
        bw = (total_w - gap * 2) // 3
        bh = int(height * 0.44)
        by = int(height * 0.32)
        base_x = (width - total_w) // 2

        for i, (metric, desc, st) in enumerate(cards):
            p = spring_damped((t - st) / 0.45)
            bx = base_x + i * (bw + gap)
            by_anim = by + int(26 * (1 - p))
            if p > 0.01:
                draw_rounded_card(canvas, (bx, by_anim, bx + bw, by_anim + bh), 24, (255, 255, 255, int(18 * min(1.0, p))), (*ACCENT_COLOR, int(90 * min(1.0, p))))
                draw_accent_bar(canvas, bx + bw // 2, by_anim + int(bh * 0.16), int(bw * 0.45), 5, min(1.0, p), (*ACCENT_COLOR, 255))
                draw_masked_text(canvas, metric, FONT_PATH, sub_sz, ACCENT_COLOR, bx + bw // 2, by_anim + int(bh * 0.34), min(1.0, p))
                draw_masked_text(canvas, desc, FONT_PATH, max(18, int(height * 0.026)), PRIMARY_TEXT, bx + bw // 2, by_anim + int(bh * 0.58), min(1.0, p))

    elif scene_idx == 3:
        # المشهد 4: خط سير العمل من الفكرة إلى الفيديو
        draw_masked_text(canvas, "خط إنتاج منظم من الكود إلى الفيديو", FONT_PATH, title_sz, PRIMARY_TEXT, cx, int(height * 0.15), ease_out_cubic(t / 0.22))
        steps = [
            "1. كتابة المشاهد والمنحنيات بلغة Python",
            "2. توليد الإطارات والرسوم والنصوص العربية",
            "3. دمج الانتقالات والصوت والموسيقى عبر FFmpeg",
            "4. تصيير النسخة النهائية ورفعها كـ Artifact",
        ]
        for i, s_txt in enumerate(steps):
            p = ease_out_cubic((t - (0.12 + i * 0.14)) / 0.28)
            sy = int(height * 0.30) + i * int(height * 0.125)
            draw_masked_text(canvas, s_txt, FONT_PATH, body_sz, PRIMARY_TEXT if i < 3 else ACCENT_COLOR, cx, sy, p)

    elif scene_idx == 4:
        # المشهد 5: عنصر بصري هندسي نابض + رسالة تقنية
        draw_masked_text(canvas, "دقة هندسية وتحكم كامل بكل إطار", FONT_PATH, title_sz, PRIMARY_TEXT, cx, int(height * 0.15), ease_out_cubic(t / 0.22))
        pulse = 1.0 + 0.08 * math.sin(t * math.pi * 4.0)
        r_outer = int(min(width, height) * 0.15 * pulse)
        layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
        d = ImageDraw.Draw(layer)
        d.ellipse([cx - r_outer, cy + int(height * 0.03) - r_outer, cx + r_outer, cy + int(height * 0.03) + r_outer], outline=(*ACCENT_COLOR, 190), width=5)
        r_inner = int(r_outer * 0.65)
        d.ellipse([cx - r_inner, cy + int(height * 0.03) - r_inner, cx + r_inner, cy + int(height * 0.03) + r_inner], fill=(*ACCENT_COLOR, 55))
        canvas.alpha_composite(layer)
        draw_masked_text(canvas, "قابل للتوسع بإضافة مشاهد ومؤثرات جديدة بسهولة", FONT_PATH, sub_sz, PRIMARY_TEXT, cx, int(height * 0.76), ease_in_out_cubic((t - 0.20) / 0.35))

    else:
        # المشهد 6: الخاتمة
        draw_masked_text(canvas, "جاهز لإنتاج فيديوهاتك القادمة", FONT_PATH, title_sz, PRIMARY_TEXT, cx, int(height * 0.36), ease_out_cubic((t - 0.10) / 0.30))
        draw_accent_bar(canvas, cx, int(height * 0.47), int(width * 0.30), max(4, int(height * 0.006)), (t - 0.22) / 0.28, (*ACCENT_COLOR, 255))
        draw_masked_text(canvas, "motion2 • مجاني ومفتوح للتطوير المستمر", FONT_PATH, sub_sz, ACCENT_COLOR, cx, int(height * 0.53), ease_out_cubic((t - 0.30) / 0.30))

    return canvas.convert("RGB")
