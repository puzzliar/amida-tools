import sys
from PIL import Image, ImageDraw
import os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from timeline import *
S = sys.argv[1]; D = S + "/assets/drive/"; G = S + "/assets/gen/"
import os; os.makedirs(G + "photos", exist_ok=True)
for f, *_ in COLD_OPEN + MONTAGE:
    Image.open(D + f).convert("RGB").resize((2560, 1920), Image.LANCZOS).save(G + "photos/" + f, quality=93)
Image.open(D + "hero_amida.png").convert("RGB").save(G + "hero.png")
# ornamental frame for the end card (gold, like the presentation tool's border)
W, H, SS = 1920, 1080, 2
im = Image.new("RGBA", (W * SS, H * SS), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
gold = (226, 170, 80, 235); gold2 = (226, 170, 80, 140)
def rect(m, c, w): d.rectangle([m * SS, m * SS, (W - m) * SS, (H - m) * SS], outline=c, width=w * SS)
rect(26, gold, 2); rect(36, gold2, 1)
def diamond(cx, cy, r, c):
    d.polygon([(cx * SS, (cy - r) * SS), ((cx + r) * SS, cy * SS), (cx * SS, (cy + r) * SS), ((cx - r) * SS, cy * SS)], fill=c)
for cx, cy in [(W / 2, 26), (W / 2, H - 26)]:
    diamond(cx, cy, 9, (10, 8, 6, 255)); diamond(cx, cy, 7, gold); diamond(cx, cy, 3, (200, 40, 30, 255))
for cx in (26, W - 26):
    for cy in (26, H - 26):
        diamond(cx, cy, 6, gold)
# divider lines around the booking plate & title
# booking plate
d.rectangle([660 * SS, 652 * SS, 1260 * SS, 762 * SS], fill=(118, 12, 9, 238))
d.rectangle([660 * SS, 652 * SS, 1260 * SS, 762 * SS], outline=gold, width=2 * SS)
d.rectangle([668 * SS, 660 * SS, 1252 * SS, 754 * SS], outline=gold2, width=1 * SS)
for cx in (660, 1260):
    diamond(cx, 707, 7, gold)
for y, half, gap in [(330, 330, 190), (812, 360, 0)]:
    if gap:
        d.line([((W / 2 - half) * SS, y * SS), ((W / 2 - gap) * SS, y * SS)], fill=gold, width=2 * SS)
        d.line([((W / 2 + gap) * SS, y * SS), ((W / 2 + half) * SS, y * SS)], fill=gold, width=2 * SS)
    else:
        d.line([((W / 2 - half) * SS, y * SS), ((W / 2 + half) * SS, y * SS)], fill=gold2, width=1 * SS)
        diamond(W / 2, y, 6, gold)
im.resize((W, H), Image.LANCZOS).save(G + "endframe.png")
print("ok")
