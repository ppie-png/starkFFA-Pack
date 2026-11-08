"""Rank icons (pack r29, owner picked style B "icon + small caps"): 8x8 pixel icons in font starkffa:ranks,
height 8 / ascent 7 like the scoreboard icons. U+E330 owner (crown), E331 admin (red shield), E332 mod (blue shield),
E333 helper (cyan heart), E334 media (white play button, cyan/pink glitch - r44), E335 stark (gold star), E336 storm (violet bolt),
E337 booster (pink gem), E338 spark (green sparkle). The text next to it is MiniMessage small caps (config)."""
import io, json
from PIL import Image
PAL = {".": None, "k": (16, 20, 28), "w": (255, 255, 255),
       "y": (255, 205, 64), "Y": (255, 238, 160), "o": (232, 140, 30),                 # gold
       "r": (255, 77, 94), "R": (255, 150, 160), "d": (176, 34, 56),                   # red
       "b": (63, 140, 255), "B": (150, 200, 255), "n": (30, 78, 196),                  # blue
       "c": (63, 224, 255), "C": (190, 248, 255), "e": (16, 148, 188),                 # cyan
       "p": (255, 77, 141), "P": (255, 186, 214), "q": (196, 40, 100), "s": (255, 156, 194),  # pink
       "v": (140, 104, 255), "V": (205, 192, 255), "u": (90, 60, 210),                 # violet
       "m": (226, 92, 255), "M": (246, 196, 255), "x": (150, 70, 230),                 # magenta
       "g": (46, 214, 134), "G": (176, 255, 214), "h": (20, 150, 96)}                  # green
ICONS = [
 ("owner",   ["........", "k..kk..k", "kYkyykYk", "kyyyyyyk", "kyrywyrk", "kyyyyyok", "kkkkkkkk", "........"]),
 ("admin",   [".kkkkkk.", "kRRrrrdk", "kRrrrrdk", "krrrrrdk", "krrrrrdk", ".krrrdk.", "..krdk..", "...kk..."]),
 ("mod",     [".kkkkkk.", "kBBbbbnk", "kBbbbbnk", "kbbbbbnk", "kbbbbbnk", ".kbbbnk.", "..kbnk..", "...kk..."]),
 ("helper",  [".kk..kk.", "kCckkcek", "kCccccek", "kcccccek", ".kcccek.", "..kcek..", "...kk...", "........"]),
 ("media",   [".kk.....", ".kwkk...", ".kwwwkk.", "ckwwwwwk", "ckwwwwsk", ".kwwskk.", ".kskk...", ".kk....."]),   # r44 pixel play + glitch
 ("stark",   ["...kk...", "..kYyk..", "kkkYykkk", "kYYYyyok", ".kYyyok.", ".kyyook.", "kyokkook", "kkk..kkk"]),
 ("storm",   ["....kkk.", "...kVvk.", "..kVvk..", ".kVvvvk.", ".kkvvk..", "..kvuk..", ".kuk....", ".kk....."]),
 ("booster", ["..kkkk..", ".kMMmxk.", "kMMmmmxk", "kkkkkkkk", ".kmmmmk.", "..kmxk..", "...kk...", "........"]),
 ("spark",   ["...kk...", "...kGk..", ".kkGgkk.", "kGGwgghk", ".kkghkk.", "...khk..", "...kk...", "........"]),
]
FIRST = 0xE330

def icon(rows):
    im = Image.new("RGBA", (8, 8), (0, 0, 0, 0))
    for y, r in enumerate(rows):
        assert len(r) == 8, (y, r)
        for x, ch in enumerate(r):
            col = PAL[ch]
            if col: im.putpixel((x, y), col + (255,))
    return im

def build():
    """{relative path: bytes} of the icon sheet + the providers to add to font/ranks.json"""
    sheet = Image.new("RGBA", (8 * len(ICONS), 8), (0, 0, 0, 0))
    for i, (_, rows) in enumerate(ICONS): sheet.alpha_composite(icon(rows), (i * 8, 0))
    buf = io.BytesIO(); sheet.save(buf, format="PNG", optimize=True)
    files = {"assets/starkffa/textures/font/ranks/icons.png": buf.getvalue()}
    prov = [{"type": "bitmap", "file": "starkffa:font/ranks/icons.png", "ascent": 7, "height": 8,
             "chars": ["".join(chr(FIRST + i) for i in range(len(ICONS)))]}]
    return files, prov, {rid: FIRST + i for i, (rid, _) in enumerate(ICONS)}

if __name__ == "__main__":
    f, p, cps = build(); print({k: hex(v) for k, v in cps.items()})
