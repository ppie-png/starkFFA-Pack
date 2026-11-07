"""Gem Shop art for pack r40: open backgrounds (5/6 rows), rarity tiles, state badges, HUD label fonts.
Writes into OUT (a copy of the pack tree) and returns the provider list for starkffa:gui."""
import json, os, math, sys
from PIL import Image

P39 = '/tmp/claude-0/-home-claude/f196a605-ce72-5550-83a8-35be259707e7/scratchpad/p39'
SHOP = 'assets/starkffa/textures/font/gui/shop'

def hx(h):
    h = h.lstrip('#'); return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))
def mix(a, b, t): return tuple(int(round(a[i] + (b[i] - a[i]) * t)) for i in range(3))
WHITE, BLACK = (255, 255, 255), (0, 0, 0)
DARK = hx('#0D1016'); PANEL = hx('#161B24'); CELLB = hx('#212834'); FRAME = hx('#343E4E')
GEM = hx('#F47FFF'); GEM2 = hx('#AC74FF')

# tile kinds: id, main colour, (optional inner ring)
KINDS = [
    ('common', '#8A96A8', None),
    ('rare', '#3FC2FF', None),
    ('epic', '#B266FF', None),
    ('legendary', '#FFAA33', None),
    ('mythic', '#FF4D6D', '#FFC94D'),
    ('exclusive', '#4DFFA0', None),
    ('gem', '#F47FFF', None),
]
TILE_BASE, BADGE_BASE = 0xE2A0, 0xE2E0          # + kind*6 + row / + badge*6 + row
BADGES = ['owned', 'equipped', 'sale']
BG5, BG6, BG6T = 0xE290, 0xE291, 0xE292
TIER_COLORS = ['#8A96A8', '#3FC2FF', '#B266FF', '#FFAA33', '#FF4D6D']

def tile(color, ring=None):
    c = hx(color)
    im = Image.new('RGBA', (18, 18), (0, 0, 0, 0)); px = im.load()
    for y in range(18):
        for x in range(18):
            corner = (x in (0, 17)) and (y in (0, 17))
            if corner: continue
            edge = x in (0, 17) or y in (0, 17)
            if edge:
                if y == 0: col = mix(c, WHITE, 0.22)
                elif y == 17: col = mix(c, BLACK, 0.35)
                else: col = mix(mix(c, WHITE, 0.22), mix(c, BLACK, 0.35), y / 17)
                px[x, y] = col + (255,)
                continue
            # inner: vertical gradient + soft centre glow
            t = (y - 1) / 15
            col = mix(mix(DARK, c, 0.48), mix(DARK, c, 0.20), t)
            d = math.hypot(x - 8.5, y - 7.5) / 9.0
            col = mix(col, mix(DARK, c, 0.72), max(0.0, 1.0 - d) * 0.6)
            if y == 1: col = mix(col, WHITE, 0.10)
            px[x, y] = col + (255,)
    if ring:
        r = hx(ring)
        for i in range(1, 17):
            for (x, y) in ((i, 1), (i, 16), (1, i), (16, i)):
                if (x in (1, 16)) and (y in (1, 16)): continue
                px[x, y] = mix(px[x, y][:3], r, 0.75) + (255,)
    return im

def badge(kind):
    im = Image.new('RGBA', (18, 18), (0, 0, 0, 0)); px = im.load()
    if kind == 'owned':
        # green check in the top-right corner, dark outline
        g = hx('#5CFF9D'); o = (8, 12, 16)
        pts = [(12, 4), (13, 5), (14, 4), (15, 3), (16, 2)]
        thick = set()
        for (x, y) in pts:
            thick.add((x, y)); thick.add((x, y + 1))
        for (x, y) in list(thick):
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    q = (x + dx, y + dy)
                    if q not in thick and 0 <= q[0] < 18 and 0 <= q[1] < 18: px[q] = o + (255,)
        for q in thick: px[q] = g + (255,)
    elif kind == 'equipped':
        w = (255, 255, 255)
        for i in range(18):
            for (x, y) in ((i, 0), (i, 17), (0, i), (17, i)):
                if (x in (0, 17)) and (y in (0, 17)): continue
                px[x, y] = w + (255,)
        for i in range(1, 17):
            for (x, y) in ((i, 1), (i, 16), (1, i), (16, i)):
                if (x in (1, 16)) and (y in (1, 16)): continue
                px[x, y] = w + (110,)
    elif kind == 'sale':
        r = hx('#FF4D5E'); hi = hx('#FFB547')
        for y in range(0, 7):
            for x in range(0, 7 - y):
                if (x, y) == (0, 0): continue
                px[x, y] = (mix(r, hi, 0.0 if x + y > 2 else 0.35)) + (255,)
        for (x, y) in ((1, 1), (2, 1), (1, 2)):
            px[x, y] = (255, 236, 200, 255)
    # every tile/badge glyph is 18 px wide (advance 19, the Java side relies on it)
    if im.getpixel((17, 9))[3] == 0:
        im.putpixel((17, 9), (0, 0, 0, 1))
    return im

def recolor_accent(im):
    """cyan accent pixels of the plain STARK background -> gem pink"""
    cy = hx('#3FE0FF'); px = im.load()
    for y in range(im.height):
        for x in range(im.width):
            r, g, b, a = px[x, y]
            if a == 0: continue
            col = (r, g, b)
            if col in (DARK, PANEL, CELLB, FRAME): continue
            # project on the CELLB -> CYAN line
            num = sum((col[i] - CELLB[i]) * (cy[i] - CELLB[i]) for i in range(3))
            den = sum((cy[i] - CELLB[i]) ** 2 for i in range(3))
            t = max(0.0, min(1.0, num / den))
            back = mix(CELLB, cy, t)
            if sum(abs(back[i] - col[i]) for i in range(3)) > 24: continue
            px[x, y] = mix(CELLB, GEM, t) + (a,)
    return im

def background(rows):
    src = Image.open(f'{P39}/assets/starkffa/textures/font/gui/chest{rows}_cyan.png').convert('RGBA')
    im = recolor_accent(src.copy()); px = im.load()
    y0, y1 = 17, 17 + rows * 18
    for y in range(y0, y1 + 1):
        for x in range(7, 169):
            px[x, y] = PANEL + (250,)
    # soft gem glow in the open panel (very faint) + a faint lower edge line
    cx, cy = 88, (y0 + y1) / 2
    for y in range(y0, y1 + 1):
        for x in range(7, 169):
            d = math.hypot((x - cx) / 82.0, (y - cy) / (rows * 11.0))
            k = max(0.0, 1.0 - d) ** 1.6 * 0.07
            px[x, y] = mix(PANEL, GEM2, k) + (250,)
    return im

def tier_background():
    im = background(6); px = im.load()
    for i, col in enumerate(TIER_COLORS):
        c = hx(col); r = i + 1
        y0, y1 = 17 + 18 * r, 17 + 18 * r + 17
        for y in range(y0, y1 + 1):
            for x in range(7, 169):
                p = px[x, y]
                fade = 1.0 - abs((x - 88) / 81.0) ** 2 * 0.6
                px[x, y] = mix(p[:3], c, 0.055 * fade) + (p[3],)
        # tier marker in the left margin (x 2..4)
        for y in range(y0 + 2, y1 - 1):
            for x in range(2, 5):
                px[x, y] = mix(c, WHITE, 0.15 if x == 2 else 0.0) + (255,)
    return im

def write(out):
    d = os.path.join(out, SHOP); os.makedirs(d, exist_ok=True)
    prov = []
    for rows, ch in ((5, BG5), (6, BG6)):
        background(rows).save(os.path.join(d, f'bg{rows}.png'))
        prov.append({'type': 'bitmap', 'file': f'starkffa:font/gui/shop/bg{rows}.png', 'ascent': 13,
                     'height': 114 + rows * 18 if rows != 5 else 204, 'chars': [chr(ch)]})
    prov[1]['height'] = 222
    tier_background().save(os.path.join(d, 'bg6t.png'))
    prov.append({'type': 'bitmap', 'file': 'starkffa:font/gui/shop/bg6t.png', 'ascent': 13, 'height': 222, 'chars': [chr(BG6T)]})
    for k, (kid, col, ring) in enumerate(KINDS):
        tile(col, ring).save(os.path.join(d, f'tile_{kid}.png'))
        for r in range(6):
            prov.append({'type': 'bitmap', 'file': f'starkffa:font/gui/shop/tile_{kid}.png', 'ascent': -4 - 18 * r,
                         'height': 18, 'chars': [chr(TILE_BASE + k * 6 + r)]})
    for b, bid in enumerate(BADGES):
        badge(bid).save(os.path.join(d, f'badge_{bid}.png'))
        for r in range(6):
            prov.append({'type': 'bitmap', 'file': f'starkffa:font/gui/shop/badge_{bid}.png', 'ascent': -4 - 18 * r,
                         'height': 18, 'chars': [chr(BADGE_BASE + b * 6 + r)]})
    return prov

# HUD label fonts: the vanilla ascii + nonlatin_european sheets moved down to a GUI row (text top = 13 - ascent)
LABEL_FONTS = {('shop_r%d' % r): 23 + 18 * r for r in range(6)}
def label_fonts(out):
    inc = json.load(open('/home/claude/ext/client263/assets/minecraft/font/include/default.json'))
    for name, top in LABEL_FONTS.items():
        provs = [{'type': 'space', 'advances': {' ': 4}},
                 {'type': 'bitmap', 'file': 'starkffa:font/symbols.png', 'ascent': 13 - top, 'height': 8,
                  'chars': ['\u26c3\u26c1\u2726\u2715\u2716\u25b8\u27b6\u279c\u265b\u27f3\u25cc\u2731\u21e1\u25aa'], 'filter': {'uniform': False}},
                 {'type': 'bitmap', 'file': 'starkffa:font/icons8.png', 'ascent': 13 - top, 'height': 8,
                  'chars': [''.join(chr(0xE000 + i) for i in range(13))]}]
        for p in inc['providers']:
            if p.get('type') != 'bitmap' or 'accented' in p['file']: continue
            q = dict(p); q['ascent'] = 13 - top
            q.setdefault('height', 8)
            provs.append(q)
        os.makedirs(os.path.join(out, 'assets/starkffa/font'), exist_ok=True)
        json.dump({'providers': provs}, open(os.path.join(out, 'assets/starkffa/font', name + '.json'), 'w'), ensure_ascii=False)

if __name__ == '__main__':
    out = sys.argv[1] if len(sys.argv) > 1 else '/home/claude/gemshop/art/out'
    prov = write(out); label_fonts(out)
    json.dump(prov, open(os.path.join(out, 'gui_providers.json'), 'w'), ensure_ascii=False, indent=1)
    print(len(prov), 'providers')
