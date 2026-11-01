# Rank badges: 7 px pixel pills (cap height of the default font), font starkffa:ranks U+E300..
import os, json
from PIL import Image
import pix5
def lerp(a, b, t): return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))
def hexc(h): return tuple(int(h[i:i + 2], 16) for i in (1, 3, 5))
RANKS = [  # id, text, fill left, fill right, text colour
    ("owner", "OWNER", "#FFB547", "#FFD58A", "#2A1A05"),
    ("admin", "ADMIN", "#3FE0FF", "#8BF0FF", "#04232B"),
    ("mod",   "MOD",   "#5B6B82", "#8A96A8", "#F2F6FA"),
    ("media", ">MEDIA", "#F2F6FA", "#C9D2DE", "#10141C"),
]
def pill(text, c1, c2, tc, pad=3):
    tw = pix5.width(text); w = tw + 2 * pad; h = 7
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    a, b = hexc(c1), hexc(c2)
    for x in range(w):
        base = lerp(a, b, x / max(1, w - 1))
        for y in range(h):
            col = base
            if y == 0: col = lerp(base, (255, 255, 255), 0.22)        # top highlight
            if y == h - 1: col = lerp(base, (0, 0, 0), 0.28)           # bottom shade
            im.putpixel((x, y), col + (255,))
    for (x, y) in [(0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1)]: im.putpixel((x, y), (0, 0, 0, 0))
    pix5.draw(im, pad, 1, text, hexc(tc) + (255,))
    return im
def build(pack):
    fdir = os.path.join(pack, "assets/starkffa/textures/font/ranks"); os.makedirs(fdir, exist_ok=True)
    prov = []; table = {}
    for i, (rid, text, c1, c2, tc) in enumerate(RANKS):
        im = pill(text, c1, c2, tc); im.save(os.path.join(fdir, rid + ".png"))
        cp = 0xE300 + i; table[rid] = hex(cp)
        prov.append({"type": "bitmap", "file": f"starkffa:font/ranks/{rid}.png", "ascent": 7, "height": 7, "chars": [chr(cp)]})
    json.dump({"providers": prov}, open(os.path.join(pack, "assets/starkffa/font/ranks.json"), "w", encoding="utf-8"), indent=2, ensure_ascii=True)
    # preview: badges at x8 on a chat-like background next to fake text height
    pv = Image.new("RGBA", (420, 20 + 64 * len(RANKS)), (24, 24, 30, 255))
    y = 10
    for rid, *_ in RANKS:
        im = Image.open(os.path.join(fdir, rid + ".png"))
        pv.alpha_composite(im.resize((im.width * 8, im.height * 8), Image.NEAREST), (10, y)); y += 64
    pv.save(os.path.join(os.path.dirname(pack), "ranks_preview.png"))
    return table
