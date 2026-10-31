"""Weapons W4-W9: handheld blade sprites (32x32, drawn by code), 3D cuboid models, HUD icons."""
import math
from PIL import Image

def hx(s, a=255):
    s = s.lstrip("#"); return (int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16), a)
def mix(a, b, t): return tuple(int(round(a[i] + (b[i] - a[i]) * t)) for i in range(4))

# ------------------------------------------------------------------ blade sprites
# Item lies on the diagonal like vanilla swords: handle bottom-left -> tip top-right.
def blade_sprite(parts, size=32, start=(3.5, 28.5), end=(28.5, 3.5), curve=0.0, glow=None):
    """parts: list of (t0, t1, halfwidth(t), colour(t, d_norm, side), is_blade) along the item axis.
    curve bends the axis sideways (katana). glow: (colour, px) soft halo around blade parts."""
    im = Image.new("RGBA", (size, size), (0, 0, 0, 0)); px = im.load()
    ax, ay = end[0] - start[0], end[1] - start[1]; L = math.hypot(ax, ay)
    ux, uy = ax / L, ay / L; nx, ny = -uy, ux
    def sample(x, y):
        qx, qy = x - start[0], y - start[1]
        t = (qx * ux + qy * uy) / L
        d = qx * nx + qy * ny - curve * L * 0.12 * 4 * t * (1 - t)
        halo = 0.0
        for (t0, t1, hw, col, is_blade) in parts:
            if t0 <= t <= t1:
                tt = (t - t0) / (t1 - t0); w = hw(tt)
                if abs(d) <= w:
                    return col(tt, d / max(w, .01), 1 if d > 0 else -1), 0.0
                if glow and is_blade and abs(d) <= w + glow[1]:
                    halo = max(halo, 1 - (abs(d) - w) / glow[1])
        return None, halo
    for y in range(size):
        for x in range(size):
            col, halo = sample(x + .5, y + .5)
            if col is None:   # supersample edges a little
                for sx, sy in ((.25, .25), (.75, .25), (.25, .75), (.75, .75)):
                    c2, h2 = sample(x + sx, y + sy)
                    if c2 is not None: col = c2; break
                    halo = max(halo, h2)
            if col is not None: px[x, y] = col
            elif halo > 0: c = glow[0]; px[x, y] = c[:3] + (int(c[3] * halo * .7),)
    return im

def soul_blade(lit=False):
    edge, body, spine, rune = hx("#E9FFF9"), hx("#9FE8D6"), hx("#3F9C88"), hx("#7FFFD4")
    if lit: edge, body, spine = hx("#FFFFFF"), hx("#C9FFF2"), hx("#5FD3B8")
    def blade(t, d, s):
        if abs(d) > .72: return edge
        if abs(d) < .22:
            return rune if (int(t * 9) % 2 == 0 and .1 < t < .85) else spine
        return body
    parts = [
        (0.00, 0.06, lambda t: 1.9, lambda t, d, s: hx("#5FD3B8") if abs(d) < .5 else hx("#2B3A3A"), False),   # pommel gem
        (0.06, 0.24, lambda t: 1.15, lambda t, d, s: hx("#3A4A4A") if int(t * 8) % 2 else hx("#1C1F26"), False),  # wrapped grip
        (0.24, 0.29, lambda t: 4.6, lambda t, d, s: hx("#7FFFD4") if abs(d) < .18 else hx("#2B3A3A") if abs(d) < .8 else hx("#4FB8A0"), False),  # guard
        (0.29, 0.99, lambda t: 2.3 * (1 - t) ** .55 + .35, blade, True),
    ]
    return blade_sprite(parts, glow=(hx("#7FFFD4", 200), 1.6) if lit else None)

def shadow_dagger():
    def blade(t, d, s):
        if s > 0 and abs(d) > .55: return hx("#B48CFF")          # plum cutting edge on one side
        return hx("#2A2236") if abs(d) > .2 else hx("#16121E")
    parts = [
        (0.00, 0.05, lambda t: 1.6, lambda t, d, s: hx("#B48CFF"), False),
        (0.05, 0.22, lambda t: 1.1, lambda t, d, s: hx("#2A2236") if int(t * 7) % 2 else hx("#0E0B14"), False),
        (0.22, 0.26, lambda t: 3.4, lambda t, d, s: hx("#6E4FB0") if abs(d) > .6 else hx("#1E1830"), False),
        (0.26, 0.66, lambda t: 2.6 * (1 - t) ** .7 + .3, blade, True),
    ]
    return blade_sprite(parts, start=(6.5, 25.5), end=(28.5, 3.5), glow=(hx("#B48CFF", 160), 1.0))

def blink_blade():
    def blade(t, d, s):
        facet = (int((t * 14) + (1 if d > 0 else 0)) % 2 == 0)
        if abs(d) > .7: return hx("#FFFFFF", 235)
        return hx("#BFEFFF", 215) if facet else hx("#E8F7FF", 200)
    parts = [
        (0.00, 0.04, lambda t: 1.3, lambda t, d, s: hx("#7FD8FF"), False),
        (0.04, 0.26, lambda t: 1.15, lambda t, d, s: hx("#F2F6FA") if (int(t * 12) % 2 == 0 and abs(d) < .5) else hx("#101318"), False),
        (0.26, 0.30, lambda t: 2.8, lambda t, d, s: hx("#2A3340") if abs(d) > .5 else hx("#7FD8FF"), False),   # round tsuba
        (0.30, 0.99, lambda t: 1.55 * (1 - t) ** .35 + .2, blade, True),
    ]
    return blade_sprite(parts, curve=1.0, glow=(hx("#BFEFFF", 150), 1.2))

# ------------------------------------------------------------------ cuboid models
ARSENAL_SWATCH = [
    "#2E3440", "#E8B23A", "#7DF9FF", "#FFF27A",   # 0 dark steel, 1 gold, 2 electric blue, 3 electric yellow
    "#9FD3F5", "#5FA8E8", "#7A8796", "#5B6B7A",   # 4 packed ice, 5 blue ice, 6 steel band, 7 frosted handle
    "#E8F8FF", "#F4F1E6", "#B07D1E", "#FFE08A",   # 8 frost white, 9 shield white, 10 dark gold, 11 rune glow
    "#1B2330", "#3A7BD5", "#C8D3DF", "#FFFFFF",   # 12 deep steel, 13 deep blue, 14 light steel, 15 white
]
def arsenal_atlas():
    im = Image.new("RGBA", (16, 16), (0, 0, 0, 0)); px = im.load()
    import random; rng = random.Random(11)
    for i, c in enumerate(ARSENAL_SWATCH):
        base = hx(c); sx, sy = (i % 4) * 4, (i // 4) * 4
        for y in range(4):
            for x in range(4):
                k = (1.1 if y == 0 else .88 if y == 3 else 1.0) * (1 + (rng.random() - .5) * .07)
                px[sx + x, sy + y] = tuple(min(255, int(v * k)) for v in base[:3]) + (255,)
    return im

def el(frm, to, sw, tex="a", rot=None, faces=None, emissive=False):
    sx, sy = (sw % 4) * 4, (sw // 4) * 4
    uv = [sx + .5, sy + .5, sx + 3.5, sy + 3.5]
    f = {k: {"uv": uv, "texture": "#" + tex} for k in ("north", "east", "south", "west", "up", "down")}
    if faces: f.update(faces)
    e = {"from": frm, "to": to, "faces": f}
    if rot: e["rotation"] = rot
    if emissive: e["light_emission"] = 12
    return e

DIAG = {"angle": -45, "axis": "z", "origin": [8, 8, 8]}     # vertical model -> sword-like diagonal

def spear():
    E = [
        el([7.4, -6, 7.4], [8.6, 16, 8.6], 12, rot=DIAG),                 # shaft
        el([7.2, -6.5, 7.2], [8.8, -5, 8.8], 1, rot=DIAG),                # butt cap
        el([7.1, 2, 7.1], [8.9, 3.2, 8.9], 1, rot=DIAG),                  # gold band
        el([7.1, 9.5, 7.1], [8.9, 10.7, 8.9], 1, rot=DIAG),               # gold band
        el([7.0, 15.5, 7.0], [9.0, 17, 9.0], 10, rot=DIAG),               # socket
        # zig-zag electric tip
        el([6.6, 17, 7.6], [9.4, 18.6, 8.4], 2, rot=DIAG, emissive=True),
        el([7.2, 18.6, 7.6], [10.0, 20.2, 8.4], 2, rot=DIAG, emissive=True),
        el([6.4, 20.2, 7.6], [9.2, 21.8, 8.4], 2, rot=DIAG, emissive=True),
        el([7.3, 21.8, 7.7], [8.7, 24.0, 8.3], 3, rot=DIAG, emissive=True),
    ]
    return E

def hammer():
    E = [
        el([7.3, -3, 7.3], [8.7, 12, 8.7], 7, rot=DIAG),                  # frosted handle
        el([7.0, -3.6, 7.0], [9.0, -2.4, 9.0], 6, rot=DIAG),              # pommel
        el([7.1, 1, 7.1], [8.9, 2, 8.9], 6, rot=DIAG),                    # grip band
        el([3.0, 12, 5.0], [13.0, 17.5, 11.0], 4, rot=DIAG),              # packed-ice head
        el([2.4, 12.6, 4.4], [3.0, 16.9, 11.6], 5, rot=DIAG),             # blue-ice face L
        el([13.0, 12.6, 4.4], [13.6, 16.9, 11.6], 5, rot=DIAG),           # blue-ice face R
        el([5.2, 11.6, 4.8], [6.2, 17.9, 11.2], 6, rot=DIAG),             # steel band
        el([9.8, 11.6, 4.8], [10.8, 17.9, 11.2], 6, rot=DIAG),            # steel band
        el([6.8, 17.5, 6.8], [9.2, 18.6, 9.2], 8, rot=DIAG),              # frost cap
    ]
    return E

def shield_front_texture():
    S = 32; im = Image.new("RGBA", (S, S), (0, 0, 0, 0)); px = im.load(); c = (S - 1) / 2
    for y in range(S):
        for x in range(S):
            r = math.hypot(x - c, (y - c) * 0.95)
            if r > 15.6: continue
            if r > 13.6: col = hx("#E8B23A") if r < 15 else hx("#B07D1E")          # gold rim
            elif r > 12.6: col = hx("#B07D1E")
            else:
                col = hx("#F4F1E6")
                ring = abs(r - 8.5) < 0.9
                spokes = r < 8.0 and r > 4.5 and (int((math.degrees(math.atan2(y - c, x - c)) + 360) / 30) % 2 == 0) and abs(r - 6.2) < .7
                if ring or spokes: col = hx("#FFE08A")
                if r < 3.2: col = hx("#E8B23A") if r > 2 else hx("#FFF4C8")
            px[x, y] = col
    return im

def shield(blocking=False):
    """Geometry matches the vanilla shield (plate 12x22) so the vanilla shield display transforms fit."""
    front = {"uv": [0, 0, 16, 16], "texture": "#f"}
    back_uv = {"uv": [16, 0, 0, 16], "texture": "#f"}
    E = [
        el([-7, -9, 1], [7, 9, 2], 9, faces={"south": front, "north": back_uv}),     # main plate (front = +z)
        el([-5, 9, 1], [5, 11, 2], 1),                                                # top cap
        el([-5, -11, 1], [5, -9, 2], 1),                                              # bottom cap
        el([-7.4, -8, 1.2], [-7, 8, 2.2], 1),                                         # side rims
        el([7, -8, 1.2], [7.4, 8, 2.2], 1),
        el([-2, -2, 2], [2, 2, 3], 1, emissive=True),                                 # glowing boss
        el([-1, -3, -5], [1, 3, 1], 12),                                              # handle
    ]
    return E

SHIELD_DISPLAY = {
    "thirdperson_righthand": {"rotation": [0, 90, 0], "translation": [10, 6, -4], "scale": [1, 1, 1]},
    "thirdperson_lefthand": {"rotation": [0, 90, 0], "translation": [10, 6, 12], "scale": [1, 1, 1]},
    "firstperson_righthand": {"rotation": [0, 180, 5], "translation": [-10, 2, -10], "scale": [1.25, 1.25, 1.25]},
    "firstperson_lefthand": {"rotation": [0, 180, 5], "translation": [10, 0, -10], "scale": [1.25, 1.25, 1.25]},
    "gui": {"rotation": [15, -25, -5], "translation": [2, 3, 0], "scale": [0.65, 0.65, 0.65]},
    "fixed": {"rotation": [0, 180, 0], "translation": [-4.5, 4.5, -5], "scale": [0.55, 0.55, 0.55]},
    "ground": {"rotation": [0, 0, 0], "translation": [2, 4, 2], "scale": [0.25, 0.25, 0.25]},
}
SHIELD_BLOCKING_DISPLAY = dict(SHIELD_DISPLAY, **{
    "thirdperson_righthand": {"rotation": [45, 135, 0], "translation": [3.51, 11, -2], "scale": [1, 1, 1]},
    "thirdperson_lefthand": {"rotation": [45, 135, 0], "translation": [13.51, 3, 5], "scale": [1, 1, 1]},
    "firstperson_righthand": {"rotation": [0, 180, -5], "translation": [-15, 5, -11], "scale": [1.25, 1.25, 1.25]},
    "firstperson_lefthand": {"rotation": [0, 180, -5], "translation": [5, 5, -11], "scale": [1.25, 1.25, 1.25]},
})

def ice_spike():
    """Spike for block_display-free ice spikes: an item_display model, base at y=0, tip at y=16."""
    return [el([5, 0, 5], [11, 6, 11], 4), el([6, 6, 6], [10, 11, 10], 5), el([7, 11, 7], [9, 15, 9], 8),
            el([7.5, 15, 7.5], [8.5, 16.5, 8.5], 15)]

# ------------------------------------------------------------------ HUD icons 9x9 (char, colour top, colour bottom)
ICON_ROWS = {
    "soul":   ["....#....", "...###...", "..#####..", "..##.##..", ".###.###.", ".#######.", "..#####..", "...###...", "....#...."],
    "shadow": [".........", "..#####..", ".##...##.", "##.###.##", "#.##.##.#", "##.###.##", ".##...##.", "..#####..", "........."],
    "blink":  ["......##.", ".....##..", "....##...", "...####..", "..####...", "...##....", "..##.....", ".##......", "##......."],
    "shield": ["..#####..", ".#######.", "###...###", "##.###.##", "##.#.#.##", "##.###.##", ".##...##.", "..#####..", "...###..."],
    "storm":  ["....###..", "...###...", "..###....", ".#######.", "....###..", "...###...", "..###....", ".##......", "#........"],
    "frost":  ["....#....", "..#.#.#..", "...###...", "#.#.#.#.#", "#########", "#.#.#.#.#", "...###...", "..#.#.#..", "....#...."],
}
ICON_COLS = {"soul": ("#E9FFF9", "#3F9C88"), "shadow": ("#D9C6FF", "#4A3470"), "blink": ("#FFFFFF", "#7FD8FF"),
             "shield": ("#FFF4C8", "#B07D1E"), "storm": ("#FFF27A", "#7DF9FF"), "frost": ("#E8F8FF", "#3A7BD5")}
def icon(name):
    rows = ICON_ROWS[name]; a, b = hx(ICON_COLS[name][0]), hx(ICON_COLS[name][1])
    im = Image.new("RGBA", (9, 9), (0, 0, 0, 0)); px = im.load()
    for y, r in enumerate(rows):
        for x, ch in enumerate(r):
            if ch == "#": px[x, y] = mix(a, b, y / 8)
    return im
