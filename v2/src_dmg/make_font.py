"""STARK damage-number font (pack r30, font starkffa:dmg).

Fortnite-style numbers: heavy condensed digits (Anton, OFL) with a thick black outline and a soft drop shadow
baked into the glyphs. The fill is a white -> light grey gradient: Minecraft multiplies glyph pixels with the text
colour, so the fill takes any colour (white / crit yellow / shield cyan / kill red) with a darker bottom, the outline
and the shadow stay black.

Glyph sets (one bitmap provider each, cells left aligned, the provider measures each glyph's width itself):
  big     '0'-'9'                  height 12, ascent 10  (cell 48 px = 4 px per font unit)
  small   U+E000-U+E009 digits,    height 8,  ascent 6   (cell 32 px, bottoms line up with the big digits)
          U+E00A '.'
  letters 'A'-'Z'                  height 10, ascent 8   (cell 40 px, for BLOCKED)
  space   U+E020 = -2 units (tight kerning between big digits), U+E021 = -1, ' ' = 3
"""
import json
import sys
from PIL import Image, ImageDraw, ImageFont, ImageFilter

FONT = sys.argv[1]
OUT = sys.argv[2]

OUTLINE = 4          # px at 4 px per font unit = 1 unit
SHADOW_DY = 3
SHADOW_A = 150


def glyph(ch, size, cell_h, cell_w, outline=OUTLINE, shadow_dy=SHADOW_DY, top_light=255, bottom_light=186):
    f = ImageFont.truetype(FONT, size)
    l, t, r, b = f.getbbox(ch)
    w, h = r - l, b - t
    pad = outline + 2
    W, H = w + 2 * pad, h + 2 * pad + shadow_dy
    # masks: body, outline (stroke)
    body = Image.new('L', (W, H), 0)
    ImageDraw.Draw(body).text((pad - l, pad - t), ch, font=f, fill=255)
    stroke = Image.new('L', (W, H), 0)
    ImageDraw.Draw(stroke).text((pad - l, pad - t), ch, font=f, fill=255, stroke_width=outline, stroke_fill=255)
    # drop shadow = the stroked shape moved down, softened a bit
    shadow = Image.new('L', (W, H), 0)
    shadow.paste(stroke, (0, shadow_dy))
    shadow = shadow.filter(ImageFilter.GaussianBlur(0.6)).point(lambda v: v * SHADOW_A // 255)
    img = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    img.putalpha(shadow)
    blk = Image.new('RGBA', (W, H), (0, 0, 0, 255))
    img = Image.composite(blk, img, stroke)
    # gradient fill over the glyph's own height (bright top, darker bottom - the tint keeps it)
    grad = Image.new('RGBA', (W, H))
    gd = ImageDraw.Draw(grad)
    y0, y1 = pad, pad + h
    for y in range(H):
        k = min(1, max(0, (y - y0) / max(1, (y1 - y0))))
        # slight highlight band at the top third, then down to bottom_light
        v = int(top_light + (bottom_light - top_light) * (k ** 1.25))
        gd.line([(0, y), (W, y)], fill=(v, v, v, 255))
    img = Image.composite(grad, img, body)
    # crop to the drawn area, place it into the cell: left aligned, the outline bottom (+ shadow) on the cell bottom
    bbox = img.getbbox()
    x0, x1 = bbox[0], bbox[2]
    top = pad - outline                      # the outline's top edge (round glyphs reach 1 px higher: bbox)
    top = min(top, bbox[1])
    bottom = y1 + outline + shadow_dy        # baseline-ish bottom shared by all glyphs of the set
    img = img.crop((x0, top, x1, bottom))
    if img.width > cell_w or img.height > cell_h:
        raise SystemExit(f'{ch!r}: glyph {img.size} bigger than cell {cell_w}x{cell_h}')
    cell = Image.new('RGBA', (cell_w, cell_h), (0, 0, 0, 0))
    cell.alpha_composite(img, (0, cell_h - img.height))
    return cell


def strip(chars, size, cell_h, cell_w=0, **kw):
    # cell width = the widest glyph of the set (the provider needs equal cells; glyphs stay left aligned)
    widest = max(glyph(ch, size, cell_h, 400, **kw).getbbox()[2] for ch in chars)
    cell_w = max(cell_w, widest + 1)
    sheet = Image.new('RGBA', (cell_w * len(chars), cell_h), (0, 0, 0, 0))
    for i, ch in enumerate(chars):
        sheet.alpha_composite(glyph(ch, size, cell_h, cell_w, **kw), (i * cell_w, 0))
    return sheet


big = strip('0123456789', 40, 48)
small = strip('0123456789.', 24, 32, shadow_dy=2)
letters_a = strip('ABCDEFGHIJKLM', 32, 40, 34)
letters_b = strip('NOPRSTUVWXYZ', 32, 40, 34)
cw = max(letters_a.width // 13, letters_b.width // 12)
letters_a = strip('ABCDEFGHIJKLM', 32, 40, cw)
letters_b = strip('NOPRSTUVWXYZ', 32, 40, cw)
letters = Image.new('RGBA', (cw * 13, 80), (0, 0, 0, 0))
letters.alpha_composite(letters_a, (0, 0))
letters.alpha_composite(letters_b, (0, 40))
big.save(f'{OUT}/dmg_big.png')
small.save(f'{OUT}/dmg_small.png')
letters.save(f'{OUT}/dmg_letters.png')

font = {"providers": [
    {"type": "space", "advances": {" ": 3, "": -2, "": -1, "": -1.5}},
    {"type": "bitmap", "file": "starkffa:font/dmg/dmg_big.png", "height": 12, "ascent": 10, "chars": ["0123456789"]},
    {"type": "bitmap", "file": "starkffa:font/dmg/dmg_small.png", "height": 8, "ascent": 6,
     "chars": ["".join(chr(0xE000 + i) for i in range(10)) + ""]},
    {"type": "bitmap", "file": "starkffa:font/dmg/dmg_letters.png", "height": 10, "ascent": 8,
     "chars": ["ABCDEFGHIJKLM", "NOPRSTUVWXYZ\u0000"]},
]}
with open(f'{OUT}/dmg.json', 'w', encoding='utf-8') as fp:
    json.dump(font, fp, indent=1, ensure_ascii=True)
print('ok', big.size, small.size, letters.size)
