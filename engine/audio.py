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

    # تدرج وتري هادئ (A minor / F major / C major / G major) كل 6 ثوانٍ
    chords = [
        (220.00, 261.63, 329.63),
        (174.61, 220.00, 261.63),
        (130.81, 196.00, 246.94),
        (196.00, 246.94, 293.66),
    ]
    seg_len = 6.0
    pad = np.zeros(total_samples, dtype=np.float64)

    for i in range(total_samples):
        sec = t[i]
        idx = int(sec // seg_len) % len(chords)
        local_t = sec % seg_len
        env = min(1.0, local_t / 1.2) * min(1.0, (seg_len - local_t) / 1.5)
        freqs = chords[idx]
        val = 0.0
        for f in freqs:
            val += 0.35 * math.sin(2.0 * math.pi * f * sec)
            val += 0.12 * math.sin(2.0 * math.pi * (f * 2.0) * sec)
        pad[i] = val * max(0.05, env)

    # نبضة إيقاعية خفيفة كل 0.5 ثانية
    beat_period = 0.5
    pulse = np.zeros(total_samples, dtype=np.float64)
    for i in range(total_samples):
        bt = t[i] % beat_period
        if bt < 0.08:
            amp = (1.0 - bt / 0.08) ** 2
            pulse[i] = 0.14 * amp * math.sin(2.0 * math.pi * 110.0 * t[i])

    # تلاشي دخول وخروج عام للموسيقى
    fade_in = np.minimum(1.0, t / 2.0)
    fade_out = np.minimum(1.0, (duration - t) / 2.5)
    mix = (pad * 0.22 + pulse) * fade_in * fade_out
    mix = np.clip(mix, -0.9, 0.9)

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

    bgm_vol = "0.24" if voice_file else "0.55"
    filter_parts.append(f"[0:a]atrim=0:{duration:.3f},asetpts=PTS-STARTPTS,volume={bgm_vol},afade=t=in:st=0:d=1.5,afade=t=out:st={max(0.0, duration-2.0):.3f}:d=2.0[bgm]")

    mix_labels = ["[bgm]"]

    if voice_file:
        inputs.extend(["-i", voice_file])
        filter_parts.append(f"[{idx}:a]atrim=0:{duration:.3f},asetpts=PTS-STARTPTS,volume=1.15[vo]")
        mix_labels.append("[vo]")
        idx += 1

    # إضافة نقرات انتقال خفيفة عند نقاط الانتقال
    for t_ev in transitions_times:
        if 0.2 < t_ev < duration - 0.5:
            click_label = f"clk{idx}"
            inputs.extend([
                "-f", "lavfi",
                "-t", "0.12",
                "-i", "sine=frequency=420:sample_rate=44100",
            ])
            filter_parts.append(
                f"[{idx}:a]volume=0.06,afade=t=in:st=0:d=0.01,afade=t=out:st=0.02:d=0.10,adelay={int(t_ev*1000)}|{int(t_ev*1000)}[{click_label}]"
            )
            mix_labels.append(f"[{click_label}]")
            idx += 1

    n_streams = len(mix_labels)
    filter_parts.append(f"{''.join(mix_labels)}amix=inputs={n_streams}:duration=first:dropout_transition=2,alimiter=limit=0.95[aout]")

    cmd = ["ffmpeg", "-y", *inputs, "-filter_complex", ";".join(filter_parts), "-map", "[aout]", "-t", f"{duration:.3f}", "-c:a", "aac", "-b:a", "192k", out_audio_path]
    subprocess.run(cmd, check=True)
