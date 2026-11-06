"""Cut the live-action chip clips out of the Drive videos as 30 fps JPEG sequences.
usage: python prep3.py [PROMO_WORK]   (videos in PROMO_WORK/assets/drive_video/, needs ffmpeg)
"""
import os, sys, subprocess, shutil
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from timeline import CLIPS, FPS

W = sys.argv[1] if len(sys.argv) > 1 else os.environ["PROMO_WORK"]
SRC = os.path.join(W, "assets", "drive_video")
OUT = os.path.join(W, "assets", "gen", "clips")

for name, video, t0, _, n, *_ in CLIPS:
    d = os.path.join(OUT, name)
    shutil.rmtree(d, ignore_errors=True)
    os.makedirs(d)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(t0), "-i", os.path.join(SRC, video),
                    "-frames:v", str(n), "-vf", f"fps={FPS},scale=1920:1080:flags=lanczos",
                    "-q:v", "2", os.path.join(d, "%04d.jpg")], check=True)
    print(name, len(os.listdir(d)), "frames")
