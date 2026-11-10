# Cinematic 3D character pipeline (Blender / Cycles, CPU)

Replaces the three.js mannequin previz. The character is an original fictional adult woman ("Lumi") built on the
MakeHuman / MPFB2 CC0 base mesh: realistic body proportions, a game-engine skeleton with MakeHuman skin weights,
SSS skin, refractive eyes, strand hair (sleek high ponytail), brows, lashes, and luxury dancewear
(gold sequin bralette, black satin shorts, gold chain straps, gold hoops, gold ponytail cuff).

Only MPFB2 *data* files are read (base mesh, morph targets, rig joints, skin weights, UV masks); no MPFB code runs.

## Setup
    pip install --user bpy                                    # Blender 5.x as a Python module (includes Cycles)
    git clone --depth 1 https://github.com/makehumancommunity/mpfb2.git <somewhere>
    DATA=<somewhere>/mpfb2/src/mpfb/data

## Character reference renders
    python3 ref_render.py $DATA out/ref            # hero (1080x1920), face (1080x1350), back 3/4
    python3 ref_render.py $DATA out/ref preview    # half-res, fast check

Files: `charlib.py` (data loading, shaping, rig), `character.py` (look: skin, eyes, hair, outfit, jewellery, posing),
`stage.py` (club set, lights, camera, render settings).

## Pole routine video (11 s, 24 fps, 9:16)
    python3 animate.py $DATA out/frames final            # 720x1280 Cycles frames (~30 s/frame on 4 CPU cores)
    python3 animate.py $DATA out/prev preview 1 264 12   # quick low-res check of every 12th frame
    ffmpeg -framerate 24 -i out/frames/f%04d.png -vf "scale=1080:1920:flags=lanczos,noise=alls=3:allf=t" \
           -c:v libx264 -crf 17 -pix_fmt yuv420p out/lumi-pole.mp4

`animate.py` solves every frame (spine FK, analytic two-bone IK for arms/legs, planted feet that step,
palm-facing grip with curled fingers) and bakes it to keyframes. The ponytail swings from a damped spring
simulation driven by the head motion (geometry-nodes bend). Cameras: push-in full body -> medium (0-3.2 s),
low-angle full body arc (3.2-8.1 s), medium push-in (8.1-11 s).
