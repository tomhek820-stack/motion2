import os
import shutil
import argparse
import subprocess
from scenes.intro_scene import render_scene_frames

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--quality", choices=["preview", "final"], default="preview")
    args = parser.parse_args()

    if args.quality == "final":
        width, height, fps = 1920, 1080, 60
    else:
        width, height, fps = 1280, 720, 30

    frames_dir = "frames"
    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, f"motion_{args.quality}.mp4")

    render_scene_frames(width, height, fps, duration=4.0, frames_dir=frames_dir)

    subprocess.run([
        "ffmpeg", "-y",
        "-framerate", str(fps),
        "-i", os.path.join(frames_dir, "frame_%05d.png"),
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-crf", "18",
        output_file
    ], check=True)

    shutil.rmtree(frames_dir, ignore_errors=True)
    print(f"Done: {output_file}")

if __name__ == "__main__":
    main()
