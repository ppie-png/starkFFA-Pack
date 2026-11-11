"""STARK crown v3 - the Minecraft crown of the #1 podium statue (pack r48, owner 11.11. 17:54: "make it look far more
like Minecraft and prettier"). Pixel art on the SKIN's pixel grid: one voxel = one skin pixel of the statue head, one
texel per pixel, no turned or hair-thin parts, vanilla gold / diamond / redstone / red-wool palettes, light from the
top left like every vanilla item. The texture is animated: a pixel glint runs once around the crown every few seconds
and the gems twinkle.

Space: "sp" = skin pixels, origin = centre of the statue head's top (base head: x/z -4..4, y -8..0; hat layer +0.53).
Item px = 8 + sp on every axis. StarkCore puts the item on the model bone ri_crown (child of the head bone, origin =
head top), BetterModel draws it with the THIRDPERSON_RIGHTHAND transform: scale 0.9375 = 1 item px per skin px
(BetterModel's player head is 7.5 model px for 8 skin px). The crown is the same seen from the front and the back
(cyan gems) and from both sides (red gems), so the item display's own half turn changes nothing.

Usage: python3 crown_mc.py <variant> <out_src_dir>   (writes items/statue_crown.json, models/item/statue_crown.json,
textures/item/statue_crown.png + .mcmeta below <out_src_dir>/assets/starkffa)."""
import json
import math
import os
import sys

from PIL import Image

H = lambda s: tuple(int(s[i:i + 2], 16) for i in (1, 3, 5)) + (255,)
# vanilla gold (gold ingot / golden armour) light -> dark
G0, G1, G2, G3, G4, G5, G6 = (H(c) for c in ('#FFFDE0', '#FDF55F', '#FAD64A', '#E9B115', '#DC9613', '#B26411', '#752802'))
GW = H('#FFFFFF')
# diamond, tinted to STARK cyan
C0, C1, C2, C3, C4 = (H(c) for c in ('#E6FFFB', '#8DF6FF', '#3FE0FF', '#1BA6C9', '#11607A'))
# redstone / ruby, tinted to STARK red
R0, R1, R2, R3, R4 = (H(c) for c in ('#FFD2D6', '#FF5A66', '#E62E40', '#A3172A', '#5E0912'))   # camera r140d: less pink
# red wool velvet
V0, V1, V2, V3 = (H(c) for c in ('#D24A3E', '#B8342C', '#992421', '#7A1A18'))
P0, P1, P2 = (H(c) for c in ('#FFFFFF', '#F2F6FA', '#C9D2DE'))
W0, W1, W2 = (H(c) for c in ('#FFFFF6', '#FFF4DC', '#E9D6AE'))   # warm pearls (white goes grey in the shade)


class Box:
    def __init__(self, f, t, mat, tag=''):
        self.f = tuple(float(v) for v in f)
        self.t = tuple(float(v) for v in t)
        self.mat = mat
        self.tag = tag


# ---------------------------------------------------------------- designs (sp coordinates)

def ring(boxes, y0, y1, inner, outer, mat, tag):
    """A square ring: N and S walls full width, W and E walls between them (no overlap)."""
    boxes.append(Box((-outer, y0, -outer), (outer, y1, -inner), mat, tag + 'N'))
    boxes.append(Box((-outer, y0, inner), (outer, y1, outer), mat, tag + 'S'))
    boxes.append(Box((-outer, y0, -inner), (-inner, y1, inner), mat, tag + 'W'))
    boxes.append(Box((inner, y0, -inner), (outer, y1, inner), mat, tag + 'E'))


def side_boxes(boxes, x0, x1, y0, y1, d0, d1, mat, tag, sides='NSWE'):
    """A box on every wall: x0..x1 along the wall (seen from outside, left -> right), d0..d1 = distance from the
    centre (d1 = outside). Same shape on all four walls."""
    for s in sides:
        if s == 'N':
            boxes.append(Box((-x1, y0, -d1), (-x0, y1, -d0), mat, tag + s))
        elif s == 'S':
            boxes.append(Box((x0, y0, d0), (x1, y1, d1), mat, tag + s))
        elif s == 'W':
            boxes.append(Box((-d1, y0, x0), (-d0, y1, x1), mat, tag + s))
        elif s == 'E':
            boxes.append(Box((d0, y0, -x1), (d1, y1, -x0), mat, tag + s))


def design_grid10(v):
    """Everything on the skin-pixel grid: the band is 10 px wide (x -5..5, like a vanilla helmet), so the middle is a
    line between two columns - centre features are 2 px wide and the crown stays symmetric."""
    b = []
    IN, OUT = 4.0, 5.0
    y0, y1 = v['band']
    ring(b, y0, y1, IN, OUT, 'gold', 'band')
    yy = y1
    for hw, hh in v['point']:                       # centre point rows (half width, height)
        side_boxes(b, -hw, hw, yy, yy + hh, IN, OUT, 'gold', 'pt%g' % yy)
        yy += hh
    if v.get('tip'):
        tw = v['tip']
        side_boxes(b, -tw, tw, yy, yy + 1, IN, OUT, 'pearl', 'tip')
    for x0, x1, h in v.get('teeth', ()):
        side_boxes(b, x0, x1, y1, y1 + h, IN, OUT, 'gold', 'tooth')
        if v.get('teeth_pearl'):
            side_boxes(b, x0, x1, y1 + h, y1 + h + 1, IN, OUT, 'pearl', 'tpearl')
    ph = v['post']
    for sx in (-1, 1):
        for sz in (-1, 1):
            if v.get('no_posts'):
                break
            x0, x1 = sorted((sx * IN, sx * OUT))
            z0, z1 = sorted((sz * IN, sz * OUT))
            if ph:
                b.append(Box((x0, y1, z0), (x1, y1 + ph, z1), 'gold', 'post'))
            if v.get('knobs'):
                b.append(Box((x0, y1 + ph, z0), (x1, y1 + ph + 1, z1), 'gold', 'knob'))
            else:
                b.append(Box((x0, y1 + ph, z0), (x1, y1 + ph + 1, z1), 'pearl', 'pearl'))
    rel = v['gem_relief']
    gm = v['gem_mid']                               # the jewel's middle row
    for mat, sides in (('cyan', 'NS'), ('red', 'WE')):
        side_boxes(b, -1, 1, y0, y1, OUT, OUT + rel, mat, 'gemc', sides)
        side_boxes(b, -2, -1, gm, gm + 1, OUT, OUT + rel, mat, 'geml', sides)
        side_boxes(b, 1, 2, gm, gm + 1, OUT, OUT + rel, mat, 'gemr', sides)
    for sx0, sx1 in v.get('studs', ()):
        side_boxes(b, sx0, sx1, gm, gm + 1, OUT, OUT + v.get('stud_relief', 0.25), v.get('stud_mat', 'gold_stud'), 'stud')
    c0, c1 = v['cap']
    b.append(Box((-IN, c0, -IN), (IN, c1, IN), 'velvet', 'cap'))
    if v.get('orb'):
        b.append(Box((-1, c1, -1), (1, c1 + 2, 1), 'gold', 'orb'))
        if v.get('orb_gem'):
            b.append(Box((-1, c1 + 2, -1), (1, c1 + 3, 1), 'cyan', 'orbgem'))
    v['inner'], v['outer'] = IN, OUT
    return b, v


def design(variant):
    v = dict(VARIANTS[variant])
    if v.get('layout') == 'grid10':
        return design_grid10(v)
    b = []
    IN, OUT = v['inner'], v['outer']
    y0, y1 = v['band']
    ring(b, y0, y1, IN, OUT, 'gold', 'band')
    # points on every wall: stepped pyramid rows (half width, height of the row)
    yy = y1
    for hw, hh in v['point']:
        side_boxes(b, -hw, hw, yy, yy + hh, IN, OUT, 'gold', 'pt%g' % yy)
        yy += hh
    if v.get('tip'):
        side_boxes(b, -0.5, 0.5, yy, yy + 1, IN, OUT, 'pearl', 'tip')
    # corner posts + pearls
    ph = v['post']
    if ph:
        for sx in (-1, 1):
            for sz in (-1, 1):
                x0, x1 = sorted((sx * IN, sx * OUT))
                z0, z1 = sorted((sz * IN, sz * OUT))
                b.append(Box((x0, y1, z0), (x1, y1 + ph, z1), 'gold', 'post'))
                b.append(Box((x0, y1 + ph, z0), (x1, y1 + ph + 1, z1), 'pearl', 'pearl'))
    # small teeth between the corner and the centre point
    for x0, x1, h in v.get('teeth', ()):
        side_boxes(b, x0, x1, y1, y1 + h, IN, OUT, 'gold', 'tooth')
    # jewels on the band (raised): front/back cyan, sides red
    gy0, gy1 = v['gem_y']
    gw = v['gem_w']
    rel = v['gem_relief']
    for mat, sides in (('cyan', v.get('cyan_sides', 'NS')), ('red', v.get('red_sides', 'WE'))):
        if v.get('gem_shape') == 'diamond':
            # a pixel diamond: centre column over the whole band + one pixel left and right in the middle row
            side_boxes(b, -0.5, 0.5, y0, y1, OUT, OUT + rel, mat, 'gemc', sides)
            side_boxes(b, -1.5, -0.5, gy0, gy1, OUT, OUT + rel, mat, 'geml', sides)
            side_boxes(b, 0.5, 1.5, gy0, gy1, OUT, OUT + rel, mat, 'gemr', sides)
        else:
            side_boxes(b, -gw, gw, gy0, gy1, OUT, OUT + rel, mat, 'gem', sides)
    for sx0, sx1 in v.get('studs', ()):
        side_boxes(b, sx0, sx1, gy0, gy1, OUT, OUT + v.get('stud_relief', 0.25), 'gold_stud', 'stud')
    # velvet cap + orb
    if v.get('cap'):
        c0, c1 = v['cap']
        b.append(Box((-IN, c0, -IN), (IN, c1, IN), 'velvet', 'cap'))
        if v.get('orb'):
            o = v['orb']
            oh = v.get('orb_h', 2 * o)
            b.append(Box((-o, c1, -o), (o, c1 + oh, o), 'gold', 'orb'))
            if v.get('orb_gem', True):
                b.append(Box((-0.5, c1 + oh, -0.5), (0.5, c1 + oh + 1, 0.5), 'cyan', 'orbgem'))
    return b, v


VARIANTS = {
    # v5 (camera r140b: b's dark band bottom gives the band its edge, beige pearls read as stone): band G1/G3/G5,
    # points lit top-left with a shine on the tip, corner posts end in a polished gold knob
    'v5': dict(layout='grid10', band=(-2, 1), point=[(3, 1), (2, 1), (1, 1)], tip=0, post=1, gem_relief=0.5, gem_mid=-1,
               studs=[(-4, -3), (3, 4)], cap=(0.55, 1.0), orb=True, band_rows=(G1, G3, G5), point_shade='mid',
               knobs=True),
    # v5b: no corner posts at all - band + four triangles (the "chic" minimum)
    'v5b': dict(layout='grid10', band=(-2, 1), point=[(3, 1), (2, 1), (1, 1)], tip=0, post=0, gem_relief=0.5, gem_mid=-1,
                studs=[(-4, -3), (3, 4)], cap=(0.55, 1.0), orb=True, band_rows=(G1, G3, G5), point_shade='mid',
                no_posts=True),
    # v4 (camera r140a: the 2 px columns looked like fingers, the pearls like grey stone): a stepped triangle 6/4/2 in
    # the middle of every wall (the highest point), low corner posts (1 + pearl), warm pearls, brighter points
    'v4': dict(layout='grid10', band=(-2, 1), point=[(3, 1), (2, 1), (1, 1)], tip=0, post=1, gem_relief=0.5, gem_mid=-1,
               studs=[(-4, -3), (3, 4)], cap=(0.55, 1.0), orb=True, band_rows=(G1, G3, G4), bright_points=True,
               warm_pearls=True),
    'v4b': dict(layout='grid10', band=(-2, 1), point=[(3, 1), (2, 1), (1, 1)], tip=1, post=1, gem_relief=0.5, gem_mid=-1,
                studs=[(-4, -3), (3, 4)], cap=(0.55, 1.0), orb=True, band_rows=(G1, G3, G4), bright_points=True,
                warm_pearls=True),
    # v4c: v4 with more contrast (darker band bottom, normal point shading)
    'v4c': dict(layout='grid10', band=(-2, 1), point=[(3, 1), (2, 1), (1, 1)], tip=0, post=1, gem_relief=0.5, gem_mid=-1,
                studs=[(-4, -3), (3, 4)], cap=(0.55, 1.0), orb=True, band_rows=(G1, G3, G5), bright_points=False,
                warm_pearls=True),
    # v3: on the skin grid (10 px band), centre point 4/2/2 + pearl, corner posts 2 + pearls, 4x3 pixel jewels
    'v3': dict(layout='grid10', band=(-2, 1), point=[(2, 1), (1, 2)], tip=1, post=2, gem_relief=0.5, gem_mid=-1,
               studs=[(-4, -3), (3, 4)], cap=(0.55, 1.0), orb=True, band_rows=(G1, G3, G4)),
    # v3b: + small pearl teeth between, lower centre (4/2 + pearl)
    'v3b': dict(layout='grid10', band=(-2, 1), point=[(2, 1), (1, 1)], tip=1, post=2, gem_relief=0.5, gem_mid=-1,
                studs=[], cap=(0.55, 1.0), orb=True, teeth=[(-3, -2, 1), (2, 3, 1)], teeth_pearl=False,
                band_rows=(G1, G3, G5)),
    # v2: band 1 px outside the HEAD (= a vanilla helmet's fit, it covers the hat layer there), pixel-diamond jewels,
    # velvet flush with the band top (seen only from above), stepped point 5/3/1, corner posts + pearls
    'v2': dict(inner=4.0, outer=5.0, band=(-2, 1), point=[(2.5, 1), (1.5, 1), (0.5, 1)], tip=False, post=2,
               gem_y=(-1, 0), gem_w=1.5, gem_relief=0.5, gem_shape='diamond', studs=[(-3.5, -2.5), (2.5, 3.5)],
               stud_relief=0.25, cap=(0.55, 1.0), orb=1.0),
    # v2b: slimmer points (3/1 + pearl tip), taller corner posts
    'v2b': dict(inner=4.0, outer=5.0, band=(-2, 1), point=[(1.5, 1), (0.5, 1)], tip=True, post=3,
                gem_y=(-1, 0), gem_w=1.5, gem_relief=0.5, gem_shape='diamond', studs=[(-3.5, -2.5), (2.5, 3.5)],
                stud_relief=0.25, cap=(0.55, 1.0), orb=1.0, teeth=[(-3.5, -2.5, 1), (2.5, 3.5, 1)]),
    # v2c: band 2 rows + rim, wide low point 7/5/3/1
    'v2c': dict(inner=4.0, outer=5.0, band=(-2, 1), point=[(3.5, 1), (2.5, 1), (1.5, 1), (0.5, 1)], tip=False, post=1,
                gem_y=(-1, 0), gem_w=1.5, gem_relief=0.5, gem_shape='diamond', studs=[], cap=(0.55, 1.0), orb=1.0),
    # v1: 1 px thick band hugging the hat layer, three rows tall (top 2 rows of the head + 1 above), a stepped point
    # (5/3/1) in the middle of every wall, corner posts with pearls, a raised jewel in the band, velvet cap + orb
    'v1': dict(inner=4.5, outer=5.5, band=(-2, 1), point=[(2.5, 1), (1.5, 1), (0.5, 1)], tip=False, post=2,
               gem_y=(-1, 0), gem_w=1.5, gem_relief=0.5, studs=[(-4.0, -3.0), (3.0, 4.0)], cap=(0.6, 1.5), orb=1.0),
}


# ---------------------------------------------------------------- faces, texels, atlas

DIRS = ('north', 'south', 'west', 'east', 'up', 'down')


def face_corners(d, f, t):
    """(top-left, top-right, bottom-left) of a face seen from outside = how Minecraft lays the uv on it."""
    x0, y0, z0 = f
    x1, y1, z1 = t
    if d == 'north':
        return (x1, y1, z0), (x0, y1, z0), (x1, y0, z0)
    if d == 'south':
        return (x0, y1, z1), (x1, y1, z1), (x0, y0, z1)
    if d == 'west':
        return (x0, y1, z0), (x0, y1, z1), (x0, y0, z0)
    if d == 'east':
        return (x1, y1, z1), (x1, y1, z0), (x1, y0, z1)
    if d == 'up':
        return (x0, y1, z0), (x1, y1, z0), (x0, y1, z1)
    return (x0, y0, z1), (x1, y0, z1), (x0, y0, z0)


def face_size(d, f, t):
    tl, tr, bl = face_corners(d, f, t)
    w = math.dist(tl, tr)
    h = math.dist(tl, bl)
    return w, h


def covered(d, box, boxes):
    """True if the face d of box lies flat against another box (completely) - never visible."""
    f, t = box.f, box.t
    ax = {'north': 2, 'south': 2, 'west': 0, 'east': 0, 'up': 1, 'down': 1}[d]
    plane = (f if d in ('north', 'west', 'down') else t)[ax]
    o1, o2 = [a for a in range(3) if a != ax]
    for o in boxes:
        if o is box:
            continue
        other_plane = (o.t if d in ('north', 'west', 'down') else o.f)[ax]
        if abs(other_plane - plane) > 1e-6:
            continue
        if o.f[o1] <= f[o1] + 1e-6 and o.t[o1] >= t[o1] - 1e-6 and o.f[o2] <= f[o2] + 1e-6 and o.t[o2] >= t[o2] - 1e-6:
            return True
    return False


def perimeter(x, z, outer):
    """Position along the outside of the ring, clockwise seen from above, 0 .. 8*outer."""
    L = 2 * outer
    if z <= -outer + 1.01 and abs(x) <= outer + 0.01:   # north wall, left -> right seen from outside = +x -> -x
        return (outer - x)
    if x <= -outer + 1.01:                                 # west wall: -z -> +z
        return L + (z + outer)
    if z >= outer - 1.01:                                  # south: -x -> +x
        return 2 * L + (x + outer)
    return 3 * L + (outer - z)                              # east: +z -> -z


def texel(box, d, p, ij, n, v, frame, frames):
    """Colour of one texel. p = world centre (sp), ij = (column, row) on the face, n = (columns, rows)."""
    x, y, z = p
    i, j = ij
    nw, nh = n
    m = box.mat
    OUT = v['outer']
    if m in ('gold', 'gold_stud'):
        y0, y1 = v['band']
        if d == 'up':
            c = G1 if box.tag.startswith(('band', 'pt', 'post', 'tooth')) else G2
            if box.tag == 'knob':
                c = G0
            if box.tag == 'orb':
                c = G1
        elif d == 'down':
            c = G5
        elif box.tag.startswith('band'):
            row = int(math.floor(y1 - y))          # 0 = top row
            rows = v.get('band_rows', (G2, G3, G4, G4, G4))
            c = rows[min(row, len(rows) - 1)]
            if d in ('west', 'east') and box.tag[-1] in 'NS' or d in ('north', 'south') and box.tag[-1] in 'WE':
                c = G4 if row else G3              # end faces of the walls (the corners' sides)
        elif box.tag == 'post':
            c = G2 if i == 0 else G3
        elif box.tag == 'knob':
            c = G1
        elif box.tag.startswith('pt') or box.tag == 'tooth':
            if v.get('point_shade') == 'mid':
                c = G1 if (i == 0 or j == 0) else G2
                if i == nw - 1 and nw > 1:
                    c = G4
                if box.tag.startswith('pt') and nw == 2 and j == 0 and i == 0:
                    c = G0                         # a shine on the tip
            elif v.get('bright_points'):
                c = G1 if (i == 0 or j == 0) else G2
                if i == nw - 1 and nw > 1:
                    c = G3
            else:
                c = G2 if (i == 0 or j == 0) else G3
                if i == nw - 1 and nw > 1:
                    c = G4
        elif m == 'gold_stud':
            c = G1
        else:
            c = G3 if j else G2
        # the glint: a pixel streak running once around the crown
        if frame > 0 and m == 'gold':
            per = perimeter(x, z, OUT)
            ph = (frame - 1) / max(1, frames - 2) * (8 * OUT + 8) - 4
            k = per - ph + 0.7 * (y - y0)
            if 0 <= k < 1.0:
                c = GW
            elif 1.0 <= k < 2.0 or -1.0 <= k < 0:
                c = G0
        return c
    if m in ('cyan', 'red'):
        pal = (C0, C1, C2, C3, C4) if m == 'cyan' else (R0, R1, R2, R3, R4)
        if d == 'up':
            return pal[1]
        if d == 'down':
            return pal[4]
        if d in ('north', 'south', 'west', 'east') and box.tag.startswith('gemc'):
            c = (pal[1], pal[2], pal[3])[min(j, 2)] if nh >= 3 else pal[2]
            if j == 1 and nh >= 3:
                c = pal[0] if frame and frame % 9 in (4, 5) else pal[1]
            return c
        if d in ('north', 'south', 'west', 'east') and box.tag.startswith('geml'):
            return pal[1]
        if d in ('north', 'south', 'west', 'east') and box.tag.startswith('gemr'):
            return pal[3]
        if d in ('north', 'south', 'west', 'east') and nw >= 3 and (box.tag.startswith('gem')):
            c = pal[2]
            if i == 0:
                c = pal[1]
            if i == nw - 1:
                c = pal[3]
            if i == 1 and nw >= 3:
                c = pal[1] if frame == 0 or frame % 7 else pal[0]
            return c
        c = pal[2] if (i + j) % 2 == 0 else pal[1]
        if box.tag == 'orbgem' and frame and frame % 9 == 3:
            c = pal[0]
        return c
    if m == 'pearl':
        if v.get('warm_pearls'):
            if d == 'up':
                return W0
            return W2 if d == 'down' else W1
        if d == 'up':
            return P0
        if d == 'down':
            return P2
        return P1 if i == 0 else P2
    if m == 'velvet':
        if d != 'up':
            return V2
        IN = v['inner']
        e = max(abs(x), abs(z))
        if e > IN - 1:
            return V2
        if e > IN - 2:
            return V1
        return V0 if (abs(x) + abs(z)) < 2.5 else V1
    raise ValueError(m)


def build(variant, out_src, name='statue_crown'):
    boxes, v = design(variant)
    faces = []
    for bx in boxes:
        for d in DIRS:
            w, h = face_size(d, bx.f, bx.t)
            if w < 1e-6 or h < 1e-6 or covered(d, bx, boxes):
                continue
            nw, nh = max(1, int(math.ceil(w - 1e-6))), max(1, int(math.ceil(h - 1e-6)))
            faces.append((bx, d, nw, nh))
    # shelf packing
    W = 64
    order = sorted(range(len(faces)), key=lambda k: -faces[k][3])
    pos = {}
    x = y = shelf = 0
    for k in order:
        nw, nh = faces[k][2], faces[k][3]
        if x + nw > W:
            x = 0
            y += shelf
            shelf = 0
        pos[k] = (x, y)
        x += nw
        shelf = max(shelf, nh)
    Hh = y + shelf
    Hh = 1 << max(4, (Hh - 1).bit_length())
    frames = v.get('frames', 28)
    sheet = Image.new('RGBA', (W, Hh * frames), (0, 0, 0, 0))
    for fr in range(frames):
        for k, (bx, d, nw, nh) in enumerate(faces):
            tl, tr, bl = face_corners(d, bx.f, bx.t)
            ox, oy = pos[k]
            for j in range(nh):
                for i in range(nw):
                    fu, fv = (i + 0.5) / nw, (j + 0.5) / nh
                    p = tuple(tl[a] + (tr[a] - tl[a]) * fu + (bl[a] - tl[a]) * fv for a in range(3))
                    sheet.putpixel((ox + i, fr * Hh + oy + j), texel(bx, d, p, (i, j), (nw, nh), v, fr, frames))
    elements = []
    by_box = {}
    for k, (bx, d, nw, nh) in enumerate(faces):
        ox, oy = pos[k]
        uv = [round(ox * 16 / W, 4), round(oy * 16 / Hh, 4), round((ox + nw) * 16 / W, 4), round((oy + nh) * 16 / Hh, 4)]
        by_box.setdefault(id(bx), (bx, {}))[1][d] = {'uv': uv, 'texture': '#c'}
    for bx, fc in by_box.values():
        elements.append({'name': bx.tag, 'from': [round(8 + a, 4) for a in bx.f], 'to': [round(8 + a, 4) for a in bx.t],
                         'faces': fc})
    s = 0.9375
    model = {
        'textures': {'c': 'starkffa:item/' + name, 'particle': 'starkffa:item/' + name},
        'texture_size': [W, Hh],
        'elements': elements,
        'display': {
            'thirdperson_righthand': {'rotation': [0, 0, 0], 'translation': [0, 0, 0], 'scale': [s, s, s]},
            'thirdperson_lefthand': {'rotation': [0, 0, 0], 'translation': [0, 0, 0], 'scale': [s, s, s]},
            'head': {'rotation': [0, 0, 0], 'translation': [0, -2.4, 0], 'scale': [1.6, 1.6, 1.6]},
            'gui': {'rotation': [24, 45, 0], 'translation': [0, -2.5, 0], 'scale': [0.95, 0.95, 0.95]},
            'ground': {'rotation': [0, 0, 0], 'translation': [0, -1, 0], 'scale': [0.5, 0.5, 0.5]},
            'fixed': {'rotation': [0, 0, 0], 'translation': [0, -2, 0], 'scale': [1, 1, 1]},
        },
    }
    a = os.path.join(out_src, 'assets', 'starkffa')
    for sub in ('items', 'models/item', 'textures/item'):
        os.makedirs(os.path.join(a, sub), exist_ok=True)
    json.dump({'model': {'type': 'minecraft:model', 'model': 'starkffa:item/' + name}},
              open(os.path.join(a, 'items', name + '.json'), 'w'), separators=(',', ':'))
    json.dump(model, open(os.path.join(a, 'models', 'item', name + '.json'), 'w'), separators=(',', ':'))
    sheet.save(os.path.join(a, 'textures', 'item', name + '.png'))
    hold = v.get('hold', 70)
    meta = {'animation': {'width': W, 'height': Hh, 'interpolate': False,
                          'frames': [{'index': 0, 'time': hold}] + [{'index': f, 'time': 1} for f in range(1, frames)]}}
    json.dump(meta, open(os.path.join(a, 'textures', 'item', name + '.png.mcmeta'), 'w'), separators=(',', ':'))
    print(variant, 'boxes', len(boxes), 'faces', len(faces), 'atlas', W, 'x', Hh, 'frames', frames)
    return model


if __name__ == '__main__':
    build(sys.argv[1], sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else 'statue_crown')
