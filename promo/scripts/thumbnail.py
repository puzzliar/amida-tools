"""Video thumbnail (1280x720): the chip hand-over, a hook line, the official logotype and a booking badge.
usage: python thumbnail.py [PROMO_WORK] out.png   (needs ffmpeg, numpy, scipy, Pillow; run prep2.py first)
"""
import os, sys, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont
from scipy import ndimage as ndi

W_ = sys.argv[1] if len(sys.argv) > 2 else os.environ["PROMO_WORK"]
OUT = sys.argv[-1]
G = os.path.join(W_, "assets", "gen")
SRC = os.path.join(W_, "assets", "drive_video", "PXL_20261017_042358932.mp4")
FB = "/usr/share/fonts/opentype/noto/NotoSerifCJK-Black.ttc"
FM = "/usr/share/fonts/opentype/noto/NotoSerifCJK-Bold.ttc"
W, H, SS = 1280, 720, 2          # draw at 2x, downsample at the end
WW, HH = W * SS, H * SS

# ---------------------------------------------------------------- background: the hand-over, graded and focused
frame = os.path.join(W_, "thumb_src.png")
subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", "9.5", "-i", SRC, "-frames:v", "1", frame], check=True)
src = np.asarray(Image.open(frame).convert("RGB"))
# extend the bottom edge (it ends up blurred and dark under the logo) so the chips can sit
# in the clear band between the hook line and the logo instead of behind the logotype
PAD = 300
src = Image.fromarray(np.pad(src, ((0, PAD), (0, 0), (0, 0)), mode="edge"))
crop = (40, 420, 1640, 1320)                     # chips right of centre, at ~45% height
bg = src.crop(crop).resize((WW, HH), Image.LANCZOS)
a = np.asarray(bg).astype(float) / 255
# focus: chips/hands sharp, the rest blurred (like the slow-motion shots)
cx, cy = (960 - crop[0]) / (crop[2] - crop[0]) * WW, (800 - crop[1]) / (crop[3] - crop[1]) * HH
yy, xx = np.mgrid[0:HH, 0:WW]
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
a = a * (vig * np.minimum(left, bottom))[..., None]
im = Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8)).convert("RGBA")
dr = ImageDraw.Draw(im)


def shadow_text(xy, txt, font, fill, anchor="la", shadow=10, spread=4, alpha=230):
    lay = Image.new("RGBA", im.size, (0, 0, 0, 0))
    ld = ImageDraw.Draw(lay)
    ld.text(xy, txt, font=font, fill=(0, 0, 0, alpha), anchor=anchor, stroke_width=spread * SS, stroke_fill=(0, 0, 0, alpha))
    lay = lay.filter(ImageFilter.GaussianBlur(shadow * SS))
    im.alpha_composite(lay)
    ImageDraw.Draw(im).text(xy, txt, font=font, fill=fill, anchor=anchor,
                            stroke_width=2 * SS, stroke_fill=(20, 6, 4, 255))


# ---------------------------------------------------------------- hook line (top left)
f_hook = ImageFont.truetype(FB, 104 * SS, index=0)
shadow_text((56 * SS, 40 * SS), "その言葉、", f_hook, (246, 238, 226, 255))
shadow_text((56 * SS, 168 * SS), "信じるか。", f_hook, (236, 52, 40, 255))
# kicker under the hook
f_k = ImageFont.truetype(FM, 34 * SS, index=0)
gold = (232, 186, 104, 255)
shadow_text((62 * SS, 318 * SS), "アミダクジ × リアル交渉ゲーム", f_k, gold, shadow=6, spread=3)

# ---------------------------------------------------------------- booking badge (top right)
dr = ImageDraw.Draw(im)
bx0, by0, bx1, by1 = 952, 36, 1244, 104
glow = Image.new("RGBA", im.size, (0, 0, 0, 0))
ImageDraw.Draw(glow).rectangle([(bx0 - 14) * SS, (by0 - 12) * SS, (bx1 + 14) * SS, (by1 + 12) * SS], fill=(0, 0, 0, 170))
im.alpha_composite(glow.filter(ImageFilter.GaussianBlur(12 * SS)))
dr = ImageDraw.Draw(im)
dr.rectangle([bx0 * SS, by0 * SS, bx1 * SS, by1 * SS], fill=(150, 14, 10, 245), outline=gold, width=3 * SS)
dr.rectangle([(bx0 + 6) * SS, (by0 + 6) * SS, (bx1 - 6) * SS, (by1 - 6) * SS], outline=(232, 186, 104, 140), width=1 * SS)
f_b = ImageFont.truetype(FB, 38 * SS, index=0)
dr.text(((bx0 + bx1) / 2 * SS, (by0 + by1) / 2 * SS + 1 * SS), "貸切予約受付中", font=f_b, fill=(250, 232, 190, 255), anchor="mm")

# ---------------------------------------------------------------- official logotype (bottom, full width)
logo = Image.open(os.path.join(G, "title_logo.png")).convert("RGBA")
lw = 1180 * SS
logo = logo.resize((lw, int(logo.height * lw / logo.width)), Image.LANCZOS)
lx, ly = (WW - lw) // 2, HH - logo.height - 34 * SS
# dark halo so the gold reads over the hands
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

out = im.resize((W, H), Image.LANCZOS).convert("RGB")
out.save(OUT)
if OUT.endswith(".png"):
    out.save(OUT[:-4] + ".jpg", quality=92)
print("wrote", OUT)
