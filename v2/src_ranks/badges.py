"""Rank badges (pack r28): fixed-width 9 px pixel pills, font starkffa:ranks.
U+E310 owner, E311 admin, E312 mod, E313 helper, E314 media, E315 stark, E316 storm, E317 booster, E318 spark, E319 member;
U+E320.. STARK shine frames (a glint sweeps across the gold bar - TAB animation rank_stark).
height 9 / ascent 8 = one pixel above the capitals to the descender row: centred on the text line."""
import sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import pix5
from PIL import Image

pix5.F["K"] = ["#..#", "#.#.", "##..", "#.#.", "#..#"]      # the 3 px K read as H at badge size

def hexc(h): return tuple(int(h[i:i + 2], 16) for i in (1, 3, 5))
def lerp(a, b, t): return tuple(int(round(a[i] + (b[i] - a[i]) * t)) for i in range(3))

H = 9
RANKS = [  # id, text, fill from, fill to, text colour
    ("owner",   "OWNER",   "#FF4D5E", "#FFB547", "#FFFFFF"),
    ("admin",   "ADMIN",   "#D92B45", "#FF5F73", "#FFFFFF"),
    ("mod",     "MOD",     "#2A63F5", "#3FB8FF", "#FFFFFF"),
    ("helper",  "HELPER",  "#0E97B8", "#3FE0FF", "#FFFFFF"),
    ("media",   "MEDIA",   "#F0306E", "#FF85B0", "#FFFFFF"),
    ("stark",   "STARK",   "#F29A16", "#FFD873", "#4A2C00"),
    ("storm",   "STORM",   "#6A4CFF", "#35C2FF", "#FFFFFF"),
    ("booster", "BOOSTER", "#D34CFF", "#8B6BFF", "#FFFFFF"),
    ("spark",   "SPARK",   "#16B86C", "#3FE0D0", "#FFFFFF"),
    ("member",  "MEMBER",  "#343C4A", "#4A5466", "#C9D2DE"),
]
CP = {rid: 0xE310 + i for i, (rid, *_) in enumerate(RANKS)}
SHINE_FIRST = 0xE320
W = max(pix5.width(t) for _, t, *_ in RANKS) + 6          # every badge has the same width -> names line up

def badge(text, c1, c2, tc, shine=None):
    tw = pix5.width(text)
    padl = (W - tw) // 2
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    a, b = hexc(c1), hexc(c2)
    for x in range(W):
        base = lerp(a, b, x / (W - 1))
        for y in range(H):
            col = base
            if y == 0: col = lerp(base, (255, 255, 255), 0.30)
            elif y == 1: col = lerp(base, (255, 255, 255), 0.12)
            elif y == H - 2: col = lerp(base, (0, 0, 0), 0.22)
            elif y == H - 1: col = lerp(base, (0, 0, 0), 0.40)
            if shine is not None:
                d = abs((x + y * 0.7) - shine)
                if d < 2.0: col = lerp(col, (255, 255, 255), 0.65 * (1 - d / 2.0))
            im.putpixel((x, y), col + (255,))
    for (x, y) in [(0, 0), (W - 1, 0), (0, H - 1), (W - 1, H - 1)]:
        im.putpixel((x, y), (0, 0, 0, 0))
    t = hexc(tc)
    dark_text = sum(t) < 300
    sh = Image.new("RGBA", (W, H), (0, 0, 0, 0)); pix5.draw(sh, padl, 3, text, (0, 0, 0, 255))
    for yy in range(H):
        for xx in range(W):
            if sh.getpixel((xx, yy))[3] and im.getpixel((xx, yy))[3]:
                p = im.getpixel((xx, yy))[:3]
                im.putpixel((xx, yy), (lerp(p, (255, 255, 255), 0.25) if dark_text else lerp(p, (0, 0, 0), 0.35)) + (255,))
    pix5.draw(im, padl, 2, text, t + (255,))
    return im

def build(pack_root):
    """Writes assets/starkffa/textures/font/ranks/*.png + assets/starkffa/font/ranks.json under pack_root; returns
    {relative path: bytes} of everything written and the number of shine frames."""
    import io
    files = {}
    prov = []
    def put(rel, im):
        buf = io.BytesIO(); im.save(buf, format="PNG", optimize=True); files[rel] = buf.getvalue()
    for rid, text, c1, c2, tc in RANKS:
        put(f"assets/starkffa/textures/font/ranks/{rid}.png", badge(text, c1, c2, tc))
        prov.append({"type": "bitmap", "file": f"starkffa:font/ranks/{rid}.png", "ascent": 8, "height": H, "chars": [chr(CP[rid])]})
    rid, text, c1, c2, tc = RANKS[5]
    n = 0
    for i, s in enumerate(range(-4, W + 6, 3)):
        put(f"assets/starkffa/textures/font/ranks/stark_shine{i}.png", badge(text, c1, c2, tc, shine=s))
        prov.append({"type": "bitmap", "file": f"starkffa:font/ranks/stark_shine{i}.png", "ascent": 8, "height": H, "chars": [chr(SHINE_FIRST + i)]})
        n += 1
    files["assets/starkffa/font/ranks.json"] = json.dumps({"providers": prov}, indent=2, ensure_ascii=True).encode("utf-8")
    if pack_root:
        for rel, data in files.items():
            p = os.path.join(pack_root, rel); os.makedirs(os.path.dirname(p), exist_ok=True)
            open(p, "wb").write(data)
    return files, n

if __name__ == "__main__":
    files, n = build(None)
    print(W, "px wide,", len(files), "files,", n, "shine frames")
