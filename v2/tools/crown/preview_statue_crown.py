"""Blender (bpy) preview of the statue crown on a Steve head, in skin pixels (1 unit = 1 skin px, origin = head top
centre, head y -8..0). Minecraft look: element boxes, vanilla face uv directions, nearest-filtered texture frame,
directional face shade (up 1.0, N/S 0.8, E/W 0.6, down 0.5) as emission.
Usage: python preview_statue_crown.py <model.json> <texture.png> <out.png> [frame] [views]   (bpy from /home/claude/bpyenv)
views: comma list of front,low,side,high,close,back (default front,low,side,high)."""
import json
import math
import os
import sys

import bpy
import mathutils
from PIL import Image

MODEL, TEX, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
FRAME = int(sys.argv[4]) if len(sys.argv) > 4 else 0
VIEWS = (sys.argv[5] if len(sys.argv) > 5 else 'front,low,side,high').split(',')
STEVE = os.environ.get('SKIN', '/tmp/claude-0/mcjar/vtex/assets/minecraft/textures/entity/player/wide/steve.png')
TMP = os.path.dirname(os.path.abspath(OUT))
SHADE = {'up': 1.0, 'down': 0.5, 'north': 0.8, 'south': 0.8, 'east': 0.6, 'west': 0.6}


def mc2b(p):
    return (p[0], -p[2], p[1])


def frame_image(path, frame):
    im = Image.open(path).convert('RGBA')
    meta = path + '.mcmeta'
    if os.path.exists(meta):
        a = json.load(open(meta))['animation']
        fw = a.get('width', im.width)
        fh = a.get('height', fw)
        n = im.height // fh
        im = im.crop((0, (frame % n) * fh, fw, (frame % n + 1) * fh))
    out = os.path.join(TMP, 'pvf_%d_%s' % (frame, os.path.basename(path)))
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
    m.blend_method = 'CLIP' if hasattr(m, 'blend_method') else None
    return m


def face_quad(d, f, t):
    x0, y0, z0 = f
    x1, y1, z1 = t
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
    return [((x0, y0, z1), (0, 0)), ((x1, y0, z1), (1, 0)), ((x1, y0, z0), (1, 1)), ((x0, y0, z0), (0, 1))]


def mesh_from(name, quads, mats):
    """quads: list of (4 points, 4 uvs, material index)."""
    verts, faces, uvs, fm = [], [], [], []
    for pts, uv, mi in quads:
        idx = []
        for p, t in zip(pts, uv):
            idx.append(len(verts))
            verts.append(mc2b(p))
            uvs.append(t)
        faces.append(idx)
        fm.append(mi)
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    uvl = me.uv_layers.new()
    for poly in me.polygons:
        for li in poly.loop_indices:
            uvl.data[li].uv = uvs[me.loops[li].vertex_index]
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    for m in mats:
        ob.data.materials.append(m)
    for poly, m in zip(me.polygons, fm):
        poly.material_index = m
    return ob


def crown():
    model = json.load(open(MODEL))
    img = frame_image(TEX, FRAME)
    mats = [material('c_' + d, img, SHADE[d]) for d in SHADE]
    md = {d: i for i, d in enumerate(SHADE)}
    quads = []
    for e in model['elements']:
        f = [a - 8 for a in e['from']]
        t = [a - 8 for a in e['to']]
        for d, fc in e['faces'].items():
            u0, v0, u1, v1 = fc['uv']
            pts, uv = [], []
            for p, (fu, fv) in face_quad(d, f, t):
                pts.append(p)
                uv.append(((u0 + (u1 - u0) * fu) / 16, 1 - (v0 + (v1 - v0) * fv) / 16))
            quads.append((pts, uv, md[d]))
    mesh_from('crown', quads, mats)


def head():
    im = Image.open(STEVE).convert('RGBA')
    path = os.path.join(TMP, 'pv_skin.png')
    im.save(path)
    W, Hh = im.size
    mats = [material('h_' + d, path, SHADE[d]) for d in SHADE]
    md = {d: i for i, d in enumerate(SHADE)}
    quads = []
    for (ox, oy), infl in (((0, 0), 0.0), ((32, 0), 0.533)):
        rects = {'up': (8, 0, 16, 8), 'down': (16, 0, 24, 8), 'east': (0, 8, 8, 16), 'north': (8, 8, 16, 16),
                 'west': (16, 8, 24, 16), 'south': (24, 8, 32, 16)}
        f, t = (-4 - infl, -8 - infl, -4 - infl), (4 + infl, 0 + infl, 4 + infl)
        for d, (a, b, c, e) in rects.items():
            pts, uv = [], []
            for p, (fu, fv) in face_quad(d, f, t):
                pts.append(p)
                uv.append(((ox + a + (c - a) * fu) / W, 1 - (oy + b + (e - b) * fv) / Hh))
            quads.append((pts, uv, md[d]))
    mesh_from('head', quads, mats)
    # a bit of torso for scale
    tq = []
    f, t = (-4, -20, -2), (4, -8, 2)
    rects = {'north': (20, 20, 28, 32), 'south': (32, 20, 40, 32), 'east': (16, 20, 20, 32), 'west': (28, 20, 32, 32),
             'up': (20, 16, 28, 20)}
    for d, (a, b, c, e) in rects.items():
        pts, uv = [], []
        for p, (fu, fv) in face_quad(d, f, t):
            pts.append(p)
            uv.append(((a + (c - a) * fu) / W, 1 - (b + (e - b) * fv) / Hh))
        tq.append((pts, uv, md[d]))
    mesh_from('torso', tq, mats)


CAMS = {
    'front': ((13, 1, -42), (0, -1.5, 0), 50),
    'low': ((12, -50, -44), (0, -1, 0), 55),
    'side': ((44, 0, -3), (0, -1.5, 0), 50),
    'high': ((14, 30, -32), (0, -1, 0), 50),
    'close': ((7, 5, -20), (0, 0, 0), 50),
    'back': ((-12, 4, 42), (0, -1, 0), 50),
}


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    s = bpy.context.scene
    s.render.engine = 'CYCLES'
    s.cycles.device = 'CPU'
    s.cycles.samples = 8
    s.render.resolution_x, s.render.resolution_y = 560, 420
    s.view_settings.view_transform = 'Standard'
    wd = bpy.data.worlds.new('w')
    wd.use_nodes = True
    wd.node_tree.nodes['Background'].inputs['Color'].default_value = (0.42, 0.62, 0.92, 1)
    s.world = wd
    crown()
    head()
    cam = bpy.data.cameras.new('cam')
    co = bpy.data.objects.new('cam', cam)
    s.collection.objects.link(co)
    s.camera = co
    shots = []
    for vname in VIEWS:
        pos, tgt, lens = CAMS[vname]
        cam.lens = lens
        co.location = mc2b(pos)
        dv = mathutils.Vector(mc2b(tgt)) - mathutils.Vector(mc2b(pos))
        co.rotation_euler = dv.to_track_quat('-Z', 'Y').to_euler()
        p = os.path.join(TMP, 'pv_view_%s.png' % vname)
        s.render.filepath = p
        bpy.ops.render.render(write_still=True)
        shots.append(p)
    ims = [Image.open(p) for p in shots]
    cols = 2 if len(ims) > 1 else 1
    rows = (len(ims) + cols - 1) // cols
    sheet = Image.new('RGB', (cols * 560, rows * 420), (20, 24, 30))
    for k, im in enumerate(ims):
        sheet.paste(im.convert('RGB'), ((k % cols) * 560, (k // cols) * 420))
    sheet.save(OUT)


main()
