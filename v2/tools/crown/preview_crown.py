"""Blender (bpy) preview of a Minecraft JSON item model the way MC bakes it: element boxes, one-axis element rotation
(right-handed), the vanilla face UV directions, nearest-filtered textures (frame 0 of animated ones, or a chosen frame),
MC's directional face shade (up 1.0, N/S 0.8, E/W 0.6, down 0.5) as emission - no scene lighting.
Usage: python preview_crown.py out.png [frame]   (bpy from /home/claude/bpyenv)."""
import json
import math
import os
import sys

import bpy
from PIL import Image

PACK = '/home/claude/starkffa-pack/v2/src/assets'
MODEL = os.environ.get('CROWN_MODEL', os.path.join(PACK, 'starkffa/models/item/crown.json'))
STEVE = '/tmp/claude-0/mcjar/vtex/assets/minecraft/textures/entity/player/wide/steve.png'
OUT = sys.argv[1] if len(sys.argv) > 1 else '/tmp/crown_preview.png'
FRAME = int(sys.argv[2]) if len(sys.argv) > 2 else 0
TMP = os.path.dirname(OUT)
SHADE = {'up': 1.0, 'down': 0.5, 'north': 0.8, 'south': 0.8, 'east': 0.6, 'west': 0.6}


def mc2b(p):
    return (p[0], -p[2], p[1])


def tex_path(ref):
    ns, path = ref.split(':') if ':' in ref else ('minecraft', ref)
    return os.path.join(PACK, ns, 'textures', path + '.png')


def frame_image(path):
    im = Image.open(path).convert('RGBA')
    meta = path + '.mcmeta'
    if os.path.exists(meta):
        a = json.load(open(meta))['animation']
        fw = a.get('width', im.width)
        fh = a.get('height', fw)
        n = im.height // fh
        f = FRAME % n
        im = im.crop((0, f * fh, fw, (f + 1) * fh))
    out = os.path.join(TMP, 'pv_' + os.path.basename(path))
    im.save(out)
    return out


def material(name, img_path, shade):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    tex = nt.nodes.new('ShaderNodeTexImage')
    tex.image = bpy.data.images.load(img_path)
    tex.interpolation = 'Closest'
    em = nt.nodes.new('ShaderNodeEmission')
    em.inputs['Strength'].default_value = shade
    mix = nt.nodes.new('ShaderNodeMixShader')
    tr = nt.nodes.new('ShaderNodeBsdfTransparent')
    nt.links.new(tex.outputs['Color'], em.inputs['Color'])
    nt.links.new(tex.outputs['Alpha'], mix.inputs['Fac'])
    nt.links.new(tr.outputs['BSDF'], mix.inputs[1])
    nt.links.new(em.outputs['Emission'], mix.inputs[2])
    nt.links.new(mix.outputs['Shader'], out.inputs['Surface'])
    return m


def face_quad(d, f, t):
    x0, y0, z0 = f
    x1, y1, z1 = t
    # corners in order: (top-left, top-right, bottom-right, bottom-left) as seen from outside, with (u, v) fractions
    if d == 'north':
        return [((x1, y1, z0), (0, 0)), ((x0, y1, z0), (1, 0)), ((x0, y0, z0), (1, 1)), ((x1, y0, z0), (0, 1))]
    if d == 'south':
        return [((x0, y1, z1), (0, 0)), ((x1, y1, z1), (1, 0)), ((x1, y0, z1), (1, 1)), ((x0, y0, z1), (0, 1))]
    if d == 'west':
        return [((x0, y1, z0), (0, 0)), ((x0, y1, z1), (1, 0)), ((x0, y0, z1), (1, 1)), ((x0, y0, z0), (0, 1))]
    if d == 'east':
        return [((x1, y1, z1), (0, 0)), ((x1, y1, z0), (1, 0)), ((x1, y0, z0), (1, 1)), ((x1, y0, z1), (0, 1))]
    if d == 'up':
        return [((x0, y1, z0), (0, 0)), ((x1, y1, z0), (1, 0)), ((x1, y1, z1), (1, 1)), ((x0, y1, z1), (0, 1))]
    if d == 'down':
        return [((x0, y0, z1), (0, 0)), ((x1, y0, z1), (1, 0)), ((x1, y0, z0), (1, 1)), ((x0, y0, z0), (0, 1))]


def rot(p, r):
    if not r:
        return p
    a = math.radians(r['angle'])
    o = r['origin']
    x, y, z = p[0] - o[0], p[1] - o[1], p[2] - o[2]
    c, s = math.cos(a), math.sin(a)
    if r['axis'] == 'y':
        x, z = x * c + z * s, -x * s + z * c
    elif r['axis'] == 'x':
        y, z = y * c - z * s, y * s + z * c
    else:
        x, y = x * c - y * s, x * s + y * c
    return (x + o[0], y + o[1], z + o[2])


def build_model(model, scale, offset, spin_deg=0.0):
    texs = {k: v for k, v in model['textures'].items()}
    mats = {}
    verts, faces, uvs, fmat = [], [], [], []
    for e in model['elements']:
        for d, fc in e['faces'].items():
            ref = fc['texture'].lstrip('#')
            path = texs[ref]
            while path.startswith('#'):
                path = texs[path[1:]]
            key = (path, d)
            if key not in mats:
                mats[key] = len(mats)
            u0, v0, u1, v1 = fc['uv']
            idx = []
            for (p, (fu, fv)) in face_quad(d, e['from'], e['to']):
                p = rot(p, e.get('rotation'))
                x, y, z = (p[0] / 16 - 0.5), (p[1] / 16 - 0.5), (p[2] / 16 - 0.5)
                a = math.radians(spin_deg)
                x, z = x * math.cos(a) + z * math.sin(a), -x * math.sin(a) + z * math.cos(a)
                q = (x * scale + offset[0], y * scale + offset[1], z * scale + offset[2])
                idx.append(len(verts))
                verts.append(mc2b(q))
                uvs.append(((u0 + (u1 - u0) * fu) / 16, 1 - (v0 + (v1 - v0) * fv) / 16))
            faces.append(idx)
            fmat.append(mats[key])
    me = bpy.data.meshes.new('crown')
    me.from_pydata(verts, [], faces)
    uvl = me.uv_layers.new()
    for poly in me.polygons:
        for li in poly.loop_indices:
            uvl.data[li].uv = uvs[me.loops[li].vertex_index]
    ob = bpy.data.objects.new('crown', me)
    bpy.context.scene.collection.objects.link(ob)
    order = sorted(mats.items(), key=lambda kv: kv[1])
    for (path, d), i in order:
        ob.data.materials.append(material('m%d' % i, frame_image(tex_path(path)), SHADE[d]))
    for poly, m in zip(me.polygons, fmat):
        poly.material_index = m
    return ob


def steve_head(center, size):
    """Steve's head cube (skin 64x64: head top 8..16 x 0..8, front 8..16 x 8..16 ...)."""
    im = Image.open(STEVE).convert('RGBA')
    path = os.path.join(TMP, 'pv_steve.png')
    im.save(path)
    W, H = im.size
    h = size / 2
    cx, cy, cz = center
    # (face, corners MC, skin rect px)
    rects = {'up': (8, 0, 16, 8), 'down': (16, 0, 24, 8), 'east': (0, 8, 8, 16), 'north': (8, 8, 16, 16),
             'west': (16, 8, 24, 16), 'south': (24, 8, 32, 16)}
    f, t = (cx - h, cy - h, cz - h), (cx + h, cy + h, cz + h)
    verts, faces, uvs, fm = [], [], [], []
    for d, (a, b, c, e) in rects.items():
        idx = []
        for p, (fu, fv) in face_quad(d, f, t):
            idx.append(len(verts))
            verts.append(mc2b(p))
            uvs.append(((a + (c - a) * fu) / W, 1 - (b + (e - b) * fv) / H))
        faces.append(idx)
        fm.append(d)
    me = bpy.data.meshes.new('head')
    me.from_pydata(verts, [], faces)
    uvl = me.uv_layers.new()
    for poly in me.polygons:
        for li in poly.loop_indices:
            uvl.data[li].uv = uvs[me.loops[li].vertex_index]
    ob = bpy.data.objects.new('head', me)
    bpy.context.scene.collection.objects.link(ob)
    for i, d in enumerate(fm):
        ob.data.materials.append(material('h%d' % i, path, SHADE[d]))
        me.polygons[i].material_index = i
    return ob


def bar(name, y0, y1, width, color):
    bpy.ops.mesh.primitive_plane_add(size=1)
    ob = bpy.context.active_object
    ob.name = name
    ob.scale = (width, y1 - y0, 1)
    ob.rotation_euler = (math.radians(90), 0, 0)
    ob.location = mc2b((0, (y0 + y1) / 2, -0.4))
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    em = nt.nodes.new('ShaderNodeEmission')
    em.inputs['Color'].default_value = color
    nt.links.new(em.outputs['Emission'], nt.nodes['Material Output'].inputs['Surface'])
    ob.data.materials.append(m)


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    s = bpy.context.scene
    s.render.engine = 'CYCLES'
    s.cycles.device = 'CPU'
    s.cycles.samples = 16
    s.render.resolution_x, s.render.resolution_y = 1200, 800
    s.view_settings.view_transform = 'Standard'
    s.render.film_transparent = False
    wd = bpy.data.worlds.new('w')
    wd.use_nodes = True
    wd.node_tree.nodes['Background'].inputs['Color'].default_value = (0.35, 0.55, 0.85, 1)
    s.world = wd
    model = json.load(open(MODEL))
    scale = float(os.environ.get('CROWN_SCALE', '0.72'))
    ty = float(os.environ.get('CROWN_Y', '2.64'))
    spin = float(os.environ.get('CROWN_SPIN', '0'))
    head_c = (0, 1.406 + 0.25, 0)
    if os.environ.get('CROWN_HEADFIT'):
        # HEAD context: the item model at 0.625 around the head centre (head 0.5 = 8 px, no player scale here)
        build_model(model, 0.625, head_c, spin)
        steve_head(head_c, 0.5)
    else:
        # crown: model bottom (y 4) sits at ty
        y_bottom_item = 4 / 16 - 0.5
        build_model(model, scale, (0, ty - y_bottom_item * scale, 0), spin)
        steve_head((0, 1.406 + 0.234, 0), 0.469)
    if not os.environ.get('CROWN_NOBARS'):
        bar('health', 2.075, 2.30, 0.34, (0.9, 0.2, 0.25, 1))
        bar('name', 2.334, 2.559, 0.62, (0.95, 0.95, 0.95, 1))
    cam = bpy.data.cameras.new('cam')
    cam.lens = float(os.environ.get('CROWN_LENS', '50'))
    co = bpy.data.objects.new('cam', cam)
    s.collection.objects.link(co)
    s.camera = co
    view = os.environ.get('CROWN_VIEW', 'front')
    target = (0, 2.2, 0)
    if view == 'front':
        pos = (1.2, 2.7, -3.2)
    elif view == 'high':
        pos = (0.8, 4.2, -2.6)
    elif view == 'close':
        pos = (0.5, 2.95, -1.6)
        target = (0, 2.78, 0)
    elif view == 'head':
        pos = (1.1, 2.15, -1.9)
        target = (0, 1.8, 0)
    elif view == 'head2':
        pos = (-1.6, 1.75, -1.2)
        target = (0, 1.85, 0)
    elif view == 'head3':
        pos = (0.4, 2.9, -1.3)
        target = (0, 1.85, 0)
    elif view == 'low':
        pos = (0.9, 1.62, -4.0)
        target = (0, 2.75, 0)
        cam.lens = 70
    else:
        pos = (3.2, 2.4, -0.5)
    co.location = mc2b(pos)
    import mathutils
    d = mathutils.Vector(mc2b(target)) - mathutils.Vector(mc2b(pos))
    co.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
    s.render.filepath = OUT
    bpy.ops.render.render(write_still=True)


main()
