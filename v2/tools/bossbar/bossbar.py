"""STARK boss bars (pack r46): every vanilla boss bar colour gets the STARK look - a slim dark glass track and a glossy
fill with a soft glow (1 px above and below), rounded ends and a light sweep that runs along the filled part. The
notched overlays become crisp 1 px cuts (10 segments = 10 hearts on the boss bar). PURPLE is the BOSS bar (StarkCore
uses it only for the server boss): crimson with a slow heartbeat.
Writes assets/minecraft/textures/gui/sprites/boss_bar/*.png (+ .mcmeta) into the pack source and a mock-up PNG.
"""
import json
import os
import sys

from PIL import Image

SRC = sys.argv[1] if len(sys.argv) > 1 else '/home/claude/starkffa-pack/v2/src'
MOCK = sys.argv[2] if len(sys.argv) > 2 else None
OUT = os.path.join(SRC, 'assets', 'minecraft', 'textures', 'gui', 'sprites', 'boss_bar')
W, H = 182, 5

COLORS = {'white': 'E9EEF4', 'blue': '3FE0FF', 'yellow': 'FFB547', 'red': 'FF4D5E', 'pink': 'FF7AD9',
          'green': '3DFFA2', 'purple': 'FF2E4A'}
NOTCH_GROUPS = {6: [30, 60, 90, 121, 151], 10: [18, 36, 54, 72, 90, 109, 127, 145, 163],
                12: [15, 30, 45, 60, 75, 90, 106, 121, 136, 151, 166], 20: [9, 18, 27, 36, 45, 54, 63, 72, 81, 90, 100, 109, 118, 127, 136, 145, 154, 163, 172]}


def hexc(h, a=255):
    return [int(h[i:i + 2], 16) for i in (0, 2, 4)] + [a]


def mix(c, d, f):
    return [int(round(c[i] + (d[i] - c[i]) * f)) for i in range(3)] + [c[3]]


def background(col):
    c = hexc(col)
    ink = hexc('0B0F16')
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    px = im.load()
    rows = {1: (mix(ink, c, 0.20), 205), 2: (mix(ink, c, 0.12), 205), 3: (mix(ink, c, 0.07), 205)}
    for x in range(W):
        cap = 0.5 if x in (0, W - 1) else 1.0
        for y, (cc, a) in rows.items():
            px[x, y] = tuple(cc[:3] + [int(a * cap)])
    return im


def fill_frame(col, shine=None, pulse=0.0):
    c = hexc(col)
    if pulse:
        c = mix(c, hexc('FFFFFF'), 0.22 * pulse)
    hi, lo = mix(c, hexc('FFFFFF'), 0.48), mix(c, hexc('000000'), 0.30)
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    px = im.load()
    for x in range(W):
        cap = 0.55 if x in (0, W - 1) else 1.0
        rows = {0: (c, 62 + int(50 * pulse)), 1: (hi, 255), 2: (c, 255), 3: (lo, 255), 4: (c, 44 + int(40 * pulse))}
        for y, (cc, a) in rows.items():
            v = list(cc)
            if shine is not None and y in (1, 2, 3):
                d = abs(x - shine - (2 - y) * 1.5)
                if d < 7:
                    v = mix(v, hexc('FFFFFF'), (1 - d / 7) ** 1.6 * 0.6)
            a = a if y in (1, 2, 3) else (0 if x in (0, W - 1) else a)
            px[x, y] = tuple(v[:3] + [int(a * (cap if y in (1, 2, 3) else 1.0))])
    return im


def strip(frames):
    s = Image.new('RGBA', (W, H * len(frames)))
    for i, f in enumerate(frames):
        s.paste(f, (0, H * i))
    return s


def progress(name, col):
    if name == 'purple':
        # heartbeat: lub-dub, then rest (36 ticks = 1.8 s)
        seq = [(0.0, 16), (0.6, 2), (1.0, 2), (0.4, 2), (0.0, 2), (0.7, 2), (0.35, 2), (0.0, 8)]
        frames = [fill_frame(col, None, p) for p, _ in seq]
        meta = {'animation': {'width': W, 'height': H, 'frames': [{'index': i, 'time': t} for i, (_, t) in enumerate(seq)]}}
        return strip(frames), meta
    # light sweep: idle 60 ticks, then the band crosses the bar in 23 frames
    pos = list(range(-8, 190, 9))
    frames = [fill_frame(col)] + [fill_frame(col, p) for p in pos]
    meta = {'animation': {'width': W, 'height': H,
                          'frames': [{'index': 0, 'time': 60}] + [{'index': i, 'time': 1} for i in range(1, len(frames))]}}
    return strip(frames), meta


def notch(n):
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    px = im.load()
    for x in NOTCH_GROUPS[n]:
        for y in (1, 2, 3):
            px[x, y] = (11, 15, 22, 235)
    return im


def main():
    os.makedirs(OUT, exist_ok=True)
    for name, col in COLORS.items():
        background(col).save(os.path.join(OUT, name + '_background.png'))
        s, meta = progress(name, col)
        s.save(os.path.join(OUT, name + '_progress.png'))
        with open(os.path.join(OUT, name + '_progress.png.mcmeta'), 'w') as f:
            json.dump(meta, f)
    for n in NOTCH_GROUPS:
        for kind in ('background', 'progress'):
            notch(n).save(os.path.join(OUT, 'notched_%d_%s.png' % (n, kind)))
    if MOCK:
        mock()


def mock():
    """Mock-up at GUI scale 3 over a sky/arena-ish backdrop: four bars at different fill levels."""
    S = 3
    bg = Image.new('RGBA', (300 * S, 120 * S), (0, 0, 0, 255))
    px = bg.load()
    for y in range(bg.height):
        for x in range(bg.width):
            t = y / bg.height
            px[x, y] = (int(120 + 60 * t), int(170 + 40 * t), int(230 - 40 * t), 255)
    def put(name, prog, notched, y):
        b = background(COLORS[name])
        fr, _ = progress(name, COLORS[name])
        f = fr.crop((0, H * (3 if name != 'purple' else 2), W, H * (4 if name != 'purple' else 3)))
        bar = b.copy()
        w = int(W * prog)
        bar.alpha_composite(f.crop((0, 0, w, H)), (0, 0))
        if notched:
            n = notch(10)
            bar.alpha_composite(n, (0, 0))
        big = bar.resize((W * S, H * S), Image.NEAREST)
        bg.alpha_composite(big, ((300 - W) // 2 * S, y * S))
    put('purple', 0.65, True, 14)
    put('pink', 0.8, True, 38)
    put('yellow', 0.4, True, 62)
    put('blue', 1.0, False, 86)
    bg.save(MOCK)


if __name__ == '__main__':
    main()
