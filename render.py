import os
import shutil
import argparse
import subprocess
from scenes.story_scenes import render_scene_frame
from engine.audio import build_final_audio

def stream_scene_to_mp4(scene_idx: int, duration: float, width: int, height: int, fps: int, out_mp4: str):
    total_frames = max(1, int(round(duration * fps)))
    proc = subprocess.Popen([
        "ffmpeg", "-y",
        "-f", "rawvideo",
        "-vcodec", "rawvideo",
        "-s", f"{width}x{height}",
        "-pix_fmt", "rgb24",
        "-r", str(fps),
        "-i", "pipe:0",
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-crf", "18",
        out_mp4,
    ], stdin=subprocess.PIPE, stderr=subprocess.DEVNULL)

    assert proc.stdin is not None
    try:
        for f in range(total_frames):
            t = f / max(1, total_frames - 1)
            frame_rgb = render_scene_frame(scene_idx, t, width, height)
            proc.stdin.write(frame_rgb.tobytes())
    finally:
        proc.stdin.close()
        ret = proc.wait()
        if ret != 0:
            raise RuntimeError(f"FFmpeg failed encoding scene {scene_idx} with exit code {ret}")

def copy_preview_to_downloads(src_path: str):
    candidates = [
        os.path.expanduser("~/storage/downloads"),
        "/sdcard/Download",
    ]
    for dl_dir in candidates:
        if os.path.isdir(dl_dir) and os.access(dl_dir, os.W_OK):
            dest_path = os.path.join(dl_dir, os.path.basename(src_path))
            shutil.copy2(src_path, dest_path)
            print(f"Copied preview to Downloads: {dest_path}")
            return

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--quality", choices=["preview", "final"], default="preview")
    parser.add_argument("--duration", type=float, default=60.0, help="Total video duration in seconds (45-120 recommended)")
    args = parser.parse_args()

    duration = max(10.0, min(300.0, args.duration))
    if args.quality == "final":
        width, height, fps = 1920, 1080, 60
    else:
        width, height, fps = 1280, 720, 30

    num_scenes = 6
    xfade_dur = 0.6
    scene_dur = (duration + xfade_dur * (num_scenes - 1)) / num_scenes

    tmp_dir = "tmp_full_render"
    out_dir = "output"
    os.makedirs(tmp_dir, exist_ok=True)
    os.makedirs(out_dir, exist_ok=True)

    scene_videos = []
    for idx in range(num_scenes):
        v_path = os.path.join(tmp_dir, f"scene_{idx}.mp4")
        stream_scene_to_mp4(idx, scene_dur, width, height, fps, v_path)
        scene_videos.append(v_path)

    transitions = ["fade", "slideleft", "smoothup", "circleopen", "fade"]
    inputs = []
    for v in scene_videos:
        inputs.extend(["-i", v])

    filter_chains = []
    transition_times = []
    prev_label = "[0:v]"
    accum_offset = 0.0

    for i in range(1, num_scenes):
        accum_offset += max(0.2, scene_dur - xfade_dur)
        transition_times.append(accum_offset)
        out_label = f"[v{i}]" if i < num_scenes - 1 else "[vout]"
        t_name = transitions[(i - 1) % len(transitions)]
        filter_chains.append(
            f"{prev_label}[{i}:v]xfade=transition={t_name}:duration={xfade_dur}:offset={accum_offset:.3f}{out_label}"
        )
        prev_label = out_label

    video_only_path = os.path.join(tmp_dir, "video_only.mp4")
    subprocess.run([
        "ffmpeg", "-y",
        *inputs,
        "-filter_complex", ";".join(filter_chains),
        "-map", "[vout]",
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-crf", "18",
        video_only_path,
    ], check=True)

    actual_total_dur = scene_dur * num_scenes - xfade_dur * (num_scenes - 1)
    audio_path = os.path.join(tmp_dir, "final_audio.aac")
    build_final_audio(audio_path, duration=actual_total_dur, transitions_times=transition_times, tmp_dir=tmp_dir)

    final_output = os.path.join(out_dir, f"motion_{args.quality}_{int(round(actual_total_dur))}s.mp4")
    subprocess.run([
        "ffmpeg", "-y",
        "-i", video_only_path,
        "-i", audio_path,
        "-c:v", "copy",
        "-c:a", "aac",
        "-shortest",
        final_output,
    ], check=True)

    if args.quality == "preview":
        copy_preview_to_downloads(final_output)

    shutil.rmtree(tmp_dir, ignore_errors=True)
    print(f"Done: {final_output} ({actual_total_dur:.1f}s)")

if __name__ == "__main__":
    main()
