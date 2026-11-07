"""STARK Hall of Fame sign (pack r37): extruded gold HALL OF FAME letters + crown + laurels + a red ribbon
"ALL-TIME KILLS" as ONE item model for an ItemDisplay (TitlesModule model mode).

Grid = half sign pixels (hp), canvas W x H, y up. Model space: x = -16 + U*hp, y = U*hp, z = Z0 + U*depth
(front = north = -z, depth grows backwards). Outputs under OUT/: models/item/fame_sign.json, items/fame_sign.json,
textures/item/fame/*.png (+ gold.png.mcmeta: shine sweep).
"""
import json
import math
import os
import sys

import numpy as np
from PIL import Image
from scipy import ndimage

W, H = 240, 80           # canvas in half sign pixels (hp)
U = 0.2                  # model units per hp (240 hp = 48 units = the full -16..32 model range)
Z0 = 7.0                 # model z of depth 0 (front face of the letters)
GT = 1                   # gold texture: texture px per hp
RT = 2                   # ribbon texture: texture px per hp
FONT = '/home/claude/ext/client263/assets/minecraft/textures/font/ascii.png'

GLYPHS = {   # 7 x 10 cells, each cell = 2 x 2 hp
    'H': ["##...##", "##...##", "##...##", "##...##", "#######", "#######", "##...##", "##...##", "##...##", "##...##"],
    'A': [".#####.", "##...##", "##...##", "##...##", "#######", "#######", "##...##", "##...##", "##...##", "##...##"],
    'L': ["##.....", "##.....", "##.....", "##.....", "##.....", "##.....", "##.....", "##.....", "#######", "#######"],
    'O': [".#####.", "##...##", "##...##", "##...##", "##...##", "##...##", "##...##", "##...##", "##...##", ".#####."],
    'F': ["#######", "#######", "##.....", "##.....", "######.", "######.", "##.....", "##.....", "##.....", "##....."],
    'M': ["##.....##", "###...###", "####.####", "##.###.##", "##..#..##", "##.....##", "##.....##", "##.....##",
          "##.....##", "##.....##"],
    'E': ["#######", "#######", "##.....", "##.....", "######.", "######.", "##.....", "##.....", "#######", "#######"],
}
CELL = 2
LETTER_Y = 27            # bottom of the letters (hp)
LETTER_H = 10 * CELL
WORDS = ["HALL", "OF", "FAME"]
GAP, WORD_GAP = 2, 12    # hp
RIB_Y0, RIB_Y1 = 6, 22
RIB_X0, RIB_X1 = 40, 200
DEPTH = {'letters': (0.0, 6.0), 'crown': (1.0, 5.0), 'laurel': (1.6, 5.2), 'outline': (3.0, 7.2),
         'band': (-1.2, 1.2), 'ends': (2.4, 4.4)}
OUTLINE = '#3A1A08'


def blank():
    return np.zeros((H, W), bool)      # [row from the bottom, col]


def round_corners(m):
    """Cut convex outer corners (1 hp) - the blocky letters get a polished bevelled silhouette."""
    out = m.copy()
    P = np.pad(m, 1)
    for y in range(H):
        for x in range(W):
            if not m[y, x]:
                continue
            up, dn, lf, rt = P[y + 2, x + 1], P[y, x + 1], P[y + 1, x], P[y + 1, x + 2]
            if (not up and not lf) or (not up and not rt) or (not dn and not lf) or (not dn and not rt):
                out[y, x] = False
    return out


def letters_mask():
    m = blank()
    widths = [sum(len(GLYPHS[c][0]) * CELL for c in w) + GAP * (len(w) - 1) for w in WORDS]
    total = sum(widths) + WORD_GAP * (len(WORDS) - 1)
    x = (W - total) // 2
    spans = []
    for wi, word in enumerate(WORDS):
        for ci, c in enumerate(word):
            g = GLYPHS[c]
            gw = len(g[0]) * CELL
            lm = blank()
            for r, row in enumerate(g):
                for k, ch in enumerate(row):
                    if ch == '#':
                        y = LETTER_Y + (len(g) - 1 - r) * CELL
                        lm[y:y + CELL, x + k * CELL:x + (k + 1) * CELL] = True
            m |= round_corners(lm)
            spans.append((c, x, x + gw))
            x += gw + (GAP if ci < len(word) - 1 else 0)
        x += WORD_GAP if wi < len(WORDS) - 1 else 0
    return m, spans


def draw(rows, x0, y_top):
    m = blank()
    for r, row in enumerate(rows):
        for k, ch in enumerate(row):
            if ch != '.':
                m[y_top - r, x0 + k] = True
    return m


def crown_mask(cx):
    """Five-spike crown on the middle of the sign: tipped with gem balls, a jewelled band, a rim.
    Returns (mask, gems [(x, y, kind)])."""
    yy, xx = np.mgrid[0:H, 0:W]
    base = 50                                    # bottom of the rim
    m = blank()
    m[base:base + 2, cx - 20:cx + 21] = True     # rim (41 wide)
    m[base + 2:base + 8, cx - 19:cx + 20] = True  # band
    top = base + 8
    spikes = [(-18, 9), (-9, 12), (0, 15), (9, 12), (18, 9)]   # (dx, height above the band)
    for dx, h in spikes:
        for y in range(top, top + h):
            f = (y - top) / h
            half = 4.6 * (1 - f) + 0.6
            x0, x1 = int(round(cx + dx - half)), int(round(cx + dx + half))
            m[y, max(0, x0):x1 + 1] = True
    # valleys between the spikes stay low: cut a shallow arc into the band top between spikes
    gems = []
    for dx, h in spikes:
        bx, by = cx + dx, top + h + 1
        disc = (xx - bx) ** 2 + (yy - by) ** 2 <= 2.3 ** 2
        m |= disc
        for (y, x) in zip(*np.nonzero(disc)):
            gems.append((x, y, 'ball'))
    # band jewels: cyan diamond in the middle, red ovals left/right
    for (y, x) in zip(*np.nonzero((np.abs(xx - cx) + np.abs(yy - (base + 5)) <= 2))):
        gems.append((x, y, 'cyan'))
    for gx in (cx - 10, cx + 10):
        for (y, x) in zip(*np.nonzero(((xx - gx) / 1.6) ** 2 + ((yy - (base + 5)) / 1.8) ** 2 <= 1.0)):
            gems.append((x, y, 'red'))
    return m, gems


def laurel(side):
    """One laurel branch: a stem curving up and outwards ('(' on the left), almond leaves pointing up the stem,
    alternating outside / inside, getting smaller towards the tip. Returns (mask, leaf list, stem points)."""
    yy, xx = np.mgrid[0:H, 0:W]
    m = blank()
    # stem as a quadratic bezier: bottom (near the ribbon end) -> far out -> top (towards the crown)
    P0, P1, P2 = np.array([34.0, 10.0]), np.array([-6.0, 30.0]), np.array([22.0, 70.0])
    pts = []
    for i in range(161):
        t = i / 160
        p = (1 - t) ** 2 * P0 + 2 * (1 - t) * t * P1 + t ** 2 * P2
        d = 2 * (1 - t) * (P1 - P0) + 2 * t * (P2 - P1)
        pts.append((p, d / np.linalg.norm(d), t))
    for p, d, t in pts:
        r = 1.25 - 0.45 * t
        m |= (xx + 0.5 - p[0]) ** 2 + (yy + 0.5 - p[1]) ** 2 <= r * r
    leaves = []
    nleaf = 8
    for j in range(nleaf):
        t = 0.06 + j * (0.86 / (nleaf - 1))
        p, d, _ = pts[int(t * 160)]
        nrm = np.array([-d[1], d[0]])            # left normal (outside for the left branch is -x side)
        if nrm[0] > 0:
            nrm = -nrm
        for k, sgn in enumerate((1, -1)):        # outside leaf, inside leaf (staggered)
            tt = min(0.97, t + (0.0 if sgn > 0 else 0.045))
            p2, d2, _ = pts[int(tt * 160)]
            dirv = d2 * 0.78 + nrm * 0.62 * sgn
            dirv /= np.linalg.norm(dirv)
            L = (10.0 - 3.6 * t) * (1.0 if sgn > 0 else 0.86)
            wid = 2.9 - 0.8 * t
            c = p2 + dirv * (L * 0.5 + 0.6)
            u = (xx + 0.5 - c[0]) * dirv[0] + (yy + 0.5 - c[1]) * dirv[1]
            v = -(xx + 0.5 - c[0]) * dirv[1] + (yy + 0.5 - c[1]) * dirv[0]
            # almond: pointed at both ends
            leaf = (np.abs(v) <= wid * np.clip(1 - (np.abs(u) / (L * 0.5)) ** 1.6, 0, 1)) & (np.abs(u) <= L * 0.5)
            m |= leaf
            leaves.append((c, dirv, L, wid, sgn))
    # tip leaf
    p, d, _ = pts[-1]
    c = p + d * 3.6
    u = (xx + 0.5 - c[0]) * d[0] + (yy + 0.5 - c[1]) * d[1]
    v = -(xx + 0.5 - c[0]) * d[1] + (yy + 0.5 - c[1]) * d[0]
    m |= (np.abs(v) <= 1.7 * np.clip(1 - (np.abs(u) / 3.6) ** 1.6, 0, 1)) & (np.abs(u) <= 3.6)
    if side == 'r':
        m = m[:, ::-1]
    return m


def ribbon_masks():
    band = blank()
    band[RIB_Y0:RIB_Y1, RIB_X0:RIB_X1] = True
    ends = blank()
    e = blank()
    ey0, ey1 = RIB_Y0 - 5, RIB_Y1 - 5
    for y in range(ey0, ey1):
        mid = (ey0 + ey1) / 2.0
        notch = 6 - abs((y + 0.5) - mid) * (6 / ((ey1 - ey0) / 2))
        for x in range(RIB_X0 - 24, RIB_X0 + 6):
            if x + 0.5 >= RIB_X0 - 24 + notch:
                e[y, x] = True
    ends = e | e[:, ::-1]
    return band, ends


# ------------------------------------------------------------------ geometry
def rects(mask):
    """Greedy meshing: maximal horizontal runs merged vertically -> [(x0, y0, x1, y1)] (x1/y1 exclusive)."""
    m = mask.copy()
    out = []
    for y in range(H):
        x = 0
        while x < W:
            if not m[y, x]:
                x += 1
                continue
            x1 = x
            while x1 < W and m[y, x1]:
                x1 += 1
            y1 = y + 1
            while y1 < H and m[y1, x:x1].all():
                y1 += 1
            m[y:y1, x:x1] = False
            out.append((x, y, x1, y1))
            x = x1
    return out


def mx(x):
    # the canvas reads left -> right when seen from the north (MC north face: u0 at the EAST edge), so canvas x
    # grows towards -x (west): canvas left = model x 32
    return round(32 - U * x, 4)


def my(y):
    return round(U * y, 4)


def mz(d):
    return round(Z0 + U * d, 4)


def uv_canvas(x0, y0, x1, y1):
    return [round(16 * x0 / W, 5), round(16 * (H - y1) / H, 5), round(16 * x1 / W, 5), round(16 * (H - y0) / H, 5)]


def element(r, d0, d1, front_tex, side_tex, back_tex, front_uv=None, mask=None):
    x0, y0, x1, y1 = r
    faces = {'north': {'uv': front_uv or uv_canvas(x0, y0, x1, y1), 'texture': front_tex},
             'south': {'uv': [0, 0, 16, 16], 'texture': back_tex}}

    def open_edge(cells):
        return mask is None or any(not (0 <= yy < H and 0 <= xx < W) or not mask[yy, xx] for yy, xx in cells)
    if open_edge([(y1, x) for x in range(x0, x1)]):
        faces['up'] = {'uv': [0, 0, 16, 4], 'texture': side_tex}
    if open_edge([(y0 - 1, x) for x in range(x0, x1)]):
        faces['down'] = {'uv': [0, 12, 16, 16], 'texture': side_tex}
    # canvas x0 edge = model east (max x), canvas x1 edge = model west
    if open_edge([(y, x0 - 1) for y in range(y0, y1)]):
        faces['east'] = {'uv': [0, 4, 16, 12], 'texture': side_tex}
    if open_edge([(y, x1) for y in range(y0, y1)]):
        faces['west'] = {'uv': [0, 4, 16, 12], 'texture': side_tex}
    return {'from': [mx(x1), my(y0), mz(d0)], 'to': [mx(x0), my(y1), mz(d1)], 'faces': faces}


def build():
    L, spans = letters_mask()
    C, gems = crown_mask(W // 2)
    LL, LR = laurel('l'), laurel('r')
    band, ends = ribbon_masks()
    gold = L | C | LL | LR
    outline = ndimage.binary_dilation(gold, structure=np.ones((5, 5), bool))      # 2 hp rim = 1 sign pixel
    outline = ndimage.binary_fill_holes(outline)
    els = []
    for r in rects(outline):
        els.append(element(r, *DEPTH['outline'], '#dark', '#dark', '#dark', front_uv=[0, 0, 16, 16], mask=outline))
    for r in rects(L):
        els.append(element(r, *DEPTH['letters'], '#gold', '#side', '#dark', mask=L))
    for r in rects(C):
        els.append(element(r, *DEPTH['crown'], '#gold', '#side', '#dark', mask=C))
    for m in (LL, LR):
        for r in rects(m):
            els.append(element(r, *DEPTH['laurel'], '#gold', '#side', '#dark', mask=m))
    for r in rects(ends):
        els.append(element(r, *DEPTH['ends'], '#ribbon_end', '#ribbon_side', '#ribbon_side', mask=ends))
    els.append(element((RIB_X0, RIB_Y0, RIB_X1, RIB_Y1), *DEPTH['band'], '#ribbon', '#ribbon_side', '#ribbon_side',
                       front_uv=[0, 0, 16, 16], mask=band))
    return dict(L=L, C=C, gems=gems, LL=LL, LR=LR, band=band, ends=ends, gold=gold, outline=outline, spans=spans), els


# ------------------------------------------------------------------ textures
def mix(a, b, t):
    t = max(0.0, min(1.0, t))
    return tuple(int(round(a[i] + (b[i] - a[i]) * t)) for i in range(3))


def hexc(h):
    h = h.lstrip('#')
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


GOLD_STOPS = [(0.0, hexc('#A85310')), (0.30, hexc('#E88A22')), (0.58, hexc('#FFB547')), (0.82, hexc('#FFDD8A')),
              (1.0, hexc('#FFF4D2'))]


def grad(t, stops=GOLD_STOPS):
    t = max(0.0, min(1.0, t))
    for (t0, c0), (t1, c1) in zip(stops, stops[1:]):
        if t <= t1:
            return mix(c0, c1, (t - t0) / (t1 - t0))
    return stops[-1][1]


def hash01(x, y, k=0):
    v = (x * 73856093) ^ (y * 19349663) ^ (k * 83492791)
    return ((v * 2654435761) & 0xFFFFFFFF) / 0xFFFFFFFF


def gold_frame(D, shine=None):
    """One frame of the gold front texture (W x H px). shine = band centre x in px (None = idle)."""
    img = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    px = img.load()
    gold = D['gold']
    parts = [(D['L'], LETTER_Y, LETTER_Y + LETTER_H), (D['C'], 50, 78), (D['LL'], 4, 76), (D['LR'], 4, 76)]
    part_of = np.full((H, W), -1)
    for i, (m, _, _) in enumerate(parts):
        part_of[m] = i
    gem_at = {(gx, gy): kind for gx, gy, kind in D['gems']}
    for row in range(H):
        ty = H - 1 - row
        for x in range(W):
            if not gold[row, x]:
                continue
            pi = part_of[row, x]
            _, y0, y1 = parts[pi]
            t = (row + 0.5 - y0) / (y1 - y0)
            c = grad(t)
            if pi >= 2:
                c = mix(c, (170, 132, 36), 0.25)
            up = row + 1 < H and gold[row + 1, x]
            dn = row - 1 >= 0 and gold[row - 1, x]
            lf = x - 1 >= 0 and gold[row, x - 1]
            rt = x + 1 < W and gold[row, x + 1]
            if not up:
                c = mix(c, (255, 253, 240), 0.7)
            elif not dn:
                c = mix(c, (110, 48, 8), 0.5)
            elif not lf:
                c = mix(c, (255, 246, 214), 0.3)
            elif not rt:
                c = mix(c, (140, 70, 14), 0.3)
            n = (hash01(x, row) - 0.5) * 0.05
            c = tuple(max(0, min(255, int(v * (1 + n)))) for v in c)
            kind = gem_at.get((x, row))
            if kind == 'ball':
                c = mix(c, (255, 250, 228), 0.55)
            elif kind in ('cyan', 'red'):
                gc = hexc('#3FE0FF') if kind == 'cyan' else hexc('#FF4D5E')
                above = gem_at.get((x, row + 1)) == kind
                below = gem_at.get((x, row - 1)) == kind
                c = mix(gc, (255, 255, 255), 0.6) if not above else (mix(gc, (20, 30, 60), 0.35) if not below else gc)
            if shine is not None:
                dist = abs((x - shine) + (row - H / 2) * 0.6)
                if dist < 10:
                    c = mix(c, (255, 255, 250), 0.8 * (1 - dist / 10) ** 1.5)
            px[x, ty] = c + (255,)
    return img


def solid(c, size=16, grad_to=None):
    img = Image.new('RGBA', (size, size), c + (255,))
    if grad_to:
        px = img.load()
        for y in range(size):
            cc = mix(c, grad_to, y / (size - 1))
            for x in range(size):
                px[x, y] = cc + (255,)
    return img


def font_glyphs():
    im = Image.open(FONT).convert('RGBA')
    px = im.load()

    def g(ch):
        c = ord(ch)
        gx, gy = (c % 16) * 8, (c // 16) * 8
        cells = [[px[gx + x, gy + y][3] > 0 for x in range(8)] for y in range(8)]
        w = max([x + 1 for y in range(8) for x in range(8) if cells[y][x]] or [3])
        return cells, w
    return g


def ribbon_texture(text='ALL-TIME KILLS', S=3):
    bw, bh = (RIB_X1 - RIB_X0) * RT, (RIB_Y1 - RIB_Y0) * RT
    img = Image.new('RGBA', (bw, bh), (0, 0, 0, 0))
    px = img.load()
    top, mid, bot = hexc('#FF8591'), hexc('#FF4D5E'), hexc('#C0283B')
    for y in range(bh):
        t = y / (bh - 1)
        c = mix(top, mid, t / 0.4) if t < 0.4 else mix(mid, bot, (t - 0.4) / 0.6)
        for x in range(bw):
            cc = c
            if y < 3:
                cc = mix(hexc('#FFE3A0'), hexc('#FFB547'), y / 3)
            elif y >= bh - 3:
                cc = mix(hexc('#C9781E'), hexc('#7A3A0A'), (y - (bh - 3)) / 3)
            n = (hash01(x, y, 3) - 0.5) * 0.04
            px[x, y] = tuple(max(0, min(255, int(v * (1 + n)))) for v in cc) + (255,)
    g = font_glyphs()
    glyphs = [g(ch) if ch != ' ' else (None, 3) for ch in text]
    width = sum((w + 1) * S for _, w in glyphs) - S
    x = (bw - width) // 2
    y0 = (bh - 7 * S) // 2 + 1
    ink, shadow = (255, 249, 238), (120, 16, 32)
    for pass_ in (0, 1):
        xx0 = x
        for cells, w in glyphs:
            if cells is not None:
                for yy in range(7):
                    for xx in range(w):
                        if cells[yy][xx]:
                            for a in range(S):
                                for b in range(S):
                                    X, Y = xx0 + xx * S + a, y0 + yy * S + b
                                    if pass_ == 0:
                                        px[X + 2, Y + 2] = shadow + (255,)
                                    else:
                                        px[X, Y] = ink + (255,)
            xx0 += (w + 1) * S
    for cxd in (16, bw - 17):
        for dy in range(-7, 8):
            for dx in range(-7, 8):
                d = abs(dx) + abs(dy)
                if d <= 7:
                    px[cxd + dx, bh // 2 + dy] = ((255, 240, 196) if d <= 3 else (255, 190, 80)) + (255,)
    return img


def write_pack(D, els, out, frames=16):
    tdir = os.path.join(out, 'assets/starkffa/textures/item/fame')
    os.makedirs(tdir, exist_ok=True)
    sheet = Image.new('RGBA', (W, H * frames))
    sheet.paste(gold_frame(D), (0, 0))
    for f in range(1, frames):
        sx = -40 + (f - 1) * (W + 80) / (frames - 2)
        sheet.paste(gold_frame(D, shine=sx), (0, H * f))
    sheet.save(os.path.join(tdir, 'gold.png'))
    seq = [{'index': 0, 'time': 80}] + [{'index': f, 'time': 2} for f in range(1, frames)]
    json.dump({'animation': {'width': W, 'height': H, 'frames': seq}}, open(os.path.join(tdir, 'gold.png.mcmeta'), 'w'))
    solid(hexc('#D2841F'), grad_to=hexc('#7C3A08')).save(os.path.join(tdir, 'side.png'))
    solid(hexc(OUTLINE)).save(os.path.join(tdir, 'dark.png'))
    ribbon_texture().save(os.path.join(tdir, 'ribbon.png'))
    solid(hexc('#B32638'), grad_to=hexc('#741020')).save(os.path.join(tdir, 'ribbon_side.png'))
    end = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    ep = end.load()
    for row in range(H):
        for x in range(W):
            if D['ends'][row, x]:
                t = (row - (RIB_Y0 - 5)) / (RIB_Y1 - RIB_Y0)
                ep[x, H - 1 - row] = mix(hexc('#86182A'), hexc('#CC3548'), t) + (255,)
    end.save(os.path.join(tdir, 'ribbon_end.png'))
    model = {
        'textures': {'particle': 'starkffa:item/fame/side', 'gold': 'starkffa:item/fame/gold', 'side': 'starkffa:item/fame/side',
                     'dark': 'starkffa:item/fame/dark', 'ribbon': 'starkffa:item/fame/ribbon',
                     'ribbon_side': 'starkffa:item/fame/ribbon_side', 'ribbon_end': 'starkffa:item/fame/ribbon_end'},
        'elements': els,
        'display': {'fixed': {'rotation': [0, 0, 0], 'translation': [0, 0, 0], 'scale': [1, 1, 1]}},
    }
    mdir = os.path.join(out, 'assets/starkffa/models/item')
    os.makedirs(mdir, exist_ok=True)
    json.dump(model, open(os.path.join(mdir, 'fame_sign.json'), 'w'), separators=(',', ':'))
    idir = os.path.join(out, 'assets/starkffa/items')
    os.makedirs(idir, exist_ok=True)
    json.dump({'model': {'type': 'minecraft:model', 'model': 'starkffa:item/fame_sign'}}, open(os.path.join(idir, 'fame_sign.json'), 'w'))
    return model


def preview2d(D, path, scale=3, frame=None):
    """Flat front view with the real textures (layout check)."""
    img = Image.new('RGBA', (W, H), (120, 170, 220, 255))
    o = np.zeros((H, W), bool)
    o[:] = D['outline']
    dark = hexc(OUTLINE)
    px = img.load()
    for row in range(H):
        for x in range(W):
            if o[row, x]:
                px[x, H - 1 - row] = dark + (255,)
    tdir = '/home/claude/fame/out/assets/starkffa/textures/item/fame/'
    ends = Image.open(tdir + 'ribbon_end.png')
    img.alpha_composite(ends)
    goldsheet = Image.open(tdir + 'gold.png')
    f = 0 if frame is None else frame
    img.alpha_composite(goldsheet.crop((0, H * f, W, H * (f + 1))))
    rib = Image.open(tdir + 'ribbon.png').resize((RIB_X1 - RIB_X0, RIB_Y1 - RIB_Y0), Image.LANCZOS)
    img.alpha_composite(rib, (RIB_X0, H - RIB_Y1))
    img.resize((W * scale, H * scale), Image.NEAREST).save(path)


if __name__ == '__main__':
    out = sys.argv[1] if len(sys.argv) > 1 else '/home/claude/fame/out'
    D, els = build()
    write_pack(D, els, out)
    preview2d(D, '/home/claude/fame/layout.png')
    preview2d(D, '/home/claude/fame/layout_shine.png', frame=7)
    nf = sum(len(e['faces']) for e in els)
    print('elements', len(els), 'faces', nf, 'letters x', D['spans'][0][1], D['spans'][-1][2])
