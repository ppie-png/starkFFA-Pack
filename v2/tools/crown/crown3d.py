"""STARK crown (pack r46): the 3D crown that floats over the head of the Hall of Fame #1 (StarkCore CrownModule,
ItemDisplay riding the player, item model starkffa:crown).

Octagonal gold band (8 panels, the diagonal ones are the N / S panels turned by +-45 degrees - MC allows one rotation
axis per element), bottom rim + top bead, a stepped spike on every panel (tall on N/E/S/W, short on the diagonals) with
a gem ball, cyan / red jewels on the band, a red velvet cap with a gold orb inside.

Texture gold.png (64 x 32 per frame, animated): every panel owns an 8 px column (left to right as seen from outside:
N NW W SW S SE E NE), so the shine band that moves along u travels around the crown. gems.png: jewels + velvet.
Writes into the pack source: models/item/crown.json, items/crown.json, textures/item/crown/{gold.png,gold.png.mcmeta,
gems.png}.
"""
import json
import math
import os
import sys

from PIL import Image

SRC = sys.argv[1] if len(sys.argv) > 1 else '/home/claude/starkffa-pack/v2/src'
A = os.path.join(SRC, 'assets', 'starkffa')

C = 8.0                     # centre x / z
Y0 = 4.0                    # bottom of the crown (model units)
TAN = math.tan(math.radians(22.5))

# ---------------- geometry ----------------
# r46b: not a regular octagon - the four axis walls are long (they carry the big points), the diagonal walls are short
# chamfers (pearls on stems). DG = how much further out the diagonal walls sit than the axis walls.
BAND_A, BAND_T, BAND_H = 5.0, 1.0, 1.7          # axis apothem (centre of the wall), wall thickness, height
DG = 0.546                                       # diagonal walls: apothem BAND_A + DG
RIM_T, RIM_H, RIM_OUT = 1.5, 0.6, 0.05           # bottom rim (wider, pushed out a little)
BEAD_T, BEAD_H = 1.3, 0.34                       # top bead
POINT = None                                     # r46b: side of the turned square = as big as fits (the lower corner must stay inside the rim)
POINT_T = 0.8
GEM_W, GEM_H, GEM_P = 1.7, 1.15, 0.38           # band jewels (axis walls), protrusion
STUD_W, STUD_P = 0.7, 0.28                       # small red jewels on the chamfers
BALL = 0.78                                      # pearl on the point tips
STEM_W, STEM_H, PEARL = 0.4, 1.25, 0.66          # pearl stems on the chamfers

# panel order left -> right as seen from outside; (base box side, rotation, u column)
PANELS = [('N', 0, 0), ('N', 45, 1), ('W', 0, 2), ('S', -45, 3), ('S', 0, 4), ('S', 45, 5), ('E', 0, 6), ('N', -45, 7)]
JEWEL = {0: 'cyan', 2: 'red', 4: 'cyan', 6: 'red'}   # u column -> band jewel colour (axis panels)
# 45-degree turn of the point square so that the texture's top-left corner (bright) ends up at the tip
POINT_ROT = {'N': ('z', 45), 'S': ('z', -45), 'E': ('x', -45), 'W': ('x', 45)}


def r2(v):
    return round(v, 4)


def gold_uv(col, region, frac0=0.0, frac1=1.0):
    """uv of a panel column in gold.png (64 x 32): band rows 0-11, spike rows 12-23, dark rows 24-31."""
    rows = {'band': (0, 12), 'spike': (12, 24), 'dark': (24, 32)}[region]
    py0 = rows[0] + (rows[1] - rows[0]) * frac0
    py1 = rows[0] + (rows[1] - rows[0]) * frac1
    u0 = col * 2.0                 # 8 px = 2 units (64 px over 16 units)
    return [r2(u0), r2(py0 / 2), r2(u0 + 2.0), r2(py1 / 2)]


GEMS = {'cyan': (0, 0, 8, 8), 'red': (8, 0, 16, 8), 'pearl': (16, 0, 24, 8), 'stud': (24, 0, 32, 8),
        'velvet': (0, 8, 16, 16), 'velvet2': (16, 8, 32, 16), 'point': (32, 0, 48, 16)}


def gem_uv(kind):
    x0, y0, x1, y1 = GEMS[kind]     # gems.png 48 x 16 -> u = px / 3, v = py
    return [r2(x0 / 3), y0, r2(x1 / 3), y1]


def box_on_side(side, half_w, a, t, y0, y1, outward=0.0):
    """Axis-aligned box standing on one side of the octagon: half width along the wall, wall from apothem a-t/2 to
    a+t/2 (+ outward shift), returns (from, to, outer face name, inner face name)."""
    lo, hi = a - t / 2 + outward, a + t / 2 + outward
    if side == 'N':
        return [C - half_w, y0, C - hi], [C + half_w, y1, C - lo], 'north', 'south'
    if side == 'S':
        return [C - half_w, y0, C + lo], [C + half_w, y1, C + hi], 'south', 'north'
    if side == 'E':
        return [C + lo, y0, C - half_w], [C + hi, y1, C + half_w], 'east', 'west'
    if side == 'W':
        return [C - hi, y0, C - half_w], [C - lo, y1, C + half_w], 'west', 'east'
    raise ValueError(side)


def element(frm, to, faces, rot=0, ry=None, name=None, axis='y', origin=None, shade=True):
    e = {'from': [r2(v) for v in frm], 'to': [r2(v) for v in to], 'faces': faces}
    if not shade:
        e['shade'] = False
    if rot:
        e['rotation'] = {'angle': rot, 'axis': axis,
                         'origin': [r2(v) for v in origin] if origin else [C, r2(ry if ry is not None else frm[1]), C]}
    if name:
        e['name'] = name
    return e


def wall_faces(outer, inner, col, region_out, region_in='dark', top='dark', bottom='dark', side_region='dark'):
    f = {outer: {'uv': gold_uv(col, region_out), 'texture': '#gold'},
         inner: {'uv': gold_uv(col, region_in), 'texture': '#gold'},
         'up': {'uv': gold_uv(col, top, 0.0, 0.25), 'texture': '#gold'},
         'down': {'uv': gold_uv(col, bottom, 0.75, 1.0), 'texture': '#gold'}}
    for s in ('north', 'south', 'east', 'west'):
        if s not in f:
            f[s] = {'uv': gold_uv(col, side_region, 0.3, 0.7), 'texture': '#gold'}
    return f


def all_faces(tex, uv):
    return {s: {'uv': uv, 'texture': tex} for s in ('north', 'south', 'east', 'west', 'up', 'down')}


def half_widths(a_mid, t):
    """Outer half lengths of the axis and diagonal walls when the axis walls sit at a_mid and the diagonal ones at
    a_mid + DG (wall centres), both of thickness t."""
    ao, bo = a_mid + t / 2, a_mid + DG + t / 2
    ax = bo * math.sqrt(2) - ao
    dg = (2 * ao - bo * math.sqrt(2)) * math.sqrt(2) / 2
    return ax + 0.06, dg + 0.06


def build():
    els = []
    yb = Y0 + 0.35 + BAND_H              # band top = bead bottom
    yt = yb + BEAD_H                     # bead top: the points and pearls stand here
    for side, rot, col in PANELS:
        axis_panel = rot == 0
        A = BAND_A if axis_panel else BAND_A + DG
        k = 0 if axis_panel else 1
        # band (outer length so the corners close; inner corners overlap inside)
        hw = half_widths(BAND_A, BAND_T)[k]
        f, t, o, i = box_on_side(side, hw, A, BAND_T, Y0 + 0.35, yb)
        els.append(element(f, t, wall_faces(o, i, col, 'band'), rot, name='band_%d' % col))
        # bottom rim
        hw = half_widths(BAND_A + RIM_OUT, RIM_T)[k]
        f, t, o, i = box_on_side(side, hw, A + RIM_OUT, RIM_T, Y0, Y0 + RIM_H)
        els.append(element(f, t, wall_faces(o, i, col, 'band', top='band', side_region='band'), rot, ry=Y0, name='rim_%d' % col))
        # top bead
        hw = half_widths(BAND_A, BEAD_T)[k]
        f, t, o, i = box_on_side(side, hw, A, BEAD_T, yb, yt)
        els.append(element(f, t, wall_faces(o, i, col, 'spike', top='spike', side_region='spike'), rot, ry=Y0, name='bead_%d' % col))
        ym = Y0 + 0.35 + BAND_H / 2
        if axis_panel:
            # the point: a square turned 45 degrees, centred on the bead top - the lower half hides inside the band
            hd = yt - Y0 - 0.04                         # half diagonal: the hidden lower corner ends just above the bottom
            h = hd / math.sqrt(2)                       # half side of the square
            f, t, o, i = box_on_side(side, h, BAND_A, POINT_T, yt - h, yt + h)
            ax, ang = POINT_ROT[side]
            org = [(f[0] + t[0]) / 2, yt, (f[2] + t[2]) / 2]
            faces = {o: {'uv': gem_uv('point'), 'texture': '#gems'},
                     i: {'uv': gold_uv(col, 'dark'), 'texture': '#gold'}}
            for s in ('north', 'south', 'east', 'west', 'up', 'down'):
                faces.setdefault(s, {'uv': gold_uv(col, 'spike', 0.2, 0.8), 'texture': '#gold'})
            els.append(element(f, t, faces, ang, axis=ax, origin=org, name='point_%d' % col))
            tip = yt + hd
            f, t, o, i = box_on_side(side, BALL / 2, BAND_A, BALL, tip - 0.25, tip - 0.25 + BALL)
            els.append(element(f, t, all_faces('#gems', gem_uv('pearl')), name='tip_%d' % col))
            f, t, o, i = box_on_side(side, GEM_W / 2, BAND_A + BAND_T / 2 + GEM_P / 2 - 0.05, GEM_P + 0.1, ym - GEM_H / 2, ym + GEM_H / 2)
            els.append(element(f, t, all_faces('#gems', gem_uv(JEWEL[col])), name='jewel_%d' % col))
        else:
            # diagonals: a pearl on a thin gold stem + a pearl stud in the band
            f, t, o, i = box_on_side(side, STEM_W / 2, A, STEM_W, yt - 0.1, yt + STEM_H)
            els.append(element(f, t, wall_faces(o, i, col, 'spike', region_in='spike', top='spike', side_region='spike'), rot, ry=Y0, name='stem_%d' % col))
            f, t, o, i = box_on_side(side, PEARL / 2, A, PEARL, yt + STEM_H - 0.15, yt + STEM_H - 0.15 + PEARL)
            els.append(element(f, t, all_faces('#gems', gem_uv('pearl')), rot, ry=Y0, name='pearl_%d' % col))
            f, t, o, i = box_on_side(side, STUD_W / 2, A + BAND_T / 2 + STUD_P / 2 - 0.05, STUD_P + 0.1, ym - STUD_W / 2, ym + STUD_W / 2)
            els.append(element(f, t, all_faces('#gems', gem_uv('red')), rot, ry=Y0, name='stud_%d' % col))
    # velvet cap: a cross of two boxes (fits the octagon) + a raised dome + the orb
    vt = Y0 + 0.5
    els.append(element([C - 4.35, vt, C - 2.6], [C + 4.35, Y0 + 2.7, C + 2.6], all_faces('#gems', gem_uv('velvet2')), name='cap_x', shade=False))
    els.append(element([C - 2.6, vt, C - 4.35], [C + 2.6, Y0 + 2.7, C + 4.35], all_faces('#gems', gem_uv('velvet2')), name='cap_z', shade=False))
    els.append(element([C - 3.2, vt, C - 3.2], [C + 3.2, Y0 + 3.5, C + 3.2], all_faces('#gems', gem_uv('velvet')), name='cap_dome', shade=False))
    els.append(element([C - 1.7, Y0 + 3.5, C - 1.7], [C + 1.7, Y0 + 4.0, C + 1.7], all_faces('#gems', gem_uv('velvet')), name='cap_top', shade=False))
    els.append(element([C - 0.6, Y0 + 4.0, C - 0.6], [C + 0.6, Y0 + 5.2, C + 0.6], all_faces('#gems', gem_uv('stud')), name='orb'))
    els.append(element([C - 0.26, Y0 + 5.2, C - 0.26], [C + 0.26, Y0 + 5.85, C + 0.26], all_faces('#gems', gem_uv('cyan')), name='orb_gem'))
    model = {
        'textures': {'gold': 'starkffa:item/crown/gold', 'gems': 'starkffa:item/crown/gems', 'particle': 'starkffa:item/crown/gems'},
        'elements': els,
        'display': {'fixed': {'rotation': [0, 0, 0], 'translation': [0, 0, 0], 'scale': [1, 1, 1]},
                    'head': {'rotation': [0, 0, 0], 'translation': [0, 0, 0], 'scale': [1, 1, 1]},
                    'gui': {'rotation': [25, 30, 0], 'translation': [0, -1.5, 0], 'scale': [1.15, 1.15, 1.15]}},
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
            # engraved line two rows under the top + a soft dot row (beads) every 4 px
            if y == 2:
                c = lerp(c, hexc('A86A1C'), 0.55)
            if y == 8 and x % 4 == 1:
                c = lerp(c, hexc('FFF6C2'), 0.6)
            px[x, y] = c
        for y in range(12):
            px[x, 12 + y] = hexc(SPIKE[y])
        for y in range(8):
            px[x, 24 + y] = hexc(DARK[y])
    if shine_x is not None:
        for y in range(24):
            for x in range(64):
                d = abs((x - shine_x) + (y % 12) * 0.35)    # slanted band
                if d < 3.2:
                    f = (1 - d / 3.2) ** 1.5 * 0.85
                    px[x, y] = lerp(px[x, y], hexc('FFFFFF'), f)
    return im


def gold_strip():
    frames = [gold_frame(None)]
    steps = list(range(-6, 72, 4))               # 20 shine positions around the crown
    for sx in steps:
        frames.append(gold_frame(sx))
    strip = Image.new('RGBA', (64, 32 * len(frames)))
    for i, f in enumerate(frames):
        strip.paste(f, (0, 32 * i))
    meta = {'animation': {'width': 64, 'height': 32, 'interpolate': False,
                          'frames': [{'index': 0, 'time': 70}] + [{'index': i, 'time': 1} for i in range(1, len(frames))]}}
    return strip, meta


def jewel(base, hi, lo):
    im = Image.new('RGBA', (8, 8), hexc(base))
    px = im.load()
    for y in range(8):
        for x in range(8):
            d = (x + y) / 14
            px[x, y] = lerp(hexc(hi), hexc(lo), d)
    for (x, y) in ((1, 1), (2, 1), (1, 2)):
        px[x, y] = hexc('FFFFFF')
    for x in range(8):
        px[x, 7] = lerp(px[x, 7], hexc('000000'), 0.35)
        px[7, x] = lerp(px[7, x], hexc('000000'), 0.35)
    return im


def point_tex():
    """16 x 16 gold for the turned point squares: bright top-left corner (= the tip), darker towards the base."""
    im = Image.new('RGBA', (16, 16))
    px = im.load()
    for y in range(16):
        for x in range(16):
            d = (x + y) / 30
            c = lerp(hexc('FFEC8C'), hexc('D88A26'), d ** 0.85)
            if x == 0 or y == 0:
                c = lerp(c, hexc('FFF6C2'), 0.7)      # the two upper edges catch the light
            if x == 15 or y == 15:
                c = lerp(c, hexc('7A4612'), 0.5)
            px[x, y] = c
    return im


def gems_png():
    im = Image.new('RGBA', (48, 16), (0, 0, 0, 0))
    im.paste(point_tex(), (32, 0))
    im.paste(jewel('3FE0FF', 'B8F6FF', '1A8FB0'), (0, 0))
    im.paste(jewel('FF4D5E', 'FFB0B8', 'A81E34'), (8, 0))
    im.paste(jewel('F2F6FA', 'FFFFFF', 'B8C2D0'), (16, 0))
    im.paste(jewel('FFD24D', 'FFF6C2', 'B8761E'), (24, 0))
    px = im.load()
    for y in range(8):                         # velvet: deep red with a soft diamond quilting
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
    os.makedirs(os.path.join(A, 'models', 'item'), exist_ok=True)
    os.makedirs(os.path.join(A, 'items'), exist_ok=True)
    tdir = os.path.join(A, 'textures', 'item', 'crown')
    os.makedirs(tdir, exist_ok=True)
    with open(os.path.join(A, 'models', 'item', 'crown.json'), 'w') as f:
        json.dump(model, f, separators=(',', ':'))
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
