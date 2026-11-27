import math

def ease_out_expo(t: float) -> float:
    t = max(0.0, min(1.0, t))
    return 1.0 if t == 1.0 else 1.0 - math.pow(2.0, -10.0 * t)

def ease_in_out_cubic(t: float) -> float:
    t = max(0.0, min(1.0, t))
    return 4 * t * t * t if t < 0.5 else 1 - math.pow(-2 * t + 2, 3) / 2

def ease_out_back(t: float, s: float = 1.70158) -> float:
    t = max(0.0, min(1.0, t))
    return 1 + (s + 1) * math.pow(t - 1, 3) + s * math.pow(t - 1, 2)
