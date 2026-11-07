# glyph widths of the vanilla bitmap fonts (as the client computes them: last opaque column + 1, advance = width + 1)
import json
from PIL import Image
INC = '/home/claude/ext/client263/assets/minecraft/font/include/default.json'
TEX = '/home/claude/ext/client263/assets/minecraft/textures/font/'
PACK_SYM = '⛃⛁✦✕✖▸➶➜♛⟳◌✱⇡▪'
_W = {}
def _load():
    d = json.load(open(INC))
    for p in d['providers']:
        if p.get('type') != 'bitmap': continue
        rows = p['chars']; f = p['file'].split('/')[-1]
        im = Image.open(TEX + f).convert('RGBA')
        cw = im.width // len(rows[0]); ch = im.height // len(rows)
        h = p.get('height', 8)
        scale = h / ch
        px = im.load()
        for r, row in enumerate(rows):
            for c, chx in enumerate(row):
                if chx in ('\u0000', ' ') or chx in _W: continue
                w = 0
                for x in range(cw - 1, -1, -1):
                    if any(px[c * cw + x, r * ch + y][3] > 0 for y in range(ch)):
                        w = x + 1; break
                _W[chx] = int(0.5 + w * scale) + 1
    _W[' '] = 4
    for s, a in zip(PACK_SYM, [8, 8, 8, 6, 7, 4, 8, 8, 8, 8, 8, 6, 6, 4]): _W[s] = a   # STARK pixel symbols (pack default font)
_load()
def adv(ch, bold=False):
    return _W.get(ch, 6) + (1 if bold and ch != ' ' else 0)
def width(s, bold=False):
    return sum(adv(c, bold) for c in s)
if __name__ == '__main__':
    for s in ['ɢᴇᴍ ꜱʜᴏᴘ', 'ᴛᴏᴅᴀʏ\'ꜱ ᴅᴇᴀʟꜱ', 'STAR1XY', '✦ 128', 'ᴀʙᴄᴅᴇꜰɢʜɪᴊᴋʟᴍɴᴏᴘǫʀꜱᴛᴜᴠᴡxʏᴢ']:
        print(repr(s), width(s), width(s, True), [adv(c) for c in s])
    print('chars known', len(_W))
