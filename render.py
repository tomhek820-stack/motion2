import os
import glob
import shutil
import argparse
import subprocess
from scenes.intro_scene import render_scene_frames as render_intro
from scenes.features_scene import render_scene_frames as render_features

def encode_scene(frames_dir: str, out_path: str, fps: int):
    subprocess.run([
        "ffmpeg", "-y",
        "-framerate", str(fps),
        "-i", os.path.join(frames_dir, "frame_%05d.png"),
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-crf", "18",
        out_path,
    ], check=True)

def find_audio_file() -> str | None:
    for ext in ("mp3", "wav", "m4a", "ogg"):
        matches = sorted(glob.glob(os.path.join("assets", "audio", f"*.{ext}")))
        if matches:
            return matches[0]
    return None

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--quality", choices=["preview", "final"], default="preview")
    args = parser.parse_args()

    if args.quality == "final":
        width, height, fps = 1920, 1080, 60
    else:
        width, height, fps = 1280, 720, 30

    d1 = 3.5
    d2 = 4.0
    xfade_dur = 0.6

    tmp_dir = "tmp_render"
    out_dir = "output"
    os.makedirs(tmp_dir, exist_ok=True)
    os.makedirs(out_dir, exist_ok=True)

    f1_dir = os.path.join(tmp_dir, "s1")
    f2_dir = os.path.join(tmp_dir, "s2")
    v1_path = os.path.join(tmp_dir, "s1.mp4")
    v2_path = os.path.join(tmp_dir, "s2.mp4")
    merged_path = os.path.join(tmp_dir, "merged.mp4")
    final_path = os.path.join(out_dir, f"motion_{args.quality}.mp4")

    render_intro(width, height, fps, duration=d1, frames_dir=f1_dir)
    render_features(width, height, fps, duration=d2, frames_dir=f2_dir)

    encode_scene(f1_dir, v1_path, fps)
    encode_scene(f2_dir, v2_path, fps)

    offset = max(0.1, d1 - xfade_dur)
    subprocess.run([
        "ffmpeg", "-y",
        "-i", v1_path,
        "-i", v2_path,
        "-filter_complex", f"[0:v][1:v]xfade=transition=fade:duration={xfade_dur}:offset={offset},format=yuv420p[v]",
        "-map", "[v]",
        "-c:v", "libx264",
        "-crf", "18",
        merged_path,
    ], check=True)

    audio_file = find_audio_file()
    total_dur = d1 + d2 - xfade_dur
    if audio_file:
        subprocess.run([
            "ffmpeg", "-y",
            "-i", merged_path,
            "-stream_loop", "-1",
            "-i", audio_file,
            "-t", f"{total_dur:.2f}",
            "-c:v", "copy",
            "-c:a", "aac",
            "-shortest",
            final_path,
        ], check=True)
    else:
        shutil.copyfile(merged_path, final_path)

    shutil.rmtree(tmp_dir, ignore_errors=True)
    print(f"Done: {final_path}")

if __name__ == "__main__":
    main()
