"""Build an original, realistic adult female character in Blender (bpy) from MakeHuman / MPFB2 CC0 *data* files.

Only data is read from MPFB2 (base mesh, morph targets, rig joint definitions, skin weights, UV masks).
Everything else -- shaping, rig construction, skin/eye/hair/outfit materials -- is done here.
"""
import gzip, json, math, os
import numpy as np
import bpy
from mathutils import Vector, Matrix

SCALE = 0.1  # MakeHuman units are decimetres


# ---------------------------------------------------------------- data
def parse_obj(path):
    verts, uvs, faces, group = [], [], [], None
    with open(path) as fh:
        for line in fh:
            if line.startswith('v '):
                verts.append([float(x) for x in line.split()[1:4]])
            elif line.startswith('vt '):
                uvs.append([float(x) for x in line.split()[1:3]])
            elif line.startswith('g '):
                group = line.split(None, 1)[1].strip()
            elif line.startswith('f '):
                vi, ti = [], []
                for tok in line.split()[1:]:
                    p = tok.split('/')
                    vi.append(int(p[0]) - 1)
                    ti.append(int(p[1]) - 1 if len(p) > 1 and p[1] else -1)
                faces.append((group, vi, ti))
    return np.array(verts, dtype=np.float64), np.array(uvs, dtype=np.float64), faces


def load_target(path):
    idx, delta = [], []
    with gzip.open(path, 'rt') as fh:
        for line in fh:
            p = line.split()
            if len(p) == 4 and not line.startswith('#'):
                idx.append(int(p[0])); delta.append([float(x) for x in p[1:]])
    return np.array(idx, dtype=np.int64), np.array(delta, dtype=np.float64).reshape(-1, 3)


def to_blender(co):
    """MakeHuman (Y up, +Z front, dm) -> Blender (Z up, -Y front, m)."""
    return np.stack([co[:, 0], -co[:, 2], co[:, 1]], axis=1) * SCALE


# ---------------------------------------------------------------- character recipe
# Original fictional adult woman (mid/late 20s). Natural proportions, slim-athletic dancer build.
MACRO = {
    'macrodetails/universal-female-young-averagemuscle-averageweight': 0.75,
    'macrodetails/universal-female-young-averagemuscle-minweight': 0.10,
    'macrodetails/universal-female-young-maxmuscle-averageweight': 0.15,
    'macrodetails/asian-female-young': 0.55,
    'macrodetails/caucasian-female-young': 0.35,
    'macrodetails/african-female-young': 0.10,
    'macrodetails/proportions/female-young-averagemuscle-averageweight-idealproportions': 0.85,
    'macrodetails/height/female-young-averagemuscle-averageweight-maxheight': 0.18,
    'breast/female-young-averagemuscle-averageweight-maxcup-averagefirmness': 0.22,
    'breast/female-young-averagemuscle-averageweight-averagecup-maxfirmness': 0.4,
}
# Facial/body refinements (file stem -> weight). Missing files are skipped with a warning.
DETAIL = {
    'head/head-oval': 0.45, 'head/head-scale-horiz-decr': 0.12,
    'chin/chin-width-decr': 0.25, 'chin/chin-prominent-incr': 0.12, 'chin/chin-height-decr': 0.1,
    'nose/nose-scale-horiz-decr': 0.3, 'nose/nose-point-width-decr': 0.35, 'nose/nose-flaring-decr': 0.3,
    'nose/nose-point-up': 0.15, 'nose/nose-scale-vert-decr': 0.1,
    'mouth/mouth-upperlip-volume-incr': 0.35, 'mouth/mouth-lowerlip-volume-incr': 0.45,
    'mouth/mouth-cupidsbow-incr': 0.4, 'mouth/mouth-angles-up': 0.12, 'mouth/mouth-scale-horiz-decr': 0.08,
    'cheek/l-cheek-bones-incr': 0.3, 'cheek/r-cheek-bones-incr': 0.3,
    'cheek/l-cheek-volume-decr': 0.2, 'cheek/r-cheek-volume-decr': 0.2,
    'eyes/l-eye-scale-incr': 0.15, 'eyes/r-eye-scale-incr': 0.15,
    'eyes/l-eye-corner2-up': 0.25, 'eyes/r-eye-corner2-up': 0.25,
    'eyes/l-eye-height2-incr': 0.15, 'eyes/r-eye-height2-incr': 0.15,
    'eyebrows/eyebrows-angle-up': 0.2,
    'neck/measure-neck-height-incr': 0.2, 'neck/neck-scale-horiz-decr': 0.15,
    'stomach/stomach-pregnant-decr': 0.5, 'stomach/stomach-tone-incr': 0.3,
    'torso/measure-waist-circ-decr': 0.35, 'torso/measure-shoulder-dist-decr': 0.08,
    'buttocks/buttocks-volume-incr': 0.25, 'hip/hip-scale-horiz-incr': 0.08,
}


def shaped_coords(D, recipe):
    base, uvs, faces = parse_obj(os.path.join(D, '3dobjs', 'base.obj'))
    co = base.copy()
    for name, w in recipe.items():
        p = os.path.join(D, 'targets', name + '.target.gz')
        if not os.path.exists(p):
            print('  [skip target]', name); continue
        i, d = load_target(p)
        co[i] += w * d
    return co, uvs, faces


# ---------------------------------------------------------------- objects
def clear_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def make_body(name, co_bl, uvs, faces, groups=('body',)):
    sel = [f for f in faces if f[0] in groups]
    used = sorted({v for f in sel for v in f[1]})
    remap = {v: i for i, v in enumerate(used)}
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(co_bl[v]) for v in used], [], [[remap[v] for v in f[1]] for f in sel])
    uvl = me.uv_layers.new(name='UVMap')
    k = 0
    for f in sel:
        for t in f[2]:
            uvl.data[k].uv = uvs[t] if t >= 0 else (0, 0); k += 1
    me.shade_smooth()
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    return ob, remap


def group_mean(co_bl, faces, gname):
    vs = sorted({v for f in faces if f[0] == gname for v in f[1]})
    return co_bl[vs].mean(axis=0) if vs else None


def group_verts(faces, gname):
    return sorted({v for f in faces if f[0] == gname for v in f[1]})


def build_rig(D, co_bl, faces, body, remap, rigname='game_engine'):
    spec = json.load(open(os.path.join(D, 'rigs', 'standard', f'rig.{rigname}.json')))
    weights = json.load(open(os.path.join(D, 'rigs', 'standard', f'weights.{rigname}.json')))['weights']

    def pos(p):
        if p['strategy'] == 'CUBE':
            return group_mean(co_bl, faces, p['cube_name'])
        return co_bl[p['vertex_indices']].mean(axis=0)

    arm = bpy.data.armatures.new('Rig')
    rig = bpy.data.objects.new('Rig', arm)
    bpy.context.scene.collection.objects.link(rig)
    bpy.context.view_layer.objects.active = rig
    bpy.ops.object.mode_set(mode='EDIT')
    ebs = {}
    for bname, b in spec.items():
        eb = arm.edit_bones.new(bname)
        eb.head = Vector(pos(b['head'])); eb.tail = Vector(pos(b['tail']))
        if (eb.tail - eb.head).length < 1e-4:
            eb.tail = eb.head + Vector((0, 0, 0.05))
        eb.roll = b.get('roll', 0.0)
        ebs[bname] = eb
    for bname, b in spec.items():
        if b['parent']:
            ebs[bname].parent = ebs[b['parent']]
            ebs[bname].use_connect = b.get('use_connect', False)
    bpy.ops.object.mode_set(mode='OBJECT')

    for bname, lst in weights.items():
        vg = body.vertex_groups.new(name=bname)
        for vi, w in lst:
            if vi in remap:
                vg.add([remap[vi]], w, 'REPLACE')
    body.parent = rig
    mod = body.modifiers.new('Armature', 'ARMATURE'); mod.object = rig
    return rig


def ground_offset(co_bl):
    return -co_bl[:, 2].min()
