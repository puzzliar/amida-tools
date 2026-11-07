"""Assemble the promo in Blender's Video Sequence Editor and encode it.
usage: python edit.py <out.mp4|still_dir> [--stills f1 f2 ...] [--save file.blend] [--pct 100]
"""
import sys, os, glob, argparse
sys.path.insert(0, os.path.dirname(__file__))
import bpy
from timeline import *
from common import S, FONT_B, FONT_M, FONT_R

ap = argparse.ArgumentParser()
ap.add_argument("out")
ap.add_argument("--stills", nargs="*", type=int)
ap.add_argument("--save")
ap.add_argument("--pct", type=int, default=100)
args = ap.parse_args(sys.argv[1:])

G = S + "/assets/gen/"
RENDER = S + "/render/"

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.name = "Edit"
sc.render.fps = FPS
sc.render.resolution_x, sc.render.resolution_y = 1920, 1080
sc.render.resolution_percentage = args.pct
sc.frame_start, sc.frame_end = 1, TOTAL
sc.view_settings.view_transform = "Standard"
se = sc.sequence_editor_create()
ST = se.strips

COL = {"ivory": (0.96, 0.93, 0.87, 1), "gold": (1.0, 0.76, 0.36, 1), "red": (0.95, 0.22, 0.18, 1)}
fonts = {p: bpy.data.fonts.load(p) for p in (FONT_B, FONT_M, FONT_R)}
_vis_ch = [1]


def next_ch():
    _vis_ch[0] += 1
    return _vis_ch[0]


def kf(obj, path, frame, value, index=-1):
    if index >= 0:
        getattr(obj, path)[index] = value
        obj.keyframe_insert(path, frame=frame, index=index)
    else:
        setattr(obj, path, value)
        obj.keyframe_insert(path, frame=frame)


def kenburns(s, f0, n, scales, drift, base=(0, 0)):
    tr = s.transform
    bpy.context.preferences.edit.keyframe_new_interpolation_type = "LINEAR"
    bx, by = base
    for f, sc_, dx, dy in [(f0, scales[0], bx, by), (f0 + n, scales[1], bx + drift[0] * 1920, by + drift[1] * 1080)]:
        tr.scale_x = tr.scale_y = sc_
        tr.offset_x, tr.offset_y = dx, dy
        for p in ("scale_x", "scale_y", "offset_x", "offset_y"):
            tr.keyframe_insert(p, frame=f)
    bpy.context.preferences.edit.keyframe_new_interpolation_type = "BEZIER"


def grade(s, mult=0.82, sat=0.78, warm=True):
    s.color_saturation = sat
    s.color_multiply = mult
    m = s.modifiers.new("contrast", "BRIGHT_CONTRAST")
    m.bright = -4
    m.contrast = 18
    cb = s.modifiers.new("cb", "COLOR_BALANCE").color_balance
    cb.correction_method = "LIFT_GAMMA_GAIN"
    cb.lift = (0.97, 0.96, 0.98)
    cb.gamma = (1.0, 0.97, 0.92) if warm else (1, 1, 1)
    cb.gain = (1.06, 0.98, 0.88) if warm else (1, 1, 1)


def photo(fname, f0, n, scales, drift, fade_in=0, fade_out=0):
    s = ST.new_image(fname, G + "photos/" + fname, next_ch(), f0, fit_method="FILL")
    s.frame_final_duration = n + fade_out
    kenburns(s, f0, n + fade_out, scales, drift, PHOTO_OFFSET.get(fname, (0, 0)))
    grade(s)
    if fade_in:
        kf(s, "blend_alpha", f0, 0.0)
        kf(s, "blend_alpha", f0 + fade_in, 1.0)
    return s


def sequence(name, f0, n, offset=0, root=None, ext="png", fit="FIT"):
    files = sorted(glob.glob((root or RENDER) + name + "/*." + ext))[offset:]
    if not files:
        print("WARNING missing", name)
        return None
    s = ST.new_image(name, files[0], next_ch(), f0, fit_method=fit)
    for f in files[1:]:
        s.elements.append(os.path.basename(f))
    s.frame_final_duration = min(n, len(files))
    if len(files) < n:
        print("WARNING short sequence", name, len(files), n)
    return s


def flash(f, strength=0.85, n=9, col=(1.0, 0.9, 0.75)):
    c = ST.new_effect(f"flash{f}", "COLOR", 40, f, length=n)
    c.color = col
    c.blend_type = "ADD"
    kf(c, "blend_alpha", f, strength)
    kf(c, "blend_alpha", f + n, 0.0)


def overlay(path, f0, n, ch, alpha=1.0, fade=8):
    s = ST.new_image(os.path.basename(path), path, ch, f0, fit_method="FIT")
    s.frame_final_duration = n
    s.blend_type = "ALPHA_OVER"
    kf(s, "blend_alpha", f0, 0.0)
    kf(s, "blend_alpha", f0 + fade, alpha)
    kf(s, "blend_alpha", f0 + n - fade, alpha)
    kf(s, "blend_alpha", f0 + n, 0.0)
    return s


_tch = [50]


def caption(txt, f0, f1, y, size, col, fnt=FONT_B, x=0.5, fade=10, box=None, drift=0.008):
    ch = _tch[0]
    _tch[0] = 50 + (_tch[0] - 49) % 8
    s = ST.new_effect("t_" + txt[:6], "TEXT", ch, f0, length=f1 - f0)
    s.text = txt
    s.font = fonts[fnt]
    s.font_size = size
    s.color = COL[col] if isinstance(col, str) else col
    s.use_shadow = True
    s.shadow_color = (0, 0, 0, 0.9)
    s.shadow_blur = 0.7
    s.shadow_offset = 0.04  # relative to the font size (3 put a blurred copy a whole line below)
    s.anchor_x = "CENTER"
    s.anchor_y = "CENTER"
    s.alignment_x = "CENTER"
    s.blend_type = "ALPHA_OVER"
    if box:
        s.use_box = True
        s.box_color = box
        s.box_margin = 0.006
        s.use_shadow = False
    bpy.context.preferences.edit.keyframe_new_interpolation_type = "LINEAR"
    s.location = (x, y - drift / 2)
    s.keyframe_insert("location", frame=f0)
    s.location = (x, y + drift / 2)
    s.keyframe_insert("location", frame=f1)
    bpy.context.preferences.edit.keyframe_new_interpolation_type = "BEZIER"
    kf(s, "blend_alpha", f0, 0.0)
    kf(s, "blend_alpha", f0 + fade, 1.0)
    kf(s, "blend_alpha", f1 - fade, 1.0)
    kf(s, "blend_alpha", f1, 0.0)
    return s


# ------------------------------------------------------------------ A: cold open
a1 = photo(*COLD_OPEN[0], fade_in=24, fade_out=10)
a2 = photo(*COLD_OPEN[1], fade_in=10)

# ------------------------------------------------------------------ 3D shots
for name, f0, n, *off in SHOTS3D:
    s3 = sequence(name, f0, n, off[0] if off else 0)
    if name == "cards" and s3:
        s3.color_multiply = 0.8  # the spot-lit tabletop sits much brighter than the shots around it
    if name == "screens" and s3:
        # push in on the panels so the presentation tool reads (timer, amida board, results)
        kenburns(s3, f0, n, (1.28, 1.40), (0.0, 0.0))

# official logotype (cut from the key art) over the title shot, so the opening matches the ending
T0 = dict((n_, f_) for n_, f_, *_ in SHOTS3D)["title"]
logo = ST.new_image("title_logo", G + "title_logo.png", 45, T0 + 8, fit_method="ORIGINAL")
logo.frame_final_duration = 150 - 8
logo.blend_type = "ALPHA_OVER"
bpy.context.preferences.edit.keyframe_new_interpolation_type = "LINEAR"
for f, sc_ in [(T0 + 8, 0.70), (T0 + 150, 0.76)]:
    logo.transform.scale_x = logo.transform.scale_y = sc_
    logo.transform.offset_y = 40
    for p_ in ("scale_x", "scale_y", "offset_y"):
        logo.transform.keyframe_insert(p_, frame=f)
bpy.context.preferences.edit.keyframe_new_interpolation_type = "BEZIER"
kf(logo, "blend_alpha", T0 + 8, 0.0)
kf(logo, "blend_alpha", T0 + 34, 1.0)
kf(logo, "blend_alpha", T0 + 140, 1.0)
kf(logo, "blend_alpha", T0 + 150, 0.0)

# ------------------------------------------------------------------ live-action chip footage
for i, (name, _, _, f0, n, scales, drift, *_) in enumerate(CLIPS):
    s = sequence(name, f0, n, root=G + "clips/", ext="jpg", fit="FILL")
    if s:
        kenburns(s, f0, n, scales, drift)
        grade(s, mult=0.80, sat=0.80)
    flash(f0, 0.6 if i == 0 else 0.4, 6)

# ------------------------------------------------------------------ F: montage (hard cuts + flashes)
for i, m in enumerate(MONTAGE):
    photo(*m)
    if i:
        flash(m[1], 0.55, 6)

# ------------------------------------------------------------------ H: key art + booking card
hero = ST.new_image("hero", G + "hero.png", next_ch(), END_START, fit_method="FIT")
hero.frame_final_duration = TOTAL - END_START + 1
# kenburns() sets transform.scale directly (overriding FIT), so scale the 1672x941 key art to the frame width
_k = 1920 / hero.elements[0].orig_width if hero.elements[0].orig_width else 1920 / 1672
kenburns(hero, END_START, TOTAL - END_START, (_k, _k * 1.03), (0.0, 0.0))  # gentle: keep the info boxes in frame
kf(hero, "blend_alpha", END_START, 0.0)
kf(hero, "blend_alpha", END_START + 14, 1.0)

# flashes on every hit
for h in HITS:
    # 0:48 cuts to an already bright tabletop: keep that flash small so the frame does not wash out
    flash(int(round(h * FPS)) + 1, 0.9 if h in (13.0, 58.0) else 0.2 if h == 48.0 else 0.7, 10)

# overlays: vignette on photo sections, bottom gradient under lower captions
for f0, n in [(1, 150), (931, 510), (1441, 180)]:
    overlay(G + "vignette.png", f0, n, 30, 1.0, fade=4)
for f0, n in [(151, 240), (541, 300), (841, 600), (1441, 180)]:
    overlay(G + "bottomgrad.png", f0 + 20, n - 20, 31, 1.0, fade=14)

# ------------------------------------------------------------------ captions
for txt, f0, f1, y, size, col, _ in CAPTIONS:
    caption(txt, f0, f1, y, size, col)

# end: the key art already carries title, tagline, players and running time - only add the booking plate
overlay(G + "booking.png", END_CARD, TOTAL - END_CARD + 1, 32, 1.0, fade=12)

# fade to black at the very end
blk = ST.new_effect("black", "COLOR", 60, TOTAL - 14, length=15)
blk.color = (0, 0, 0)
kf(blk, "blend_alpha", TOTAL - 14, 0.0)
kf(blk, "blend_alpha", TOTAL, 1.0)

# ------------------------------------------------------------------ audio
snd = ST.new_sound("score", S + "/assets/audio/score.wav", 70, 1)

if args.save:
    bpy.ops.wm.save_as_mainfile(filepath=args.save)

r = sc.render
if args.stills:
    r.image_settings.media_type = "IMAGE"
    r.image_settings.file_format = "JPEG"
    r.image_settings.quality = 90
    os.makedirs(args.out, exist_ok=True)
    for f in args.stills:
        sc.frame_set(f)
        r.filepath = os.path.join(args.out, f"f{f:04d}.jpg")
        bpy.ops.render.render(write_still=True)
else:
    r.image_settings.media_type = "VIDEO"
    r.image_settings.file_format = "FFMPEG"
    r.ffmpeg.format = "MPEG4"
    r.ffmpeg.codec = "H264"
    r.ffmpeg.constant_rate_factor = "HIGH"
    r.ffmpeg.ffmpeg_preset = "GOOD"
    r.ffmpeg.gopsize = 30
    r.ffmpeg.audio_codec = "AAC"
    r.ffmpeg.audio_bitrate = 256
    r.ffmpeg.audio_mixrate = 48000
    r.ffmpeg.audio_channels = "STEREO"
    r.filepath = args.out
    bpy.ops.render.render(animation=True)
print("EDIT DONE")
