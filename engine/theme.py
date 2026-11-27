import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONT_PATH = os.path.join(BASE_DIR, "assets", "fonts", "Cairo-Bold.ttf")

PALETTE = {
    "bg_dark": (13, 17, 26),
    "bg_card": (22, 29, 45),
    "primary": (56, 189, 248),
    "secondary": (129, 140, 248),
    "accent": (245, 158, 11),
    "text": (248, 250, 252),
    "muted": (148, 163, 184),
}

BG_COLOR = (13, 17, 26)
PRIMARY_TEXT = (248, 250, 252)
ACCENT_COLOR = (56, 189, 248)
FONT_PATH = "assets/fonts/Cairo-Bold.ttf"
