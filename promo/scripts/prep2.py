import sys
from PIL import Image, ImageDraw
import os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from timeline import *
S = sys.argv[1]; D = S + "/assets/drive/"; G = S + "/assets/gen/"
import os; os.makedirs(G + "photos", exist_ok=True)
for f, *_ in COLD_OPEN + MONTAGE:
    Image.open(D + f).convert("RGB").resize((2560, 1920), Image.LANCZOS).save(G + "photos/" + f, quality=93)
Image.open(D + "hero_amida.png").convert("RGB").save(G + "hero.png")
# booking plate laid over the key art at the end (bottom centre, between the logo and the info boxes)
from PIL import ImageFont, ImageFilter
W, H, SS = 1920, 1080, 2
im = Image.new("RGBA", (W * SS, H * SS), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
gold = (226, 176, 92, 245); gold2 = (226, 176, 92, 150)
def diamond(cx, cy, r, c):
    d.polygon([(cx * SS, (cy - r) * SS), ((cx + r) * SS, cy * SS), (cx * SS, (cy + r) * SS), ((cx - r) * SS, cy * SS)], fill=c)
X0, Y0, X1, Y1 = 650, 952, 1270, 1040
cy = (Y0 + Y1) / 2
# soft dark halo so the plate separates from the silhouettes behind it
halo = Image.new("RGBA", im.size, (0, 0, 0, 0))
ImageDraw.Draw(halo).rectangle([(X0 - 30) * SS, (Y0 - 24) * SS, (X1 + 30) * SS, (Y1 + 24) * SS], fill=(0, 0, 0, 170))
im = Image.alpha_composite(im, halo.filter(ImageFilter.GaussianBlur(24 * SS))); d = ImageDraw.Draw(im)
d.rectangle([X0 * SS, Y0 * SS, X1 * SS, Y1 * SS], fill=(112, 10, 8, 240))
d.rectangle([X0 * SS, Y0 * SS, X1 * SS, Y1 * SS], outline=gold, width=2 * SS)
d.rectangle([(X0 + 8) * SS, (Y0 + 8) * SS, (X1 - 8) * SS, (Y1 - 8) * SS], outline=gold2, width=1 * SS)
for cx in (X0, X1):
    diamond(cx, cy, 9, (10, 8, 6, 255)); diamond(cx, cy, 7, gold)
font = ImageFont.truetype("/usr/share/fonts/opentype/noto/NotoSerifCJK-Black.ttc", 54 * SS, index=0)
txt = "貸切予約　受付中"
tw = d.textlength(txt, font=font)
d.text((W / 2 * SS + 3 * SS - tw / 2, cy * SS + 3 * SS), txt, font=font, fill=(0, 0, 0, 200), anchor="lm")
d.text((W / 2 * SS - tw / 2, cy * SS), txt, font=font, fill=(244, 214, 150, 255), anchor="lm")
im.resize((W, H), Image.LANCZOS).save(G + "booking.png")
print("ok")
