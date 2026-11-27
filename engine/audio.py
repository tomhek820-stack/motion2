import os
import glob
import math
import subprocess
import numpy as np

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

def synthesize_ambient_music(out_wav: str, duration: float, sample_rate: int = 44100):
    total_samples = int(duration * sample_rate)
    t = np.arange(total_samples, dtype=np.float64) / sample_rate

    # تدرج وتري واضح ومريح للأذن كل 6 ثوانٍ (Am -> F -> C -> G)
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

    # أرپيجيو ناعم كل 0.25 ثانية
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

        # طبقة الأوتار الناعمة
        chord_wave = (
            0.34 * np.sin(2.0 * np.pi * f1 * tm)
            + 0.28 * np.sin(2.0 * np.pi * f2 * tm)
            + 0.24 * np.sin(2.0 * np.pi * f3 * tm)
            + 0.10 * np.sin(2.0 * np.pi * (f3 * 2.0) * tm)
        )
        pad[mask] = chord_wave * em

        # طبقة البيس العميقة الهادئة
        bass[mask] = 0.26 * np.sin(2.0 * np.pi * (f1 * 0.5) * tm) * em

    # نغمة الأرپيجيو المتنقلة بين درجات الأكورد الحالي
    notes_per_chord = [
        [220.00, 261.63, 329.63, 440.00],
        [174.61, 220.00, 261.63, 349.23],
        [130.81, 196.00, 261.63, 329.63],
        [196.00, 246.94, 293.66, 392.00],
    ]
    for i in range(total_samples):
        c_notes = notes_per_chord[seg_idx[i]]
        note_f = c_notes[step_idx[i] % len(c_notes)]
        arp[i] = 0.20 * arp_env[i] * math.sin(2.0 * math.pi * note_f * t[i])

    # نبضة إيقاعية خفيفة كل 0.5 ثانية
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
    bgm_file, voice_file = find_audio_assets()
    if bgm_file is None:
        bgm_file = os.path.join(tmp_dir, "synth_bgm.wav")
        synthesize_ambient_music(bgm_file, duration=duration)

    inputs = ["-stream_loop", "-1", "-i", bgm_file]
    filter_parts = []
    idx = 1

    bgm_vol = "0.30" if voice_file else "0.85"
    filter_parts.append(
        f"[0:a]atrim=0:{duration:.3f},asetpts=PTS-STARTPTS,volume={bgm_vol},afade=t=in:st=0:d=1.2,afade=t=out:st={max(0.0, duration-1.8):.3f}:d=1.8[bgm]"
    )

    mix_labels = ["[bgm]"]

    if voice_file:
        inputs.extend(["-i", voice_file])
        filter_parts.append(f"[{idx}:a]atrim=0:{duration:.3f},asetpts=PTS-STARTPTS,volume=1.20[vo]")
        mix_labels.append("[vo]")
        idx += 1

    # مؤثر انتقال صوتي ناعم (whoosh + نبضة) عند كل انتقال بين المشاهد
    for t_ev in transitions_times:
        if 0.2 < t_ev < duration - 0.4:
            swish_label = f"sw{idx}"
            inputs.extend([
                "-f", "lavfi",
                "-t", "0.28",
                "-i", "anoisesrc=color=pink:amplitude=0.18",
            ])
            filter_parts.append(
                f"[{idx}:a]highpass=f=260,lowpass=f=1800,afade=t=in:st=0:d=0.08,afade=t=out:st=0.10:d=0.18,volume=0.35,adelay={max(0, int((t_ev-0.12)*1000))}|{max(0, int((t_ev-0.12)*1000))}[{swish_label}]"
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
