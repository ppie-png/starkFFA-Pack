"""Mockup renderer: STARK GUI backgrounds + tiles + vanilla item sprites + vanilla bitmap font text (with shadows)."""
import json, os, math
from PIL import Image
import fontw
INC = '/home/claude/ext/client263/assets/minecraft/font/include/default.json'
TEX = '/home/claude/ext/client263/assets/minecraft/textures/font/'
ITEMS = '/home/claude/ext/mcassets/data/26.1/items/'
BLOCKS = '/home/claude/ext/mcassets/data/26.1/blocks/'
P39 = '/tmp/claude-0/-home-claude/f196a605-ce72-5550-83a8-35be259707e7/scratchpad/p39'
SYMS = '⛃⛁✦✕✖▸➶➜♛⟳◌✱⇡▪'
_G = {}
def _load():
    sym = Image.open(P39 + '/assets/starkffa/textures/font/symbols.png').convert('RGBA')
    for i, c in enumerate(SYMS): _G[c] = (sym.crop((i * 8, 0, i * 8 + 8, 8)), 7, 8)
    d = json.load(open(INC))
    for p in d['providers']:
        if p.get('type') != 'bitmap': continue
        rows = p['chars']; im = Image.open(TEX + p['file'].split('/')[-1]).convert('RGBA')
        cw = im.width // len(rows[0]); ch = im.height // len(rows); h = p.get('height', 8); asc = p.get('ascent', 7)
        for r, row in enumerate(rows):
            for c, chx in enumerate(row):
                if chx in ('\u0000',) or chx in _G: continue
                g = im.crop((c * cw, r * ch, c * cw + cw, r * ch + ch))
                if h != ch: g = g.resize((max(1, round(cw * h / ch)), h), Image.NEAREST)
                _G[chx] = (g, asc, h)
_load()
def tint(g, col, a=255):
    out = Image.new('RGBA', g.size, (0, 0, 0, 0)); po = out.load(); pg = g.load()
    for y in range(g.height):
        for x in range(g.width):
            if pg[x, y][3] > 0:
                r, gg, b, aa = pg[x, y]
                po[x, y] = (r * col[0] // 255, gg * col[1] // 255, b * col[2] // 255, aa * a // 255)
    return out
def draw_text(img, x, y, runs, shadow=True, shadow_col=None):
    """runs: list of (text, (r,g,b), bold). y = top of the line (vanilla: glyph top = y + 7 - ascent)."""
    cx = x
    for text, col, bold in runs:
        for ch in text:
            if ch == ' ': cx += 4 + (0 if not bold else 0); continue
            g = _G.get(ch)
            if g is None: cx += 6; continue
            gi, asc, h = g
            top = y + 7 - asc
            sc = shadow_col if shadow_col is not None else tuple(v // 4 for v in col)
            for bx in ((0, 1) if bold else (0,)):
                if shadow: img.alpha_composite(tint(gi, sc), (cx + bx + 1, top + 1))
            for bx in ((0, 1) if bold else (0,)):
                img.alpha_composite(tint(gi, col), (cx + bx, top))
            cx += fontw.adv(ch, bold)
    return cx
def text_width(runs): return sum(fontw.width(t, b) for t, c, b in runs)
def gradient_runs(text, stops, bold=False):
    n = len(text); out = []
    for i, ch in enumerate(text):
        t = i / max(1, n - 1) * (len(stops) - 1); k = min(int(t), len(stops) - 2)
        a, b = stops[k], stops[k + 1]; f = t - k
        out.append((ch, tuple(int(a[j] + (b[j] - a[j]) * f) for j in range(3)), bold))
    return out
_icache = {}
def item_icon(name):
    if name in _icache: return _icache[name]
    p = ITEMS + name + '.png'
    if not os.path.exists(p):
        q = BLOCKS + name + '.png'
        if os.path.exists(q):
            im = Image.open(q).convert('RGBA').crop((0, 0, 16, 16))
            # fake isometric: shrink a bit
            im = im.resize((14, 14), Image.NEAREST); c = Image.new('RGBA', (16, 16), (0, 0, 0, 0)); c.alpha_composite(im, (1, 1)); im = c
        else:
            im = Image.new('RGBA', (16, 16), (255, 0, 255, 255))
    else:
        im = Image.open(p).convert('RGBA')
        if im.height > 16: im = im.crop((0, 0, 16, 16))
    _icache[name] = im
    return im
def slot_xy(s): return 8 + (s % 9) * 18, 18 + (s // 9) * 18
def hx(h): h = h.lstrip('#'); return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))
def tooltip(lines):
    """lines: list of run lists; vanilla tooltip box."""
    w = max(text_width(r) for r in lines) + 8; h = len(lines) * 10 + 6 + (2 if len(lines) > 1 else 0)
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0)); px = im.load()
    bg = (16, 0, 16, 240); b1 = (80, 0, 255, 80); b2 = (40, 0, 127, 80)
    for y in range(h):
        for x in range(w):
            if (x in (0, w - 1) and y in (0, h - 1)): continue
            px[x, y] = bg
    for x in range(1, w - 1):
        px[x, 1] = b1[:3] + (255,); px[x, h - 2] = b2[:3] + (255,)
    for y in range(1, h - 1):
        t = y / h; c = tuple(int(b1[i] + (b2[i] - b1[i]) * t) for i in range(3))
        px[1, y] = c + (255,); px[w - 2, y] = c + (255,)
    y = 3
    for i, r in enumerate(lines):
        draw_text(im, 4, y, r)
        y += 12 if i == 0 else 10
    return im
