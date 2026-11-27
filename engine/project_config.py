import os
import json

DEFAULT_CONFIG = {
    "duration": 60.0,
    "theme": {
        "bg_color": [11, 15, 25],
        "primary_text": [248, 250, 252],
        "accent_color": [56, 189, 248],
        "secondary_accent": [16, 185, 129],
        "font_path": "assets/fonts/Cairo-Bold.ttf",
    },
    "intro": {
        "title": "محرك موشن جرافيك برمجي احترافي",
        "subtitle": "إنتاج متكامل 45-120 ثانية بالصوت والحركة والخط العربي",
    },
    "outro": {
        "title": "motion2 • محرك إنتاج مرئي متكامل",
        "subtitle": "اختبار سريع في Termux وتصيير سحابي عبر GitHub Actions",
    },
}

def load_project_config(path: str = "config/project.json") -> dict:
    cfg = json.loads(json.dumps(DEFAULT_CONFIG))
    if os.path.isfile(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict):
                for k, v in data.items():
                    if isinstance(v, dict) and isinstance(cfg.get(k), dict):
                        cfg[k].update(v)
                    else:
                        cfg[k] = v
        except Exception:
            pass
    return cfg
