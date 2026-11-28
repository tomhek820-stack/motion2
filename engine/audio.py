import os
import glob
import math
import subprocess
import numpy as np
import sherpa_onnx
from engine.project_config import load_project_config

SUPERTONIC_DIR = "models/sherpa-onnx-supertonic-3-tts-int8-2026-05-11"

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

def _extract_narration_lines(cfg: dict) -> list[str]:
    lines: list[str] = []

    raw_narr = cfg.get("narration")
    if isinstance(raw_narr, list):
        for item in raw_narr:
            if isinstance(item, str) and item.strip():
                lines.append(item.strip())
            elif isinstance(item, dict):
                for k in ("text", "narration", "script", "title"):
                    v = item.get(k)
                    if isinstance(v, str) and v.strip():
                        lines.append(v.strip())
                        break
    elif isinstance(raw_narr, str) and raw_narr.strip():
        lines.append(raw_narr.strip())

    if lines:
        return lines

    for section_key in ("intro", "outro"):
        sec = cfg.get(section_key)
        if isinstance(sec, str) and sec.strip():
            lines.append(sec.strip())
        elif isinstance(sec, dict):
            parts = []
            for k in ("title", "subtitle", "text", "narration", "description"):
                v = sec.get(k)
                if isinstance(v, str) and v.strip():
                    parts.append(v.strip())
            if parts:
                lines.append(" . ".join(parts))

    scenes = cfg.get("scenes")
    if isinstance(scenes, list):
        for sc in scenes:
            if isinstance(sc, str) and sc.strip():
                lines.append(sc.strip())
            elif isinstance(sc, dict):
                for k in ("narration", "text", "title", "subtitle", "description"):
                    v = sc.get(k)
                    if isinstance(v, str) and v.strip():
                        lines.append(v.strip())
                        break

    if not lines:
        lines = [
            "مرحباً بكم في محرك الموشن الجرافيك البرمجي المتكامل.",
            "تصميم وتوليد المشاهد والانتقالات بسلاسة عالية.",
            "تعليق صوتي عربي واضح متزامن مع الموسيقى الخلفية.",
            "تصدير سريع وجاهز للمعاينة والمشاركة الفورية.",
        ]

    return lines

def _create_supertonic_tts():
    model_dir = SUPERTONIC_DIR
    if not os.path.isdir(model_dir):
        matches = glob.glob("models/*supertonic*", recursive=False)
        if matches:
            model_dir = matches[0]
    if not os.path.isdir(model_dir):
        return None

    dur_pred = os.path.join(model_dir, "duration_predictor.int8.onnx")
    txt_enc = os.path.join(model_dir, "text_encoder.int8.onnx")
    vec_est = os.path.join(model_dir, "vector_estimator.int8.onnx")
    voc = os.path.join(model_dir, "vocoder.int8.onnx")
    tts_json = os.path.join(model_dir, "tts.json")
    idx_bin = os.path.join(model_dir, "unicode_indexer.bin")
    voice_style = os.path.join(model_dir, "voice.bin")

    if not all(os.path.isfile(p) for p in (dur_pred, txt_enc, vec_est, voc)):
        return None

    num_threads = min(4, os.cpu_count() or 2)

    supertonic_cfg = sherpa_onnx.OfflineTtsSupertonicModelConfig(
        duration_predictor=dur_pred,
        text_encoder=txt_enc,
        vector_estimator=vec_est,
        vocoder=voc,
        tts_json=tts_json if os.path.isfile(tts_json) else "",
        unicode_indexer=idx_bin if os.path.isfile(idx_bin) else "",
        voice_style=voice_style if os.path.isfile(voice_style) else "",
    )

    model_cfg = sherpa_onnx.OfflineTtsModelConfig(
        supertonic=supertonic_cfg,
        num_threads=num_threads,
        debug=False,
        provider="cpu",
    )

    tts_cfg = sherpa_onnx.OfflineTtsConfig(model=model_cfg)
    return sherpa_onnx.OfflineTts(tts_cfg)

def _save_samples_wav(samples, sample_rate: int, out_wav: str):
    arr = np.asarray(samples, dtype=np.float32)
    arr = np.clip(arr, -0.98, 0.98)
    pcm16 = (arr * 32767.0).astype(np.int16).tobytes()
    subprocess.run([
        "ffmpeg", "-y",
        "-f", "s16le",
        "-ar", str(sample_rate),
        "-ac", "1",
        "-i", "pipe:0",
        "-ar", "44100",
        "-ac", "2",
        "-c:a", "pcm_s16le",
        out_wav,
    ], input=pcm16, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def _build_supertonic_narration(lines: list[str], out_wav: str, total_duration: float, sid: int = 5, speed: float = 1.0) -> bool:
    if not lines:
        return False

    tts = _create_supertonic_tts()
    if tts is None:
        return False

    max_sid = max(0, int(getattr(tts, "num_speakers", 10)) - 1)
    safe_sid = max(0, min(sid, max_sid))

    tmp_dir = os.path.dirname(out_wav)
    n_lines = len(lines)
    slot_dur = total_duration / max(1, n_lines)

    concat_inputs = []
    concat_parts = []
    seg_counter = 0
    cursor = 0.0

    for idx, line in enumerate(lines):
        if cursor >= total_duration - 0.15:
            break
        clean_line = str(line).strip()
        if not clean_line:
            continue

        desired_start = idx * slot_dur + 0.15
        gap_dur = max(0.0, desired_start - cursor)
        if gap_dur > 0.02:
            gap_wav = os.path.join(tmp_dir, f"st3_gap_{idx}.wav")
            subprocess.run([
                "ffmpeg", "-y",
                "-f", "lavfi",
                "-t", f"{gap_dur:.3f}",
                "-i", "anullsrc=r=44100:cl=stereo",
                "-c:a", "pcm_s16le",
                gap_wav,
            ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            concat_inputs.extend(["-i", gap_wav])
            concat_parts.append(f"[{seg_counter}:a]")
            seg_counter += 1
            cursor += gap_dur

        raw_seg_wav = os.path.join(tmp_dir, f"st3_raw_{idx}.wav")
        audio = tts.generate(clean_line, sid=safe_sid, speed=speed)
        if audio is None or not getattr(audio, "samples", None) or len(audio.samples) == 0:
            continue

        sr = int(getattr(audio, "sample_rate", 44100) or 44100)
        _save_samples_wav(audio.samples, sr, raw_seg_wav)

        rem_total = max(0.1, total_duration - cursor)
        seg_wav = os.path.join(tmp_dir, f"st3_seg_{idx}.wav")
        subprocess.run([
            "ffmpeg", "-y",
            "-i", raw_seg_wav,
            "-af", f"atrim=0:{rem_total:.3f},asetpts=PTS-STARTPTS",
            "-c:a", "pcm_s16le",
            seg_wav,
        ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        probe = subprocess.run([
            "ffprobe", "-v", "error", "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1", seg_wav
        ], capture_output=True, text=True, check=False)
        try:
            seg_dur = float((probe.stdout or "0").strip())
        except ValueError:
            seg_dur = 0.0

        concat_inputs.extend(["-i", seg_wav])
        concat_parts.append(f"[{seg_counter}:a]")
        seg_counter += 1
        cursor += max(0.0, seg_dur)

    if seg_counter == 0:
        return False

    if cursor < total_duration - 0.02:
        tail_dur = total_duration - cursor
        tail_wav = os.path.join(tmp_dir, "st3_tail.wav")
        subprocess.run([
            "ffmpeg", "-y",
            "-f", "lavfi",
            "-t", f"{tail_dur:.3f}",
            "-i", "anullsrc=r=44100:cl=stereo",
            "-c:a", "pcm_s16le",
            tail_wav,
        ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        concat_inputs.extend(["-i", tail_wav])
        concat_parts.append(f"[{seg_counter}:a]")
        seg_counter += 1

    filter_expr = f"{''.join(concat_parts)}concat=n={seg_counter}:v=0:a=1,atrim=0:{total_duration:.3f},asetpts=PTS-STARTPTS[vo_out]"
    subprocess.run([
        "ffmpeg", "-y",
        *concat_inputs,
        "-filter_complex", filter_expr,
        "-map", "[vo_out]",
        "-c:a", "pcm_s16le",
        out_wav,
    ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    ok = os.path.isfile(out_wav) and os.path.getsize(out_wav) > 400
    if ok:
        print(f"Supertonic 3 narration ready (sid={safe_sid}, lines={len(lines)}): {out_wav}")
    return ok

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
    narration_lines = _extract_narration_lines(cfg)
    voice_cfg = cfg.get("voice") if isinstance(cfg.get("voice"), dict) else {}
    sid = int(voice_cfg.get("sid", 5))
    speed = float(voice_cfg.get("speed", 1.0))

    bgm_file, voice_file = find_audio_assets()
    if bgm_file is None:
        bgm_file = os.path.join(tmp_dir, "synth_bgm.wav")
        synthesize_ambient_music(bgm_file, duration=duration)

    if voice_file is None and narration_lines:
        vo_out = os.path.join(tmp_dir, "supertonic_narration.wav")
        if _build_supertonic_narration(narration_lines, vo_out, total_duration=duration, sid=sid, speed=speed):
            voice_file = vo_out

    inputs = ["-stream_loop", "-1", "-i", bgm_file]
    filter_parts = []
    idx = 1

    bgm_vol = "0.14" if voice_file else "0.85"
    filter_parts.append(
        f"[0:a]atrim=0:{duration:.3f},asetpts=PTS-STARTPTS,volume={bgm_vol},afade=t=in:st=0:d=1.2,afade=t=out:st={max(0.0, duration-1.8):.3f}:d=1.8[bgm]"
    )

    mix_labels = ["[bgm]"]

    if voice_file:
        inputs.extend(["-i", voice_file])
        filter_parts.append(f"[{idx}:a]atrim=0:{duration:.3f},asetpts=PTS-STARTPTS,volume=1.75[vo]")
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
                f"[{idx}:a]highpass=f=260,lowpass=f=1800,afade=t=in:st=0:d=0.08,afade=t=out:st=0.10:d=0.18,volume=0.18,adelay={max(0, int((t_ev-0.12)*1000))}|{max(0, int((t_ev-0.12)*1000))}[{swish_label}]"
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
