import os
from PIL import Image, ImageDraw
from engine.theme import BG_COLOR, PRIMARY_TEXT, ACCENT_COLOR, FONT_PATH
from engine.typography import draw_masked_text
from engine.easing import ease_out_cubic
from engine.shapes import draw_accent_bar, draw_rounded_card

def render_scene_frames(width: int, height: int, fps: int, duration: float, frames_dir: str):
    os.makedirs(frames_dir, exist_ok=True)
    total_frames = max(1, int(round(duration * fps)))

    title_size = max(36, int(height * 0.072))
    sub_size = max(24, int(height * 0.040))

    for f in range(total_frames):
        t = f / max(1, total_frames - 1)
        canvas = Image.new("RGBA", (width, height), (*BG_COLOR, 255))

        # بطاقة خلفية مركزية ناعمة
        card_w = int(width * 0.78)
        card_h = int(height * 0.56)
        cx = width // 2
        cy = height // 2
        p_card = ease_out_cubic((t - 0.05) / 0.35)
        if p_card > 0:
            draw_rounded_card(
                canvas,
                (cx - card_w // 2, cy - card_h // 2 + int(20 * (1.0 - p_card)), cx + card_w // 2, cy + card_h // 2 + int(20 * (1.0 - p_card))),
                radius=28,
                fill_rgba=(255, 255, 255, int(18 * p_card)),
                border_rgba=(255, 255, 255, int(36 * p_card)),
                border_width=2,
            )

        p_title = ease_out_cubic((t - 0.12) / 0.35)
        draw_masked_text(
            canvas,
            "محرك موشن جرافيك برمجي متكامل",
            FONT_PATH,
            title_size,
            PRIMARY_TEXT,
            cx,
            int(height * 0.36),
            p_title,
        )

        draw_accent_bar(
            canvas,
            cx,
            int(height * 0.47),
            max_width=int(width * 0.28),
            height=max(4, int(height * 0.006)),
            progress=(t - 0.25) / 0.30,
            color_rgba=(*ACCENT_COLOR, 255),
        )

        p_sub = ease_out_cubic((t - 0.32) / 0.35)
        draw_masked_text(
            canvas,
            "تصيير سريع عبر Termux وسحابي عبر GitHub Actions",
            FONT_PATH,
            sub_size,
            ACCENT_COLOR,
            cx,
            int(height * 0.53),
            p_sub,
        )

        canvas.convert("RGB").save(os.path.join(frames_dir, f"frame_{f:05d}.png"))
