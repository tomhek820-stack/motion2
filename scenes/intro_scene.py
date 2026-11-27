import os
from PIL import Image, ImageDraw
from engine.easing import ease_out_expo, ease_in_out_cubic, ease_out_back
from engine.theme import PALETTE, FONT_PATH
from engine.typography import draw_masked_text

def render_scene_frames(width: int, height: int, fps: int, duration: float, frames_dir: str):
    os.makedirs(frames_dir, exist_ok=True)
    total_frames = int(fps * duration)

    for f in range(total_frames):
        t = f / max(1, total_frames - 1)
        canvas = Image.new("RGBA", (width, height), (*PALETTE["bg_dark"], 255))
        draw = ImageDraw.Draw(canvas)

        # عناصر هندسية داعمة (دوائر وخطوط بسمك موحد)
        stroke_w = max(2, width // 480)
        p_ring = ease_out_expo(min(1.0, t * 2.5))
        r_outer = int(min(width, height) * 0.36 * p_ring)
        draw.ellipse(
            [width // 2 - r_outer, height // 2 - r_outer, width // 2 + r_outer, height // 2 + r_outer],
            outline=(*PALETTE["secondary"], 90),
            width=stroke_w,
        )

        # البطاقة المركزية بحركة ارتداد ناعمة
        p_card = ease_out_back(min(1.0, t * 2.2))
        card_w = int(width * 0.64)
        card_h = int(height * 0.44)
        cx = width // 2
        cy = int(height * 1.15 - (height * 0.65) * p_card)

        draw.rounded_rectangle(
            [cx - card_w // 2, cy - card_h // 2, cx + card_w // 2, cy + card_h // 2],
            radius=int(height * 0.035),
            fill=(*PALETTE["bg_card"], 255),
            outline=(*PALETTE["primary"], 255),
            width=stroke_w,
        )

        # شريط إبراز متحرك
        p_bar = ease_out_expo(max(0.0, (t - 0.12) * 2.0))
        bar_w = int(card_w * 0.28 * p_bar)
        bar_h = max(6, height // 110)
        draw.rounded_rectangle(
            [cx - bar_w // 2, cy - int(card_h * 0.24), cx + bar_w // 2, cy - int(card_h * 0.24) + bar_h],
            radius=bar_h // 2,
            fill=(*PALETTE["accent"], 255),
        )

        # العنوان الرئيسي والعنوان الفرعي باللغة العربية عبر قناع
        p_title = ease_in_out_cubic(max(0.0, (t - 0.18) * 2.2))
        p_sub = ease_in_out_cubic(max(0.0, (t - 0.32) * 2.2))

        draw_masked_text(
            canvas,
            "محرك موشن جرافيك برمجي",
            FONT_PATH,
            max(28, int(height * 0.062)),
            PALETTE["text"],
            cx,
            cy - int(card_h * 0.06),
            p_title,
        )

        draw_masked_text(
            canvas,
            "تصيير مجاني بالكامل عبر Termux و GitHub Actions",
            FONT_PATH,
            max(18, int(height * 0.034)),
            PALETTE["primary"],
            cx,
            cy + int(card_h * 0.16),
            p_sub,
        )

        canvas.convert("RGB").save(os.path.join(frames_dir, f"frame_{f:05d}.png"))
