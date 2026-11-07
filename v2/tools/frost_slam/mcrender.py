"""Blender preview of Minecraft item models (cloud-Claude r75).

Elements with rotation (origin / axis / angle), per-face UV, light_emission, MC-like flat face shading; vanilla
generated items (layer0) are extruded per pixel. Display transforms follow ItemTransform.apply:
    v = T(translation/16) * Rxyz(rotation) * S(scale) * T(-0.5) * v_model/16
Scene coordinates are Minecraft's (x east, y up, z south); Blender gets (x, -z, y).

usage (bpy python):  mcrender.py <out.png> <scene-name>
"""
import json
import math
import os
import sys

import bpy

_imgs = {}
import mathutils
import numpy as np
from PIL import Image

SHADE = {'north': 0.8, 'south': 0.8, 'up': 1.0, 'down': 0.5, 'east': 0.6, 'west': 0.6}
ROOTS = ['/home/claude/wpn/out/assets/', '/tmp/claude-0/pk/assets/', '/tmp/claude-0/mcjar/vtex/assets/', '/home/claude/ext/client263/assets/']
VANILLA_MODELS = '/tmp/claude-0/mcjar/vm/'
TMP = '/tmp/claude-0/mcr/'
os.makedirs(TMP, exist_ok=True)


def tex_path(ref):
    ns, path = ref.split(':') if ':' in ref else ('minecraft', ref)
    for r in ROOTS:
        p = os.path.join(r, ns, 'textures', path + '.png')
        if os.path.exists(p):
            return p
    raise FileNotFoundError(ref)


def load_model(ref):
    if isinstance(ref, dict):
        return ref
    if ref.endswith('.json') and os.path.exists(ref):
        return json.load(open(ref))
    ns, path = ref.split(':') if ':' in ref else ('minecraft', ref)
    for r in ROOTS:
        p = os.path.join(r, ns, 'models', path + '.json')
        if os.path.exists(p):
            return json.load(open(p))
    p = os.path.join(VANILLA_MODELS, path.split('/')[-1] + '.json')
    return json.load(open(p))


def resolve(ref):
    """merge parents: textures, elements, display"""
    m = load_model(ref)
    out = {'textures': {}, 'display': {}, 'elements': None}
    chain = [m]
    while 'parent' in chain[-1] and not chain[-1]['parent'].endswith('builtin/generated'):
        par = chain[-1]['parent']
        if par.split('/')[-1] in ('generated',):
            break
        try:
            chain.append(load_model(par))
        except Exception:
            break
    for mm in reversed(chain):
        out['textures'].update(mm.get('textures', {}))
        out['display'].update(mm.get('display', {}))
        if mm.get('elements') is not None:
            out['elements'] = mm['elements']
    return out


def reset(w, h, bg=(0.11, 0.14, 0.2), samples=8):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    _imgs.clear()
    sc = bpy.context.scene
    sc.render.engine = 'CYCLES'
    sc.cycles.samples = samples
    sc.cycles.use_denoising = False
    sc.render.resolution_x, sc.render.resolution_y = w, h
    sc.view_settings.view_transform = 'Standard'
    world = bpy.data.worlds.new('w')
    sc.world = world
    world.use_nodes = True
    world.node_tree.nodes['Background'].inputs[0].default_value = (*bg, 1)




def image(path):
    if path not in _imgs:
        _imgs[path] = bpy.data.images.load(path, check_existing=False)
    return _imgs[path]


def material(path, face, light):
    key = f'{path}|{face}|{light}'
    if key in bpy.data.materials:
        return bpy.data.materials[key]
    m = bpy.data.materials.new(key)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    em = nt.nodes.new('ShaderNodeEmission')
    ti = nt.nodes.new('ShaderNodeTexImage')
    ti.image = image(path)
    ti.interpolation = 'Closest'
    tr = nt.nodes.new('ShaderNodeBsdfTransparent')
    mix = nt.nodes.new('ShaderNodeMixShader')
    em.inputs['Strength'].default_value = 1.0 if light else SHADE[face]
    nt.links.new(ti.outputs['Color'], em.inputs['Color'])
    nt.links.new(ti.outputs['Alpha'], mix.inputs['Fac'])
    nt.links.new(tr.outputs[0], mix.inputs[1])
    nt.links.new(em.outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], out.inputs['Surface'])
    return m


def rot_matrix(axis, deg):
    a = math.radians(deg)
    c, s = math.cos(a), math.sin(a)
    if axis == 'x':
        return np.array([[1, 0, 0], [0, c, -s], [0, s, c]])
    if axis == 'y':
        return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]])
    return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])


def display_matrix(t):
    """4x4 in block units acting on model coords /16 (centre already at 0.5)."""
    tr = np.array(t.get('translation', [0, 0, 0]), float) / 16.0
    rx, ry, rz = [math.radians(v) for v in t.get('rotation', [0, 0, 0])]
    sc = np.array(t.get('scale', [1, 1, 1]), float)
    R = rot_matrix('x', math.degrees(rx)) @ rot_matrix('y', math.degrees(ry)) @ rot_matrix('z', math.degrees(rz))
    M = np.eye(4)
    M[:3, :3] = R @ np.diag(sc)
    M[:3, 3] = tr
    T = np.eye(4)
    T[:3, 3] = -0.5
    return M @ T


CORNERS = {
    'north': lambda a, b: [(b[0], a[1], a[2]), (a[0], a[1], a[2]), (a[0], b[1], a[2]), (b[0], b[1], a[2])],
    'south': lambda a, b: [(a[0], a[1], b[2]), (b[0], a[1], b[2]), (b[0], b[1], b[2]), (a[0], b[1], b[2])],
    'east': lambda a, b: [(b[0], a[1], b[2]), (b[0], a[1], a[2]), (b[0], b[1], a[2]), (b[0], b[1], b[2])],
    'west': lambda a, b: [(a[0], a[1], a[2]), (a[0], a[1], b[2]), (a[0], b[1], b[2]), (a[0], b[1], a[2])],
    'up': lambda a, b: [(a[0], b[1], b[2]), (b[0], b[1], b[2]), (b[0], b[1], a[2]), (a[0], b[1], a[2])],
    'down': lambda a, b: [(a[0], a[1], a[2]), (b[0], a[1], a[2]), (b[0], a[1], b[2]), (a[0], a[1], b[2])],
}


def generated_elements(texref):
    """vanilla item/generated: one 1 px cube per opaque pixel (front/back + edges), texture = the pixel's own UV"""
    im = np.array(Image.open(tex_path(texref)).convert('RGBA'))
    h, w = im.shape[:2]
    els = []
    for y in range(h):
        for x in range(w):
            if im[y, x, 3] < 10:
                continue
            u0, v0 = x * 16.0 / w, y * 16.0 / h
            uv = [u0 + 0.05, v0 + 0.05, u0 + 16.0 / w - 0.05, v0 + 16.0 / h - 0.05]
            fr = [x * 16.0 / w, 16 - (y + 1) * 16.0 / h, 7.5]
            to = [(x + 1) * 16.0 / w, 16 - y * 16.0 / h, 8.5]
            els.append({'from': fr, 'to': to, 'faces': {f: {'uv': uv, 'texture': '#layer0'} for f in CORNERS}})
    return els


def build(ref, M_world, name='m'):
    """ref: model ref or dict; M_world: 4x4 placing the item (incl. display transform)"""
    m = resolve(ref)
    texs = m['textures']
    els = m['elements'] if m['elements'] is not None else generated_elements(texs['layer0'])

    def tex_of(t):
        while t.startswith('#'):
            t = texs[t[1:]]
        return tex_path(t)

    verts, faces, uvs, mats = [], [], [], []
    mat_index = {}
    for e in els:
        a = np.array(e['from'], float)
        b = np.array(e['to'], float)
        R, o = None, None
        if 'rotation' in e:
            R = rot_matrix(e['rotation']['axis'], e['rotation']['angle'])
            o = np.array(e['rotation']['origin'], float)
        light = e.get('light_emission', 0) > 0
        for fname, f in e['faces'].items():
            u0, v0, u1, v1 = [c / 16.0 for c in f['uv']]
            base = len(verts)
            for c in CORNERS[fname](a, b):
                p = np.array(c, float)
                if R is not None:
                    p = R @ (p - o) + o
                q = M_world @ np.append(p / 16.0, 1.0)
                verts.append((q[0], -q[2], q[1]))
            faces.append((base, base + 1, base + 2, base + 3))
            uvs.append([(u0, 1 - v1), (u1, 1 - v1), (u1, 1 - v0), (u0, 1 - v0)])
            key = (tex_of(f['texture']), fname, light)
            if key not in mat_index:
                mat_index[key] = len(mat_index)
            mats.append(mat_index[key])
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    uvl = me.uv_layers.new()
    for i, poly in enumerate(me.polygons):
        for k, li in enumerate(poly.loop_indices):
            uvl.data[li].uv = uvs[i][k]
        poly.material_index = mats[i]
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    for key, idx in sorted(mat_index.items(), key=lambda kv: kv[1]):
        ob.data.materials.append(material(*key))
    return ob


def place(x=0.0, y=0.0, z=0.0, yaw=0.0, scale=1.0):
    M = np.eye(4)
    M[:3, :3] = rot_matrix('y', yaw) * scale
    M[:3, 3] = [x, y, z]
    return M


def camera(eye, target, fov=None, ortho=None):
    cam = bpy.data.cameras.new('c')
    if ortho:
        cam.type = 'ORTHO'
        cam.ortho_scale = ortho
    else:
        cam.sensor_fit = 'VERTICAL'          # Minecraft's FOV is the vertical one (hand: fixed 70)
        cam.angle_y = math.radians(fov or 40)
    ob = bpy.data.objects.new('c', cam)
    bpy.context.scene.collection.objects.link(ob)
    e = np.array((eye[0], -eye[2], eye[1]))
    t = np.array((target[0], -target[2], target[1]))
    ob.location = e
    ob.rotation_euler = mathutils.Vector(t - e).to_track_quat('-Z', 'Y').to_euler()
    bpy.context.scene.camera = ob


def render(out):
    bpy.context.scene.render.filepath = out
    bpy.ops.render.render(write_still=True)


# ---------------------------------------------------------------- scenes
NEW = '/home/claude/wpn/out/assets/starkffa/models/item/frost_slam.json'
OLD = {'parent': 'minecraft:item/handheld_mace', 'textures': {'layer0': 'starkffa:item/frost_slam'}}


def scene_compare(out):
    """vanilla-style flat mace vs the new 3D mace under the same display transforms (hand frame = identity)"""
    reset(1500, 900)
    ctxs = ['thirdperson_righthand', 'firstperson_righthand', 'gui']
    for i, ctx in enumerate(ctxs):
        for j, ref in enumerate((OLD, NEW)):
            d = resolve(ref)['display'].get(ctx, {})
            M = place(x=(i - 1) * 1.6, y=(0.75 - j * 1.5)) @ display_matrix(d)
            build(ref, M, f'{ctx}_{j}')
    camera((0, 0, 8), (0, 0, 0), ortho=4.8)
    render(out)


def scene_turn(out):
    """the new model alone from 4 sides (model space, no display transform)"""
    reset(1600, 520)
    for i, yaw in enumerate((0, 45, 90, 200)):
        M = place(x=(i - 1.5) * 1.25, y=-0.15, yaw=yaw, scale=1.0) @ display_matrix({})
        build(NEW, M, f'turn{i}')
    camera((0, 0.1, 9), (0, 0.1, 0), ortho=5.2)
    render(out)


def scene_crystal(out):
    reset(1200, 520, bg=(0.16, 0.2, 0.26))
    C = '/home/claude/wpn/out/assets/starkffa/models/item/fx_crystal.json'
    for i, (yaw, sc) in enumerate(((0, 1.0), (30, 1.4), (60, 0.8), (15, 1.9))):
        M = place(x=(i - 1.5) * 1.1, y=-0.9, yaw=yaw, scale=sc) @ np.array(
            [[1, 0, 0, 0], [0, 1, 0, 0.5], [0, 0, 1, 0], [0, 0, 0, 1]]) @ display_matrix({})
        build(C, M, f'c{i}')
    camera((0, 0.6, 7), (0, 0.2, 0), ortho=4.6)
    render(out)


if __name__ == '__main__':
    out, scene = sys.argv[1], sys.argv[2]
    {'compare': scene_compare, 'turn': scene_turn, 'crystal': scene_crystal}[scene](out)
