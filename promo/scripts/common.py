"""Shared helpers for the 削減アミダクジ promo 3D shots (Blender 5.2 / bpy)."""
import bpy, math, random
from mathutils import Vector, Euler

import os
# working directory holding assets/ and render/ (see promo/README.md)
S = os.environ.get("PROMO_WORK", os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "work"))
ASSETS = S + "/assets"
FONT_B = "/usr/share/fonts/opentype/noto/NotoSerifCJK-Black.ttc"
FONT_M = "/usr/share/fonts/opentype/noto/NotoSerifCJK-Bold.ttc"
FONT_R = "/usr/share/fonts/opentype/noto/NotoSerifCJK-Medium.ttc"

GOLD = (1.0, 0.70, 0.28)
RED = (0.92, 0.10, 0.08)
IVORY = (0.95, 0.92, 0.86)
LAV = (0.66, 0.62, 0.95)

_fonts = {}


def font(path=FONT_M):
    if path not in _fonts:
        _fonts[path] = bpy.data.fonts.load(path)
    return _fonts[path]


def reset(fps=30, res=(1920, 1080), samples=10):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    sc.cycles.device = "CPU"
    sc.cycles.samples = samples
    sc.cycles.use_denoising = True
    sc.cycles.denoising_quality = "FAST"
    sc.cycles.denoising_prefilter = "FAST"
    sc.cycles.max_bounces = 3
    sc.cycles.caustics_reflective = False
    sc.cycles.caustics_refractive = False
    sc.cycles.blur_glossy = 1.0
    sc.cycles.glossy_bounces = 2
    sc.cycles.diffuse_bounces = 2
    sc.cycles.transmission_bounces = 2
    sc.cycles.transparent_max_bounces = 8
    sc.cycles.use_adaptive_sampling = True
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.render.resolution_percentage = 100
    sc.render.fps = fps
    sc.render.image_settings.file_format = "PNG"
    sc.render.image_settings.color_mode = "RGB"
    sc.view_settings.view_transform = "Standard"
    sc.view_settings.look = "None"
    sc.render.film_transparent = False
    w = bpy.data.worlds.new("W")
    sc.world = w
    w.use_nodes = True
    bg = w.node_tree.nodes["Background"]
    bg.inputs[0].default_value = (0.004, 0.0035, 0.003, 1)
    bg.inputs[1].default_value = 1.0
    return sc


def set_interp(kind):
    bpy.context.preferences.edit.keyframe_new_interpolation_type = kind


def key(obj, path, frame, value=None, index=-1):
    if value is not None:
        if index >= 0:
            getattr(obj, path)[index] = value
        else:
            setattr(obj, path, value)
    obj.keyframe_insert(path, frame=frame, index=index)


def alpha_key(obj, frame, a):
    c = list(obj.color)
    c[3] = a
    obj.color = c
    obj.keyframe_insert("color", frame=frame, index=3)


def color_key(obj, frame, rgba):
    obj.color = rgba
    obj.keyframe_insert("color", frame=frame)


def link(obj, coll=None):
    (coll or bpy.context.scene.collection).objects.link(obj)
    return obj


# ---------------------------------------------------------------- materials
def mat_emit_obj(name, strength=4.0, transparent=True):
    """Emission whose colour = object.color.rgb and strength = object.color.a * strength.
    Alpha also fades towards transparent so elements vanish cleanly."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    m.cycles.emission_sampling = "NONE"
    nt = m.node_tree
    nt.nodes.clear()
    oi = nt.nodes.new("ShaderNodeObjectInfo")
    em = nt.nodes.new("ShaderNodeEmission")
    mul = nt.nodes.new("ShaderNodeMath")
    mul.operation = "MULTIPLY"
    mul.inputs[1].default_value = strength
    nt.links.new(oi.outputs["Alpha"], mul.inputs[0])
    nt.links.new(oi.outputs["Color"], em.inputs["Color"])
    nt.links.new(mul.outputs[0], em.inputs["Strength"])
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    if transparent:
        tr = nt.nodes.new("ShaderNodeBsdfTransparent")
        mix = nt.nodes.new("ShaderNodeMixShader")
        cl = nt.nodes.new("ShaderNodeMath")
        cl.operation = "MINIMUM"
        cl.inputs[1].default_value = 1.0
        nt.links.new(oi.outputs["Alpha"], cl.inputs[0])
        nt.links.new(cl.outputs[0], mix.inputs[0])
        nt.links.new(tr.outputs[0], mix.inputs[1])
        nt.links.new(em.outputs[0], mix.inputs[2])
        nt.links.new(mix.outputs[0], out.inputs[0])
    else:
        nt.links.new(em.outputs[0], out.inputs[0])
    return m


def mat_gold(name="gold", rough=0.22, emit=0.0, alpha_obj=False, color=GOLD):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    p = nt.nodes["Principled BSDF"]
    p.inputs["Base Color"].default_value = (*color, 1)
    p.inputs["Metallic"].default_value = 1.0
    p.inputs["Roughness"].default_value = rough
    if emit:
        p.inputs["Emission Color"].default_value = (*color, 1)
        p.inputs["Emission Strength"].default_value = emit
    if alpha_obj:
        out = nt.nodes["Material Output"]
        oi = nt.nodes.new("ShaderNodeObjectInfo")
        tr = nt.nodes.new("ShaderNodeBsdfTransparent")
        mix = nt.nodes.new("ShaderNodeMixShader")
        cl = nt.nodes.new("ShaderNodeMath")
        cl.operation = "MINIMUM"
        cl.inputs[1].default_value = 1.0
        nt.links.new(oi.outputs["Alpha"], cl.inputs[0])
        nt.links.new(cl.outputs[0], mix.inputs[0])
        nt.links.new(tr.outputs[0], mix.inputs[1])
        nt.links.new(p.outputs[0], mix.inputs[2])
        nt.links.new(mix.outputs[0], out.inputs[0])
    return m


def mat_principled(name, color, rough=0.5, metallic=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    p = m.node_tree.nodes["Principled BSDF"]
    p.inputs["Base Color"].default_value = (*color, 1)
    p.inputs["Roughness"].default_value = rough
    p.inputs["Metallic"].default_value = metallic
    return m


def mat_image(name, path, strength=1.0, alpha_obj=True, back_path=None):
    """Emissive image (screens, cards). Optional different image on the back face."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = bpy.data.images.load(path, check_existing=True)
    tex.interpolation = "Cubic"
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Strength"].default_value = strength
    col = tex.outputs["Color"]
    if back_path:
        tex2 = nt.nodes.new("ShaderNodeTexImage")
        tex2.image = bpy.data.images.load(back_path, check_existing=True)
        tc = nt.nodes.new("ShaderNodeTexCoord")
        mp = nt.nodes.new("ShaderNodeMapping")  # mirror U on the back
        mp.inputs["Scale"].default_value = (-1, 1, 1)
        mp.inputs["Location"].default_value = (1, 0, 0)
        nt.links.new(tc.outputs["UV"], mp.inputs[0])
        nt.links.new(mp.outputs[0], tex2.inputs[0])
        geo = nt.nodes.new("ShaderNodeNewGeometry")
        mx = nt.nodes.new("ShaderNodeMix")
        mx.data_type = "RGBA"
        nt.links.new(geo.outputs["Backfacing"], mx.inputs[0])
        nt.links.new(tex.outputs["Color"], mx.inputs[6])
        nt.links.new(tex2.outputs["Color"], mx.inputs[7])
        col = mx.outputs[2]
    nt.links.new(col, em.inputs["Color"])
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    if alpha_obj:
        oi = nt.nodes.new("ShaderNodeObjectInfo")
        tr = nt.nodes.new("ShaderNodeBsdfTransparent")
        mix = nt.nodes.new("ShaderNodeMixShader")
        nt.links.new(oi.outputs["Alpha"], mix.inputs[0])
        nt.links.new(tr.outputs[0], mix.inputs[1])
        nt.links.new(em.outputs[0], mix.inputs[2])
        nt.links.new(mix.outputs[0], out.inputs[0])
    else:
        nt.links.new(em.outputs[0], out.inputs[0])
    return m


# ---------------------------------------------------------------- geometry
_cyl = None


def unit_cyl():
    """Cylinder of radius 1, length 1 along +X starting at origin."""
    global _cyl
    if _cyl is None:
        import bmesh
        me = bpy.data.meshes.new("ucyl")
        bm = bmesh.new()
        bmesh.ops.create_cone(bm, cap_ends=True, segments=10, radius1=1, radius2=1, depth=1)
        bmesh.ops.rotate(bm, verts=bm.verts, cent=(0, 0, 0), matrix=__import__("mathutils").Matrix.Rotation(math.radians(90), 3, "Y"))
        bmesh.ops.translate(bm, verts=bm.verts, vec=(0.5, 0, 0))
        bm.to_mesh(me)
        bm.free()
        _cyl = me
    return _cyl


def rod(name, p0, p1, radius, mat, coll=None):
    p0, p1 = Vector(p0), Vector(p1)
    d = p1 - p0
    o = bpy.data.objects.new(name, unit_cyl())
    o.location = p0
    o.rotation_mode = "QUATERNION"
    o.rotation_quaternion = Vector((1, 0, 0)).rotation_difference(d.normalized())
    o.scale = (d.length, radius, radius)
    link(o, coll)
    if len(o.data.materials) == 0:
        o.data.materials.append(mat)
    o.material_slots[0].link = "OBJECT"
    o.material_slots[0].material = mat
    return o


def text(name, body, size=1.0, mat=None, fnt=None, extrude=0.0, bevel=0.0, align="CENTER", spacing=1.0, coll=None):
    cu = bpy.data.curves.new(name, "FONT")
    cu.body = body
    cu.font = fnt or font()
    cu.size = size
    cu.extrude = extrude
    cu.bevel_depth = bevel
    cu.bevel_resolution = 2
    cu.align_x = align
    cu.align_y = "CENTER"
    cu.space_character = spacing
    o = bpy.data.objects.new(name, cu)
    if mat:
        cu.materials.append(mat)
    link(o, coll)
    return o


def plane(name, w, h, mat, coll=None):
    import bmesh
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    vs = [bm.verts.new(v) for v in [(-w / 2, -h / 2, 0), (w / 2, -h / 2, 0), (w / 2, h / 2, 0), (-w / 2, h / 2, 0)]]
    f = bm.faces.new(vs)
    uv = bm.loops.layers.uv.new()
    for lp, c in zip(f.loops, [(0, 0), (1, 0), (1, 1), (0, 1)]):
        lp[uv].uv = c
    bm.to_mesh(me)
    bm.free()
    o = bpy.data.objects.new(name, me)
    me.materials.append(mat)
    link(o, coll)
    return o


# ---------------------------------------------------------------- amida
class Amida:
    """Radial amida: N spokes from r_in to r_out, ROWS rungs per sector (staggered)."""

    def __init__(self, n=15, rows=6, r_in=0.75, r_out=4.6, rot=0.0):
        # 15 players -> 15 spokes, numbered 1-15 like the medals and the presentation tool
        # rot: turns the whole board (degrees, counter-clockwise seen from above)
        self.n, self.rows, self.r_in, self.r_out, self.rot = n, rows, r_in, r_out, rot
        self.rungs = []  # (sector, radius)
        span = r_out - r_in
        # stagger neighbouring sectors so no two rungs meet a spoke at the same radius
        # (2-way works for even n; odd n needs 3-way, which also closes the ring when n % 3 == 0)
        k = 2 if n % 2 == 0 else 3
        for row in range(rows):
            for s in range(n):
                level = row + 1 + (s % k) / k
                r = r_out - level * span / (rows + 1.6)
                self.rungs.append((s, r))

    def ang(self, i):
        return math.radians(90 + self.rot - i * 360 / self.n)

    def pt(self, i, r, z=0.0):
        a = self.ang(i % self.n)
        return Vector((r * math.cos(a), r * math.sin(a), z))

    def trace(self, start, active):
        """Return (points, crossings) for a route from spoke `start` inward."""
        cur, rad = start, self.r_out + 0.0
        pts = [self.pt(cur, self.r_out + 0.25)]
        cnt = 0
        while True:
            best = None
            for k, (s, r) in enumerate(self.rungs):
                if not active[k] or r >= rad - 1e-6:
                    continue
                if s == cur or (s + 1) % self.n == cur:
                    if best is None or r > self.rungs[best][1]:
                        best = k
            if best is None:
                pts.append(self.pt(cur, self.r_in))
                pts.append(Vector((0, 0, 0)))
                return pts, cnt
            s, r = self.rungs[best]
            pts.append(self.pt(cur, r))
            cur = (s + 1) % self.n if s == cur else s
            pts.append(self.pt(cur, r))
            rad = r
            cnt += 1

    def build(self, coll=None, spoke_r=0.022, rung_r=0.03, label=True, label_size=0.32):
        self.m_spoke = mat_emit_obj("m_spoke", 1.0)
        self.m_rung = mat_emit_obj("m_rung", 1.0)
        self.m_label = mat_emit_obj("m_label", 1.0)
        self.spokes, self.rung_objs, self.labels = [], [], []
        for i in range(self.n):
            o = rod(f"spoke{i}", self.pt(i, self.r_in), self.pt(i, self.r_out + 0.25), spoke_r, self.m_spoke, coll)
            o.color = (0.62, 0.52, 0.38, 1.0)
            self.spokes.append(o)
            if label:
                t = text(f"lab{i}", str(i + 1), label_size, self.m_label, font(FONT_M), coll=coll)
                t.location = self.pt(i, self.r_out + 0.62)
                t.color = (*LAV, 1.0)
                self.labels.append(t)
        for k, (s, r) in enumerate(self.rungs):
            a, b = self.pt(s, r), self.pt(s + 1, r)
            o = rod(f"rung{k}", a, b, rung_r, self.m_rung, coll)
            o.color = (*RED, 1.7)
            self.rung_objs.append(o)
        # centre dot
        import bmesh
        me = bpy.data.meshes.new("dot")
        bm = bmesh.new()
        bmesh.ops.create_uvsphere(bm, u_segments=24, v_segments=12, radius=0.12)
        bm.to_mesh(me)
        bm.free()
        self.dot = link(bpy.data.objects.new("dot", me), coll)
        me.materials.append(mat_emit_obj("m_dot", 1.0))
        self.dot.color = (*RED, 6.0)
        # faint ornamental rings
        self.rings = []
        for rr, a in [(self.r_out + 1.15, 0.5), (self.r_out + 1.25, 0.25), (self.r_in - 0.15, 0.6)]:
            cu = bpy.data.curves.new("ring", "CURVE")
            cu.dimensions = "3D"
            sp = cu.splines.new("POLY")
            seg = 128
            sp.points.add(seg)
            for j in range(seg + 1):
                t = 2 * math.pi * j / seg
                sp.points[j].co = (rr * math.cos(t), rr * math.sin(t), 0, 1)
            cu.bevel_depth = 0.008
            o = link(bpy.data.objects.new("ring", cu), coll)
            cu.materials.append(mat_emit_obj("m_ring", 1.0))
            o.color = (*GOLD, a)
            self.rings.append(o)
        return self


def route_curve(points, mat, radius=0.05, coll=None):
    cu = bpy.data.curves.new("route", "CURVE")
    cu.dimensions = "3D"
    sp = cu.splines.new("POLY")
    sp.points.add(len(points) - 1)
    for p, q in zip(sp.points, points):
        p.co = (q.x, q.y, q.z + 0.02, 1)
    cu.bevel_depth = radius
    cu.bevel_resolution = 3
    cu.use_fill_caps = True
    cu.bevel_factor_mapping_end = "SPLINE"
    cu.materials.append(mat)
    return link(bpy.data.objects.new("route", cu), coll)


# ---------------------------------------------------------------- medal
def medal(name, number=8, coll=None, mats={}):
    """Official medal: a disc whose two faces carry the medal artwork (gen/medal_<n>.png), rim in its base colour."""
    import bmesh
    key_ = f"mesh{number}"
    if key_ not in mats:
        tex = S + f"/assets/gen/medal_{number}.png"
        base = [int(v) / 255 for v in open(S + f"/assets/gen/medal_{number}.base").read().split()]
        base = tuple(c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in base)
        rim = mat_principled(f"medal_rim{number}", base, 0.25, 0.45)
        face = bpy.data.materials.new(f"medal_face{number}")
        face.use_nodes = True
        nt = face.node_tree
        p = nt.nodes["Principled BSDF"]
        im = nt.nodes.new("ShaderNodeTexImage")
        im.image = bpy.data.images.load(tex)
        im.interpolation = "Smart"
        nt.links.new(im.outputs["Color"], p.inputs["Base Color"])
        nt.links.new(im.outputs["Color"], p.inputs["Emission Color"])
        p.inputs["Emission Strength"].default_value = 0.18   # keeps the numerals legible in the dark scenes
        p.inputs["Roughness"].default_value = 0.42
        p.inputs["Coat Weight"].default_value = 0.35
        me = bpy.data.meshes.new(f"medal{number}")
        bm = bmesh.new()
        bmesh.ops.create_cone(bm, cap_ends=True, segments=64, radius1=0.42, radius2=0.42, depth=0.07)
        uv = bm.loops.layers.uv.new("UVMap")
        for f in bm.faces:
            f.normal_update()
            cap = abs(f.normal.z) > 0.9
            f.material_index = 1 if cap else 0
            f.smooth = not cap
            if cap:
                for l in f.loops:
                    x, y = l.vert.co.x / 0.84, l.vert.co.y / 0.84
                    l[uv].uv = (0.5 + (x if f.normal.z > 0 else -x), 0.5 + y)
        bm.to_mesh(me)
        bm.free()
        me.materials.append(rim)
        me.materials.append(face)
        mats[key_] = me
    return link(bpy.data.objects.new(name, mats[key_]), coll)


# ---------------------------------------------------------------- dust / camera / compositor
def dust(count=160, box=((-9, 9), (-9, 9), (-1, 6)), seed=3, frames=300, coll=None, size=0.018, color=GOLD, strength=3.0):
    import bmesh
    rnd = random.Random(seed)
    me = bpy.data.meshes.new("dust")
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=1, radius=size)
    bm.to_mesh(me)
    bm.free()
    m = mat_emit_obj("m_dust", strength)
    me.materials.append(m)
    set_interp("LINEAR")
    for i in range(count):
        o = link(bpy.data.objects.new(f"dust{i}", me), coll)
        p0 = Vector([rnd.uniform(*b) for b in box])
        v = Vector((rnd.uniform(-1, 1), rnd.uniform(-1, 1), rnd.uniform(0.2, 1))) * 0.004
        o.color = (*color, rnd.uniform(0.15, 1.0))
        s = rnd.uniform(0.5, 1.6)
        o.scale = (s, s, s)
        o.location = p0
        o.keyframe_insert("location", frame=1)
        o.location = p0 + v * frames
        o.keyframe_insert("location", frame=frames)
    set_interp("BEZIER")


def camera(lens=35, dof=None):
    cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam"))
    link(cam)
    cam.data.lens = lens
    cam.data.clip_end = 300
    tgt = link(bpy.data.objects.new("cam_tgt", None))
    c = cam.constraints.new("TRACK_TO")
    c.target = tgt
    c.track_axis = "TRACK_NEGATIVE_Z"
    c.up_axis = "UP_Y"
    if dof:
        cam.data.dof.use_dof = True
        cam.data.dof.focus_object = tgt
        cam.data.dof.aperture_fstop = dof
    bpy.context.scene.camera = cam
    return cam, tgt


def cam_keys(cam, tgt, keys):
    """keys: list of (frame, cam_loc, tgt_loc)."""
    for f, cl, tl in keys:
        cam.location = cl
        cam.keyframe_insert("location", frame=f)
        tgt.location = tl
        tgt.keyframe_insert("location", frame=f)


QUALITY = "Low"

def compositor(threshold=0.85, strength=0.6, size=0.6, vignette=True):
    sc = bpy.context.scene
    ng = bpy.data.node_groups.new("Comp", "CompositorNodeTree")
    sc.compositing_node_group = ng
    rl = ng.nodes.new("CompositorNodeRLayers")
    gl = ng.nodes.new("CompositorNodeGlare")
    gl.inputs["Type"].default_value = "Bloom"
    gl.inputs["Quality"].default_value = QUALITY
    gl.inputs["Threshold"].default_value = threshold
    gl.inputs["Strength"].default_value = strength
    gl.inputs["Size"].default_value = size
    ng.links.new(rl.outputs["Image"], gl.inputs["Image"])
    last = gl.outputs[0]
    ng.interface.new_socket("Image", in_out="OUTPUT", socket_type="NodeSocketColor")
    out = ng.nodes.new("NodeGroupOutput")
    ng.links.new(last, out.inputs[0])
    return ng


def area_light(name, loc, rot, size, energy, color=(1, 0.85, 0.65), shape="RECTANGLE", size_y=None, camera_visible=False):
    ld = bpy.data.lights.new(name, "AREA")
    ld.energy = energy
    ld.color = color
    ld.shape = shape
    ld.size = size
    if size_y:
        ld.size_y = size_y
    o = link(bpy.data.objects.new(name, ld))
    o.location = loc
    o.rotation_euler = rot
    return o
