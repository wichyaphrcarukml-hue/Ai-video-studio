"""Original character "Lumi": realistic adult woman, luxury dancewear, sleek high ponytail.

build(D) -> dict(rig=..., body=..., parts=[...], L=landmarks)
D is the MPFB2 data folder (only data files are read from it).
"""
import math, os, random
import numpy as np
import bpy, bmesh
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree
from mathutils.kdtree import KDTree
import charlib as C

RNG = np.random.default_rng(7)


# ======================================================================= helpers
def link(ob):
    bpy.context.scene.collection.objects.link(ob)
    return ob


def parent_to_bone(ob, rig, bone):
    mw = ob.matrix_world.copy()
    ob.parent = rig; ob.parent_type = 'BONE'; ob.parent_bone = bone
    bpy.context.view_layer.update()
    ob.matrix_world = mw


def node(nt, kind, loc=(0, 0), **props):
    n = nt.nodes.new(kind); n.location = loc
    for k, v in props.items():
        setattr(n, k, v)
    return n


def mix_rgb(nt, fac, a, b, blend='MIX'):
    m = nt.nodes.new('ShaderNodeMix'); m.data_type = 'RGBA'; m.blend_type = blend
    _feed(nt, m.inputs[0], fac); _feed(nt, m.inputs[6], a); _feed(nt, m.inputs[7], b)
    return m.outputs[2]


def mix_float(nt, fac, a, b):
    m = nt.nodes.new('ShaderNodeMix'); m.data_type = 'FLOAT'
    _feed(nt, m.inputs[0], fac); _feed(nt, m.inputs[2], a); _feed(nt, m.inputs[3], b)
    return m.outputs[0]


def math_node(nt, op, a, b=None, clamp=False):
    m = nt.nodes.new('ShaderNodeMath'); m.operation = op; m.use_clamp = clamp
    _feed(nt, m.inputs[0], a)
    if b is not None:
        _feed(nt, m.inputs[1], b)
    return m.outputs[0]


def _feed(nt, sock, val):
    if hasattr(val, 'is_output'):
        nt.links.new(val, sock)
    elif isinstance(val, (tuple, list)):
        sock.default_value = tuple(val) + ((1.0,) if len(val) == 3 and len(sock.default_value) == 4 else ())
    else:
        sock.default_value = val


def new_material(name):
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = node(nt, 'ShaderNodeOutputMaterial', (900, 0))
    return m, nt, out


def principled(nt, **inputs):
    p = node(nt, 'ShaderNodeBsdfPrincipled', (500, 0))
    for k, v in inputs.items():
        _feed(nt, p.inputs[k], v)
    return p


def image_mask(nt, path, uv):
    img = bpy.data.images.load(path, check_existing=True)
    img.colorspace_settings.name = 'Non-Color'
    t = node(nt, 'ShaderNodeTexImage'); t.image = img
    nt.links.new(uv, t.inputs['Vector'])
    return t.outputs['Color']


def surface_bvh(ob):
    dg = bpy.context.evaluated_depsgraph_get()
    return BVHTree.FromObject(ob, dg)


def weights_from_body(target, body, rest_body_co):
    """Copy armature weights from the nearest body vertex to every vertex of `target` (rest pose)."""
    kd = KDTree(len(rest_body_co))
    for i, c in enumerate(rest_body_co):
        kd.insert(c, i)
    kd.balance()
    gnames = {g.index: g.name for g in body.vertex_groups}
    vw = [[] for _ in range(len(body.data.vertices))]
    for v in body.data.vertices:
        for g in v.groups:
            vw[v.index].append((gnames[g.group], g.weight))
    groups = {}
    for v in target.data.vertices:
        _, i, _ = kd.find(target.matrix_world @ v.co)
        for gname, w in vw[i]:
            if gname not in groups:
                groups[gname] = target.vertex_groups.new(name=gname)
            groups[gname].add([v.index], w, 'REPLACE')


def bind(ob, rig, body, rest_co):
    weights_from_body(ob, body, rest_co)
    ob.parent = rig
    m = ob.modifiers.new('Armature', 'ARMATURE'); m.object = rig
    return m


def make_curves(name, strands, r_root, r_tip, mat):
    cv = bpy.data.hair_curves.new(name)
    sizes = [len(s) for s in strands]
    cv.add_curves(sizes)
    pos = np.concatenate(strands).astype(np.float32)
    cv.attributes['position'].data.foreach_set('vector', pos.ravel())
    if 'radius' not in cv.attributes:
        cv.attributes.new('radius', 'FLOAT', 'POINT')
    rad = np.concatenate([np.linspace(r_root, r_tip, n) for n in sizes]).astype(np.float32)
    cv.attributes['radius'].data.foreach_set('value', rad)
    cv.materials.append(mat)
    return link(bpy.data.objects.new(name, cv))


# ======================================================================= materials
def skin_material(D):
    m, nt, out = new_material('Skin')
    tex = os.path.join(D, 'textures')
    uv = node(nt, 'ShaderNodeTexCoord').outputs['UV']
    obj = node(nt, 'ShaderNodeTexCoord').outputs['Object']
    lips = image_mask(nt, os.path.join(tex, 'mpfb_lips.jpg'), uv)
    lids = image_mask(nt, os.path.join(tex, 'mpfb_eyelids.jpg'), uv)
    fn = image_mask(nt, os.path.join(tex, 'mpfb_fingernails.jpg'), uv)
    tn = image_mask(nt, os.path.join(tex, 'mpfb_toenails.jpg'), uv)
    nails = math_node(nt, 'MAXIMUM', fn, tn)

    # warm light-medium skin with subtle mottling
    n1 = node(nt, 'ShaderNodeTexNoise'); n1.inputs['Scale'].default_value = 9; n1.inputs['Detail'].default_value = 6
    nt.links.new(obj, n1.inputs['Vector'])
    ramp = node(nt, 'ShaderNodeValToRGB'); nt.links.new(n1.outputs['Fac'], ramp.inputs['Fac'])
    ramp.color_ramp.elements[0].position = 0.35; ramp.color_ramp.elements[1].position = 0.7
    base = mix_rgb(nt, math_node(nt, 'MULTIPLY', ramp.outputs['Color'], 0.35), (0.33, 0.19, 0.13), (0.31, 0.155, 0.108))
    scalp = node(nt, 'ShaderNodeAttribute'); scalp.attribute_name = 'scalp'
    base = mix_rgb(nt, scalp.outputs['Fac'], base, (0.035, 0.022, 0.016))
    lipcol = (0.26, 0.05, 0.055)
    col = mix_rgb(nt, math_node(nt, 'MULTIPLY', lips, 0.85), base, lipcol)
    col = mix_rgb(nt, math_node(nt, 'MULTIPLY', lids, 0.45), col, (0.22, 0.12, 0.08))          # bronze eyeshadow
    col = mix_rgb(nt, nails, col, (0.20, 0.008, 0.015))                                         # deep red polish

    rough = mix_float(nt, lips, 0.46, 0.3)
    rough = mix_float(nt, nails, rough, 0.08)
    # pores + fine detail bump
    p1 = node(nt, 'ShaderNodeTexNoise'); p1.inputs['Scale'].default_value = 1400; p1.inputs['Detail'].default_value = 2
    nt.links.new(obj, p1.inputs['Vector'])
    p2 = node(nt, 'ShaderNodeTexNoise'); p2.inputs['Scale'].default_value = 160; p2.inputs['Detail'].default_value = 4
    nt.links.new(obj, p2.inputs['Vector'])
    b1 = node(nt, 'ShaderNodeBump'); b1.inputs['Strength'].default_value = 0.06; b1.inputs['Distance'].default_value = 0.0002
    nt.links.new(p1.outputs['Fac'], b1.inputs['Height'])
    b2 = node(nt, 'ShaderNodeBump'); b2.inputs['Strength'].default_value = 0.04; b2.inputs['Distance'].default_value = 0.0005
    nt.links.new(p2.outputs['Fac'], b2.inputs['Height']); nt.links.new(b1.outputs['Normal'], b2.inputs['Normal'])
    rough = math_node(nt, 'ADD', rough, math_node(nt, 'MULTIPLY', math_node(nt, 'SUBTRACT', p2.outputs['Fac'], 0.5), 0.12))

    p = principled(nt, **{'Subsurface Weight': 1.0, 'Subsurface Radius': (1.0, 0.35, 0.2), 'Subsurface Scale': 0.0045,
                          'Coat Weight': 0.0, 'Sheen Weight': 0.15, 'Sheen Roughness': 0.45,
                          'Specular IOR Level': 0.38})
    p.subsurface_method = 'RANDOM_WALK_SKIN'
    nt.links.new(col, p.inputs['Base Color']); nt.links.new(rough, p.inputs['Roughness'])
    nt.links.new(b2.outputs['Normal'], p.inputs['Normal'])
    nt.links.new(p.outputs[0], out.inputs['Surface'])
    return m


def hair_material(name, melanin=0.98, redness=0.22, rough=0.24):
    m, nt, out = new_material(name)
    h = node(nt, 'ShaderNodeBsdfHairPrincipled', (400, 0))
    h.parametrization = 'MELANIN'
    for k, v in {'Melanin': melanin, 'Melanin Redness': redness, 'Roughness': rough, 'Radial Roughness': 0.35,
                 'Coat': 0.1, 'Random Roughness': 0.12, 'Random Color': 0.15}.items():
        if k in h.inputs:
            h.inputs[k].default_value = v
    nt.links.new(h.outputs[0], out.inputs['Surface'])
    return m


def gold_material(name='Gold', rough=0.16):
    m, nt, out = new_material(name)
    p = principled(nt, **{'Base Color': (1.0, 0.72, 0.36), 'Metallic': 1.0, 'Roughness': rough})
    nt.links.new(p.outputs[0], out.inputs['Surface'])
    return m


def garment_material(name, kind):
    """Fabric with a smooth cut-out edge: attribute 'cut' (metres, >0 inside) -> alpha; thin gold trim at the edge."""
    m, nt, out = new_material(name)
    cut = node(nt, 'ShaderNodeAttribute'); cut.attribute_name = 'cut'
    alpha = math_node(nt, 'ADD', math_node(nt, 'MULTIPLY', cut.outputs['Fac'], 1500.0), 0.5, clamp=True)
    trim = math_node(nt, 'LESS_THAN', cut.outputs['Fac'], 0.0032)
    obj = node(nt, 'ShaderNodeTexCoord').outputs['Object']
    if kind == 'sequin':
        vor = node(nt, 'ShaderNodeTexVoronoi'); vor.inputs['Scale'].default_value = 650
        nt.links.new(obj, vor.inputs['Vector'])
        tilt = node(nt, 'ShaderNodeVectorMath'); tilt.operation = 'SUBTRACT'
        nt.links.new(vor.outputs['Color'], tilt.inputs[0]); tilt.inputs[1].default_value = (0.5, 0.5, 0.5)
        sc = node(nt, 'ShaderNodeVectorMath'); sc.operation = 'SCALE'; nt.links.new(tilt.outputs[0], sc.inputs[0])
        sc.inputs['Scale'].default_value = 0.9
        geo = node(nt, 'ShaderNodeNewGeometry')
        add = node(nt, 'ShaderNodeVectorMath'); add.operation = 'ADD'
        nt.links.new(geo.outputs['Normal'], add.inputs[0]); nt.links.new(sc.outputs[0], add.inputs[1])
        nrm = node(nt, 'ShaderNodeVectorMath'); nrm.operation = 'NORMALIZE'; nt.links.new(add.outputs[0], nrm.inputs[0])
        fabric = principled(nt, **{'Base Color': (0.80, 0.58, 0.34), 'Metallic': 1.0, 'Roughness': 0.2})
        nt.links.new(nrm.outputs[0], fabric.inputs['Normal'])
    else:  # black satin
        fabric = principled(nt, **{'Base Color': (0.012, 0.011, 0.013), 'Roughness': 0.24, 'Anisotropic': 0.6,
                                   'Sheen Weight': 0.6, 'Sheen Tint': (0.55, 0.45, 0.4), 'Coat Weight': 0.25,
                                   'Coat Roughness': 0.15})
    gold = principled(nt, **{'Base Color': (1.0, 0.72, 0.36), 'Metallic': 1.0, 'Roughness': 0.14})
    sh = nt.nodes.new('ShaderNodeMixShader'); nt.links.new(trim, sh.inputs[0])
    nt.links.new(fabric.outputs[0], sh.inputs[1]); nt.links.new(gold.outputs[0], sh.inputs[2])
    tr = nt.nodes.new('ShaderNodeBsdfTransparent')
    sh2 = nt.nodes.new('ShaderNodeMixShader'); nt.links.new(alpha, sh2.inputs[0])
    nt.links.new(tr.outputs[0], sh2.inputs[1]); nt.links.new(sh.outputs[0], sh2.inputs[2])
    nt.links.new(sh2.outputs[0], out.inputs['Surface'])
    return m


# ======================================================================= parts
def landmarks(b, faces):
    L = {}
    for side, s in (('l', 1), ('r', -1)):
        vs = C.group_verts(faces, f'helper-{side}-eye')
        L[f'eye_{side}'] = Vector(b[vs].mean(axis=0))
        L[f'eye_rad'] = float((b[vs].max(axis=0) - b[vs].min(axis=0)).max() / 2)
    bodyv = sorted({v for f in faces if f[0] == 'body' for v in f[1]})
    B = b[bodyv]
    L['eye_z'] = L['eye_l'].z
    scalp = B[B[:, 2] > L['eye_z'] + 0.02]
    L['head_c'] = Vector(((scalp[:, 0].max() + scalp[:, 0].min()) / 2, (scalp[:, 1].max() + scalp[:, 1].min()) / 2,
                          L['eye_z'] + 0.005))
    sel = B[(B[:, 0] > 0.04) & (B[:, 0] < 0.15) & (B[:, 2] > 1.1) & (B[:, 2] < 1.35)]
    L['bust'] = Vector(sel[sel[:, 1].argmin()])
    return L


def make_eyes(L, rig):
    parts = []
    sclera_iris, nt, out = new_material('Eye')
    oc = node(nt, 'ShaderNodeTexCoord').outputs['Object']
    sep = node(nt, 'ShaderNodeSeparateXYZ'); nt.links.new(oc, sep.inputs[0])
    x, y, z = sep.outputs
    r = math_node(nt, 'SQRT', math_node(nt, 'ADD', math_node(nt, 'MULTIPLY', x, x), math_node(nt, 'MULTIPLY', z, z)))
    front = math_node(nt, 'LESS_THAN', y, 0.0)
    iris = math_node(nt, 'MULTIPLY', front, math_node(nt, 'SMOOTH_MIN', 1.0,
                     math_node(nt, 'MULTIPLY', math_node(nt, 'SUBTRACT', 0.5, r), 40.0)), clamp=True)
    iris = math_node(nt, 'MAXIMUM', iris, 0.0)
    pupil = math_node(nt, 'MULTIPLY', front, math_node(nt, 'LESS_THAN', r, 0.19))
    ang = math_node(nt, 'ARCTAN2', z, x)
    comb = node(nt, 'ShaderNodeCombineXYZ'); nt.links.new(math_node(nt, 'MULTIPLY', ang, 6.0), comb.inputs[0])
    nt.links.new(math_node(nt, 'MULTIPLY', r, 3.0), comb.inputs[1])
    nz = node(nt, 'ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 3.0; nz.inputs['Detail'].default_value = 8
    nt.links.new(comb.outputs[0], nz.inputs['Vector'])
    irc = mix_rgb(nt, nz.outputs['Fac'], (0.03, 0.014, 0.006), (0.30, 0.15, 0.05))
    limbal = math_node(nt, 'MULTIPLY', math_node(nt, 'GREATER_THAN', r, 0.42), 0.75)
    irc = mix_rgb(nt, limbal, irc, (0.01, 0.006, 0.004))
    sclera = mix_rgb(nt, math_node(nt, 'MULTIPLY', math_node(nt, 'GREATER_THAN', r, 0.7), 0.4),
                     (0.78, 0.74, 0.70), (0.75, 0.55, 0.50))
    col = mix_rgb(nt, iris, sclera, irc)
    col = mix_rgb(nt, pupil, col, (0.002, 0.002, 0.002))
    p = principled(nt, **{'Roughness': 0.35, 'Subsurface Weight': 0.2, 'Subsurface Scale': 0.002})
    nt.links.new(col, p.inputs['Base Color']); nt.links.new(p.outputs[0], out.inputs['Surface'])

    cornea, nt2, out2 = new_material('Cornea')
    g = principled(nt2, **{'Transmission Weight': 1.0, 'Roughness': 0.0, 'IOR': 1.376, 'Base Color': (1, 1, 1)})
    nt2.links.new(g.outputs[0], out2.inputs['Surface'])

    for side in ('l', 'r'):
        for kind in ('ball', 'cornea'):
            me = bpy.data.meshes.new(f'eye_{side}_{kind}')
            bm = bmesh.new()
            bmesh.ops.create_uvsphere(bm, u_segments=48, v_segments=32, radius=1.0)
            if kind == 'cornea':
                for v in bm.verts:
                    if v.co.y < -0.55:
                        v.co.y -= 0.12 * ((-v.co.y - 0.55) / 0.45) ** 1.5
            bm.to_mesh(me); bm.free()
            for poly in me.polygons:
                poly.use_smooth = True
            ob = link(bpy.data.objects.new(me.name, me))
            ob.location = L[f'eye_{side}'] + Vector((0, 0.001, 0))
            s = L['eye_rad'] * (0.97 if kind == 'ball' else 1.0)
            ob.scale = (s, s, s)
            me.materials.append(sclera_iris if kind == 'ball' else cornea)
            if kind == 'cornea':
                ob.visible_shadow = False
            bpy.context.view_layer.update()
            parent_to_bone(ob, rig, 'head')
            parts.append(ob)
    return parts


def make_lashes(b, faces, L, rig, mat):
    strands = []
    for side in ('l', 'r'):
        c = np.array(L[f'eye_{side}'])
        for g, n, up, length in ((f'helper-{side}-eyelashes-2', 150, 1, 1.35), (f'helper-{side}-eyelashes-1', 55, -1, 0.9)):
            vs = np.array(C.group_verts(faces, g))
            P = b[vs]
            d = np.linalg.norm(P - c, axis=1)
            med = np.median(d)
            roots, tips = P[d < med], P[d >= med]
            roots = roots[np.argsort(roots[:, 0])]
            for k in range(n):
                t = RNG.uniform(0, len(roots) - 1.001)
                i = int(t); f = t - i
                r0 = roots[i] * (1 - f) + roots[i + 1] * f
                tip = tips[np.argmin(np.linalg.norm(tips - r0, axis=1))]
                dirv = (tip - r0) * length * RNG.uniform(0.8, 1.1)
                curl = np.array([0, 0, up * np.linalg.norm(dirv) * 0.35])
                pts = np.array([r0 + dirv * s + curl * s * s - np.array([0, 0.0006, 0]) * s for s in np.linspace(0, 1, 5)])
                strands.append(pts)
    ob = make_curves('Lashes', strands, 0.0001, 0.00003, mat)
    parent_to_bone(ob, rig, 'head')
    return ob


def make_brows(bvh, L, rig, mat):
    strands = []
    ez = L['eye_z']
    for side, s in (('l', 1), ('r', -1)):
        cx = abs(L[f'eye_{side}'].x)
        for k in range(800):
            u = RNG.uniform(0, 1) ** 0.9
            x = s * (0.009 + u * (cx + 0.025 - 0.009))
            arch = math.sin(min(u / 0.65, 1) * math.pi / 2) if u < 0.65 else 1 - 1.6 * (u - 0.65)
            zc = ez + 0.0175 + 0.0065 * arch
            th = 0.0068 * (1 - u) + 0.0024 * u
            z = zc + RNG.uniform(-0.5, 0.5) * th
            hit, nrm, _, _ = bvh.ray_cast(Vector((x, -0.4, z)), Vector((0, 1, 0)))
            if hit is None:
                continue
            nrm = nrm.normalized()
            dirv = Vector((s * (0.25 + 1.4 * u), 0, (1.3 - 1.4 * u) + RNG.uniform(-0.25, 0.25)))
            dirv = (dirv - nrm * dirv.dot(nrm)).normalized()
            ln = RNG.uniform(0.0045, 0.0075)
            root = hit + nrm * 0.0003
            pts = [root + dirv * ln * t + nrm * (0.0006 * t) for t in np.linspace(0, 1, 4)]
            strands.append(np.array([tuple(p) for p in pts]))
    ob = make_curves('Brows', strands, 0.00006, 0.000025, mat)
    parent_to_bone(ob, rig, 'head')
    return ob


def make_hair(body, bvh, L, rig, mat, gold, n_strands=16000):
    """Sleek, pulled-back high ponytail. Strands run from the scalp to a gold cuff and on down the tail."""
    hc = L['head_c']; ez = L['eye_z']
    me = body.data
    co = np.array([v.co for v in me.vertices])

    def in_scalp(p):
        rel = p - np.array(hc)
        rxy = math.hypot(rel[0], rel[1]) + 1e-9
        f = -rel[1] / rxy   # 1 = front, -1 = back
        th = np.interp(f, [-1, -0.3, 0.0, 0.3, 0.6, 1.0], [-0.115, -0.075, 0.0, 0.03, 0.05, 0.056])
        if abs(rel[0]) > 0.068 and p[2] < ez + 0.012 and f > -0.55:
            return False   # ears
        return p[2] > ez + th

    mask = np.array([in_scalp(c) for c in co])
    a = me.attributes.new('scalp', 'FLOAT', 'POINT'); a.data.foreach_set('value', mask.astype(np.float32))
    tris, areas = [], []
    for poly in me.polygons:
        vs = list(poly.vertices)
        if all(mask[v] for v in vs):
            for k in range(1, len(vs) - 1):
                a, b_, c_ = co[vs[0]], co[vs[k]], co[vs[k + 1]]
                tris.append((a, b_, c_)); areas.append(np.linalg.norm(np.cross(b_ - a, c_ - a)) / 2)
    areas = np.array(areas); prob = areas / areas.sum()

    # ponytail anchor: high on the back of the head
    dA = Vector((0, 0.72, 0.69)).normalized()
    loc, nA, _, _ = bvh.ray_cast(hc + dA * 0.3, -dA)
    A = loc + dA * 0.016
    T0 = Vector((0, 0.75, 0.2)).normalized()      # tail leaves the cuff going back, then falls
    tail_ctrl = [A, A + T0 * 0.07, A + Vector((0, 0.12, -0.10)), A + Vector((0, 0.11, -0.43))]

    def bez(t):
        p0, p1, p2, p3 = tail_ctrl
        return p0 * (1 - t) ** 3 + p1 * 3 * (1 - t) ** 2 * t + p2 * 3 * (1 - t) * t ** 2 + p3 * t ** 3

    strands = []
    picks = RNG.choice(len(tris), size=n_strands, p=prob)
    for k, ti in enumerate(picks):
        a, b_, c_ = tris[ti]
        u, v = RNG.random(), RNG.random()
        if u + v > 1:
            u, v = 1 - u, 1 - v
        p = Vector(a + u * (b_ - a) + v * (c_ - a))
        loc, nrm, _, _ = bvh.find_nearest(p)
        root = loc + nrm * 0.0004
        d0 = (root - hc).normalized()
        layer = RNG.random()
        pts = []
        ang = d0.angle(dA)
        for t in np.linspace(0, 1, 12):
            dt = d0.slerp(dA, t) if ang > 1e-4 else dA
            hit, _, _, _ = bvh.ray_cast(hc + dt * 0.3, -dt)
            surf = hit if hit is not None else hc + dt * 0.1
            off = 0.0006 + 0.0025 * layer * t + 0.008 * t ** 3
            pts.append(surf + dt * off)
        # converge into the cuff
        ring = Vector((RNG.normal(), 0, RNG.normal())).normalized() * 0.008 * math.sqrt(RNG.random())
        pts[-1] = A + Vector((ring.x, ring.z * 0.3, ring.z))
        pts[-2] = pts[-2].lerp(pts[-1], 0.5)
        # tail
        Li = RNG.uniform(0.72, 1.0)
        rdir = Vector((RNG.normal(), RNG.normal(), RNG.normal()))
        phase = RNG.uniform(0, 6.28)
        for t in np.linspace(0, Li, 18)[1:]:
            c = bez(t)
            tan = (bez(min(t + 0.01, 1)) - bez(max(t - 0.01, 0))).normalized()
            nvec = (rdir - tan * rdir.dot(tan)).normalized()
            R = 0.008 + 0.028 * math.sin(min(t / 0.55, 1) * math.pi / 2) - 0.014 * max(0, t - 0.6) / 0.4
            rr = R * math.sqrt(layer)
            wave = 0.004 * math.sin(t * 18 + phase)
            pts.append(c + nvec * (rr + wave))
        strands.append(np.array([tuple(q) for q in pts]))
    # a few soft flyaways near the hairline
    for k in range(50):
        ti = RNG.choice(len(tris), p=prob)
        p = Vector(tris[ti][0]); loc, nrm, _, _ = bvh.find_nearest(p)
        dirv = Vector((RNG.normal(), RNG.normal(), RNG.normal() + 1)).normalized()
        strands.append(np.array([tuple(loc + nrm * 0.0005 + (dirv * 0.012 + nrm * 0.004) * t * t + dirv * 0.006 * t)
                                 for t in np.linspace(0, 1, 6)]))
    hair = make_curves('Hair', strands, 0.00008, 0.00003, mat)
    parent_to_bone(hair, rig, 'head')

    # gold cuff
    me2 = bpy.data.meshes.new('Cuff'); bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=False, segments=48, radius1=0.0125, radius2=0.0115, depth=0.022)
    bm.to_mesh(me2); bm.free()
    cuff = link(bpy.data.objects.new('Cuff', me2))
    cuff.location = A + T0 * 0.008
    cuff.rotation_euler = Vector((0, 0, 1)).rotation_difference(T0).to_euler()
    me2.materials.append(gold)
    m = cuff.modifiers.new('Bevel', 'SOLIDIFY'); m.thickness = 0.0015
    cuff.modifiers.new('Sub', 'SUBSURF').levels = 2
    for poly in me2.polygons:
        poly.use_smooth = True
    bpy.context.view_layer.update()
    parent_to_bone(cuff, rig, 'head')
    return hair, cuff, A


def make_garment(body, rest_co, name, field, mat, offset):
    """Copy body faces where the design field is near/inside, store the field as attribute 'cut'."""
    me = body.data
    val = np.array([field(c) for c in rest_co])
    keep = [p for p in me.polygons if max(val[v] for v in p.vertices) > -0.004]
    used = sorted({v for p in keep for v in p.vertices}); remap = {v: i for i, v in enumerate(used)}
    gm = bpy.data.meshes.new(name)
    gm.from_pydata([tuple(rest_co[v]) for v in used], [], [[remap[v] for v in p.vertices] for p in keep])
    gm.shade_smooth()
    a = gm.attributes.new('cut', 'FLOAT', 'POINT')
    a.data.foreach_set('value', val[used].astype(np.float32))
    gm.materials.append(mat)
    ob = link(bpy.data.objects.new(name, gm))
    # same skinning as the body vertices it came from
    gnames = {g.index: g.name for g in body.vertex_groups}
    groups = {}
    for v in used:
        for g in me.vertices[v].groups:
            nm = gnames[g.group]
            if nm not in groups:
                groups[nm] = ob.vertex_groups.new(name=nm)
            groups[nm].add([remap[v]], g.weight, 'REPLACE')
    return ob


def outfit_fields(L):
    zb = L['bust'].z; xb = abs(L['bust'].x)
    zu = zb - 0.075                       # under-bust line

    def top_field(c):
        x, y, z = c
        ax = abs(x)
        if ax > 0.2:
            return -1.0
        # cups: plunge V at centre, peak at the strap point, down to the side seam
        front_top = np.interp(ax, [0.0, 0.012, xb - 0.02, xb + 0.06, 0.2], [zb - 0.035, zb - 0.03, zb + 0.075, zb + 0.015, zb - 0.02])
        back_top = zu + 0.012
        w = np.clip((y + 0.02) / 0.08, 0, 1)                 # 0 at front, 1 at back
        ztop = front_top * (1 - w) + back_top * w
        zlow = zu - 0.03 + 0.004 * w
        return min(ztop - z, z - zlow)

    def shorts_field(c):
        x, y, z = c
        if abs(x) > 0.22 or z < 0.6:
            return -1.0
        zw = 1.0 + 0.04 * min(1, abs(x) / 0.13) + 0.02 * np.clip((y + 0.05) / 0.12, 0, 1)
        if abs(x) < 0.025:
            zc = 0.76
        else:
            s = 1 if x > 0 else -1
            ox, fy = (x - s * 0.095) * s, -(y + 0.02)
            n = math.hypot(ox, fy) + 1e-9
            ox, fy = ox / n, fy / n
            zc = 0.815 + 0.085 * max(0, ox) + 0.02 * max(0, fy) - 0.03 * max(0, -fy) * (1 - max(0, ox))
        return min(zw - z, z - zc)
    return top_field, shorts_field


def make_strap_path(bvh, pts, offset=0.0022, n=60):
    from mathutils import geometry
    ctrl = [Vector(p) for p in pts]
    out = []
    for i in range(n):
        t = i / (n - 1) * (len(ctrl) - 1); k = min(int(t), len(ctrl) - 2); f = t - k
        p0 = ctrl[max(k - 1, 0)]; p1 = ctrl[k]; p2 = ctrl[k + 1]; p3 = ctrl[min(k + 2, len(ctrl) - 1)]
        p = 0.5 * ((2 * p1) + (-p0 + p2) * f + (2 * p0 - 5 * p1 + 4 * p2 - p3) * f * f + (-p0 + 3 * p1 - 3 * p2 + p3) * f ** 3)
        loc, nrm, _, _ = bvh.find_nearest(p)
        out.append(loc + nrm * offset)
    return out


def tube(name, path, radius, mat):
    cu = bpy.data.curves.new(name, 'CURVE'); cu.dimensions = '3D'
    cu.bevel_depth = radius; cu.bevel_resolution = 3
    sp = cu.splines.new('POLY'); sp.points.add(len(path) - 1)
    for i, p in enumerate(path):
        sp.points[i].co = (p.x, p.y, p.z, 1)
    tmp = link(bpy.data.objects.new(name + '_c', cu))
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(tmp.evaluated_get(dg))
    bpy.data.objects.remove(tmp)
    me.materials.clear(); me.materials.append(mat)
    for poly in me.polygons:
        poly.use_smooth = True
    return link(bpy.data.objects.new(name, me))


def find_lobes(rest_co, L):
    out = {}
    for side, s in (('l', 1), ('r', -1)):
        sel = rest_co[(rest_co[:, 0] * s > 0.06) & (rest_co[:, 2] < L['eye_z'] - 0.01) & (rest_co[:, 2] > L['eye_z'] - 0.075)
                      & (np.abs(rest_co[:, 1] - L['head_c'].y) < 0.035)]
        far = sel[np.argsort(-sel[:, 0] * s)[:60]]
        out[side] = Vector(far[far[:, 2].argmin()])
    return out


# ======================================================================= build
def build(D, hair_strands=30000):
    C.clear_scene()
    co, uvs, faces = C.shaped_coords(D, {**C.MACRO, **C.DETAIL})
    b = C.to_blender(co)
    bodyv = sorted({v for f in faces if f[0] == 'body' for v in f[1]})
    b[:, 2] -= b[bodyv, 2].min()
    body, remap = C.make_body('Body', b, uvs, faces)
    rig = C.build_rig(D, b, faces, body, remap)
    L = landmarks(b, faces)
    rest_co = np.array([v.co for v in body.data.vertices])
    body.data.materials.append(skin_material(D))
    sub = body.modifiers.new('Sub', 'SUBSURF'); sub.levels = 1; sub.render_levels = 2
    bpy.context.view_layer.update()
    bvh = surface_bvh(body)

    parts = []
    parts += make_eyes(L, rig)
    parts.append(make_lashes(b, faces, L, rig, hair_material('Lash', 1.0, 0.1, 0.3)))
    parts.append(make_brows(bvh, L, rig, hair_material('Brow', 0.97, 0.3, 0.35)))
    gold = gold_material()
    hair, cuff, anchor = make_hair(body, bvh, L, rig, hair_material('Hair'), gold, hair_strands)
    parts += [hair, cuff]

    top_f, shorts_f = outfit_fields(L)
    for name, f, kind, off in (('Top', top_f, 'sequin', 0.0026), ('Shorts', shorts_f, 'satin', 0.0016)):
        g = make_garment(body, rest_co, name, f, garment_material(name + 'Mat', kind), off)
        g.parent = rig
        g.modifiers.new('Armature', 'ARMATURE').object = rig
        s = g.modifiers.new('Sub', 'SUBSURF'); s.levels = 1; s.render_levels = 2
        d = g.modifiers.new('Offset', 'DISPLACE'); d.strength = off; d.mid_level = 0
        parts.append(g)

    # gold chain straps: cup peak -> over the shoulder -> back band
    zb, xb = L['bust'].z, abs(L['bust'].x)
    for s in (1, -1):
        pts = [(s * (xb - 0.02), -0.2, zb + 0.072), (s * 0.085, -0.08, 1.37), (s * 0.095, 0.0, 1.415),
               (s * 0.09, 0.09, 1.36), (s * 0.075, 0.2, zb - 0.06)]
        st = tube(f'Strap_{s}', make_strap_path(bvh, pts), 0.0014, gold)
        bind(st, rig, body, rest_co); parts.append(st)
    # hoop earrings
    for side, lobe in find_lobes(rest_co, L).items():
        me = bpy.data.meshes.new('Hoop'); bm = bmesh.new()
        bmesh.ops.create_circle(bm, segments=64, radius=0.011)
        bm.to_mesh(me); bm.free()
        ring = link(bpy.data.objects.new(f'Hoop_{side}', me))
        sk = ring.modifiers.new('Skin', 'SKIN')
        for v in me.skin_vertices[0].data:
            v.radius = (0.0009, 0.0009)
        ring.modifiers.new('Sub', 'SUBSURF').levels = 2
        me.materials.append(gold)
        ring.location = lobe + Vector((0, 0, -0.0105))
        ring.rotation_euler = (0, math.radians(90), 0)
        bpy.context.view_layer.update()
        parent_to_bone(ring, rig, 'head'); parts.append(ring)
    return dict(rig=rig, body=body, parts=parts, L=L, anchor=anchor, rest_co=rest_co)


# ======================================================================= posing
def rot(rig, bone, axis, deg):
    pb = rig.pose.bones[bone]
    h = pb.head.copy()
    R = Matrix.Translation(h) @ Matrix.Rotation(math.radians(deg), 4, axis) @ Matrix.Translation(-h)
    pb.matrix = R @ pb.matrix
    bpy.context.view_layer.update()


def pose_relaxed(rig):
    X, Y, Z = Vector((1, 0, 0)), Vector((0, 1, 0)), Vector((0, 0, 1))
    rot(rig, 'pelvis', Y, -3); rot(rig, 'pelvis', Z, 6)
    rot(rig, 'spine_02', Y, 3); rot(rig, 'spine_03', Y, 1.5)
    rot(rig, 'upperarm_l', Y, 36); rot(rig, 'upperarm_r', Y, -38)
    rot(rig, 'upperarm_l', X, -4); rot(rig, 'upperarm_r', X, -6)
    rot(rig, 'lowerarm_l', X, -14); rot(rig, 'lowerarm_r', X, -10)
    rot(rig, 'thigh_r', X, -7); rot(rig, 'calf_r', X, 14); rot(rig, 'thigh_r', Y, 2)
    rot(rig, 'neck_01', Y, -2); rot(rig, 'head', Y, -4); rot(rig, 'head', Z, -6)
    curl_fingers(rig)


def curl_fingers(rig, amount=1.0):
    """Relaxed hand: each finger joint flexes toward the palm (about the bone's local X axis)."""
    for side in ('l', 'r'):
        for f, base in (('index', 12), ('middle', 16), ('ring', 20), ('pinky', 24), ('thumb', 8)):
            for j, k in (('01', 1.0), ('02', 1.3), ('03', 1.0)):
                pb = rig.pose.bones.get(f'{f}_{j}_{side}')
                if pb:
                    pb.rotation_mode = 'XYZ'
                    pb.rotation_euler.x = math.radians(base * k * amount) * FINGER_SIGN
    bpy.context.view_layer.update()


FINGER_SIGN = 1.0
