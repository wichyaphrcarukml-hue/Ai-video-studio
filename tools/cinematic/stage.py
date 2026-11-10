"""Luxury club set: glossy black marble floor, chrome pole, warm bokeh, soft spotlight + gold rim lights."""
import math
import numpy as np
import bpy, bmesh
from mathutils import Vector
from character import new_material, principled, node, math_node, mix_rgb, link


def floor_material():
    m, nt, out = new_material('Marble')
    oc = node(nt, 'ShaderNodeTexCoord').outputs['Object']
    warp = node(nt, 'ShaderNodeTexNoise'); warp.inputs['Scale'].default_value = 1.2; warp.inputs['Detail'].default_value = 6
    nt.links.new(oc, warp.inputs['Vector'])
    wave = node(nt, 'ShaderNodeTexWave'); wave.inputs['Scale'].default_value = 0.8; wave.inputs['Distortion'].default_value = 14
    wave.inputs['Detail'].default_value = 8
    nt.links.new(warp.outputs['Color'], wave.inputs['Vector'])
    ramp = node(nt, 'ShaderNodeValToRGB'); nt.links.new(wave.outputs['Fac'], ramp.inputs['Fac'])
    e = ramp.color_ramp.elements
    e[0].position, e[0].color = 0.0, (0.004, 0.004, 0.004, 1)
    e[1].position, e[1].color = 0.985, (0.006, 0.0055, 0.005, 1)
    ramp.color_ramp.elements.new(1.0).color = (0.035, 0.028, 0.02, 1)
    p = principled(nt, **{'Roughness': 0.12, 'Coat Weight': 0.6, 'Coat Roughness': 0.05})
    nt.links.new(ramp.outputs['Color'], p.inputs['Base Color'])
    nt.links.new(p.outputs[0], out.inputs['Surface'])
    return m


def emissive(name, color, strength):
    m, nt, out = new_material(name)
    e = node(nt, 'ShaderNodeEmission'); e.inputs['Color'].default_value = (*color, 1); e.inputs['Strength'].default_value = strength
    nt.links.new(e.outputs[0], out.inputs['Surface'])
    return m


def build_stage(with_pole=True, pole_x=0.0, pole_y=0.0):
    sc = bpy.context.scene
    # floor
    me = bpy.data.meshes.new('Floor'); bm = bmesh.new(); bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=12)
    bm.to_mesh(me); bm.free(); me.materials.append(floor_material())
    link(bpy.data.objects.new('Floor', me))
    # dark back wall with faint vertical gold light strips (out of focus)
    me = bpy.data.meshes.new('Wall'); bm = bmesh.new(); bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=10)
    bm.to_mesh(me); bm.free()
    wall = link(bpy.data.objects.new('Wall', me)); wall.rotation_euler = (math.radians(90), 0, 0); wall.location = (0, 6, 3)
    m, nt, out = new_material('WallMat'); p = principled(nt, **{'Base Color': (0.006, 0.005, 0.005), 'Roughness': 0.4})
    nt.links.new(p.outputs[0], out.inputs['Surface']); me.materials.append(m)
    strip = emissive('Strip', (1.0, 0.55, 0.22), 6.0)
    for x in (-2.6, -1.3, 1.5, 2.8):
        me = bpy.data.meshes.new('Strip'); bm = bmesh.new()
        bmesh.ops.create_cube(bm, size=1.0); bm.to_mesh(me); bm.free(); me.materials.append(strip)
        o = link(bpy.data.objects.new('Strip', me)); o.scale = (0.03, 0.03, 2.6); o.location = (x, 5.8, 1.6)
    # bokeh bulbs
    bulb = emissive('Bulb', (1.0, 0.62, 0.3), 25.0)
    rng = np.random.default_rng(3)
    for i in range(26):
        me = bpy.data.meshes.new('Bulb'); bm = bmesh.new(); bmesh.ops.create_icosphere(bm, subdivisions=2, radius=0.03)
        bm.to_mesh(me); bm.free(); me.materials.append(bulb)
        o = link(bpy.data.objects.new('Bulb', me))
        o.location = (rng.uniform(-3.5, 3.5), rng.uniform(3.5, 5.5), rng.uniform(1.6, 3.6))
    # chrome pole
    if with_pole:
        m, nt, out = new_material('Chrome')
        p = principled(nt, **{'Base Color': (0.95, 0.95, 0.95), 'Metallic': 1.0, 'Roughness': 0.04})
        nt.links.new(p.outputs[0], out.inputs['Surface'])
        me = bpy.data.meshes.new('Pole'); bm = bmesh.new()
        bmesh.ops.create_cone(bm, cap_ends=True, segments=64, radius1=0.0225, radius2=0.0225, depth=4.0)
        bm.to_mesh(me); bm.free(); me.materials.append(m)
        for poly in me.polygons:
            poly.use_smooth = True
        pole = link(bpy.data.objects.new('Pole', me)); pole.location = (pole_x, pole_y, 2.0)
        me = bpy.data.meshes.new('Base'); bm = bmesh.new()
        bmesh.ops.create_cone(bm, cap_ends=True, segments=64, radius1=0.09, radius2=0.08, depth=0.015)
        bm.to_mesh(me); bm.free(); me.materials.append(m)
        b = link(bpy.data.objects.new('PoleBase', me)); b.location = (pole_x, pole_y, 0.0075)

    def area(name, loc, aim, power, color, size, shape='DISK', glossy=True):
        l = bpy.data.lights.new(name, 'AREA'); l.energy = power; l.color = color; l.shape = shape; l.size = size
        o = link(bpy.data.objects.new(name, l)); o.location = loc; o.visible_camera = False; o.visible_glossy = glossy
        o.rotation_euler = (Vector(aim) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
        return o

    def spot(name, loc, aim, power, color, angle, radius):
        l = bpy.data.lights.new(name, 'SPOT'); l.energy = power; l.color = color
        l.spot_size = math.radians(angle); l.spot_blend = 0.6; l.shadow_soft_size = radius
        o = link(bpy.data.objects.new(name, l)); o.location = loc
        o.rotation_euler = (Vector(aim) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
        return o

    area('Key', (-1.6, -2.4, 2.7), (0, 0, 1.25), 220, (1.0, 0.86, 0.74), 1.0, glossy=False)
    area('Fill', (2.2, -2.6, 1.3), (0, 0, 1.1), 30, (0.75, 0.82, 1.0), 2.0, glossy=False)
    area('RimL', (-1.5, 1.6, 2.3), (0, 0, 1.2), 600, (1.0, 0.62, 0.28), 0.6)
    area('RimR', (1.6, 1.5, 2.0), (0, 0, 1.1), 560, (1.0, 0.58, 0.25), 0.6)
    spot('Top', (0.1, -0.4, 3.9), (0, 0, 0.9), 900, (1.0, 0.88, 0.75), 38, 0.25)
    w = bpy.data.worlds.new('World'); sc.world = w; w.use_nodes = True
    w.node_tree.nodes['Background'].inputs['Color'].default_value = (0.0015, 0.0012, 0.001, 1)


def camera(name, pos, aim, lens, fstop, focus_point):
    cd = bpy.data.cameras.new(name); cd.lens = lens; cd.sensor_width = 36
    cd.dof.use_dof = True; cd.dof.aperture_fstop = fstop; cd.dof.aperture_blades = 7
    cam = link(bpy.data.objects.new(name, cd)); cam.location = pos
    cam.rotation_euler = (aim - pos).to_track_quat('-Z', 'Y').to_euler()
    cd.dof.focus_distance = (focus_point - pos).length
    return cam


def render_settings(sc, samples=128):
    sc.render.engine = 'CYCLES'
    sc.cycles.device = 'CPU'
    sc.cycles.samples = samples
    sc.cycles.use_adaptive_sampling = True
    sc.cycles.adaptive_threshold = 0.02
    sc.cycles.use_denoising = True
    sc.cycles.max_bounces = 8; sc.cycles.transparent_max_bounces = 16
    sc.cycles.caustics_reflective = False; sc.cycles.caustics_refractive = False
    sc.cycles.sample_clamp_indirect = 8
    sc.view_settings.view_transform = 'AgX'
    sc.view_settings.look = 'AgX - Medium High Contrast'
    sc.view_settings.exposure = -0.25
    sc.render.image_settings.file_format = 'PNG'
    sc.render.film_transparent = False
