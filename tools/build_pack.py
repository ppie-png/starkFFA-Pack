"""Builds the StarkFFA resource pack from code (all textures are generated, nothing hand-painted).

    python3 tools/build_pack.py   ->  pack/ (sources) + dist/StarkFFA-pack.zip + dist/sha1.txt

Contents
  tooltip styles  starkffa:<theme>   gradient tooltip background + frame per weapon theme
                                     (item component `tooltip_style`, see docs/TOOLTIPS.md)
  items starkffa:plunger_grappler   3D plunger grappler (+ _empty while the plunger is out, plunger_head for the anchor)
  font starkffa:hud                  HUD glyphs for the action bar: bar segment, ability icons,
                                     pixel-exact spaces (see docs/HUD.md)
Add a weapon theme: add an entry to THEMES (+ an icon in ICONS) and rebuild.
"""
import json, os, hashlib, zipfile, shutil
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = os.path.join(ROOT, "pack")
NS = "starkffa"
PACK_FORMAT = 97          # Minecraft 26.3 (same as the GemFall pack)

def w(path, data):
    path = os.path.join(P, path); os.makedirs(os.path.dirname(path), exist_ok=True)
    if isinstance(data, Image.Image):
        data.save(path); return
    if isinstance(data, (dict, list)): data = json.dumps(data, indent=2, ensure_ascii=False)
    open(path, "w", encoding="utf-8").write(data)

def hx(s, a=255):
    s = s.lstrip("#"); return (int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16), a)

def lerp(a, b, t): return tuple(int(round(a[i] + (b[i] - a[i]) * t)) for i in range(4))

# ------------------------------------------------------------------ weapon themes
# bg_*:    tooltip background gradient (top -> bottom), slightly see-through like vanilla
# frame_*: 1 px frame gradient (top -> bottom)
# accent:  ability colour used by the plugin (HUD bar, texts)
THEMES = {
    "wind": dict(bg_top=hx("#14303F", 242), bg_bottom=hx("#0B1322", 242),
                 frame_top=hx("#B8F6FF"), frame_bottom=hx("#3F86B4", 230),
                 accent="#A0F0FF"),
    "void": dict(bg_top=hx("#24173A", 242), bg_bottom=hx("#0B0814", 242),
                 frame_top=hx("#E2CCFF"), frame_bottom=hx("#6B3FB5", 230),
                 accent="#C9A7FF"),
    "hook": dict(bg_top=hx("#3A2318", 242), bg_bottom=hx("#170D0A", 242),
                 frame_top=hx("#FFC59A"), frame_bottom=hx("#B5542A", 230),
                 accent="#FFB37A"),
}

# ------------------------------------------------------------------ tooltip textures
# Vanilla draws the tooltip sprites 12 px larger than the text area on every side (3 padding + 9 margin).
# 100x100 nine-slice: background visible from px 8 (4 px around the text, corners cut),
# frame = 1 px ring at px 9. Rows/cols inside the fixed border keep a constant colour,
# the gradient lives in the stretched centre -> seamless at any tooltip size.
S, BG_IN, FR_IN = 100, 8, 9

def grad_t(y, lo, hi):
    if y <= lo: return 0.0
    if y >= hi: return 1.0
    return (y - lo) / (hi - lo)

def tooltip_background(th):
    im = Image.new("RGBA", (S, S), (0, 0, 0, 0)); px = im.load()
    a, b = BG_IN, S - 1 - BG_IN
    for y in range(a, b + 1):
        c = lerp(th["bg_top"], th["bg_bottom"], grad_t(y, 10, 89))
        for x in range(a, b + 1):
            if (x in (a, b)) and (y in (a, b)): continue          # cut corners like vanilla
            px[x, y] = c
    return im

def tooltip_frame(th):
    im = Image.new("RGBA", (S, S), (0, 0, 0, 0)); px = im.load()
    a, b = FR_IN, S - 1 - FR_IN
    for y in range(a, b + 1):
        c = lerp(th["frame_top"], th["frame_bottom"], grad_t(y, 10, 89))
        if y in (a, b):
            for x in range(a, b + 1): px[x, y] = c
        else:
            px[a, y] = c; px[b, y] = c
    # soft inner highlight under the top edge (1 px, faint)
    hl = th["frame_top"][:3] + (40,)
    for x in range(a + 1, b): px[x, a + 1] = hl
    return im

def nine_slice(border):
    return {"gui": {"scaling": {"type": "nine_slice", "width": S, "height": S,
                                "border": border, "stretch_inner": True}}}

for name, th in THEMES.items():
    base = f"assets/{NS}/textures/gui/sprites/tooltip/{name}"
    w(base + "_background.png", tooltip_background(th))
    w(base + "_background.png.mcmeta", nine_slice(9))
    w(base + "_frame.png", tooltip_frame(th))
    w(base + "_frame.png.mcmeta", nine_slice(10))

# ------------------------------------------------------------------ HUD font
# Bitmap glyphs are tinted by the text colour -> textures are white/grey, the plugin colours them.
def segment():
    # 5x7 chunky "battery cell": rounded corners, bright top edge, darker bottom edge.
    # 10 of them = the whole bar (simple to read at a glance).
    W, H = 5, 7
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0)); px = im.load()
    for y in range(H):
        for x in range(W):
            if (x in (0, W - 1)) and (y in (0, H - 1)): continue
            v = 235
            if y == 1: v = 255
            if y == H - 1: v = 185
            if x in (0, W - 1): v -= 15
            px[x, y] = (v, v, v, 255)
    return im

def diamond():
    im = Image.new("RGBA", (3, 3), (0, 0, 0, 0)); px = im.load()
    for (x, y) in [(1, 0), (0, 1), (1, 1), (2, 1), (1, 2)]: px[x, y] = (255, 255, 255, 255)
    return im

ICONS = {
    # 9x9 pixel art, coloured (drawn with <white> text colour so the colours stay true)
    "wind": [
        "..#####..",
        ".#.....#.",
        "........#",
        ".######..",
        ".........",
        "#######..",
        ".......#.",
        "..####.#.",
        "......#..",
    ],
    "hook": [            # plunger: cup on the left, stick to the right
        "..#......",
        ".##......",
        "###......",
        "#########",
        "#########",
        "###......",
        ".##......",
        "..#......",
        ".........",
    ],
}
def icon(rows, top, bottom):
    h = len(rows); wd = len(rows[0])
    im = Image.new("RGBA", (wd, h), (0, 0, 0, 0)); px = im.load()
    for y, row in enumerate(rows):
        c = lerp(top, bottom, y / (h - 1))
        for x, ch in enumerate(row):
            if ch == "#": px[x, y] = c
    return im

w(f"assets/{NS}/textures/font/hud/segment.png", segment())
w(f"assets/{NS}/textures/font/hud/diamond.png", diamond())
w(f"assets/{NS}/textures/font/hud/icon_wind.png", icon(ICONS["wind"], hx("#E8FDFF"), hx("#5FB8D6")))
w(f"assets/{NS}/textures/font/hud/icon_hook.png", icon(ICONS["hook"], hx("#FFC59A"), hx("#D6453D")))
import sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import voidbow as _vb
w(f"assets/{NS}/textures/font/hud/icon_void.png", _vb.icon())

SPACES = {"": -1, "": -2, "": -4, "": -8,
          "": 1, "": 2, "": 4, "": 8}
w(f"assets/{NS}/font/hud.json", {"providers": [
    {"type": "space", "advances": SPACES},
    {"type": "bitmap", "file": f"{NS}:font/hud/segment.png", "ascent": 7, "height": 7, "chars": [""]},
    {"type": "bitmap", "file": f"{NS}:font/hud/diamond.png", "ascent": 5, "height": 3, "chars": [""]},
    {"type": "bitmap", "file": f"{NS}:font/hud/icon_wind.png", "ascent": 8, "height": 9, "chars": [""]},
    {"type": "reference", "id": "minecraft:default"},
]})


# ------------------------------------------------------------------ 3D item models
# Low-poly cuboid models, textured from one 16x16 swatch atlas (4x4 px per colour).
# Convention: barrel points NORTH (-z) = forward in the player's hand.
SWATCH = [  # index -> colour
    "#23324A", "#FF9F5A", "#3A3F4A", "#2A2422",   # 0 body navy, 1 accent orange, 2 dark metal, 3 grip
    "#C88A4E", "#D6453D", "#9E2B26", "#E8D9B0",   # 4 wood stick, 5 rubber red, 6 rubber rim, 7 rope
    "#9AA6B5", "#FFD3A8", "#1A2333", "#FFFFFF",   # 8 light metal, 9 warm light, 10 deep navy, 11 white
]
def atlas():
    im = Image.new("RGBA", (16, 16), (0, 0, 0, 0)); px = im.load()
    import random; rng = random.Random(7)
    for i, c in enumerate(SWATCH):
        base = hx(c); sx, sy = (i % 4) * 4, (i // 4) * 4
        for y in range(4):
            for x in range(4):
                k = 1.08 if y == 0 else (0.9 if y == 3 else 1.0)
                k *= 1 + (rng.random() - .5) * .06
                px[sx + x, sy + y] = tuple(min(255, int(v * k)) for v in base[:3]) + (255,)
    return im
w(f"assets/{NS}/textures/item/atlas_tools.png", atlas())

def el(frm, to, sw, rot=None):
    sx, sy = (sw % 4) * 4, (sw // 4) * 4
    uv = [sx + .5, sy + .5, sx + 3.5, sy + 3.5]
    e = {"from": frm, "to": to,
         "faces": {f: {"uv": uv, "texture": "#t"} for f in ("north", "east", "south", "west", "up", "down")}}
    if rot: e["rotation"] = rot
    return e

GUN_BODY = [
    el([7, 0, 9], [9, 6, 11.5], 3, {"angle": -22.5, "axis": "x", "origin": [8, 6, 10]}),   # grip
    el([6.5, 5, 4], [9.5, 8.5, 13], 0),          # body
    el([6.4, 6.2, 5], [9.6, 7.2, 12], 1),        # orange stripe
    el([6.8, 5.3, 13], [9.2, 8.2, 14], 2),       # rear cap
    el([7, 5.5, 0.5], [9, 8, 4], 2),             # barrel
    el([6.7, 5.2, 1], [9.3, 8.3, 2], 1),         # barrel ring
    el([7.5, 3.8, 8], [8.5, 5, 9], 2),           # trigger
    el([7.2, 8.5, 6], [8.8, 9.6, 10], 7),        # rope coil
    el([7.6, 8.5, 11], [8.4, 9.3, 12.5], 8),     # sight
]
PLUNGER = [
    el([7.5, 6.25, -4], [8.5, 7.25, 0.5], 4),    # wooden stick
    el([6.9, 5.65, -4.3], [9.1, 7.85, -3.6], 5), # cup neck (bell shape)
    el([6.2, 4.95, -5.2], [9.8, 8.55, -4.3], 5), # cup body
    el([5.7, 4.45, -6], [10.3, 9.05, -5.2], 5),  # cup mouth
    el([5.4, 4.15, -6.5], [10.6, 9.35, -6], 6),  # cup rim
]
GUN_DISPLAY = {
    "thirdperson_righthand": {"rotation": [0, 0, 0], "translation": [0, 2.5, 2], "scale": [0.6, 0.6, 0.6]},
    "thirdperson_lefthand":  {"rotation": [0, 0, 0], "translation": [0, 2.5, 2], "scale": [0.6, 0.6, 0.6]},
    "firstperson_righthand": {"rotation": [0, -5, 0], "translation": [1.5, 3.5, 1], "scale": [0.7, 0.7, 0.7]},
    "firstperson_lefthand":  {"rotation": [0, 5, 0], "translation": [1.5, 3.5, 1], "scale": [0.7, 0.7, 0.7]},
    "gui":    {"rotation": [20, -90, 0], "translation": [-1.5, -1, 0], "scale": [0.75, 0.75, 0.75]},
    "ground": {"rotation": [0, 0, 0], "translation": [0, 2, 0], "scale": [0.45, 0.45, 0.45]},
    "fixed":  {"rotation": [0, -90, 0], "translation": [-1.5, 0, 0], "scale": [0.8, 0.8, 0.8]},
}
def model(elements, display=None):
    m = {"textures": {"t": f"{NS}:item/atlas_tools", "particle": f"{NS}:item/atlas_tools"}, "elements": elements}
    if display: m["display"] = display
    return m
w(f"assets/{NS}/models/item/plunger_grappler.json", model(GUN_BODY + PLUNGER, GUN_DISPLAY))
w(f"assets/{NS}/models/item/plunger_grappler_empty.json", model(GUN_BODY, GUN_DISPLAY))
# the plunger stuck in a wall / player (item_display); centred on the cup rim
HEAD = [el([7.5, 7.5, 9], [8.5, 8.5, 15], 4),                       # stick sticking out
        el([7, 7, 8.3], [9, 9, 9], 5), el([6.3, 6.3, 7.3], [9.7, 9.7, 8.3], 5),
        el([5.8, 5.8, 6.5], [10.2, 10.2, 7.3], 5), el([5.5, 5.5, 6], [10.5, 10.5, 6.5], 6)]
w(f"assets/{NS}/models/item/plunger_head.json", model(HEAD))
for name in ("plunger_grappler", "plunger_grappler_empty", "plunger_head"):
    w(f"assets/{NS}/items/{name}.json", {"model": {"type": "minecraft:model", "model": f"{NS}:item/{name}"}})


# ------------------------------------------------------------------ Black Hole Bow (2D sprites, vanilla bow display)
w(f"assets/{NS}/textures/item/void_bow.png", _vb.bow(None))
for i in range(3): w(f"assets/{NS}/textures/item/void_bow_pulling_{i}.png", _vb.bow(i))
for n in ["void_bow"] + [f"void_bow_pulling_{i}" for i in range(3)]:
    w(f"assets/{NS}/models/item/{n}.json", {"parent": "minecraft:item/bow", "textures": {"layer0": f"{NS}:item/{n}"}})
w(f"assets/{NS}/items/void_bow.json", {"model": {
    "type": "minecraft:condition", "property": "minecraft:using_item",
    "on_false": {"type": "minecraft:model", "model": f"{NS}:item/void_bow"},
    "on_true": {"type": "minecraft:range_dispatch", "property": "minecraft:use_duration", "scale": 0.05,
                "fallback": {"type": "minecraft:model", "model": f"{NS}:item/void_bow_pulling_0"},
                "entries": [{"threshold": 0.65, "model": {"type": "minecraft:model", "model": f"{NS}:item/void_bow_pulling_1"}},
                            {"threshold": 0.9, "model": {"type": "minecraft:model", "model": f"{NS}:item/void_bow_pulling_2"}}]}}})
# the black hole itself: animated sprite for an item_display (billboard: center)
w(f"assets/{NS}/textures/item/black_hole.png", _vb.black_hole())
w(f"assets/{NS}/textures/item/black_hole.png.mcmeta", {"animation": {"frametime": 2, "interpolate": True}})
w(f"assets/{NS}/models/item/black_hole.json", {"parent": "minecraft:item/generated", "textures": {"layer0": f"{NS}:item/black_hole"}})
w(f"assets/{NS}/items/black_hole.json", {"model": {"type": "minecraft:model", "model": f"{NS}:item/black_hole"}})

# ------------------------------------------------------------------ sounds (synthesised, see tools/sounds.py)
import sounds as _snd
SOUND_DEFS = _snd.build(os.path.join(P, "assets"), NS)
w(f"assets/{NS}/sounds.json", SOUND_DEFS)
w(f"assets/{NS}/lang/en_us.json", {
    "subtitles.starkffa.grappler.fire": "Plunger fires", "subtitles.starkffa.grappler.stick": "Plunger sticks",
    "subtitles.starkffa.grappler.reel": "Grappler reels in", "subtitles.starkffa.grappler.release": "Plunger pops off",
    "subtitles.starkffa.grappler.yank": "Player yanked",
    "subtitles.starkffa.void.launch": "Black hole fired", "subtitles.starkffa.void.hum": "Black hole pulls",
    "subtitles.starkffa.void.collapse": "Black hole collapses"})

# ------------------------------------------------------------------ pack.mcmeta + pack.png
w("pack.mcmeta", {"pack": {
    "description": [
        {"text": "StarkFFA", "color": "#A0F0FF", "bold": True},
        {"text": "\nWeapons, HUD & tooltips", "color": "#BDB2FF"}],
    "min_format": [PACK_FORMAT, 0], "max_format": [PACK_FORMAT, 1]}})

def pack_png():
    N = 256
    im = Image.new("RGBA", (N, N)); d = ImageDraw.Draw(im)
    for y in range(N):
        d.line([(0, y), (N, y)], fill=lerp(hx("#14303F"), hx("#0B1322"), y / (N - 1)))
    # big wind icon in the middle (nearest-neighbour scaled pixel art)
    ic = icon(ICONS["wind"], hx("#E8FDFF"), hx("#5FB8D6")).resize((126, 126), Image.NEAREST)
    im.alpha_composite(ic, ((N - 126) // 2, 38))
    try: f = ImageFont.truetype("/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf", 46)
    except OSError: f = ImageFont.load_default()
    t = "FFA"; tw = d.textlength(t, font=f)
    d.text(((N - tw) / 2, 176), t, font=f, fill=hx("#E0FBFF"))
    d.rectangle([0, 0, N - 1, N - 1], outline=hx("#A0F0FF"), width=4)
    return im
w("pack.png", pack_png())

# ------------------------------------------------------------------ zip + sha1
os.makedirs(os.path.join(ROOT, "dist"), exist_ok=True)
out = os.path.join(ROOT, "dist", "StarkFFA-pack.zip")
with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
    for base, _, files in os.walk(P):
        for fn in sorted(files):
            full = os.path.join(base, fn)
            info = zipfile.ZipInfo(os.path.relpath(full, P).replace(os.sep, "/"), (2026, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            z.writestr(info, open(full, "rb").read())
sha1 = hashlib.sha1(open(out, "rb").read()).hexdigest()
open(os.path.join(ROOT, "dist", "sha1.txt"), "w").write(sha1 + "\n")
print("built", out, sha1)
