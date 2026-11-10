"""STARK crown v2 (pack r47, owner 10.11. 21:37: "I pictured the crown square, simply sitting on the player's head and
sparkling a little - a very chic item"). The crown is the LOOK of the #1's helmet: StarkCore swaps the helmet's
item_model to starkffa:crown and takes the armour asset out of its equippable component, so the client draws this model
on the head (CustomHeadLayer, HEAD context) - it turns and nods with the head, client-side.

HEAD context space: the item model is drawn at 0.625 around the head centre, so the head (8 px) spans model units
1.6 .. 14.4 on every axis (1 head pixel = 1.6 units) and the hat layer (+0.5 px) 0.8 .. 15.2. Model north = his face.
The band sits OUTSIDE the hat layer, around the top of the head, the points rise above it - all of it stays below the
TAB hearts line over the head.

Parts: four walls (band) with a bottom rim and a top bead, a turned-square point in the middle of every wall, corner
posts with pearls, a cyan jewel front and back, red jewels left and right with gold studs, a red velvet top with a gold
orb. Texture gold.png (64 x 32 per frame, animated): every wall owns a 16 px column (left to right seen from outside:
N W S E) - the light band that runs along u travels around the crown. The JSON opens in Blockbench as a Java model.
"""
import json
import math
import os
import sys

from PIL import Image

SRC = sys.argv[1] if len(sys.argv) > 1 else '/home/claude/starkffa-pack/v2/src'
A = os.path.join(SRC, 'assets', 'starkffa')
C = 8.0
PX = 1.6                         # one head pixel in model units (HEAD context)

IN = 7.25                        # inner half width of the band (just outside the hat layer at 7.2)
T = 0.8                          # band wall thickness
OUT = IN + T
Y_BOT, Y_TOP = 13.5, 16.3        # band: the top 1.1 px of the hat layer + 0.7 px above it (1.75 px tall)
RIM_H, RIM_O = 0.45, 0.22        # bottom rim height / how far it stands out
BEAD_H, BEAD_O = 0.3, 0.18        # top bead
HD = 3.0                         # half diagonal of the turned square
LIFT = 0.25                      # its centre sits this much over the band top, the lower corner stays inside the band
POINT_T = 0.6
POST = 1.6                       # corner post (1 px)
POST_TOP = 17.7
PEARL = 0.75
SIDES = [('N', 0), ('W', 1), ('S', 2), ('E', 3)]   # wall, gold column (left -> right seen from outside)
JEWEL = {'N': 'cyan', 'S': 'cyan', 'W': 'red', 'E': 'red'}


def r2(v):
    return round(v, 4)


def gold_uv(col, region, f0=0.0, f1=1.0, u0f=0.0, u1f=1.0):
    rows = {'band': (0, 12), 'spike': (12, 24), 'dark': (24, 32)}[region]
    py0 = rows[0] + (rows[1] - rows[0]) * f0
    py1 = rows[0] + (rows[1] - rows[0]) * f1
    u0 = col * 4.0                  # 16 px column = 4 units (64 px over 16 units)
    return [r2(u0 + 4.0 * u0f), r2(py0 / 2), r2(u0 + 4.0 * u1f), r2(py1 / 2)]


GEMS = {'cyan': (0, 0, 8, 8), 'red': (8, 0, 16, 8), 'pearl': (16, 0, 24, 8), 'stud': (24, 0, 32, 8),
        'velvet': (0, 8, 16, 16), 'velvet2': (16, 8, 32, 16), 'point': (32, 0, 48, 16)}


def gem_uv(kind):
    x0, y0, x1, y1 = GEMS[kind]     # gems.png 48 x 16 -> u = px / 3, v = py
    return [r2(x0 / 3), y0, r2(x1 / 3), y1]


def wall(side, half_len, inner, thick, y0, y1):
    """Box of a wall on one side: along the wall +-half_len, from the inner face outwards."""
    lo, hi = inner, inner + thick
    if side == 'N':
        return [C - half_len, y0, C - hi], [C + half_len, y1, C - lo], 'north', 'south'
    if side == 'S':
        return [C - half_len, y0, C + lo], [C + half_len, y1, C + hi], 'south', 'north'
    if side == 'W':
        return [C - hi, y0, C - half_len], [C - lo, y1, C + half_len], 'west', 'east'
    return [C + lo, y0, C - half_len], [C + hi, y1, C + half_len], 'east', 'west'


def el(frm, to, faces, name, rot=None, shade=True):
    e = {'name': name, 'from': [r2(v) for v in frm], 'to': [r2(v) for v in to], 'faces': faces}
    if rot:
        e['rotation'] = rot
    if not shade:
        e['shade'] = False
    return e


def faces_wall(outer, inner, col, out_region='band', top='spike', bottom='dark', side='spike'):
    f = {outer: {'uv': gold_uv(col, out_region), 'texture': '#gold'},
         inner: {'uv': gold_uv(col, 'dark'), 'texture': '#gold'},
         'up': {'uv': gold_uv(col, top, 0.0, 0.2), 'texture': '#gold'},
         'down': {'uv': gold_uv(col, bottom, 0.7, 1.0), 'texture': '#gold'}}
    for s in ('north', 'south', 'east', 'west'):
        f.setdefault(s, {'uv': gold_uv(col, side, 0.2, 0.8, 0.0, 0.1), 'texture': '#gold'})
    return f


def all_faces(tex, uv):
    return {s: {'uv': uv, 'texture': tex} for s in ('north', 'south', 'east', 'west', 'up', 'down')}


def build():
    els = []
    for side, col in SIDES:
        # band: the N / S walls run the full width, the W / E walls fit between them
        hl = OUT if side in 'NS' else IN
        f, t, o, i = wall(side, hl, IN, T, Y_BOT + RIM_H * 0.5, Y_TOP)
        els.append(el(f, t, faces_wall(o, i, col), 'band_' + side))
        hl = OUT + RIM_O if side in 'NS' else IN
        f, t, o, i = wall(side, hl, IN, T + RIM_O, Y_BOT, Y_BOT + RIM_H)
        els.append(el(f, t, faces_wall(o, i, col, 'spike', top='spike', side='spike'), 'rim_' + side))
        hl = OUT + BEAD_O if side in 'NS' else IN
        f, t, o, i = wall(side, hl, IN, T + BEAD_O, Y_TOP - BEAD_H, Y_TOP)
        els.append(el(f, t, faces_wall(o, i, col, 'spike', top='spike', side='spike'), 'bead_' + side))
        # the point: a square turned 45 degrees in the wall's plane, centred on the band top (lower half hidden)
        h = HD / math.sqrt(2)
        yc = Y_TOP + LIFT
        assert yc - HD > Y_BOT, 'the lower corner of the point would show under the band'
        f, t, o, i = wall(side, h, IN + (T - POINT_T) / 2, POINT_T, yc - h, yc + h)
        axis = 'z' if side in 'NS' else 'x'
        # turn so that the texture's bright top-left corner ends up at the tip (see crown3d.py)
        ang = {'N': 45, 'S': -45, 'E': -45, 'W': 45}[side]
        org = [r2((f[0] + t[0]) / 2), r2(yc), r2((f[2] + t[2]) / 2)]
        faces = {o: {'uv': gem_uv('point'), 'texture': '#gems'}, i: {'uv': gold_uv(col, 'dark'), 'texture': '#gold'}}
        for s in ('north', 'south', 'east', 'west', 'up', 'down'):
            faces.setdefault(s, {'uv': gold_uv(col, 'spike', 0.2, 0.8, 0.0, 0.1), 'texture': '#gold'})
        els.append(el(f, t, faces, 'point_' + side, {'angle': ang, 'axis': axis, 'origin': org}))
        tip = yc + HD
        f, t, o, i = wall(side, PEARL / 2, IN + T / 2 - PEARL / 2, PEARL, tip - 0.3, tip - 0.3 + PEARL)
        els.append(el(f, t, all_faces('#gems', gem_uv('pearl')), 'tip_' + side))
        # jewel in the middle of the band, two gold studs beside it
        ym = (Y_BOT + RIM_H + Y_TOP - BEAD_H) / 2
        gw, gh, gp = 2.4, 1.3, 0.4
        f, t, o, i = wall(side, gw / 2, OUT - 0.05, gp, ym - gh / 2, ym + gh / 2)
        els.append(el(f, t, all_faces('#gems', gem_uv(JEWEL[side])), 'jewel_' + side))
        for k, off in (('a', -4.2), ('b', 4.2)):
            f, t, o, i = wall(side, 0.45, OUT - 0.05, 0.3, ym - 0.45, ym + 0.45)
            if side in 'NS':
                f[0] += off; t[0] += off
            else:
                f[2] += off; t[2] += off
            els.append(el(f, t, all_faces('#gems', gem_uv('stud')), 'stud_%s_%s' % (side, k)))
    # corner posts with pearls
    for cx in (-1, 1):
        for cz in (-1, 1):
            x0 = C + cx * OUT - (POST if cx > 0 else 0)
            z0 = C + cz * OUT - (POST if cz > 0 else 0)
            x0 = C - OUT if cx < 0 else C + OUT - POST
            z0 = C - OUT if cz < 0 else C + OUT - POST
            col = 0 if cz < 0 else 2
            post = {s: {'uv': gold_uv(col, 'band', 0.15, 0.95, 0.0, 0.1), 'texture': '#gold'} for s in ('north', 'south', 'east', 'west')}
            post['up'] = {'uv': gold_uv(col, 'spike', 0.35, 0.45, 0.0, 0.1), 'texture': '#gold'}
            post['down'] = {'uv': gold_uv(col, 'dark', 0.8, 1.0, 0.0, 0.1), 'texture': '#gold'}
            els.append(el([x0 - 0.1, Y_BOT, z0 - 0.1], [x0 + POST + 0.1, POST_TOP, z0 + POST + 0.1], post, 'post_%d_%d' % (cx, cz)))
            px0, pz0 = x0 + POST / 2 - PEARL / 2, z0 + POST / 2 - PEARL / 2
            els.append(el([px0, POST_TOP - 0.15, pz0], [px0 + PEARL, POST_TOP - 0.15 + PEARL, pz0 + PEARL], all_faces('#gems', gem_uv('pearl')),
                          'pearl_%d_%d' % (cx, cz)))
    # red velvet top on the hat layer, a raised middle and a gold orb with a cyan gem
    els.append(el([C - IN + 0.05, 15.15, C - IN + 0.05], [C + IN - 0.05, 16.05, C + IN - 0.05], all_faces('#gems', gem_uv('velvet2')), 'cap', shade=False))
    els.append(el([C - 4.0, 16.05, C - 4.0], [C + 4.0, 16.75, C + 4.0], all_faces('#gems', gem_uv('velvet')), 'cap_top', shade=False))
    els.append(el([C - 0.7, 16.75, C - 0.7], [C + 0.7, 18.15, C + 0.7], all_faces('#gems', gem_uv('stud')), 'orb'))
    els.append(el([C - 0.3, 18.15, C - 0.3], [C + 0.3, 18.85, C + 0.3], all_faces('#gems', gem_uv('cyan')), 'orb_gem'))
    model = {
        'credit': 'STARK FFA - crown of the Hall of Fame #1 (tools/crown/crown_square.py)',
        'textures': {'gold': 'starkffa:item/crown/gold', 'gems': 'starkffa:item/crown/gems', 'particle': 'starkffa:item/crown/gems'},
        'elements': els,
        'display': {
            # 1 unit lower than the geometry: the pearls stay clear of the TAB hearts line (camera test)
            'head': {'rotation': [0, 0, 0], 'translation': [0, -1, 0], 'scale': [1, 1, 1]},
            'gui': {'rotation': [24, 45, 0], 'translation': [0, -6.5, 0], 'scale': [0.95, 0.95, 0.95]},
            'ground': {'rotation': [0, 0, 0], 'translation': [0, -3, 0], 'scale': [0.6, 0.6, 0.6]},
            'fixed': {'rotation': [0, 0, 0], 'translation': [0, -6, 0], 'scale': [1, 1, 1]},
            'thirdperson_righthand': {'rotation': [70, 0, 0], 'translation': [0, -2, -4], 'scale': [0.5, 0.5, 0.5]},
            'firstperson_righthand': {'rotation': [10, 30, 0], 'translation': [0, -4, 0], 'scale': [0.5, 0.5, 0.5]},
        },
    }
    return model


# ---------------- textures ----------------
def hexc(h, a=255):
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4)) + (a,)


def lerp(c0, c1, f):
    return tuple(int(round(c0[i] + (c1[i] - c0[i]) * f)) for i in range(4))


BAND = ['FFFBE0', 'FFEE9A', 'FFE36A', 'FFD84D', 'FFCB45', 'FFBE40', 'FBB03A', 'F2A236', 'E39331', 'D3842B', 'BC7224', '8A5016']
SPIKE = ['FFFDEB', 'FFF5BC', 'FFEC94', 'FFE274', 'FFD85C', 'FFCD4C', 'FFC244', 'FBB53E', 'F2A838', 'E69A31', 'D58B2A', 'B4721F']
DARK = ['C08A3A', 'B07C32', 'A06E2B', '906125', '80551F', '704A1A', '614016', '523612']


def gold_frame(shine_x=None):
    im = Image.new('RGBA', (64, 32))
    px = im.load()
    for x in range(64):
        for y in range(12):
            c = hexc(BAND[y])
            if y == 2:
                c = lerp(c, hexc('A86A1C'), 0.5)            # engraved line under the top
            if y == 9:
                c = lerp(c, hexc('A86A1C'), 0.35)           # and over the rim
            if y == 6 and x % 4 == 1:
                c = lerp(c, hexc('FFF6C2'), 0.7)            # a row of beads
            px[x, y] = c
        for y in range(12):
            px[x, 12 + y] = hexc(SPIKE[y])
        for y in range(8):
            px[x, 24 + y] = hexc(DARK[y])
    if shine_x is not None:
        for y in range(24):
            for x in range(64):
                d = abs((x - shine_x) + (y % 12) * 0.4)
                if d < 3.0:
                    px[x, y] = lerp(px[x, y], hexc('FFFFFF'), (1 - d / 3.0) ** 1.4 * 0.9)
    return im


def gold_strip():
    frames = [gold_frame(None)]
    for sx in range(-6, 72, 3):                      # 26 steps around the crown
        frames.append(gold_frame(sx))
    strip = Image.new('RGBA', (64, 32 * len(frames)))
    for i, f in enumerate(frames):
        strip.paste(f, (0, 32 * i))
    meta = {'animation': {'width': 64, 'height': 32, 'interpolate': False,
                          'frames': [{'index': 0, 'time': 60}] + [{'index': i, 'time': 1} for i in range(1, len(frames))]}}
    return strip, meta


def jewel(hi, lo):
    im = Image.new('RGBA', (8, 8))
    px = im.load()
    for y in range(8):
        for x in range(8):
            px[x, y] = lerp(hexc(hi), hexc(lo), (x + y) / 14)
    for (x, y) in ((1, 1), (2, 1), (1, 2)):
        px[x, y] = hexc('FFFFFF')
    for x in range(8):
        px[x, 7] = lerp(px[x, 7], hexc('000000'), 0.35)
        px[7, x] = lerp(px[7, x], hexc('000000'), 0.35)
    return im


def point_tex():
    im = Image.new('RGBA', (16, 16))
    px = im.load()
    for y in range(16):
        for x in range(16):
            c = lerp(hexc('FFEC8C'), hexc('D88A26'), ((x + y) / 30) ** 0.85)
            if x == 0 or y == 0:
                c = lerp(c, hexc('FFF6C2'), 0.7)
            if x == 15 or y == 15:
                c = lerp(c, hexc('7A4612'), 0.5)
            px[x, y] = c
    return im


def gems_png():
    im = Image.new('RGBA', (48, 16), (0, 0, 0, 0))
    im.paste(point_tex(), (32, 0))
    im.paste(jewel('B8F6FF', '1A8FB0'), (0, 0))
    im.paste(jewel('FFB0B8', 'A81E34'), (8, 0))
    im.paste(jewel('FFFFFF', 'B8C2D0'), (16, 0))
    im.paste(jewel('FFF6C2', 'B8761E'), (24, 0))
    px = im.load()
    for y in range(8):
        for x in range(32):
            base = hexc('C8283F') if x < 16 else hexc('B02238')
            q = ((x + y) % 4 == 0) or ((x - y) % 4 == 0)
            c = lerp(base, hexc('6E0F22'), 0.4) if q else base
            if y == 0:
                c = lerp(c, hexc('FF6B80'), 0.35)
            px[x, 8 + y] = c
    return im


def main():
    model = build()
    tdir = os.path.join(A, 'textures', 'item', 'crown')
    for d in (os.path.join(A, 'models', 'item'), os.path.join(A, 'items'), tdir):
        os.makedirs(d, exist_ok=True)
    with open(os.path.join(A, 'models', 'item', 'crown.json'), 'w') as f:
        json.dump(model, f, indent=1)
    with open(os.path.join(A, 'items', 'crown.json'), 'w') as f:
        json.dump({'model': {'type': 'minecraft:model', 'model': 'starkffa:item/crown'}}, f)
    strip, meta = gold_strip()
    strip.save(os.path.join(tdir, 'gold.png'))
    with open(os.path.join(tdir, 'gold.png.mcmeta'), 'w') as f:
        json.dump(meta, f)
    gems_png().save(os.path.join(tdir, 'gems.png'))
    xs = [v for e in model['elements'] for v in (e['from'][0], e['to'][0])]
    ys = [v for e in model['elements'] for v in (e['from'][1], e['to'][1])]
    print('elements', len(model['elements']), 'x', min(xs), max(xs), 'y', min(ys), max(ys))


if __name__ == '__main__':
    main()
