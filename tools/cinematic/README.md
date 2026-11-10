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
