"""Build & render the 3D shots of the 削減アミダクジ promo.
usage: python scenes3d.py <shot> <outdir> [--frames a b] [--res 960 540] [--samples n] [--save blend]
shots: build, title, rule, screens, cards
"""
import sys, os, math, random, argparse
sys.path.insert(0, os.path.dirname(__file__))
import bpy
from mathutils import Vector
from common import *

ap = argparse.ArgumentParser()
ap.add_argument("shot")
ap.add_argument("outdir")
ap.add_argument("--frames", nargs=2, type=int)
ap.add_argument("--res", nargs=2, type=int, default=[1920, 1080])
ap.add_argument("--samples", type=int, default=10)
ap.add_argument("--save")
ap.add_argument("--only", nargs="*", type=int)
args = ap.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:])

PRES = ASSETS + "/present/"
GEN = ASSETS + "/gen/"

# ------------------------------------------------------------------ amida route setup (shared by build/rule)
AM = Amida()
REMOVE, ROUTE_START = None, 7   # spoke index 7 = player 8 (blue 8 medals)


def pick_removal():
    """Choose 18 rungs to remove so that player 8 gets the unique shortest route."""
    rnd = random.Random(11)
    best = None
    for _ in range(4000):
        rem = set(rnd.sample(range(len(AM.rungs)), 18))
        active = [k not in rem for k in range(len(AM.rungs))]
        counts = [AM.trace(i, active)[1] for i in range(AM.n)]
        b = counts[ROUTE_START]
        others = sorted(c for i, c in enumerate(counts) if i != ROUTE_START)
        if b < others[0]:
            score = (b, -others[0])
            if best is None or score < best[0]:
                best = (score, rem, counts)
    return best


SCORE, REMOVE, COUNTS = pick_removal()
ACTIVE = [k not in REMOVE for k in range(len(AM.rungs))]


def amida_scene_base(frames, dust_n=180):
    sc = reset(samples=args.samples, res=tuple(args.res))
    sc.frame_start, sc.frame_end = 1, frames
    AM.build()
    dust(dust_n, frames=frames)
    compositor(threshold=0.9, strength=0.55, size=0.62)
    return sc


# ------------------------------------------------------------------ shot B: amida materialises
def shot_build():
    F = 252
    sc = amida_scene_base(F)
    cam, tgt = camera(32, dof=4.0)
    # spokes grow outward
    for i, o in enumerate(AM.spokes):
        f0 = 8 + i * 2
        key(o, "scale", f0, 0.0001, index=0)
        o.scale[0] = (AM.pt(i, AM.r_out + 0.25) - AM.pt(i, AM.r_in)).length
        o.keyframe_insert("scale", frame=f0 + 28, index=0)
        alpha_key(o, f0, 0.0)
        alpha_key(o, f0 + 6, 1.6)
        alpha_key(o, f0 + 30, 0.9)
    # rungs pop in, outer ring first
    order = sorted(range(len(AM.rungs)), key=lambda k: (-AM.rungs[k][1], AM.rungs[k][0]))
    for j, k in enumerate(order):
        o = AM.rung_objs[k]
        f0 = 58 + j * 1.15
        sy = o.scale[1]
        o.scale = (o.scale[0], 0.0001, 0.0001)
        o.keyframe_insert("scale", frame=int(f0))
        o.scale = (o.scale[0], sy * 2.2, sy * 2.2)
        o.keyframe_insert("scale", frame=int(f0) + 4)
        o.scale = (o.scale[0], sy, sy)
        o.keyframe_insert("scale", frame=int(f0) + 10)
        color_key(o, int(f0), (1, 0.85, 0.8, 0.0))
        color_key(o, int(f0) + 3, (1, 0.6, 0.5, 6.0))
        color_key(o, int(f0) + 14, (*RED, 1.7))
    for i, t in enumerate(AM.labels):
        alpha_key(t, 1, 0.0)
        alpha_key(t, 150 + i * 2, 0.0)
        alpha_key(t, 170 + i * 2, 1.4)
    for r in AM.rings:
        a = r.color[3]
        alpha_key(r, 20, 0.0)
        alpha_key(r, 90, a * 2.5)
        alpha_key(r, 140, a)
    alpha_key(AM.dot, 1, 0.0)
    alpha_key(AM.dot, 6, 14.0)
    alpha_key(AM.dot, 30, 5.0)
    cam_keys(cam, tgt, [
        (1, (0.0, -0.6, 9.5), (0, 0, 0)),
        (110, (2.6, -6.5, 8.6), (0, 0.2, 0)),
        (F, (0.0, -10.2, 6.3), (0, 0.9, 0)),
    ])
    cam.data.dof.aperture_fstop = 5.6


# ------------------------------------------------------------------ shot D: rule (remove rungs, route, medals)
def shot_rule():
    F = 312
    # turn the board so player 8's spoke sits back-right (where spoke 2 is in the build shot):
    # the camera travels that way, so the highlight starts on screen instead of below the frame
    AM.rot = (ROUTE_START - 1) * 360 / AM.n
    sc = amida_scene_base(F)
    cam, tgt = camera(32, dof=5.0)
    for t in AM.labels:
        t.color = (*LAV, 1.4)
    rem = sorted(REMOVE, key=lambda k: (k * 37) % len(AM.rungs))
    for j, k in enumerate(rem):
        o = AM.rung_objs[k]
        f0 = 16 + j * 5
        color_key(o, 1, (*RED, 1.7))
        color_key(o, f0, (*RED, 1.7))
        color_key(o, f0 + 3, (1, 1, 1, 9.0))
        color_key(o, f0 + 12, (1, 0.3, 0.2, 0.0))
        sx, sy, sz = o.scale
        o.keyframe_insert("scale", frame=f0 + 3)
        o.scale = (sx, 0.0001, 0.0001)
        o.keyframe_insert("scale", frame=f0 + 12)
    # dim everything except the route once removal finished
    for k, o in enumerate(AM.rung_objs):
        if k in REMOVE:
            continue
        color_key(o, 112, (*RED, 1.7))
        color_key(o, 132, (*RED, 1.1))
    for o in AM.spokes:
        alpha_key(o, 112, 0.9)
        alpha_key(o, 132, 0.45)
    pts, cnt = AM.trace(ROUTE_START, ACTIVE)
    print("ROUTE", ROUTE_START, cnt, "counts", COUNTS)
    rmat = mat_emit_obj("m_route", 1.0)
    rc = route_curve(pts, rmat, 0.055)
    rc.color = (*GOLD, 9.0)
    rc.data.bevel_factor_end = 0.0
    rc.data.keyframe_insert("bevel_factor_end", frame=118)
    rc.data.bevel_factor_end = 1.0
    rc.data.keyframe_insert("bevel_factor_end", frame=178)
    lab = AM.labels[ROUTE_START]
    color_key(lab, 112, (*LAV, 1.4))
    color_key(lab, 122, (*GOLD, 6.0))
    key(lab, "scale", 112, (1, 1, 1))
    key(lab, "scale", 124, (1.6, 1.6, 1.6))
    alpha_key(AM.dot, 170, 5.0)
    alpha_key(AM.dot, 180, 30.0)
    alpha_key(AM.dot, 200, 8.0)
    # medals rain onto the centre
    rnd = random.Random(5)
    area_light("key", (2.5, -3.5, 6.0), (math.radians(35), 0, math.radians(25)), 4.0, 900)
    area_light("rim", (-4, 3, 2.5), (math.radians(-60), math.radians(-40), 0), 3.0, 500, color=(1, 0.3, 0.2))
    area_light("fill", (0, -6, 1.5), (math.radians(80), 0, 0), 6.0, 120, color=(1, 0.8, 0.6))
    for i in range(14):
        m = medal(f"medal{i}", ROUTE_START + 1)
        stack = i % 3
        base = [(0.0, 0.0), (0.95, 0.35), (-0.9, 0.45)][stack]
        h = i // 3
        target = Vector((base[0] + rnd.uniform(-0.03, 0.03), base[1] + rnd.uniform(-0.03, 0.03), 0.06 + h * 0.074))
        f0 = 186 + i * 6
        m.location = target + Vector((rnd.uniform(-1.5, 1.5), rnd.uniform(-1.0, 1.5), 8.0))
        m.rotation_euler = (rnd.uniform(-2, 2), rnd.uniform(-2, 2), rnd.uniform(0, 6))
        m.keyframe_insert("location", frame=1)
        m.keyframe_insert("location", frame=f0)
        m.keyframe_insert("rotation_euler", frame=f0)
        set_interp("QUAD")
        m.location = target + Vector((0, 0, 0.12))
        m.keyframe_insert("location", frame=f0 + 14)
        set_interp("BEZIER")
        m.location = target + Vector((0, 0, 0.04))
        m.keyframe_insert("location", frame=f0 + 17)
        m.location = target
        m.keyframe_insert("location", frame=f0 + 20)
        m.rotation_euler = (rnd.uniform(-0.03, 0.03), rnd.uniform(-0.03, 0.03), rnd.uniform(-0.4, 0.4))
        m.keyframe_insert("rotation_euler", frame=f0 + 16)
    cam_keys(cam, tgt, [
        (1, (0.0, -10.2, 6.3), (0, 0.9, 0)),
        (100, (0.4, -9.6, 6.6), (0, 0.6, 0)),
        (178, (2.2, -6.8, 6.4), (0.4, 1.2, 0)),
        (215, (1.6, -5.4, 3.4), (0.1, 0.4, 0.2)),
        (F, (0.6, -3.9, 1.65), (0.0, 0.25, 0.3)),
    ])


# ------------------------------------------------------------------ shot C: title
def shot_title():
    F = 162
    sc = reset(samples=args.samples, res=tuple(args.res))
    sc.frame_start, sc.frame_end = 1, F
    compositor(threshold=0.9, strength=0.7, size=0.7)
    # background amida standing behind the title
    piv = link(bpy.data.objects.new("piv", None))
    am = Amida(r_out=5.2).build(label=False)
    for o in am.spokes + am.rung_objs + am.rings + [am.dot]:
        o.parent = piv
        o.color = (*o.color[:3], o.color[3] * 0.16)
    piv.location = (0, 9.5, 0.2)
    piv.rotation_euler = (math.radians(90), 0, 0)
    set_interp("LINEAR")
    key(piv, "rotation_euler", 1, None, index=1)
    piv.rotation_euler[1] = math.radians(14)
    piv.keyframe_insert("rotation_euler", frame=F, index=1)
    set_interp("BEZIER")
    dust(140, box=((-8, 8), (-3, 8), (-4, 4)), frames=F)
    # the title itself is the official logotype cut out of the key art (prep2.py -> title_logo.png),
    # laid over this shot in edit.py so it matches the key art at the end
    tag = text("tag", "阿弥陀を消して、生き残れ。", 0.50, mat_emit_obj("m_tag", 1.0), font(FONT_M), spacing=1.12)
    tag.data.materials.append(mat_emit_obj("m_tag_red", 1.0))
    body = tag.data.body
    i0 = body.index("生き残れ")
    for i in range(i0, i0 + 4):
        tag.data.body_format[i].material_index = 1
    # red part: different material constant colour (object colour can't vary per char) -> override
    red = tag.data.materials[1]
    nt = red.node_tree
    em = [n for n in nt.nodes if n.type == "EMISSION"][0]
    for l in list(nt.links):
        if l.to_node == em and l.to_socket.name == "Color":
            nt.links.remove(l)
    em.inputs["Color"].default_value = (1.0, 0.16, 0.12, 1)
    tag.rotation_euler = (math.radians(90), 0, 0)
    tag.location = (0, -0.05, -1.0)
    tag.color = (*IVORY, 0.0)
    alpha_key(tag, 62, 0.0)
    alpha_key(tag, 92, 1.5)
    lm = mat_emit_obj("m_line", 1.0)
    for sx in (-1, 1):
        r = rod(f"line{sx}", (sx * 3.85, -0.05, -1.0), (sx * 5.4, -0.05, -1.0), 0.008, lm)
        r.color = (*GOLD, 0.0)
        alpha_key(r, 70, 0.0)
        alpha_key(r, 100, 2.0)
    # lights: sweeping glint across the title + soft reflectors
    sweep = area_light("sweep", (-9, -3.5, 1.8), (math.radians(70), 0, math.radians(-20)), 1.2, 2200, color=(1, 0.9, 0.7))
    key(sweep, "location", 20, (-9, -3.5, 1.8))
    key(sweep, "location", 120, (9, -3.5, 1.8))
    area_light("top", (0, -2.5, 6), (math.radians(20), 0, 0), 8.0, 500, color=(1, 0.8, 0.55))
    area_light("low", (0, -3, -4), (math.radians(150), 0, 0), 8.0, 160, color=(1, 0.45, 0.25))
    refl = plane("refl", 30, 8, mat_principled("reflm", (0, 0, 0)))
    em2 = bpy.data.materials.new("reflem")
    em2.use_nodes = True
    nt = em2.node_tree
    nt.nodes.clear()
    e = nt.nodes.new("ShaderNodeEmission")
    e.inputs[0].default_value = (1, 0.75, 0.45, 1)
    e.inputs[1].default_value = 0.6
    o = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(e.outputs[0], o.inputs[0])
    refl.data.materials[0] = em2
    refl.location = (0, -14, 3)
    refl.rotation_euler = (math.radians(80), 0, 0)
    refl.visible_camera = False
    cam, tgt = camera(45, dof=None)
    cam_keys(cam, tgt, [(1, (0, -10.5, 0.55), (0, 0, 0.15)), (F, (0, -9.0, 0.35), (0, 0, 0.15))])


# ------------------------------------------------------------------ shot E: floating presentation screens
def shot_screens():
    F = 282
    sc = reset(samples=args.samples, res=tuple(args.res))
    sc.frame_start, sc.frame_end = 1, F
    compositor(threshold=0.92, strength=0.45, size=0.6)
    shots = ["s01_rule_game-title", "s02_rule_goal", "s09_rule_minus", "s13_rule_route", "s26_turn-start_t1", "s55_amida-result_t5", "s29_result-announce_t1"]
    W, H = 3.2, 1.8
    gap = 3.9
    fm = mat_emit_obj("m_frame", 1.0)
    panels = []
    for i, s in enumerate(shots):
        x = i * gap
        y = 0.9 if i % 2 else -0.2
        p = plane(f"scr{i}", W, H, mat_image(f"mi{i}", PRES + s + ".png", 1.25, alpha_obj=True))
        p.location = (x, y, 1.2)
        p.rotation_euler = (math.radians(90), 0, math.radians(-12 if i % 2 else 10))
        p.color = (1, 1, 1, 1)
        for (a, b) in [((-W / 2, -H / 2), (W / 2, -H / 2)), ((W / 2, -H / 2), (W / 2, H / 2)), ((W / 2, H / 2), (-W / 2, H / 2)), ((-W / 2, H / 2), (-W / 2, -H / 2))]:
            r = rod("fr", (a[0] * 1.02, a[1] * 1.03, 0), (b[0] * 1.02, b[1] * 1.03, 0), 0.008, fm)
            r.parent = p
            r.color = (*GOLD, 2.5)
        set_interp("SINE")
        for f in range(1, F + 1, 60):
            p.location.z = 1.2 + 0.06 * math.sin(i * 1.7 + f / 30)
            p.keyframe_insert("location", frame=f, index=2)
        set_interp("BEZIER")
        panels.append(p)
    floor = plane("floor", 80, 30, mat_principled("floor", (0.012, 0.011, 0.01), 0.18, 0.0))
    floor.location = (12, 2, -0.35)
    dust(220, box=((-6, 30), (-4, 6), (-0.3, 4)), frames=F, strength=2.5)
    cam, tgt = camera(35, dof=3.5)
    set_interp("LINEAR")
    cam_keys(cam, tgt, [(1, (-2.2, -4.6, 1.55), (0.4, 0.3, 1.2)), (F, ((len(shots) - 1) * gap - 2.0, -4.4, 1.35), ((len(shots) - 1) * gap + 0.4, 0.3, 1.2))])
    set_interp("BEZIER")


# ------------------------------------------------------------------ shot G: cards on the table
def shot_cards():
    F = 192
    sc = reset(samples=args.samples, res=tuple(args.res))
    sc.frame_start, sc.frame_end = 1, F
    compositor(threshold=0.95, strength=0.45, size=0.6)
    tm = bpy.data.materials.new("table")
    tm.use_nodes = True
    nt = tm.node_tree
    p = nt.nodes["Principled BSDF"]
    nz = nt.nodes.new("ShaderNodeTexNoise")
    nz.inputs["Scale"].default_value = 3.0
    nz.inputs["Detail"].default_value = 8
    cr = nt.nodes.new("ShaderNodeValToRGB")
    cr.color_ramp.elements[0].color = (0.012, 0.016, 0.012, 1)
    cr.color_ramp.elements[1].color = (0.05, 0.035, 0.022, 1)
    nt.links.new(nz.outputs["Fac"], cr.inputs[0])
    nt.links.new(cr.outputs[0], p.inputs["Base Color"])
    p.inputs["Roughness"].default_value = 0.42
    table = plane("table", 30, 30, tm)
    sp = bpy.data.lights.new("spot", "SPOT")
    sp.energy = 1700
    sp.spot_size = math.radians(48)
    sp.spot_blend = 0.6
    sp.color = (1, 0.82, 0.6)
    spo = link(bpy.data.objects.new("spot", sp))
    spo.location = (0.3, 0.4, 5.5)
    area_light("redrim", (-4, 4, 1.2), (math.radians(-70), math.radians(-45), 0), 3.0, 260, color=(1, 0.15, 0.1))
    area_light("fillc", (0, -6, 2.5), (math.radians(70), 0, 0), 5.0, 40, color=(1, 0.8, 0.6))
    cw, ch = 0.98, 1.4
    cards = [
        ("card_back", True, (-1.55, 0.55, 0.0), 0.35),
        ("card_minus", False, (1.1, 0.8, 0.0), -0.2),   # official minus card (face up at 0:49)
        ("card_back", True, (-0.4, 1.35, 0.0), -0.1),
        ("card_back", True, (1.9, -0.35, 0.0), 0.55),
        ("card_main", False, (0.05, 0.05, 0.0), 0.08),
    ]
    rnd = random.Random(9)
    for i, (img, face_down, pos, rz) in enumerate(cards):
        front = GEN + ("card_back" if face_down else img) + ".png"
        mat = mat_image(f"cm{i}", GEN + img + ".png", 0.0, alpha_obj=False, back_path=GEN + "card_back.png")
        # lit cards: convert emission into principled base colour for realism
        nt = mat.node_tree
        em = [n for n in nt.nodes if n.type == "EMISSION"][0]
        pr = nt.nodes.new("ShaderNodeBsdfPrincipled")
        pr.inputs["Roughness"].default_value = 0.35
        src = em.inputs["Color"].links[0].from_socket
        nt.links.new(src, pr.inputs["Base Color"])
        nt.links.new(src, pr.inputs["Emission Color"])
        pr.inputs["Emission Strength"].default_value = 0.08
        out = [n for n in nt.nodes if n.type == "OUTPUT_MATERIAL"][0]
        nt.links.new(pr.outputs[0], out.inputs[0])
        iw, ih = __import__("PIL.Image", fromlist=["Image"]).open(GEN + img + ".png").size
        c = plane(f"card{i}", ch * iw / ih if not face_down else cw, ch, mat)
        z = 0.004 + i * 0.003
        target_rot = (math.pi if face_down else 0.0, 0.0, rz)
        f0 = 6 + i * 16
        c.location = (pos[0] + rnd.uniform(-2, 2), pos[1] + rnd.uniform(1, 3), 4.5)
        c.rotation_euler = (rnd.uniform(-1.5, 1.5) + target_rot[0], rnd.uniform(-1, 1), rz + rnd.uniform(-2, 2))
        c.keyframe_insert("location", frame=1)
        c.keyframe_insert("location", frame=f0)
        c.keyframe_insert("rotation_euler", frame=f0)
        c.location = (pos[0], pos[1], z)
        c.keyframe_insert("location", frame=f0 + 22)
        c.rotation_euler = target_rot
        c.keyframe_insert("rotation_euler", frame=f0 + 22)
    # medals of many players around the cards; 16 sits in the clear spot the final close-up ends on
    TABLE_MEDALS = [
        (16, (0.85, -0.4)), (3, (-1.05, -0.55)), (12, (1.75, 0.55)), (6, (-1.6, -1.25)),
        (1, (-0.35, 2.35)), (8, (2.55, -0.9)), (14, (-2.3, 1.45)), (5, (0.75, 2.2)),
        (10, (-2.35, -0.2)), (2, (2.2, 1.65)), (11, (1.55, -1.45)), (7, (-0.6, -1.55)),
    ]
    for i, (num, (x, y)) in enumerate(TABLE_MEDALS):
        m = medal(f"tm{i}", num)
        m.location = (x + rnd.uniform(-0.05, 0.05), y + rnd.uniform(-0.05, 0.05), 0.023)
        m.rotation_euler = (0, 0, rnd.uniform(-0.5, 0.5))   # numerals roughly upright to the camera
        m.scale = (0.62, 0.62, 0.62)
    dust(120, box=((-4, 4), (-3, 4), (0.1, 4)), frames=F, strength=2.0, size=0.012)
    cam, tgt = camera(40, dof=2.2)
    cam_keys(cam, tgt, [
        (1, (0.3, -2.2, 7.2), (0.1, 0.4, 0)),
        (100, (0.6, -3.4, 4.0), (0.1, 0.3, 0)),
        (F, (0.45, -2.35, 1.25), (0.05, 0.15, 0.05)),
    ])


SHOTS = {"build": shot_build, "rule": shot_rule, "title": shot_title, "screens": shot_screens, "cards": shot_cards}
SHOTS[args.shot]()
sc = bpy.context.scene
if os.environ.get("NODENOISE"): sc.cycles.use_denoising = False
if os.environ.get("DQ"):
    sc.cycles.denoising_quality = os.environ["DQ"]; sc.cycles.denoising_prefilter = "FAST"; sc.cycles.denoising_input_passes = os.environ.get("DP", "RGB_ALBEDO")
if os.environ.get("NOCOMP"): sc.render.use_compositing = False
if os.environ.get("PERSIST"): sc.render.use_persistent_data = True
os.makedirs(args.outdir, exist_ok=True)
if args.save:
    bpy.ops.wm.save_as_mainfile(filepath=args.save)
frames = args.only or range(*(args.frames[0], args.frames[1] + 1) if args.frames else (sc.frame_start, sc.frame_end + 1))
import time
for f in frames:
    out = os.path.join(args.outdir, f"{f:04d}.png")
    if os.path.exists(out) and not args.only:
        continue
    sc.frame_set(f)
    sc.render.filepath = out
    t = time.time()
    bpy.ops.render.render(write_still=True)
    print(f"FRAME {args.shot} {f} {time.time() - t:.1f}s", flush=True)
