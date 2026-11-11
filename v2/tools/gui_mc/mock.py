"""Offline mock of a chest menu the way the client draws it at GUI scale 1: background texture, title (vanilla font,
coloured, with shadow), item sprites in the slots, the player's kit in the inventory part. Saved 3x (nearest).
Usage: python3 mock.py <background.png> <rows> <title> <accent hex> <out.png> [slot=item ...]"""
import os
import sys

from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gui_mc  # noqa: E402

ITEMS = '/tmp/claude-0/vref2/assets/minecraft/textures/item/'


def sprite(name):
    if name == 'potion':
        base = Image.open(ITEMS + 'potion.png').convert('RGBA')
        ov = Image.open(ITEMS + 'potion_overlay.png').convert('RGBA')
        tint = Image.new('RGBA', ov.size, (248, 36, 35, 255))
        ov2 = Image.composite(tint, Image.new('RGBA', ov.size, (0, 0, 0, 0)), ov.split()[3])
        out = Image.new('RGBA', base.size)
        out.alpha_composite(ov2)
        out.alpha_composite(base)
        return out
    return Image.open(ITEMS + name + '.png').convert('RGBA')


def main():
    bg, rows, title, accent, out = sys.argv[1], int(sys.argv[2]), sys.argv[3], gui_mc.H(sys.argv[4]), sys.argv[5]
    items = dict(a.split('=') for a in sys.argv[6:])
    im = Image.open(bg).convert('RGBA')
    W, Hh = im.size
    scene = Image.new('RGBA', (W + 40, Hh + 40), (58, 62, 70, 255))
    scene.alpha_composite(im, (20, 20))

    class C:  # tiny canvas adapter for the font
        def put(self, x, y, c, a=255):
            if 0 <= x < scene.width and 0 <= y < scene.height:
                scene.putpixel((x, y), tuple(c) + (a,))
    f = gui_mc.font()
    f.draw(C(), 20 + 8, 20 + 6, title, accent)
    for k, v in items.items():
        s = int(k)
        if '@' in v:
            v, tile = v.split('@')
            t = Image.open(os.environ.get('TILE_DIR', '/tmp/claude-0/r48x/assets/starkffa/textures/font/gui/shop') + '/tile_' + tile + '.png').convert('RGBA')
            scene.alpha_composite(t, (20 + gui_mc.sx(s) - 1, 20 + gui_mc.sy(s) - 1))
        scene.alpha_composite(sprite(v), (20 + gui_mc.sx(s), 20 + gui_mc.sy(s)))
    py = 18 + rows * 18 + 13
    kit = ['diamond_sword', 'bow', 'golden_apple', 'ender_pearl', 'wind_charge', 'potion', 'potion', 'cooked_beef', 'arrow']
    for c, n in enumerate(kit):
        scene.alpha_composite(sprite(n), (20 + 8 + c * 18, 20 + py + 58))
    for r in range(3):
        for c in range(9):
            if (r + c) % 3 == 0:
                scene.alpha_composite(sprite('potion'), (20 + 8 + c * 18, 20 + py + r * 18))
    scene = scene.resize((scene.width * 3, scene.height * 3), Image.NEAREST)
    scene.save(out)


main()
