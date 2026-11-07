import sys
from PIL import Image, ImageDraw
import os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from timeline import *
S = sys.argv[1]; D = S + "/assets/drive/"; G = S + "/assets/gen/"
import os; os.makedirs(G + "photos", exist_ok=True)
for f, *_ in COLD_OPEN + MONTAGE:
    Image.open(D + f).convert("RGB").resize((2560, 1920), Image.LANCZOS).save(G + "photos/" + f, quality=93)
Image.open(D + "hero_amida.png").convert("RGB").save(G + "hero.png")
# ---------------------------------------------------------------- official logotype cut out of the key art
# (bright, low-saturation gold glyphs; the orange floor pattern and small specks are rejected)
import numpy as np
from scipy import ndimage as ndi
a = np.asarray(Image.open(D + "hero_amida.png").convert("RGB")).astype(float) / 255
c = a[350:585, 170:1490]
mx, mn = c.max(2), c.min(2)
sat = (mx - mn) / (mx + 1e-6)
lum = 0.3 * c[..., 0] + 0.59 * c[..., 1] + 0.11 * c[..., 2]
m = ndi.binary_closing((lum > 0.36) & (sat < 0.66), iterations=2)
lab, n = ndi.label(m)
sizes = np.array(ndi.sum(m, lab, range(1, n + 1)))
keep = np.zeros(n + 1, bool); keep[1:] = sizes > 120
m = ndi.binary_dilation(ndi.binary_fill_holes(keep[lab]), iterations=2)
al = ndi.gaussian_filter(m.astype(float), 1.0)
al[212:, :] = 0                      # ornament rule under the title
al[9:47, 1105:1145] = 0              # stray glint above ク
ys, xs = np.where(al > 0.05)
x0, y0, x1, y1 = max(xs.min() - 6, 0), max(ys.min() - 6, 0), xs.max() + 7, ys.max() + 7
rgba = np.dstack([c, al])[y0:y1, x0:x1]
Image.fromarray((np.clip(rgba, 0, 1) * 255).astype(np.uint8), "RGBA").save(G + "title_logo.png")

# ---------------------------------------------------------------- booking call to action over the key art
from PIL import ImageFont, ImageFilter
import qrcode
W, H, SS = 1920, 1080, 2
im = Image.new("RGBA", (W * SS, H * SS), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
gold = (226, 176, 92, 245); gold2 = (226, 176, 92, 150)
def diamond(cx, cy, r, c):
    d.polygon([(cx * SS, (cy - r) * SS), ((cx + r) * SS, cy * SS), (cx * SS, (cy + r) * SS), ((cx - r) * SS, cy * SS)], fill=c)
def halo(box, pad=30, alpha=170, blur=24):
    global im, d
    h = Image.new("RGBA", im.size, (0, 0, 0, 0))
    ImageDraw.Draw(h).rectangle([(box[0] - pad) * SS, (box[1] - pad) * SS, (box[2] + pad) * SS, (box[3] + pad) * SS], fill=(0, 0, 0, alpha))
    im = Image.alpha_composite(im, h.filter(ImageFilter.GaussianBlur(blur * SS))); d = ImageDraw.Draw(im)
FB = "/usr/share/fonts/opentype/noto/NotoSerifCJK-Black.ttc"
FM = "/usr/share/fonts/opentype/noto/NotoSerifCJK-Bold.ttc"
def ctext(txt, size, cy, fill, fpath=FB):
    f = ImageFont.truetype(fpath, size * SS, index=0)
    tw = d.textlength(txt, font=f)
    d.text((W / 2 * SS + 2 * SS - tw / 2, cy * SS + 2 * SS), txt, font=f, fill=(0, 0, 0, 200), anchor="lm")
    d.text((W / 2 * SS - tw / 2, cy * SS), txt, font=f, fill=fill, anchor="lm")
# plate: two lines, bottom centre between the logo and the info boxes
X0, Y0, X1, Y1 = 620, 906, 1300, 1050
halo((X0, Y0, X1, Y1))
d.rectangle([X0 * SS, Y0 * SS, X1 * SS, Y1 * SS], fill=(112, 10, 8, 240))
d.rectangle([X0 * SS, Y0 * SS, X1 * SS, Y1 * SS], outline=gold, width=2 * SS)
d.rectangle([(X0 + 8) * SS, (Y0 + 8) * SS, (X1 - 8) * SS, (Y1 - 8) * SS], outline=gold2, width=1 * SS)
for cx in (X0, X1):
    diamond(cx, (Y0 + Y1) / 2, 9, (10, 8, 6, 255)); diamond(cx, (Y0 + Y1) / 2, 7, gold)
ctext("貸切予約　受付中", 54, 952, (244, 214, 150, 255))
d.line([((W / 2 - 230) * SS, 990 * SS), ((W / 2 + 230) * SS, 990 * SS)], fill=gold2, width=1 * SS)
diamond(W / 2, 990, 4, gold)
url = BOOKING_URL.split("://")[-1].rstrip("/")
ctext(f"詳細・ご予約は　{url}", 30, 1020, (245, 236, 220, 255), FM)
# QR code, top right over the dark pillars
q = qrcode.QRCode(border=2, box_size=10, error_correction=qrcode.constants.ERROR_CORRECT_M)
q.add_data(BOOKING_URL); q.make(fit=True)
qr = q.make_image(fill_color=(16, 12, 10), back_color=(246, 238, 222)).convert("RGBA").resize((150 * SS, 150 * SS), Image.NEAREST)
QX, QY = 1722, 34
halo((QX - 10, QY - 10, QX + 160, QY + 196), pad=16, alpha=150, blur=14)
d.rectangle([(QX - 8) * SS, (QY - 8) * SS, (QX + 158) * SS, (QY + 194) * SS], fill=(14, 10, 8, 235), outline=gold, width=2 * SS)
im.alpha_composite(qr, (QX * SS, QY * SS)); d = ImageDraw.Draw(im)
f = ImageFont.truetype(FM, 19 * SS, index=0)
t = "ご予約・詳細"
d.text(((QX + 75) * SS - d.textlength(t, font=f) / 2, (QY + 172) * SS), t, font=f, fill=(244, 214, 150, 255), anchor="lm")
im.resize((W, H), Image.LANCZOS).save(G + "booking.png")
print("ok")
