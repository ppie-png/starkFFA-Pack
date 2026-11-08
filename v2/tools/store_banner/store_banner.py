"""/store dialog banner (pack font starkffa:store): two product cards like the web store - RANKS (the three paid rank
badges) and GEMS (our pink 3D gem). Drawn at 2x (texture 564x184 -> glyph 282x92 GUI px) so the art is crisp at GUI
scale 2/4. Text is the vanilla bitmap font (small caps), baked in."""
import sys
sys.path.insert(0, '/home/claude/gemshop/art')
from PIL import Image, ImageDraw, ImageFilter
import mock, fontw
from mock import hx, draw_text, gradient_runs

GW, GH = 282, 92          # banner size in GUI px
CW, GAP = 140, 2          # card width (GUI px) and the gap = the dialog's button columns (140 + 2 + 140)
S = 2
ICONS = '/home/claude/gemshop/pack41/build/assets/starkffa/textures/font/ranks/icons.png'
GEM = '/home/claude/storeui/gem_card.png'
GRAY = hx('#A9B3C4')


def rounded(w, h, r, top, bottom, alpha):
    img = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    grad = Image.new('RGBA', (w, h))
    px = grad.load()
    for y in range(h):
        t = y / (h - 1)
        c = tuple(int(top[i] + (bottom[i] - top[i]) * t) for i in range(3))
        for x in range(w):
            px[x, y] = c + (alpha,)
    mask = Image.new('L', (w, h), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, w - 1, h - 1), radius=r, fill=255)
    img.paste(grad, (0, 0), mask)
    return img, mask


def border(w, h, r, col, width=2):
    ring = Image.new('L', (w, h), 0)
    d = ImageDraw.Draw(ring)
    d.rounded_rectangle((0, 0, w - 1, h - 1), radius=r, outline=255, width=width)
    out = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    px = out.load(); pr = ring.load()
    for y in range(h):
        a = int(255 - 150 * (y / (h - 1)))
        for x in range(w):
            if pr[x, y]:
                out[x, y] if False else None
                px[x, y] = col + (a * pr[x, y] // 255,)
    return out


def glow(w, h, cx, cy, rad, col, a):
    g = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(g).ellipse((cx - rad, cy - rad * 0.8, cx + rad, cy + rad * 0.8), fill=col + (a,))
    return g.filter(ImageFilter.GaussianBlur(rad * 0.45))


def card(kind):
    w, h = CW * S, GH * S
    accent = hx('#FFB547') if kind == 'ranks' else hx('#FF8AD8')
    base, mask = rounded(w, h, 7, (34, 24, 56), (17, 12, 29), 236)
    out = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    out.alpha_composite(base)
    gl = glow(w, h, w // 2, 46 if kind == 'ranks' else 62, 70 if kind == 'ranks' else 76,
              hx('#7B5CFF') if kind == 'ranks' else hx('#FF5FC8'), 70)
    gl.putalpha(Image.composite(gl.getchannel('A'), Image.new('L', (w, h), 0), mask))
    out.alpha_composite(gl)
    text = Image.new('RGBA', (CW, GH), (0, 0, 0, 0))     # 1x layer for the vanilla font
    if kind == 'ranks':
        icons = Image.open(ICONS).convert('RGBA')
        ranks = [(8, 'ꜱᴘᴀʀᴋ', ['#3DFFA2', '#3FE0FF'], '#3DFFA2'), (6, 'ꜱᴛᴏʀᴍ', ['#7B6CFF', '#3FE0FF'], '#8F7BFF'),
                 (5, 'ꜱᴛᴀʀᴋ', ['#FFB547', '#FFF0B8', '#FFB547'], '#FFB547')]
        for i, (idx, name, stops, gcol) in enumerate(ranks):
            cx = int(w * (i + 0.5) / 3)
            out.alpha_composite(glow(w, h, cx, 44, 26, hx(gcol), 90))
            ic = icons.crop((idx * 8, 0, idx * 8 + 8, 8)).resize((48, 48), Image.NEAREST)
            out.alpha_composite(ic, (cx - 24, 20))
            runs = gradient_runs(name, [hx(s) for s in stops], True)
            tw = mock.text_width(runs)
            draw_text(text, cx // S - tw // 2, 37, runs, shadow_col=(0, 0, 0))
        lines = ['ʏᴏᴜʀ ʙᴀᴅɢᴇ ɪɴ ᴄʜᴀᴛ,', 'ᴛᴀʙ & ᴀʙᴏᴠᴇ ʏᴏᴜʀ ʜᴇᴀᴅ']
    else:
        gem = Image.open(GEM).convert('RGBA')
        k = 132 / gem.height
        gem = gem.resize((int(gem.width * k), 132), Image.LANCZOS)
        out.alpha_composite(gem, ((w - gem.width) // 2, 0))
        lines = ['ᴋɪʟʟ ᴇꜰꜰᴇᴄᴛꜱ, ᴛʀᴀɪʟꜱ,', 'ɴᴀᴍᴇ ꜱᴛʏʟᴇꜱ & ᴍᴏʀᴇ']
    for j, ln in enumerate(lines):
        runs = [(ln, GRAY, False)]
        tw = mock.text_width(runs)
        draw_text(text, (CW - tw) // 2, 66 + 11 * j, runs, shadow_col=(0, 0, 0))
    out.alpha_composite(text.resize((w, h), Image.NEAREST))
    # keep everything inside the rounded card, then the border on top
    a = Image.composite(out.getchannel('A'), Image.new('L', (w, h), 0), mask)
    out.putalpha(a)
    out.alpha_composite(border(w, h, 7, accent))
    return out


def banner():
    img = Image.new('RGBA', (GW * S, GH * S), (0, 0, 0, 0))
    img.alpha_composite(card('ranks'), (0, 0))
    img.alpha_composite(card('gems'), ((CW + GAP) * S, 0))
    return img


def strip():
    """The font atlas takes glyphs up to 256 px: each card is cut into two 140x184 halves -> 4 glyphs U+E000-E003
    in one row (no gap; the gap between the cards is a space glyph in the font)."""
    a, b = card('ranks'), card('gems')
    out = Image.new('RGBA', (4 * CW, GH * S), (0, 0, 0, 0))
    for i, c in enumerate((a, b)):
        out.alpha_composite(c.crop((0, 0, CW, GH * S)), (2 * i * CW, 0))
        out.alpha_composite(c.crop((CW, 0, 2 * CW, GH * S)), ((2 * i + 1) * CW, 0))
    return out


if __name__ == '__main__':
    b = banner()
    b.save('/home/claude/storeui/banner_2x.png')
    strip().save('/home/claude/storeui/banner_strip.png')
    for t in ['ʏᴏᴜʀ ʙᴀᴅɢᴇ ɪɴ ᴛʜᴇ ᴄʜᴀᴛ,', 'ᴛᴀʙ ʟɪꜱᴛ & ᴀʙᴏᴠᴇ ʏᴏᴜʀ ʜᴇᴀᴅ', 'ɴᴀᴍᴇ ꜱᴛʏʟᴇꜱ, ᴋɪʟʟ ᴇꜰꜰᴇᴄᴛꜱ,', 'ᴋɪʟʟ ᴍᴇꜱꜱᴀɢᴇꜱ & ᴛʀᴀɪʟꜱ']:
        print(t, fontw.width(t))
    print(b.size)
