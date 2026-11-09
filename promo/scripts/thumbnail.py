"""Video thumbnails (1280x720) with the hook line, the official logotype and a booking badge.
usage: python thumbnail.py [PROMO_WORK] [--layout chips|amida] out.png
  chips : the chip hand-over from the live-action footage (thumbnail.png)
  amida : the radial amida from the 3D build shot at 0:11 (thumbnail_amida.png)
(needs ffmpeg, numpy, scipy, Pillow; run prep2.py first for title_logo.png)
"""
import os, sys, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont
from scipy import ndimage as ndi

args = sys.argv[1:]
layout = "chips"
if "--layout" in args:
    i = args.index("--layout")
    layout = args[i + 1]
    del args[i:i + 2]
W_ = args[0] if len(args) > 1 else os.environ["PROMO_WORK"]
OUT = args[-1]
G = os.path.join(W_, "assets", "gen")
FB = "/usr/share/fonts/opentype/noto/NotoSerifCJK-Black.ttc"
FM = "/usr/share/fonts/opentype/noto/NotoSerifCJK-Bold.ttc"
W, H, SS = 1280, 720, 2          # draw at 2x, downsample at the end
WW, HH = W * SS, H * SS
GOLD = (232, 186, 104, 255)
yy, xx = np.mgrid[0:HH, 0:WW]


def bg_chips():
    src_video = os.path.join(W_, "assets", "drive_video", "PXL_20261017_042358932.mp4")
    frame = os.path.join(W_, "thumb_src.png")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", "9.5", "-i", src_video, "-frames:v", "1", frame], check=True)
    src = np.asarray(Image.open(frame).convert("RGB"))
    # extend the bottom edge (it ends up blurred and dark under the logo) so the chips can sit
    # in the clear band between the hook line and the logo instead of behind the logotype
    src = Image.fromarray(np.pad(src, ((0, 300), (0, 0), (0, 0)), mode="edge"))
    crop = (40, 420, 1640, 1320)                     # chips right of centre, at ~45% height
    a = np.asarray(src.crop(crop).resize((WW, HH), Image.LANCZOS)).astype(float) / 255
    # focus: chips/hands sharp, the rest blurred (like the slow-motion shots)
    cx, cy = (960 - crop[0]) / (crop[2] - crop[0]) * WW, (800 - crop[1]) / (crop[3] - crop[1]) * HH
    d = np.sqrt(((xx - cx) / (0.30 * WW)) ** 2 + ((yy - cy) / (0.36 * HH)) ** 2)
    focus = np.clip(1.6 - d, 0, 1)[..., None]
    blur = np.stack([ndi.gaussian_filter(a[..., c], 14 * SS) for c in range(3)], -1)
    a = a * focus + blur * (1 - focus)
    # grade: deep crimson, crushed blacks, warm highlights
    lum = a @ [0.3, 0.59, 0.11]
    a = a * 0.55 + lum[..., None] * 0.45 * np.array([1.05, 0.62, 0.52])
    a = np.clip((a - 0.04) * 1.25, 0, 1) ** 1.15
    # vignette + dark wash on the left (type) and bottom (logo)
    vig = np.clip(1 - 0.85 * (((xx - cx) / WW) ** 2 + ((yy - HH * 0.5) / HH) ** 2) * 2.2, 0.15, 1)
    left = np.clip(1 - (1 - xx / (WW * 0.55)) * 0.75, 0.25, 1)
    bottom = np.clip(1 - (yy / HH - 0.62) / 0.38 * 0.8, 0.2, 1)
    return a * (vig * np.minimum(left, bottom))[..., None]


def bg_amida():
    # frame 181 of the build shot = 0:11 in the edit (fully built radial amida, no flashes)
    src = Image.open(os.path.join(W_, "render", "build", "0181.png")).convert("RGB")
    a = np.asarray(src.resize((WW, HH), Image.LANCZOS)).astype(float) / 255
    # push the dish down so its hub sits under the logo and the starfield above holds the hook line
    shift = 110 * SS
    top = np.zeros((shift, WW, 3)) + a[:12].mean((0, 1))
    rng = np.random.default_rng(5)
    for _ in range(70):                               # extend the starfield into the new strip
        x, y, r = rng.integers(0, WW), rng.integers(0, shift), rng.uniform(1.0, 2.6) * SS
        g = np.exp(-(((xx[:shift] - x) ** 2 + (yy[:shift] - y) ** 2) / (2 * r * r)))
        top += g[..., None] * np.array([1.0, 0.82, 0.5]) * rng.uniform(0.3, 0.9)
    a = np.concatenate([top, a[:HH - shift]], 0)
    # slightly deeper blacks; darken the centre band behind the logo and the bottom behind the badge
    a = np.clip((a - 0.02) * 1.08, 0, 1)
    band = 1 - 0.55 * np.exp(-((yy / HH - 0.47) / 0.11) ** 2)
    bottom = np.clip(1 - (yy / HH - 0.72) / 0.28 * 0.55, 0.45, 1)
    vig = np.clip(1 - 0.9 * (((xx - WW / 2) / WW) ** 2 + ((yy - HH * 0.55) / HH) ** 2) * 1.6, 0.25, 1)
    return a * (band * bottom * vig)[..., None]


a = bg_chips() if layout == "chips" else bg_amida()
im = Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8)).convert("RGBA")


def shadow_text(xy, txt, font, fill, anchor="la", shadow=10, spread=4, alpha=230):
    lay = Image.new("RGBA", im.size, (0, 0, 0, 0))
    ImageDraw.Draw(lay).text(xy, txt, font=font, fill=(0, 0, 0, alpha), anchor=anchor,
                             stroke_width=spread * SS, stroke_fill=(0, 0, 0, alpha))
    im.alpha_composite(lay.filter(ImageFilter.GaussianBlur(shadow * SS)))
    ImageDraw.Draw(im).text(xy, txt, font=font, fill=fill, anchor=anchor,
                            stroke_width=2 * SS, stroke_fill=(20, 6, 4, 255))


def badge(bx0, by0, bx1, by1, size=38):
    glow = Image.new("RGBA", im.size, (0, 0, 0, 0))
    ImageDraw.Draw(glow).rectangle([(bx0 - 14) * SS, (by0 - 12) * SS, (bx1 + 14) * SS, (by1 + 12) * SS], fill=(0, 0, 0, 170))
    im.alpha_composite(glow.filter(ImageFilter.GaussianBlur(12 * SS)))
    dr = ImageDraw.Draw(im)
    dr.rectangle([bx0 * SS, by0 * SS, bx1 * SS, by1 * SS], fill=(150, 14, 10, 245), outline=GOLD, width=3 * SS)
    dr.rectangle([(bx0 + 6) * SS, (by0 + 6) * SS, (bx1 - 6) * SS, (by1 - 6) * SS], outline=(232, 186, 104, 140), width=1 * SS)
    f_b = ImageFont.truetype(FB, size * SS, index=0)
    dr.text(((bx0 + bx1) / 2 * SS, (by0 + by1) / 2 * SS + 1 * SS), "貸切予約受付中", font=f_b, fill=(250, 232, 190, 255), anchor="mm")


def place_logo(width, cx, cy=None, bottom=None):
    logo = Image.open(os.path.join(G, "title_logo.png")).convert("RGBA")
    lw = width * SS
    logo = logo.resize((lw, int(logo.height * lw / logo.width)), Image.LANCZOS)
    lx = int(cx * SS - lw / 2)
    ly = int(cy * SS - logo.height / 2) if cy is not None else HH - logo.height - bottom * SS
    # dark halo so the gold reads over the background
    halo = Image.new("RGBA", im.size, (0, 0, 0, 0))
    halo.alpha_composite(Image.merge("RGBA", (*[Image.new("L", logo.size, 0)] * 3, logo.getchannel("A"))), (lx, ly))
    halo = halo.filter(ImageFilter.GaussianBlur(16 * SS))
    halo.putalpha(halo.getchannel("A").point(lambda v: min(255, int(v * 2.4))))
    im.alpha_composite(halo)
    # a little warm bloom on the glyphs
    bloom = Image.new("RGBA", im.size, (0, 0, 0, 0))
    bloom.alpha_composite(logo, (lx, ly))
    bloom = bloom.filter(ImageFilter.GaussianBlur(10 * SS))
    bloom.putalpha(bloom.getchannel("A").point(lambda v: int(v * 0.45)))
    im.alpha_composite(bloom)
    im.alpha_composite(logo, (lx, ly))
    return ly / SS, (ly + logo.height) / SS


if layout == "chips":
    f_hook = ImageFont.truetype(FB, 104 * SS, index=0)
    shadow_text((56 * SS, 40 * SS), "その言葉、", f_hook, (246, 238, 226, 255))
    shadow_text((56 * SS, 168 * SS), "信じるか。", f_hook, (236, 52, 40, 255))
    shadow_text((62 * SS, 318 * SS), "アミダクジ × リアル交渉ゲーム", ImageFont.truetype(FM, 34 * SS, index=0), GOLD, shadow=6, spread=3)
    badge(952, 36, 1244, 104)
    place_logo(1180, W / 2, bottom=34)
else:
    # poster layout: hook on the starfield, logo across the dish, kicker + badge at the bottom
    f_hook = ImageFont.truetype(FB, 92 * SS, index=0)
    hook_w = ImageDraw.Draw(im).textlength("その言葉、信じるか。", font=f_hook)
    x0 = (WW - hook_w) / 2
    first_w = ImageDraw.Draw(im).textlength("その言葉、", font=f_hook)
    shadow_text((x0, 34 * SS), "その言葉、", f_hook, (246, 238, 226, 255))
    shadow_text((x0 + first_w, 34 * SS), "信じるか。", f_hook, (236, 52, 40, 255))
    top, bot = place_logo(1160, W / 2, cy=338)
    f_k = ImageFont.truetype(FM, 36 * SS, index=0)
    ky = bot + 34
    kw = ImageDraw.Draw(im).textlength("アミダクジ × リアル交渉ゲーム", font=f_k) / SS
    plate = Image.new("RGBA", im.size, (0, 0, 0, 0))   # soft dark ribbon so the kicker reads over the spokes
    ImageDraw.Draw(plate).rectangle([(W / 2 - kw / 2 - 40) * SS, (ky - 8) * SS, (W / 2 + kw / 2 + 40) * SS, (ky + 52) * SS], fill=(6, 3, 2, 215))
    im.alpha_composite(plate.filter(ImageFilter.GaussianBlur(14 * SS)))
    shadow_text((W / 2 * SS, ky * SS), "アミダクジ × リアル交渉ゲーム", f_k, GOLD, anchor="mt", shadow=6, spread=3)
    badge(W / 2 - 170, 600, W / 2 + 170, 674, size=42)

out = im.resize((W, H), Image.LANCZOS).convert("RGB")
out.save(OUT)
if OUT.endswith(".png"):
    out.save(OUT[:-4] + ".jpg", quality=92)
print("wrote", OUT)
