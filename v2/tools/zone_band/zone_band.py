"""Hot-zone edge band (pack r47, owner 10.11. 21:37: "the hot-zone rings look cheap, flat and not glowing - 2 or 3
pixels high and a glow"). One unit cube model, shade off (lit on its own, also at night), stretched by StarkCore
(events/HotZone) into 3 px high bars that run along the ground from light pillar to light pillar. The texture's
light spot runs along every bar (u = the bar's length). Two looks: fx_zone_band (live, amber) and fx_zone_band_soon
(announced, cream)."""
import json
import os
import sys

from PIL import Image

SRC = sys.argv[1] if len(sys.argv) > 1 else '/home/claude/starkffa-pack/v2/src'
A = os.path.join(SRC, 'assets', 'starkffa')


def hexc(h, a=255):
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4)) + (a,)


def lerp(c0, c1, f):
    return tuple(int(round(c0[i] + (c1[i] - c0[i]) * f)) for i in range(4))


LOOKS = {'fx_zone_band': ('FFF1CF', 'FFB547', 'E8781E'),        # top rim, body, bottom
         'fx_zone_band_soon': ('FFFFFF', 'FFE6B0', 'D9C08A')}


def frame(look, spot=None):
    top, body, bot = (hexc(c) for c in LOOKS[look])
    im = Image.new('RGBA', (16, 16))
    px = im.load()
    for y in range(16):
        base = lerp(top, body, y / 4) if y < 4 else (body if y < 11 else lerp(body, bot, (y - 11) / 4))
        for x in range(16):
            c = base
            if spot is not None:
                d = abs(x - spot)
                d = min(d, 16 - d)                       # wraps, so it runs on into the next bar
                if d < 4:
                    c = lerp(c, hexc('FFFFFF'), (1 - d / 4) ** 1.3 * 0.85)
            px[x, y] = c
    return im


def main():
    tdir = os.path.join(A, 'textures', 'item')
    for look in LOOKS:
        frames = [frame(look, s) for s in range(16)]
        strip = Image.new('RGBA', (16, 16 * len(frames)))
        for i, f in enumerate(frames):
            strip.paste(f, (0, 16 * i))
        strip.save(os.path.join(tdir, look + '.png'))
        with open(os.path.join(tdir, look + '.png.mcmeta'), 'w') as f:
            json.dump({'animation': {'frametime': 2, 'interpolate': True}}, f)
        uv = [0, 0, 16, 16]
        faces = {s: {'uv': uv, 'texture': '#0'} for s in ('north', 'south', 'up', 'down')}
        faces['east'] = {'uv': [0, 0, 2, 16], 'texture': '#0'}
        faces['west'] = {'uv': [0, 0, 2, 16], 'texture': '#0'}
        model = {'textures': {'0': 'starkffa:item/' + look, 'particle': 'starkffa:item/' + look},
                 'elements': [{'from': [0, 0, 0], 'to': [16, 16, 16], 'shade': False, 'faces': faces}]}
        with open(os.path.join(A, 'models', 'item', look + '.json'), 'w') as f:
            json.dump(model, f, indent=1)
        with open(os.path.join(A, 'items', look + '.json'), 'w') as f:
            json.dump({'model': {'type': 'minecraft:model', 'model': 'starkffa:item/' + look}}, f)
    print('ok', list(LOOKS))


if __name__ == '__main__':
    main()
