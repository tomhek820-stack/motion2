import os
import glob
import math
import subprocess
import numpy as np
from engine.project_config import load_project_config

def find_audio_assets() -> tuple[str | None, str | None]:
    bgm = None
    voice = None

    for ext in ("mp3", "wav", "m4a", "ogg"):
        for path in sorted(glob.glob(os.path.join("assets", "audio", f"*.{ext}"))):
            name = os.path.basename(path).lower()
            if ("voice" in name or "narration" in name or "vo" in name) and voice is None:
                voice = path
            elif bgm is None:
                bgm = path
    return bgm, voice

def _synthesize_spoken_line(text: str, out_wav: str, max_dur: float, sample_rate: int = 44100):
    # توليد صوت كلامي إيقاعي واضح (formant + syllable envelope) يطابق طول الجملة العربية
    words = [w for w in text.strip().split() if w]
    syllables = sum(max(1, len(w) // 2) for w in words) if words else 4
    est_dur = min(max_dur, max(1.4, min(max_dur * 0.92, syllables * 0.14)))
    total_samples = max(1, int(est_dur * sample_rate))
    t = np.arange(total_samples, dtype=np.float64) / sample_rate

    # غلاف مقاطع كلامية متناسقة مع الكلمات
    syl_rate = max(2.2, syllables / max(0.5, est_dur))
    syl_phase = (t * syl_rate) % 1.0
    syl_env = np.sin(np.pi * syl_phase) ** 1.4

    # غلاف جملة (دخول وخروج ناعم)
    sent_env = np.minimum(1.0, t / 0.14) * np.minimum(1.0, (est_dur - t) / 0.20)
    sent_env = np.maximum(0.0, sent_env)

    # طبقة صوتية دافئة بنبرة كلامية متغيرة قليلاً لتجنب الرتابة
    f0 = 132.0 + 14.0 * np.sin(2.0 * np.pi * 0.85 * t)
    phase = 2.0 * np.pi * np.cumsum(f0) / sample_rate

    # توافقيات صوتية قريبة من طابع الصوت البشري
    voice_wave = (
        0.55 * np.sin(phase)
        + 0.32 * np.sin(2.0 * phase + 0.3)
        + 0.18 * np.sin(3.0 * phase + 0.7)
        + 0.08 * np.sin(5.0 * phase)
    )

    # همس خفيف مصاحب للمقاطع لإضفاء وضوح نطقي
    rng = np.random.default_rng(abs(hash(text)) % (2**32))
    breath = rng.standard_normal(total_samples) * 0.06 * syl_env

    signal = (voice_wave * 0.55 * syl_env + breath) * sent_env
    signal = np.clip(signal, -0.9, 0.9)

    pcm16 = (signal * 32767.0).astype(np.int16)
    stereo = np.column_stack((pcm16, pcm16)).tobytes()

    subprocess.run([
        "ffmpeg", "-y",
        "-f", "s16le",
        "-ar", str(sample_rate),
        "-ac", "2",
        "-i", "pipe:0",
        "-c:a", "pcm_s16le",
        out_wav,
    ], input=stereo, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def _build_narration_track(lines: list[str], out_wav: str, total_duration: float, sample_rate: int = 44100) -> bool:
    if not lines:
        return False
    tmp_dir = os.path.dirname(out_wav)
    n_lines = len(lines)
    slot_dur = total_duration / max(1, n_lines)

    inputs = [
        "-f", "lavfi",
        "-t", f"{total_duration:.3f}",
        "-i", f"anullsrc=r={sample_rate}:cl=stereo",
    ]
    filter_parts = []
    mix_labels = ["[0:a]"]

    for idx, line in enumerate(lines):
        seg_wav = os.path.join(tmp_dir, f"vo_seg_{idx}.wav")
        _synthesize_spoken_line(line, seg_wav, max_dur=max(1.2, slot_dur - 0.6), sample_rate=sample_rate)
        if not os.path.isfile(seg_wav) or os.path.getsize(seg_wav) < 200:
            continue

        in_idx = idx + 1
        delay_ms = int(idx * slot_dur * 1000) + 300
        inputs.extend(["-i", seg_wav])
        lbl = f"vo{idx}"
        filter_parts.append(
            f"[{in_idx}:a]asetpts=PTS-STARTPTS,volume=1.30,adelay={delay_ms}|{delay_ms}[{lbl}]"
        )
        mix_labels.append(f"[{lbl}]")

    if len(mix_labels) == 1:
        return False

    filter_parts.append(
        f"{''.join(mix_labels)}amix=inputs={len(mix_labels)}:duration=first:dropout_transition=1,alimiter=limit=0.95[vo_out]"
    )

    subprocess.run(
        ["ffmpeg", "-y", *inputs, "-filter_complex", ";".join(filter_parts), "-map", "[vo_out]", "-c:a", "pcm_s16le", out_wav],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return os.path.isfile(out_wav) and os.path.getsize(out_wav) > 200

def synthesize_ambient_music(out_wav: str, duration: float, sample_rate: int = 44100):
    total_samples = int(duration * sample_rate)
    t = np.arange(total_samples, dtype=np.float64) / sample_rate

    chords = [
        (220.00, 261.63, 329.63),
        (174.61, 220.00, 261.63),
        (130.81, 196.00, 246.94),
        (196.00, 246.94, 293.66),
    ]
    seg_len = 6.0
    seg_idx = np.floor(t / seg_len).astype(np.int64) % len(chords)
    local_t = t % seg_len
    env = np.minimum(1.0, local_t / 1.0) * np.minimum(1.0, (seg_len - local_t) / 1.2)
    env = np.maximum(0.12, env)

    pad = np.zeros(total_samples, dtype=np.float64)
    arp = np.zeros(total_samples, dtype=np.float64)
    bass = np.zeros(total_samples, dtype=np.float64)

    step_dur = 0.25
    step_idx = np.floor(t / step_dur).astype(np.int64)
    step_local = t % step_dur
    arp_env = np.exp(-step_local * 11.0)

    for c_i, (f1, f2, f3) in enumerate(chords):
        mask = (seg_idx == c_i)
        if not np.any(mask):
            continue
        tm = t[mask]
        em = env[mask]

        chord_wave = (
            0.34 * np.sin(2.0 * np.pi * f1 * tm)
            + 0.28 * np.sin(2.0 * np.pi * f2 * tm)
            + 0.24 * np.sin(2.0 * np.pi * f3 * tm)
            + 0.10 * np.sin(2.0 * np.pi * (f3 * 2.0) * tm)
        )
        pad[mask] = chord_wave * em
        bass[mask] = 0.26 * np.sin(2.0 * np.pi * (f1 * 0.5) * tm) * em

    notes_per_chord = [
        [220.00, 261.63, 329.63, 440.00],
        [174.61, 220.00, 261.63, 349.23],
        [130.81, 196.00, 261.63, 329.63],
        [196.00, 246.94, 293.66, 392.00],
    ]
    for i in range(total_samples):
        c_notes = notes_per_chord[seg_idx[i]]
        note_f = c_notes[step_idx[i] % len(c_notes)]
        arp[i] = 0.20 * arp_env[i] * math.sin(2.0 * np.pi * note_f * t[i])

    beat_t = t % 0.5
    kick = np.where(beat_t < 0.09, 0.22 * ((1.0 - beat_t / 0.09) ** 2) * np.sin(2.0 * np.pi * 95.0 * t), 0.0)

    fade_in = np.minimum(1.0, t / 1.5)
    fade_out = np.minimum(1.0, (duration - t) / 2.0)

    mix = (pad * 0.42 + arp * 0.35 + bass * 0.32 + kick) * fade_in * fade_out
    mix = np.clip(mix, -0.92, 0.92)

    pcm16 = (mix * 32767.0).astype(np.int16)
    stereo = np.column_stack((pcm16, pcm16)).tobytes()

    subprocess.run([
        "ffmpeg", "-y",
        "-f", "s16le",
        "-ar", str(sample_rate),
        "-ac", "2",
        "-i", "pipe:0",
        "-c:a", "pcm_s16le",
        out_wav,
    ], input=stereo, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def build_final_audio(
    out_audio_path: str,
    duration: float,
    transitions_times: list[float],
    tmp_dir: str,
):
    cfg = load_project_config()
    narration_lines = cfg.get("narration", [])

    bgm_file, voice_file = find_audio_assets()
    if bgm_file is None:
        bgm_file = os.path.join(tmp_dir, "synth_bgm.wav")
        synthesize_ambient_music(bgm_file, duration=duration)

    if voice_file is None and narration_lines:
        vo_out = os.path.join(tmp_dir, "narration_track.wav")
        if _build_narration_track(narration_lines, vo_out, total_duration=duration):
            voice_file = vo_out

    inputs = ["-stream_loop", "-1", "-i", bgm_file]
    filter_parts = []
    idx = 1

    bgm_vol = "0.26" if voice_file else "0.85"
    filter_parts.append(
        f"[0:a]atrim=0:{duration:.3f},asetpts=PTS-STARTPTS,volume={bgm_vol},afade=t=in:st=0:d=1.2,afade=t=out:st={max(0.0, duration-1.8):.3f}:d=1.8[bgm]"
    )

    mix_labels = ["[bgm]"]

    if voice_file:
        inputs.extend(["-i", voice_file])
        filter_parts.append(f"[{idx}:a]atrim=0:{duration:.3f},asetpts=PTS-STARTPTS,volume=1.35[vo]")
        mix_labels.append("[vo]")
        idx += 1

    for t_ev in transitions_times:
        if 0.2 < t_ev < duration - 0.4:
            swish_label = f"sw{idx}"
            inputs.extend([
                "-f", "lavfi",
                "-t", "0.28",
                "-i", "anoisesrc=color=pink:amplitude=0.18",
            ])
            filter_parts.append(
                f"[{idx}:a]highpass=f=260,lowpass=f=1800,afade=t=in:st=0:d=0.08,afade=t=out:st=0.10:d=0.18,volume=0.32,adelay={max(0, int((t_ev-0.12)*1000))}|{max(0, int((t_ev-0.12)*1000))}[{swish_label}]"
            )
            mix_labels.append(f"[{swish_label}]")
            idx += 1

    n_streams = len(mix_labels)
    filter_parts.append(
        f"{''.join(mix_labels)}amix=inputs={n_streams}:duration=first:dropout_transition=2,alimiter=limit=0.95[aout]"
    )

    cmd = [
        "ffmpeg", "-y",
        *inputs,
        "-filter_complex", ";".join(filter_parts),
        "-map", "[aout]",
        "-t", f"{duration:.3f}",
        "-c:a", "aac",
        "-b:a", "192k",
        out_audio_path,
    ]
    subprocess.run(cmd, check=True)
