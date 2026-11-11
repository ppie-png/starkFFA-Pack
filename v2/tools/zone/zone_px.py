"""r143 hot zone in crisp pixel art (owner 11.11. 21:46, players: "the hot zone looks ugly"): the soft, blurred light
streaks (fx_beam) become Minecraft-like pixel models - a beacon-style beam for the middle, short light posts for the
edge, the ground band as a clean 3-tone pixel line with a running glint. Hard pixels, no gradients, no interpolation.
Every model has a live (amber) and a soon (cream, calmer) look, colours baked in (no tint).
Usage: python3 zone_px.py <assets dir (…/assets)> [preview.png]"""
import json
import os
import sys

from PIL import Image

LIVE = {'deep': (200, 116, 26), 'amber': (255, 181, 71), 'light': (255, 213, 138), 'core': (255, 243, 214), 'white': (255, 255, 255)}
SOON = {'deep': (168, 146, 108), 'amber': (214, 196, 160), 'light': (236, 224, 198), 'core': (250, 244, 230), 'white': (255, 252, 244)}
UP = {'deep': 'amber', 'amber': 'light', 'light': 'core', 'core': 'white', 'white': 'white'}


def beacon(pal, frames=16, h=128, alpha_mul=1.0, pulse_period=32, pulse_len=4, step=2):
    """Beacon-style beam, 16 px wide: soft-looking but made of hard pixel columns, light packets rising."""
    cols = {1: ('deep', 70), 2: ('deep', 120), 3: ('amber', 170), 4: ('amber', 230), 5: ('amber', 255), 6: ('light', 255), 7: ('core', 255)}
    out = Image.new('RGBA', (16, h * frames), (0, 0, 0, 0))
    for f in range(frames):
        for y in range(h):
            fade = 1.0
            if y < 24:
                fade = [0.15, 0.3, 0.45, 0.6, 0.75, 0.9][y // 4]
            pulse = ((y + f * step) % pulse_period) < pulse_len
            for x in range(16):
                c = x if x < 8 else 15 - x
                if c not in cols:
                    continue
                tone, a = cols[c]
                if pulse:
                    tone, a = UP[tone], min(255, a + 40)
                if y >= h - 2:
                    tone, a = UP[tone], min(255, a + 30)
                out.putpixel((x, f * h + y), pal[tone] + (int(round(a * fade * alpha_mul)),))
    return out


def post(pal, frames=8, h=32, alpha_mul=1.0):
    """Short light post: slim core, a bright cap, a socket at the foot, one spark rising per period."""
    cols = {4: ('deep', 110), 5: ('amber', 200), 6: ('light', 255), 7: ('core', 255)}
    out = Image.new('RGBA', (16, h * frames), (0, 0, 0, 0))
    for f in range(frames):
        spark = (h - 4 - f * 4) % h
        for y in range(h):
            for x in range(16):
                c = x if x < 8 else 15 - x
                px = None
                if y == 0 and c == 7:
                    px = ('core', 170)
                elif y in (1, 2) and c >= 6:
                    px = ('white', 255)
                elif y >= h - 3 and c >= 3:
                    px = ('deep' if c < 5 else 'amber', 150 if c < 5 else 255)
                elif y >= 3 and c in cols:
                    tone, a = cols[c]
                    if spark <= y < spark + 2 and c >= 5:
                        tone, a = UP[tone], 255
                    px = (tone, a)
                if px:
                    out.putpixel((x, f * h + y), pal[px[0]] + (int(round(px[1] * alpha_mul)),))
    return out


def band(pal, frames=16, glint=3):
    """Ground band: rows 0-3 highlight, 4-11 body, 12-15 shadow; a white glint runs along it (1 px per frame)."""
    out = Image.new('RGBA', (16, 16 * frames), (0, 0, 0, 0))
    for f in range(frames):
        for y in range(16):
            for x in range(16):
                tone = 'light' if y < 4 else 'amber' if y < 12 else 'deep'
                if (x - f) % 16 < glint and y < 12:
                    tone = 'white' if y < 4 else 'core'
                out.putpixel((x, f * 16 + y), pal[tone] + (255,))
    return out


QUAD = {"textures": {"0": None, "particle": None}, "elements": [{"from": [0, 0, 8], "to": [16, 16, 8], "shade": False, "faces": {
    "north": {"uv": [16, 0, 0, 16], "texture": "#0"}, "south": {"uv": [0, 0, 16, 16], "texture": "#0"}}}]}


def write(assets, name, img, frame_h, frametime, model):
    tex = os.path.join(assets, 'starkffa/textures/item', name + '.png')
    img.save(tex)
    json.dump({"animation": {"frametime": frametime, "interpolate": False, "width": 16, "height": frame_h}}, open(tex + '.mcmeta', 'w'))
    m = json.loads(json.dumps(model))
    m['textures'] = {"0": "starkffa:item/" + name, "particle": "starkffa:item/" + name}
    json.dump(m, open(os.path.join(assets, 'starkffa/models/item', name + '.json'), 'w'), indent=1)
    json.dump({"model": {"type": "minecraft:model", "model": "starkffa:item/" + name}}, open(os.path.join(assets, 'starkffa/items', name + '.json'), 'w'))


def main():
    assets = sys.argv[1]
    band_model = json.load(open(os.path.join(assets, 'starkffa/models/item/fx_zone_band.json')))
    write(assets, 'fx_zone_beacon', beacon(LIVE), 128, 2, QUAD)
    write(assets, 'fx_zone_beacon_soon', beacon(SOON, alpha_mul=0.75, pulse_period=64, pulse_len=3), 128, 3, QUAD)
    write(assets, 'fx_zone_post', post(LIVE), 32, 2, QUAD)
    write(assets, 'fx_zone_post_soon', post(SOON, alpha_mul=0.8), 32, 3, QUAD)
    write(assets, 'fx_zone_band_px', band(LIVE), 16, 2, band_model)
    write(assets, 'fx_zone_band_px_soon', band(SOON, glint=2), 16, 3, band_model)
    if len(sys.argv) > 2:
        prev = Image.new('RGBA', (16 * 6 + 50, 128), (52, 56, 64, 255))
        x = 4
        for n, fh in (('fx_zone_beacon', 128), ('fx_zone_beacon_soon', 128), ('fx_zone_post', 32), ('fx_zone_post_soon', 32), ('fx_zone_band_px', 16), ('fx_zone_band_px_soon', 16)):
            im = Image.open(os.path.join(assets, 'starkffa/textures/item', n + '.png')).convert('RGBA').crop((0, 0, 16, fh))
            prev.alpha_composite(im, (x, 0))
            x += 24
        prev.resize((prev.width * 5, prev.height * 5), Image.NEAREST).save(sys.argv[2])


main()
