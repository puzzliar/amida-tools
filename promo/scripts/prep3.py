"""Cut the live-action chip clips out of the Drive videos as 30 fps JPEG sequences,
slowed down (motion-interpolated) and roughened with film grain, flicker and short glitches.
usage: python prep3.py [PROMO_WORK] [--only name ...]   (videos in PROMO_WORK/assets/drive_video/, needs ffmpeg)
"""
import os, sys, subprocess, shutil
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from timeline import CLIPS, FPS, clip_glitches

args = [a for a in sys.argv[1:]]
only = args[args.index("--only") + 1:] if "--only" in args else None
if "--only" in args:
    args = args[:args.index("--only")]
W = args[0] if args else os.environ["PROMO_WORK"]
SRC = os.path.join(W, "assets", "drive_video")
OUT = os.path.join(W, "assets", "gen", "clips")


def glitch(frames):
    """frames where the picture tears: RGB split + heavy noise for 2 frames"""
    return "+".join(f"between(n,{f},{f + 1})" for f in frames)


for idx, (name, video, t0, _, n, _, _, speed) in enumerate(CLIPS):
    if only and name not in only:
        continue
    d = os.path.join(OUT, name)
    shutil.rmtree(d, ignore_errors=True)
    os.makedirs(d)
    g = glitch(clip_glitches(idx, n))
    vf = ",".join([
        f"setpts=PTS/{speed}",
        f"minterpolate=fps={FPS}:mi_mode=mci:mc_mode=aobmc:me_mode=bidir:vsbmc=1",
        "scale=1920:1080:flags=lanczos",
        # unsteady exposure, like a failing bulb
        "eq=eval=frame:brightness='0.035*sin(n*1.31)*sin(n*0.23)-0.01*gt(random(1),0.93)'",
        "noise=alls=16:allf=t",                                   # film grain
        f"rgbashift=rh=-14:bh=14:gv=4:enable='{g}'",              # chromatic tear
        f"noise=alls=70:allf=t:enable='{g}'",                     # static burst
    ])
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(t0), "-t", f"{n / FPS * speed + 0.3:.3f}",
                    "-i", os.path.join(SRC, video), "-vf", vf, "-frames:v", str(n),
                    "-q:v", "2", os.path.join(d, "%04d.jpg")], check=True)
    print(name, len(os.listdir(d)), "frames")
