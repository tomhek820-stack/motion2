import os
from PIL import Image
from engine.theme import BG_COLOR, PRIMARY_TEXT, ACCENT_COLOR, FONT_PATH
from engine.typography import draw_masked_text
from engine.easing import ease_out_cubic
from engine.shapes import draw_rounded_card, draw_progress_meter, draw_badge_icon

def render_scene_frames(width: int, height: int, fps: int, duration: float, frames_dir: str):
    os.makedirs(frames_dir, exist_ok=True)
    total_frames = max(1, int(round(duration * fps)))

    head_size = max(32, int(height * 0.058))
    item_size = max(22, int(height * 0.035))

    items = [
        ("سرعة اختبار عالية على الهاتف", "bolt", 0.92, 0.15),
        ("نصوص عربية متصلة وواضحة", "check", 1.00, 0.30),
        ("تصيير سحابي مجاني بالكامل", "play", 0.96, 0.45),
    ]

    for f in range(total_frames):
        t = f / max(1, total_frames - 1)
        canvas = Image.new("RGBA", (width, height), (*BG_COLOR, 255))

        p_head = ease_out_cubic(t / 0.25)
        draw_masked_text(
            canvas,
            "أبرز قدرات الإنتاج",
            FONT_PATH,
            head_size,
            PRIMARY_TEXT,
            width // 2,
            int(height * 0.14),
            p_head,
        )

        row_h = int(height * 0.17)
        start_y = int(height * 0.28)
        card_w = int(width * 0.76)
        card_x0 = (width - card_w) // 2
        card_x1 = card_x0 + card_w

        for idx, (label, icon_kind, target_ratio, start_t) in enumerate(items):
            p = ease_out_cubic((t - start_t) / 0.35)
            y0 = start_y + idx * (row_h + int(height * 0.03)) + int(24 * (1.0 - p))
            y1 = y0 + row_h

            if p > 0:
                draw_rounded_card(
                    canvas,
                    (card_x0, y0, card_x1, y1),
                    radius=20,
                    fill_rgba=(255, 255, 255, int(16 * p)),
                    border_rgba=(255, 255, 255, int(30 * p)),
                    border_width=2,
                )

                icon_r = max(18, int(row_h * 0.26))
                icon_cx = card_x1 - int(card_w * 0.07)
                icon_cy = y0 + row_h // 2
                draw_badge_icon(
                    canvas,
                    icon_cx,
                    icon_cy,
                    icon_r,
                    icon_kind,
                    circle_rgba=(*ACCENT_COLOR, int(230 * p)),
                    icon_rgba=(*BG_COLOR, int(255 * p)),
                )

                draw_masked_text(
                    canvas,
                    label,
                    FONT_PATH,
                    item_size,
                    PRIMARY_TEXT,
                    card_x0 + int(card_w * 0.58),
                    y0 + int(row_h * 0.18),
                    p,
                )

                meter_w = int(card_w * 0.62)
                meter_h = max(8, int(height * 0.011))
                meter_x = card_x0 + int(card_w * 0.28)
                meter_y = y0 + int(row_h * 0.66)
                draw_progress_meter(
                    canvas,
                    meter_x,
                    meter_y,
                    meter_w,
                    meter_h,
                    progress=p * target_ratio,
                    bg_rgba=(255, 255, 255, int(28 * p)),
                    fg_rgba=(*ACCENT_COLOR, int(255 * p)),
                )

        canvas.convert("RGB").save(os.path.join(frames_dir, f"frame_{f:05d}.png"))
