import math

def clamp01(t: float) -> float:
    return max(0.0, min(1.0, t))

def ease_out_cubic(t: float) -> float:
    t = clamp01(t)
    return 1.0 - ((1.0 - t) ** 3)

def ease_in_out_cubic(t: float) -> float:
    t = clamp01(t)
    if t < 0.5:
        return 4.0 * (t ** 3)
    return 1.0 - (((-2.0 * t + 2.0) ** 3) / 2.0)

def ease_out_back(t: float, overshoot: float = 1.70158) -> float:
    t = clamp01(t)
    c3 = overshoot + 1.0
    return 1.0 + c3 * ((t - 1.0) ** 3) + overshoot * ((t - 1.0) ** 2)

def spring_damped(t: float, freq: float = 8.0, decay: float = 5.0) -> float:
    t = clamp01(t)
    if t >= 1.0:
        return 1.0
    return 1.0 - math.exp(-decay * t) * math.cos(freq * t)

def ease_out_expo(t: float) -> float:
    t = clamp01(t)
    if t >= 1.0:
        return 1.0
    return 1.0 - (2.0 ** (-10.0 * t))

def ease_out_expo(t: float) -> float:
    t = clamp01(t)
    if t >= 1.0:
        return 1.0
    return 1.0 - (2.0 ** (-10.0 * t))
