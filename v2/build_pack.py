"""FFA resource pack: 8x8 pixel icons in font starkffa:icons -> pack/ + dist/ffa-pack.zip + dist/sha1.txt"""
import sys as _s; _s.path.insert(0, os.path.dirname(os.path.abspath(__file__))) if False else None
import json, os, shutil, zipfile, hashlib, sys
from PIL import Image
ROOT = os.path.dirname(os.path.abspath(__file__))
PAL = {".": None, "k": (34, 20, 46), "w": (255, 255, 255), "y": (255, 216, 77), "Y": (255, 240, 160), "o": (240, 130, 40),
       "O": (255, 190, 80), "r": (255, 96, 110), "R": (255, 170, 180), "d": (200, 50, 80), "p": (255, 138, 216), "P": (255, 200, 240),
       "v": (150, 70, 210), "l": (189, 178, 255), "L": (230, 225, 255), "c": (155, 246, 255), "C": (90, 180, 230),
       "g": (120, 230, 120), "G": (60, 170, 70), "s": (200, 205, 215), "S": (130, 135, 150), "a": (160, 196, 255), "h": (120, 150, 230)}
ICONS = {
 "sword":  ["......kk", ".....kck", "....kcsk", "k..kcsk.", "kkkcsk..", ".kykkk..", "kyk.kk..", "kk......"],
 "skull":  [".kkkkkk.", "kwwwwwwk", "kwkwwkwk", "kwkwwkwk", "kwwwwwwk", ".kwkkwk.", ".kwkwkk.", "..kkkk.."],
 "flame":  ["...k....", "..kok...", "..koyk..", ".kooyok.", "kooyYyok", "kooyYyok", ".kooyok.", "..kkkk.."],
 "heart":  [".kk..kk.", "kRrkkrrk", "kRrrrrdk", "krrrrrdk", ".krrrdk.", "..krdk..", "...kk...", "........"],
 "signal": ["......kk", "......gk", "....kkgk", "....gkgk", "..kkgkgk", "..gkgkgk", "kkgkgkgk", "gkgkgkgk"],
 "online": ["..kkkk..", ".kgggGk.", "kgwgggGk", "kggggGGk", "kggggGGk", "kgggGGGk", ".kGGGGk.", "..kkkk.."],
 "coin":   ["..kkkk..", ".kyYYyk.", "kyYyyoyk", "kyYyyoyk", "kyyyyoyk", "kyyoooyk", ".kyyyyk.", "..kkkk.."],
 "gem":    ["..kkkk..", ".kPPpvk.", "kPPpppvk", "kkkkkkkk", ".kppppk.", "..kpvk..", "...kk...", "........"],
 "crown":  ["........", "k..kk..k", "kYkyykYk", "kyyyyyyk", "kyrypyrk", "kyyyyyyk", "kkkkkkkk", "........"],
 "star":   ["...kk...", "..kLlk..", "kkkLlkkk", "kLLLllLk", ".kLlllk.", ".kllllk.", "kllkkllk", "kkk..kkk"],
 "pulse":  ["........", "..c.....", "..cc....", ".cCc..c.", "cC.cCcCc", "C..cc.C.", "...Cc...", "....C..."],
}
ORDER = ["sword", "skull", "flame", "heart", "signal", "online", "coin", "gem", "crown", "star", "pulse"]
CHARS = [chr(0xE000 + i) for i in range(len(ORDER))]

def render(name):
    im = Image.new("RGBA", (8, 8), (0, 0, 0, 0))
    for y, row in enumerate(ICONS[name]):
        assert len(row) == 8, (name, y, row)
        for x, ch in enumerate(row):
            c = PAL[ch]
            if c: im.putpixel((x, y), c + (255,))
    return im

def main():
    pack = os.path.join(ROOT, "pack"); shutil.rmtree(pack, ignore_errors=True)
    fdir = os.path.join(pack, "assets/starkffa/textures/font"); os.makedirs(fdir)
    sheet = Image.new("RGBA", (8 * len(ORDER), 8), (0, 0, 0, 0))
    for i, n in enumerate(ORDER): sheet.alpha_composite(render(n), (i * 8, 0))
    sheet.save(os.path.join(fdir, "icons8.png"))
    os.makedirs(os.path.join(pack, "assets/starkffa/font"))
    json.dump({"providers": [{"type": "bitmap", "file": "starkffa:font/icons8.png", "ascent": 7, "height": 8, "chars": ["".join(CHARS)]}]},
              open(os.path.join(pack, "assets/starkffa/font/icons.json"), "w", encoding="utf-8"), indent=2, ensure_ascii=True)

    # ---- UI font: dark scoreboard panel rows (one 120x9 cell per sidebar line) + negative/positive spaces
    PANEL_W, ROWS = 120, 11
    def mix(a, b, t): return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))
    STOPS = [(63, 224, 255), (40, 120, 150), (255, 181, 71)]          # cyan -> violet -> pink accent bar
    def stripe(t):
        return mix(STOPS[0], STOPS[1], t * 2) if t < 0.5 else mix(STOPS[1], STOPS[2], (t - 0.5) * 2)
    rows = Image.new("RGBA", (PANEL_W, 9 * ROWS), (0, 0, 0, 0))
    for r in range(ROWS):
        t = r / (ROWS - 1)
        for y in range(9):
            for x in range(PANEL_W):
                a = 205                                              # panel darkness (vanilla bar sits underneath)
                col = (16, 20, 28, a)
                if x < 2: col = stripe(t) + (255,)                   # accent bar
                elif x == 2: col = (10, 8, 28, 200)                  # soft edge next to the bar
                # rounded corners on the first / last row
                if r == 0 and y == 0 and (x < 2 or x >= PANEL_W - 1): col = (0, 0, 0, 0)
                if r == ROWS - 1 and y == 8 and (x < 2 or x >= PANEL_W - 1): col = (0, 0, 0, 0)
                rows.putpixel((x, r * 9 + y), col)
    rows.save(os.path.join(fdir, "panel_rows.png"))
    json.dump({"providers": [
        {"type": "bitmap", "file": "starkffa:font/panel_rows.png", "ascent": 7, "height": 9, "chars": [chr(0xE100 + i) for i in range(ROWS)]},
        {"type": "space", "advances": {"\uF800": -(PANEL_W + 1), "\uF801": 4, "\uF802": 8}}]},
        open(os.path.join(pack, "assets/starkffa/font/ui.json"), "w", encoding="utf-8"), indent=2, ensure_ascii=True)

    # ---- weapon tooltips: soft vertical gradient background + gradient frame per weapon (item component tooltip_style = starkffa:<id>)
    T3, T4, T5 = ("3FE0FF", "1A8FB0"), ("8BF0FF", "3FE0FF"), ("FFD58A", "FFB547")     # STARK DARK tier accents
    TIPS = {"wind_mace": T3, "plunger_grappler": T3, "repulsion_shield": T3,
            "blink_blade": T4, "soul_blade": T4, "shadow_dagger": T4, "lightning_dash_spear": T4, "glacial_slam": T4,
            "black_hole_bow": T5}
    tdir = os.path.join(pack, "assets/starkffa/textures/gui/sprites/tooltip"); os.makedirs(tdir)
    hexrgb = lambda h: tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))
    BASE = (13, 16, 22)
    TW, TH = 16, 64
    for wid, (c1, c2) in TIPS.items():
        a, b = hexrgb(c1), hexrgb(c2)
        bg = Image.new("RGBA", (TW, TH)); fr = Image.new("RGBA", (TW, TH))
        for y in range(TH):
            t = y / (TH - 1)
            tint = tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))
            col = tuple(int(BASE[i] + (tint[i] - BASE[i]) * 0.10) for i in range(3)) + (244,)
            for x in range(TW):
                bg.putpixel((x, y), col)
            line = tuple(int(tint[i] * 0.85 + 255 * 0.15) for i in range(3)) + (255,)
            for x in range(TW):
                edge = (x == 3 or x == TW - 4) or (y == 3 or y == TH - 4)
                inside = 3 <= x <= TW - 4 and 3 <= y <= TH - 4
                corner = (x, y) in [(3, 3), (TW - 4, 3), (3, TH - 4), (TW - 4, TH - 4)]
                if edge and inside and not corner:
                    fr.putpixel((x, y), line)
        bg.save(os.path.join(tdir, wid + "_background.png")); fr.save(os.path.join(tdir, wid + "_frame.png"))
        for kind in ("background", "frame"):
            json.dump({"gui": {"scaling": {"type": "nine_slice", "width": TW, "height": TH, "border": 4}}},
                      open(os.path.join(tdir, f"{wid}_{kind}.png.mcmeta"), "w"), indent=2)
    import gui_part; print("gui", gui_part.build(pack))
    import rank_part; print("ranks", rank_part.build(pack))
    json.dump({"pack": {"description": [{"text": "◆ STARK FFA", "color": "#3FE0FF", "bold": True}, {"text": "\nMenus, icons, badges & weapon tooltips", "color": "#8A96A8"}],
                        "min_format": [97, 0], "max_format": [97, 1]}},
              open(os.path.join(pack, "pack.mcmeta"), "w", encoding="utf-8"), indent=2, ensure_ascii=False)
    # pack.png: gradient tile with the sword
    png = Image.new("RGBA", (64, 64))
    for y in range(64):
        for x in range(64):
            t = (x + y) / 126
            edge = min(x, y, 63 - x, 63 - y)
            base = (int(13 + 13 * t), int(16 + 18 * t), int(22 + 26 * t))
            glow = max(0.0, 1 - edge / 6.0) * 0.55
            png.putpixel((x, y), tuple(int(base[i] + ((63, 224, 255)[i] - base[i]) * glow) for i in range(3)) + (255,))
    big = render("sword").resize((48, 48), Image.NEAREST); png.alpha_composite(big, (8, 8)); png.save(os.path.join(pack, "pack.png"))
    os.makedirs(os.path.join(ROOT, "dist"), exist_ok=True)
    zp = os.path.join(ROOT, "dist", "ffa-pack.zip")
    with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED) as z:
        for base, _, files in sorted(os.walk(pack)):
            for f in sorted(files):
                full = os.path.join(base, f); arc = os.path.relpath(full, pack).replace(os.sep, "/")
                zi = zipfile.ZipInfo(arc, date_time=(2026, 1, 1, 0, 0, 0)); zi.compress_type = zipfile.ZIP_DEFLATED
                z.writestr(zi, open(full, "rb").read())
    sha = hashlib.sha1(open(zp, "rb").read()).hexdigest()
    open(os.path.join(ROOT, "dist", "sha1.txt"), "w").write(sha + "\n")
    # preview (x14, dark bg) for eyeballing
    prev = Image.new("RGBA", (8 * len(ORDER) * 14 + 20, 8 * 14 + 20), (40, 40, 52, 255))
    prev.alpha_composite(sheet.resize((sheet.width * 14, sheet.height * 14), Image.NEAREST), (10, 10)); prev.save(os.path.join(ROOT, "preview.png"))
    print("sha1", sha, "icons", " ".join(f"{n}={hex(ord(c))}" for n, c in zip(ORDER, CHARS)))
main()
