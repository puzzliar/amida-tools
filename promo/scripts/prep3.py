"""Cut the live-action chip clips out of the Drive videos as 30 fps JPEG sequences.
1. slow down with motion interpolation  -> PROMO_WORK/assets/gen/clips_raw/<name>/*.png
2. optional reframing (FOCUS): crop in on the tracked hands, blur the background
3. film grain, flicker and short RGB-split glitches -> PROMO_WORK/assets/gen/clips/<name>/*.jpg
usage: python prep3.py [PROMO_WORK] [--only name ...] [--keep-raw]
(videos in PROMO_WORK/assets/drive_video/; needs ffmpeg, numpy and Pillow)
"""
import os, sys, subprocess, shutil, glob
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from timeline import CLIPS, FPS, FOCUS, clip_glitches

args = sys.argv[1:]
keep_raw = "--keep-raw" in args
args = [a for a in args if a != "--keep-raw"]
only = args[args.index("--only") + 1:] if "--only" in args else None
if "--only" in args:
    args = args[:args.index("--only")]
W = args[0] if args else os.environ["PROMO_WORK"]
SRC = os.path.join(W, "assets", "drive_video")
RAW = os.path.join(W, "assets", "gen", "clips_raw")
OUT = os.path.join(W, "assets", "gen", "clips")


def ff(*a):
    subprocess.run(["ffmpeg", "-v", "error", "-y", *a], check=True)


def interp(track, f):
    for (f0, *a), (f1, *b) in zip(track, track[1:]):
        if f0 <= f <= f1:
            t = (f - f0) / (f1 - f0)
            return [u + (v - u) * t for u, v in zip(a, b)]
    return track[0][1:] if f < track[0][0] else track[-1][1:]


def smooth(track, n, k=9):
    pts = [interp(track, f) for f in range(n)]
    out = []
    for i in range(n):
        win = pts[max(0, i - k):i + k + 1]
        out.append([sum(p[j] for p in win) / len(win) for j in range(2)])
    return out


def focus(src_dir, dst_dir, cfg):
    import numpy as np
    from PIL import Image, ImageDraw, ImageFilter
    PAD = 240
    files = sorted(glob.glob(src_dir + "/*.png"))
    path = smooth(cfg["track"], len(files))
    z = cfg["zoom"]
    cw, ch = 1920 / z, 1080 / z
    ax, ay = cfg["sharp"]
    for f, (x, y) in zip(files, path):
        # edge-pad the source so the crop can centre a subject near the edge (the pad lands in the blur)
        a = np.asarray(Image.open(f).convert("RGB"))
        im = Image.fromarray(np.pad(a, ((PAD, PAD), (PAD, PAD), (0, 0)), mode="edge"))
        x0 = min(max(x - cw / 2, -PAD), 1920 + PAD - cw)
        y0 = min(max(y - ch / 2, -PAD), 1080 + PAD - ch)
        im = im.resize((1920, 1080), Image.LANCZOS, box=(x0 + PAD, y0 + PAD, x0 + PAD + cw, y0 + PAD + ch))
        # tracked point in output pixels -> centre of the sharp ellipse
        px, py = (x - x0) * z, (y - y0) * z
        mask = Image.new("L", (1920, 1080), 0)
        ImageDraw.Draw(mask).ellipse((px - ax, py - ay, px + ax, py + ay), fill=255)
        mask = mask.filter(ImageFilter.GaussianBlur(110))
        bg = im.filter(ImageFilter.GaussianBlur(cfg["blur"]))
        bg = Image.eval(bg, lambda v: int(v * 0.82))  # background also falls a little darker
        Image.composite(im, bg, mask).save(os.path.join(dst_dir, os.path.basename(f)))


for idx, (name, video, t0, _, n, _, _, speed) in enumerate(CLIPS):
    if only and name not in only:
        continue
    raw = os.path.join(RAW, name)
    d = os.path.join(OUT, name)
    for p in (raw, d):
        shutil.rmtree(p, ignore_errors=True)
        os.makedirs(p)
    ff("-ss", str(t0), "-t", f"{n / FPS * speed + 0.3:.3f}", "-i", os.path.join(SRC, video),
       "-vf", f"setpts=PTS/{speed},minterpolate=fps={FPS}:mi_mode=mci:mc_mode=aobmc:me_mode=bidir:vsbmc=1,"
              "scale=1920:1080:flags=lanczos",
       "-frames:v", str(n), os.path.join(raw, "%04d.png"))
    src = raw
    if name in FOCUS:
        src = raw + "_focus"
        shutil.rmtree(src, ignore_errors=True)
        os.makedirs(src)
        focus(raw, src, FOCUS[name])
    g = "+".join(f"between(n,{f},{f + 1})" for f in clip_glitches(idx, n))
    vf = ",".join([
        # unsteady exposure, like a failing bulb
        "eq=eval=frame:brightness='0.035*sin(n*1.31)*sin(n*0.23)-0.01*gt(random(1),0.93)'",
        "noise=alls=16:allf=t",                                   # film grain
        f"rgbashift=rh=-14:bh=14:gv=4:enable='{g}'",              # chromatic tear
        f"noise=alls=70:allf=t:enable='{g}'",                     # static burst
    ])
    ff("-framerate", str(FPS), "-i", os.path.join(src, "%04d.png"), "-vf", vf, "-q:v", "2",
       os.path.join(d, "%04d.jpg"))
    if not keep_raw:
        shutil.rmtree(raw, ignore_errors=True)
        shutil.rmtree(raw + "_focus", ignore_errors=True)
    print(name, len(os.listdir(d)), "frames")
