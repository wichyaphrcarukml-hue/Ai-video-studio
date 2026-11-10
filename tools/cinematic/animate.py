"""Pole routine for Lumi (11 s, 24 fps, 9:16) rendered with Cycles.

python3 animate.py <mpfb-data-dir> <out-dir> [preview|final] [first_frame last_frame step]

Choreography (pole at the origin, she starts on its left with the pole at her right hand):
  0.0-3.2  right hand on the pole at head height, slow body wave chest -> hips      | push-in: full body -> medium
  3.2-4.6  steps around the pole, left hand comes to the pole                        | low angle, full body
  4.6-8.0  front hook spin: outside knee hooks, body lifts and leans out, ~1 turn    | low angle, slow arc
  8.0-9.0  lands, pivots to face camera, back to the pole (left hand on it)
  9.0-11   final pose: hip sway, right hand to the waist, look to camera             | medium shot push-in
Animation is solved per frame (FK spine + analytic two-bone IK + foot planting) and baked to keyframes.
The ponytail swings from a damped spring simulation driven by the head's motion (geometry nodes bend).
"""
import sys, os, math, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import bpy
from mathutils import Vector, Matrix, Quaternion
import character as CH
import stage

FPS, DUR = 24, 11.0
NF = int(FPS * DUR)
X, Y, Z = Vector((1, 0, 0)), Vector((0, 1, 0)), Vector((0, 0, 1))
FINGER_SIGN = {'l': 1.0, 'r': float(os.environ.get('RSIGN', '-1'))}


def clamp01(x):
    return max(0.0, min(1.0, x))


def ss(a, b, x):
    t = clamp01((x - a) / (b - a))
    return t * t * (3 - 2 * t)


def lerp(a, b, t):
    return a + (b - a) * t


# ------------------------------------------------------------------ timeline
def orbit_deg(t):
    """Angle around the pole (degrees, clockwise seen from above). Walk + spin in one continuous ease."""
    return 480.0 * ss(3.2, 8.3, t)


def hook_w(t):
    return ss(4.5, 5.0, t) * (1 - ss(7.6, 8.15, t))


def wave_at(t, lag):
    env = ss(0.3, 0.9, t) * (1 - ss(2.9, 3.4, t)) + 0.35 * ss(9.2, 9.8, t)
    return math.sin(2 * math.pi * (t - 0.4) / 2.2 - lag) * env


# ------------------------------------------------------------------ rig helpers
class Poser:
    def __init__(self, rig):
        self.rig = rig
        self.pb = rig.pose.bones
        for pb in self.pb:
            pb.rotation_mode = 'QUATERNION'
        self.len = {b.name: b.length for b in rig.data.bones}
        # palm normal of each hand in bone-local space (rest palms face down / slightly in)
        self.palm = {}
        for s, side in ((1, 'l'), (-1, 'r')):
            m = rig.data.bones[f'hand_{side}'].matrix_local.to_3x3()
            want = Vector((-0.25 * s, 0, -1)).normalized()
            best = max(((ax * sg), (m @ (ax * sg)).dot(want)) for ax in (X, Z) for sg in (1, -1))
            best = max([(ax * sg, (m @ (ax * sg)).dot(want)) for ax in (X, Z) for sg in (1, -1)], key=lambda p: p[1])
            self.palm[side] = best[0]

    def update(self):
        bpy.context.view_layer.update()

    def reset(self):
        for pb in self.pb:
            pb.rotation_quaternion = (1, 0, 0, 0); pb.location = (0, 0, 0); pb.scale = (1, 1, 1)

    def rot(self, bone, axis, deg):
        pb = self.pb[bone]
        h = pb.head.copy()
        R = Matrix.Translation(h) @ Matrix.Rotation(math.radians(deg), 4, axis) @ Matrix.Translation(-h)
        pb.matrix = R @ pb.matrix
        self.update()

    def to_arm(self, w):
        return self.rig.matrix_world.inverted() @ Vector(w)

    def to_world(self, a):
        return self.rig.matrix_world @ Vector(a)

    def aim(self, bone, target):
        pb = self.pb[bone]
        M = pb.matrix.copy(); h = M.translation.copy()
        yv = (M.to_3x3() @ Y).normalized()
        d = (target - h)
        if d.length < 1e-6:
            return
        q = yv.rotation_difference(d.normalized())
        pb.matrix = Matrix.Translation(h) @ q.to_matrix().to_4x4() @ Matrix.Translation(-h) @ M
        self.update()

    def twist_to(self, bone, local_axis, want):
        """Rotate a bone about its own Y so that local_axis points as close as possible to `want`."""
        pb = self.pb[bone]
        M = pb.matrix.copy(); h = M.translation.copy(); R3 = M.to_3x3()
        yv = (R3 @ Y).normalized()
        cur = (R3 @ local_axis); cur = (cur - yv * cur.dot(yv)).normalized()
        w = want - yv * want.dot(yv)
        if w.length < 1e-6:
            return
        w.normalize()
        ang = math.atan2(cur.cross(w).dot(yv), cur.dot(w))
        pb.matrix = Matrix.Translation(h) @ Matrix.Rotation(ang, 4, yv) @ Matrix.Translation(-h) @ M
        self.update()

    def two_bone(self, up, lo, target, hint):
        S = self.pb[up].head.copy()
        a, b = self.len[up], self.len[lo]
        d = target - S
        dist = min(max(d.length, 0.05), a + b - 0.003)
        d.normalize()
        cosA = (a * a + dist * dist - b * b) / (2 * a * dist)
        sinA = math.sqrt(max(0.0, 1 - cosA * cosA))
        perp = hint - d * hint.dot(d)
        perp.normalize()
        E = S + d * (a * cosA) + perp * (a * sinA)
        self.aim(up, E)
        self.aim(lo, target)

    def place(self, up, lo, mid, end):
        self.aim(up, mid); self.aim(lo, end)

    def fingers(self, side, amount, thumb=None):
        """Curl every finger joint toward the palm (axis = bone direction x palm normal, in armature space)."""
        hand = self.pb[f'hand_{side}']
        n = (hand.matrix.to_3x3() @ self.palm[side]).normalized()
        for f, base in (('index', 12), ('middle', 16), ('ring', 20), ('pinky', 24), ('thumb', 8)):
            amt = (thumb if (f == 'thumb' and thumb is not None) else amount)
            for j, k in (('01', 1.0), ('02', 1.3), ('03', 1.0)):
                pb = self.pb.get(f'{f}_{j}_{side}')
                if not pb:
                    continue
                R3 = pb.matrix.to_3x3()
                axis = (R3 @ Y).normalized().cross(n)
                if axis.length < 1e-4:
                    continue
                local = (R3.inverted() @ axis).normalized()
                pb.rotation_quaternion = Quaternion(local, math.radians(base * k * amt))
        self.update()

    def key(self, frame):
        for pb in self.pb:
            pb.keyframe_insert('rotation_quaternion', frame=frame)
            pb.keyframe_insert('location', frame=frame)
            pb.keyframe_insert('scale', frame=frame)
        self.rig.keyframe_insert('location', frame=frame)
        self.rig.keyframe_insert('rotation_euler', frame=frame)


# ------------------------------------------------------------------ choreography
class Feet:
    """Planted feet that step when the body has moved away from them."""
    def __init__(self):
        self.state = {}

    def update(self, side, t, desired, other_busy, hooked):
        st = self.state.setdefault(side, dict(planted=desired.copy(), stepping=False, t0=0.0, frm=desired.copy()))
        if hooked > 0.5:                       # airborne: re-plant under the body for the landing
            st['planted'] = desired.copy(); st['stepping'] = False
            return desired.copy(), False
        if not st['stepping'] and (desired - st['planted']).length > 0.07 and not other_busy:
            st.update(stepping=True, t0=t, frm=st['planted'].copy())
        if st['stepping']:
            u = clamp01((t - st['t0']) / 0.3)
            p = st['frm'].lerp(desired, u * u * (3 - 2 * u))
            p.z += 0.055 * math.sin(math.pi * u)
            if u >= 1:
                st['stepping'] = False; st['planted'] = desired.copy()
            return p, st['stepping']
        return st['planted'].copy(), False


def pole_point(h):
    return Vector((0, 0, h))


def solve_frame(P, feet, t, cam_pos, rest):
    rig = P.rig
    a = math.radians(orbit_deg(t))
    hook = hook_w(t)
    final = ss(8.1, 9.0, t)
    r = lerp(0.47, 0.34, hook)
    r = lerp(r, 0.40, final)
    lift = 0.17 * hook
    phi = -a
    yaw = -0.45 * hook + math.radians(120) * final
    lean = 0.20 * hook
    # body wave pushes the hips forward / back
    fwd = Vector((-math.sin(phi + yaw), -math.cos(phi + yaw), 0)) * 0  # placeholder, set below
    rig.rotation_euler = (0, 0, phi + yaw)
    base = Vector((r * math.cos(phi), r * math.sin(phi), -0.015 + lift))
    face = Matrix.Rotation(phi + yaw, 3, 'Z') @ Vector((0, -1, 0))
    rig.location = base + face * (0.035 * wave_at(t, 2.4))
    P.reset(); P.update()

    # ---- spine / pelvis FK (armature space: front = -Y, her left = +X)
    w = [wave_at(t, k) for k in (0.0, 0.8, 1.6, 2.4)]
    sway = 0.5 * ss(9.0, 9.6, t) * math.sin(2 * math.pi * (t - 9.0) / 1.6)
    P.rot('pelvis', X, -7 * w[3] - 4 * hook)
    P.rot('pelvis', Y, 6 * sway + 3 * (1 - hook) * (1 - final))
    P.rot('pelvis', Z, 6 * (1 - hook) * (1 - final))
    P.rot('spine_01', X, 6 * w[2] + 3 * hook)
    P.rot('spine_02', X, 7 * w[1] - 6 * hook)
    P.rot('spine_03', X, 9 * w[0] - 4 * hook)
    P.rot('spine_02', Y, -lean * 40 - 4 * sway)
    P.rot('spine_03', Y, -lean * 20)
    P.rot('neck_01', X, -5 * w[0] + 4 * w[1])
    # head: chin slightly down, eyes to camera late; thrown back a little in the spin
    look = P.to_arm(cam_pos) - P.pb['head'].head
    turn = math.degrees(math.atan2(look.x, -look.y))
    P.rot('head', Z, max(-35, min(35, turn)) * (0.55 * (1 - hook) + 0.9 * final) - 15 * hook)
    P.rot('head', X, 5 - 18 * hook + 3 * w[0])
    P.rot('head', Y, -6 + 10 * hook - 4 * final)

    # ---- hands
    shoulder_r = P.pb['upperarm_r'].head
    def grip_target(h, side_sign):
        axis_pt = P.to_arm(pole_point(h))
        sh = P.pb['upperarm_r' if side_sign < 0 else 'upperarm_l'].head
        toward = Vector((sh.x - axis_pt.x, sh.y - axis_pt.y, 0))
        toward = toward.normalized() if toward.length > 1e-6 else X
        tang = Z.cross(toward).normalized()
        if tang.dot(Vector((0, -1, 0))) < 0:
            tang = -tang
        return axis_pt + toward * 0.042 - tang * 0.03, axis_pt

    # right hand: on the pole (head height, higher in the spin); after the spin -> waist
    rh_pole, rh_axis = grip_target(lerp(1.62, 1.76, hook), -1)
    rh_waist = Vector((-0.17, -0.02, 1.0))
    rel_r = ss(8.3, 9.0, t)
    rh = rh_pole.lerp(rh_waist, rel_r)
    P.two_bone('upperarm_r', 'lowerarm_r', rh, Vector((-0.6, 0.35, -0.5)).normalized())
    # left hand: hip -> pole (spin) -> pole behind her at the end
    lh_hip = Vector((0.18, -0.01, 1.0))
    lh_pole, lh_axis = grip_target(lerp(1.15, 1.2, hook) + 0.35 * final, 1)
    to_pole = ss(3.6, 4.6, t)
    lh = lh_hip.lerp(lh_pole, to_pole)
    P.two_bone('upperarm_l', 'lowerarm_l', lh, Vector((0.7, 0.3, -0.5)).normalized())

    def orient_hand(side, grip_w, axis_pt, rest_dir):
        hb = f'hand_{side}'
        wrist = P.pb[hb].head
        if grip_w > 0.01:
            to_axis = Vector((axis_pt.x - wrist.x, axis_pt.y - axis_pt.y * 0 - wrist.y, 0))
            to_axis = to_axis.normalized() if to_axis.length > 1e-6 else Y
            tang = Z.cross(to_axis).normalized()
            if tang.dot(Vector((0, -1, 0))) < 0:
                tang = -tang
            fdir = (tang * 0.85 + to_axis * 0.2 + Z * 0.25).normalized()
            cur = (P.pb[hb].matrix.to_3x3() @ Y).normalized()
            P.aim(hb, wrist + cur.lerp(fdir, grip_w).normalized())
            P.twist_to(hb, P.palm[side], to_axis)
        else:
            P.aim(hb, wrist + rest_dir)

    orient_hand('r', 1 - rel_r, rh_axis, Vector((-0.2, -0.3, -1)).normalized())
    orient_hand('l', to_pole, lh_axis, Vector((-0.1, -0.5, -1)).normalized())
    P.fingers('r', lerp(3.2, 1.6, rel_r), thumb=lerp(2.5, 1.0, rel_r))
    P.fingers('l', lerp(1.0, 3.2, to_pole), thumb=lerp(1.0, 2.5, to_pole))

    # ---- legs
    face_arm = Vector((0, -1, 0))
    knee_hint = Vector((0, -1, 0.15)).normalized()
    stance = {'l': rest['ankle_l'] + Vector((0.01, -0.02, 0)), 'r': rest['ankle_r'] + Vector((-0.02, -0.05, 0))}
    rig_rot = Matrix.Rotation(phi + yaw, 4, 'Z')
    targets = {}
    busy = {s: feet.state.get(s, {}).get('stepping', False) for s in ('l', 'r')}
    for side in ('l', 'r'):
        des_w = Matrix.Translation(Vector((rig.location.x, rig.location.y, 0))) @ rig_rot @ stance[side]
        des_w.z = rest['ankle_l'].z
        other = 'r' if side == 'l' else 'l'
        p, stepping = feet.update(side, t, des_w, busy[other], hook)
        busy[side] = stepping
        targets[side] = P.to_arm(p)
    orbit = Matrix.Translation(Vector((0, 0, 0))) @ Matrix.Rotation(phi, 4, 'Z')
    # inside (right) leg extended down and back while airborne, toes pointed
    r_air = Vector((-0.1, 0.24, 0.2 + 0.0))
    r_end = targets['r'].lerp(r_air, hook)
    P.two_bone('thigh_r', 'calf_r', r_end, knee_hint)
    # outside (left) leg: knee hooks the front of the pole, shin wraps behind it
    knee_hook = P.to_arm(orbit @ Vector((0.025, -0.07, 0.93 + lift)))
    ankle_hook = P.to_arm(orbit @ Vector((-0.12, 0.09, 0.80 + lift)))
    S = P.pb['thigh_l'].head; a_, b_ = P.len['thigh_l'], P.len['calf_l']
    # knee from IK for the planted leg, blended to the hook knee
    d = targets['l'] - S; dist = min(max(d.length, 0.05), a_ + b_ - 0.003); d.normalize()
    cosA = (a_ * a_ + dist * dist - b_ * b_) / (2 * a_ * dist); sinA = math.sqrt(max(0, 1 - cosA * cosA))
    perp = (knee_hint - d * knee_hint.dot(d)).normalized()
    knee_stand = S + d * (a_ * cosA) + perp * (a_ * sinA)
    P.place('thigh_l', 'calf_l', knee_stand.lerp(knee_hook, hook), targets['l'].lerp(ankle_hook, hook))
    for side in ('l', 'r'):
        fb = f'foot_{side}'
        ank = P.pb[fb].head
        flat = ank + Vector((0.03 if side == 'l' else -0.03, -0.14, -0.06))
        shin = (ank - P.pb[f'calf_{side}'].head).normalized()
        pointed = ank + (shin * 0.8 + Vector((0, -0.3, 0))).normalized() * 0.14
        P.aim(fb, flat.lerp(pointed, hook))
    return dict(head=(rig.matrix_world @ P.pb['head'].matrix).copy())


# ------------------------------------------------------------------ ponytail dynamics
def ponytail_modifier(hair):
    ng = bpy.data.node_groups.new('PonytailSwing', 'GeometryNodeTree')
    ng.interface.new_socket('Geometry', in_out='INPUT', socket_type='NodeSocketGeometry')
    sx = ng.interface.new_socket('SwingX', in_out='INPUT', socket_type='NodeSocketFloat')
    sy = ng.interface.new_socket('SwingY', in_out='INPUT', socket_type='NodeSocketFloat')
    ng.interface.new_socket('Geometry', in_out='OUTPUT', socket_type='NodeSocketGeometry')
    N = ng.nodes; Lk = ng.links
    gi = N.new('NodeGroupInput'); go = N.new('NodeGroupOutput')
    attr = N.new('GeometryNodeInputNamedAttribute'); attr.data_type = 'FLOAT'; attr.inputs['Name'].default_value = 'tailw'
    pos = N.new('GeometryNodeInputPosition')
    A = Vector(hair['anchor'])
    mx = N.new('ShaderNodeMath'); mx.operation = 'MULTIPLY'
    Lk.new(attr.outputs[0], mx.inputs[0]); Lk.new(gi.outputs['SwingX'], mx.inputs[1])
    my = N.new('ShaderNodeMath'); my.operation = 'MULTIPLY'
    Lk.new(attr.outputs[0], my.inputs[0]); Lk.new(gi.outputs['SwingY'], my.inputs[1])
    r1 = N.new('ShaderNodeVectorRotate'); r1.rotation_type = 'X_AXIS'
    Lk.new(pos.outputs[0], r1.inputs['Vector']); r1.inputs['Center'].default_value = A
    Lk.new(mx.outputs[0], r1.inputs['Angle'])
    r2 = N.new('ShaderNodeVectorRotate'); r2.rotation_type = 'Y_AXIS'
    Lk.new(r1.outputs[0], r2.inputs['Vector']); r2.inputs['Center'].default_value = A
    Lk.new(my.outputs[0], r2.inputs['Angle'])
    sp = N.new('GeometryNodeSetPosition')
    Lk.new(gi.outputs['Geometry'], sp.inputs['Geometry']); Lk.new(r2.outputs[0], sp.inputs['Position'])
    Lk.new(sp.outputs[0], go.inputs['Geometry'])
    mod = hair.modifiers.new('Swing', 'NODES'); mod.node_group = ng
    ids = [it.identifier for it in ng.interface.items_tree if it.in_out == 'INPUT' and it.socket_type == 'NodeSocketFloat']
    return mod, ids


def simulate_ponytail(hair, mod, ids, heads, head_rest):
    """Damped spring pendulum for the tail tip, driven by the anchor's motion and gravity."""
    A = Vector(hair['anchor']); E = Vector(hair['tail_end'])
    u0 = (E - A).normalized(); Lp = (E - A).length * 0.75
    dt = 1.0 / FPS; sub = 8; h = dt / sub
    g = Vector((0, 0, -9.81)); k_stiff = 55.0; damp = 3.2
    rest_inv = head_rest.inverted()
    def frame_tf(i):
        M = heads[i] @ rest_inv   # hair object space -> world at frame i
        return M
    M0 = frame_tf(0)
    p = M0 @ (A + u0 * Lp); v = Vector((0, 0, 0))
    out = []
    for i in range(len(heads)):
        Ma = frame_tf(max(i - 1, 0)); Mb = frame_tf(i)
        for s in range(sub):
            f = (s + 1) / sub
            Aw = (Ma @ A).lerp(Mb @ A, f)
            R = Mb.to_3x3()
            rest_tip = Aw + (R @ u0).normalized() * Lp
            acc = g * 0.35 + (rest_tip - p) * k_stiff - v * damp
            v += acc * h; p += v * h
            d = p - Aw
            p = Aw + d.normalized() * Lp
            v -= d.normalized() * v.dot(d.normalized())
        Rinv = Mb.to_3x3().inverted()
        u = (Rinv @ (p - Mb @ A)).normalized()
        q = u0.rotation_difference(u)
        axis, ang = q.to_axis_angle()
        w = axis * ang
        out.append((max(-1.2, min(1.2, w.x)), max(-1.2, min(1.2, w.y))))
    sx = getattr(mod.properties.inputs, ids[0]); sy = getattr(mod.properties.inputs, ids[1])
    for i, (wx, wy) in enumerate(out):
        sx.value = wx; sy.value = wy
        sx.keyframe_insert('value', frame=i + 1); sy.keyframe_insert('value', frame=i + 1)


# ------------------------------------------------------------------ cameras
def cameras(sc, rig):
    def cam(name, lens):
        cd = bpy.data.cameras.new(name); cd.lens = lens; cd.sensor_width = 36
        cd.dof.use_dof = True; cd.dof.aperture_fstop = 2.8; cd.dof.aperture_blades = 7
        cd.dof.focus_object = rig; cd.dof.focus_subtarget = 'head'
        o = CH.link(bpy.data.objects.new(name, cd))
        tgt = CH.link(bpy.data.objects.new(name + '_aim', None))
        c = o.constraints.new('TRACK_TO'); c.target = tgt; c.track_axis = 'TRACK_NEGATIVE_Z'; c.up_axis = 'UP_Y'
        return o, tgt

    def keys(o, frames_vals, path='location'):
        for f, v in frames_vals:
            setattr(o, path, v); o.keyframe_insert(path, frame=f)

    f = lambda s: int(round(s * FPS)) + 1
    A, At = cam('CamA', 40)
    keys(A, [(f(0), (0.75, -3.7, 1.0)), (f(3.2), (0.55, -1.75, 1.38))])
    keys(At, [(f(0), (0.35, 0, 0.92)), (f(3.2), (0.42, 0, 1.3))])
    keys(A.data, [(f(0), 40), (f(3.2), 50)], 'lens')
    B, Bt = cam('CamB', 30)
    keys(B, [(f(3.2), (1.5, -2.7, 0.42)), (f(8.1), (0.35, -3.05, 0.4))])
    keys(Bt, [(f(3.2), (0.1, 0, 1.05)), (f(8.1), (0.0, 0, 1.12))])
    B.data.dof.aperture_fstop = 4.0
    Cc, Ct = cam('CamC', 50)
    keys(Cc, [(f(8.1), (0.05, -2.35, 1.4)), (f(11), (-0.12, -1.7, 1.5))])
    keys(Ct, [(f(8.1), (-0.22, -0.4, 1.28)), (f(11), (-0.23, -0.42, 1.44))])
    keys(Cc.data, [(f(8.1), 45), (f(11), 50)], 'lens')
    for o in (A, At, B, Bt, Cc, Ct):
        ad = o.animation_data if o.type != 'CAMERA' else o.animation_data
    for cobj in (A, B, Cc):
        for fc in (cobj.animation_data.action.fcurves if hasattr(cobj.animation_data.action, 'fcurves') else []):
            for kp in fc.keyframe_points:
                kp.interpolation = 'BEZIER'
    for name, o in (('A', A), ('B', B), ('C', Cc)):
        pass
    for fr, o in ((1, A), (f(3.2), B), (f(8.1), Cc)):
        m = sc.timeline_markers.new(f'cut{fr}', frame=fr); m.camera = o
    sc.camera = A
    return [A, B, Cc]


def camera_pos_at(cams, t):
    return Vector((0.4, -2.5, 1.3)) if t < 8.1 else Vector((-0.05, -2.0, 1.4))


# ------------------------------------------------------------------ main
def main():
    D, OUT = sys.argv[1], sys.argv[2]
    mode = sys.argv[3] if len(sys.argv) > 3 else 'preview'
    f0, f1, step = (int(x) for x in sys.argv[4:7]) if len(sys.argv) > 6 else (1, NF, 1)
    os.makedirs(OUT, exist_ok=True)
    t0 = time.time()
    ch = CH.build(D, hair_strands=4000 if mode == 'preview' else 30000)
    rig = ch['rig']
    hair = bpy.data.objects['Hair']
    stage.build_stage(with_pole=True, pole_x=0.0)
    sc = bpy.context.scene
    sc.render.fps = FPS; sc.frame_start = 1; sc.frame_end = NF

    # speed up the bake: no mesh evaluation while posing
    mods = [m for o in bpy.data.objects for m in o.modifiers if m.type != 'ARMATURE']
    for m in mods:
        m.show_viewport = False
    P = Poser(rig)
    rest = {'ankle_l': rig.data.bones['foot_l'].head_local.copy(), 'ankle_r': rig.data.bones['foot_r'].head_local.copy()}
    head_rest = (rig.matrix_world @ rig.data.bones['head'].matrix_local).copy()
    feet = Feet()
    cams = cameras(sc, rig)
    heads = []
    for i in range(NF):
        t = i / FPS
        out = solve_frame(P, feet, t, camera_pos_at(cams, t), rest)
        P.key(i + 1)
        heads.append(out['head'])
    print('baked', NF, 'frames in', round(time.time() - t0, 1), 's')
    mod, ids = ponytail_modifier(hair)
    simulate_ponytail(hair, mod, ids, heads, head_rest)
    for m in mods:
        m.show_viewport = True
    for o in bpy.data.objects:
        if o.animation_data and o.animation_data.action:
            pass

    if mode.startswith('debug'):
        bone = mode.split(':')[1]
        cd = bpy.data.cameras.new('dbg'); cd.lens = 60
        dbg = CH.link(bpy.data.objects.new('dbg', cd)); sc.camera = dbg
        for m in list(sc.timeline_markers):
            sc.timeline_markers.remove(m)
        stage.render_settings(sc, samples=8)
        sc.render.resolution_x, sc.render.resolution_y = 600, 600
        for fr in range(f0, f1 + 1, step):
            sc.frame_set(fr)
            tgt = rig.matrix_world @ rig.pose.bones[bone].head
            dbg.location = tgt + Vector((0.25, -0.45, 0.1))
            dbg.rotation_euler = (tgt - dbg.location).to_track_quat('-Z', 'Y').to_euler()
            sc.render.filepath = os.path.join(OUT, f'dbg_{bone}_{fr:04d}.png')
            bpy.ops.render.render(write_still=True)
        return
    if mode == 'preview':
        stage.render_settings(sc, samples=6)
        sc.render.resolution_x, sc.render.resolution_y = 360, 640
        sc.cycles.use_denoising = True
    else:
        stage.render_settings(sc, samples=22)
        sc.cycles.adaptive_threshold = 0.035
        sc.cycles.max_bounces = 6
        sc.render.resolution_x, sc.render.resolution_y = 720, 1280
    sc.render.use_persistent_data = True
    sc.render.image_settings.file_format = 'PNG'
    for fr in range(f0, f1 + 1, step):
        sc.frame_set(fr)
        sc.render.filepath = os.path.join(OUT, f'f{fr:04d}.png')
        t1 = time.time()
        bpy.ops.render.render(write_still=True)
        print(f'frame {fr} {round(time.time() - t1, 1)}s', flush=True)
    print('done')


if __name__ == '__main__':
    main()
