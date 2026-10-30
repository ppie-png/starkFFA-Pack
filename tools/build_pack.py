"""Builds the StarkFFA resource pack from code (all textures are generated, nothing hand-painted).

    python3 tools/build_pack.py   ->  pack/ (sources) + dist/StarkFFA-pack.zip + dist/sha1.txt

Contents
  tooltip styles  starkffa:<theme>   gradient tooltip background + frame per weapon theme
                                     (item component `tooltip_style`, see docs/TOOLTIPS.md)
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

SPACES = {"": -1, "": -2, "": -4, "": -8,
          "": 1, "": 2, "": 4, "": 8}
w(f"assets/{NS}/font/hud.json", {"providers": [
    {"type": "space", "advances": SPACES},
    {"type": "bitmap", "file": f"{NS}:font/hud/segment.png", "ascent": 7, "height": 7, "chars": [""]},
    {"type": "bitmap", "file": f"{NS}:font/hud/diamond.png", "ascent": 5, "height": 3, "chars": [""]},
    {"type": "bitmap", "file": f"{NS}:font/hud/icon_wind.png", "ascent": 8, "height": 9, "chars": [""]},
    {"type": "reference", "id": "minecraft:default"},
]})

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
