"""Character reference renders (Cycles): full-body hero + face/medium close-up in the club set.

python3 ref_render.py <mpfb-data-dir> <out-dir> [preview]
"""
import sys, os, math, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy
from mathutils import Vector
import character as CH
import stage

D, OUT = sys.argv[1], sys.argv[2]
preview = len(sys.argv) > 3 and sys.argv[3] == 'preview'
os.makedirs(OUT, exist_ok=True)
t = time.time()
ch = CH.build(D, hair_strands=10000 if preview else 30000)
CH.pose_relaxed(ch['rig'])
print('character built', round(time.time() - t, 1), 's')
stage.build_stage(with_pole=True, pole_x=-0.62)
sc = bpy.context.scene
stage.render_settings(sc, samples=24 if preview else 160)

shots = [
    ('hero', (1080, 1920), 50, Vector((0.55, -3.05, 1.0)), Vector((0.0, 0.0, 0.86)), 2.8, Vector((0, -0.1, 1.55))),
    ('back', (1080, 1350), 50, Vector((-1.25, 1.9, 1.5)), Vector((0.0, 0.0, 1.3)), 2.8, Vector((0, 0.1, 1.45))),
    ('face', (1080, 1350), 85, Vector((0.22, -1.25, 1.52)), Vector((0.0, 0.0, 1.46)), 2.0, Vector((0.02, -0.12, 1.59))),
]
for name, (w, h), lens, pos, aim, fstop, focus in shots:
    if preview:
        w, h = w // 2, h // 2
    cam = stage.camera(name, pos, aim, lens, fstop, focus)
    sc.camera = cam
    sc.render.resolution_x, sc.render.resolution_y = w, h
    sc.render.filepath = os.path.join(OUT, f'{name}.png')
    t = time.time()
    bpy.ops.render.render(write_still=True)
    print('rendered', name, round(time.time() - t, 1), 's')
