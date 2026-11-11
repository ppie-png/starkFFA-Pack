"""STARK menus v3 (pack r49, owner 11.11. 18:53: "the dark lifeless tone without gradients or a block texture like
Minecraft has ... the quest items aren't sorted fittingly ... the background may say DAILY and WEEKLY, but don't bake
all the text into the GUI"). Every menu background is built here from one style:

- panel: a vertical colour gradient times a pixel block texture (4 shades of value noise, stretched like deepslate),
  a 1 px outline with vanilla's notched corners and a 2 px bevel (light top-left, dark bottom-right) like the vanilla
  container, the menu's accent glowing in from the header;
- slots: vanilla insets (dark top-left, light bottom-right, a darker centre);
- sections: inset panels with an accent frame; labels in the VANILLA font (assets/minecraft/textures/font/ascii.png),
  only short words (DAILY, WEEKLY ...), everything else stays in item names and lore.

GUI coordinates as in vanilla: 176 px wide, chest row r at y = 18 + 18 r, slot s at x = 8 + 18 (s % 9);
player inventory at y = 18 + 18 rows + 13, hotbar 58 px lower.
Usage: python3 gui_mc.py <style> <out_dir> [menus...]   -> <out_dir>/<file>.png for every menu (and a mock preview)."""
import math
import os
import sys

from PIL import Image

FONT_PNG = os.environ.get('MC_ASCII', '/tmp/claude-0/vref2/assets/minecraft/textures/font/ascii.png')
H = lambda s: tuple(int(s[i:i + 2], 16) for i in (1, 3, 5))

ACCENTS = {
    'cyan': H('#3FE0FF'), 'amber': H('#FFB547'), 'red': H('#FF4D5E'), 'green': H('#3DFFA2'), 'purple': H('#AC74FF'),
    'pink': H('#F47FFF'), 'gold': H('#FFD24D'),
}

STYLES = {
    # S1: neutral deepslate, the accent only in the header glow, lines and section frames
    'deepslate': dict(top=H('#3A4556'), bottom=H('#1A1F28'), tint=0.0, glow=0.22, glow_h=26, tex=0.16,
                      outline=H('#07090D'), light=H('#5E6D84'), dark=H('#0D1016'),
                      slot_in=H('#141922'), slot_tl=H('#0A0D12'), slot_br=H('#4B586E'), slot_tex=0.05),
    # S2: the whole panel is tinted by the menu's accent (quests green, gem shop purple, shop amber ...)
    'tinted': dict(top=H('#3A4556'), bottom=H('#171B23'), tint=0.30, glow=0.30, glow_h=40, tex=0.16,
                   outline=H('#07090D'), light=H('#66768E'), dark=H('#0D1016'),
                   slot_in=H('#12161E'), slot_tl=H('#090B10'), slot_br=H('#4B586E'), slot_tex=0.05),
    # S3: polished blackstone - darker, stronger block pattern, the accent glows down from the header
    # S2b: tinted + polished-deepslate tiles + a soft vignette
    'tiles': dict(top=H('#3D4859'), bottom=H('#151920'), tint=0.34, glow=0.34, glow_h=44, tex=0.13, tiles=True,
                  vignette=0.35, outline=H('#07090D'), light=H('#6B7B93'), dark=H('#0B0E13'),
                  slot_in=H('#11151C'), slot_tl=H('#080A0E'), slot_br=H('#4E5C73'), slot_tex=0.05),
    'blackstone': dict(top=H('#2E2A33'), bottom=H('#141218'), tint=0.10, glow=0.42, glow_h=60, tex=0.24,
                       outline=H('#050407'), light=H('#5A5462'), dark=H('#09080B'),
                       slot_in=H('#100E13'), slot_tl=H('#070609'), slot_br=H('#4A4452'), slot_tex=0.06),
}


def lerp(a, b, t):
    t = max(0.0, min(1.0, t))
    return tuple(int(round(a[i] + (b[i] - a[i]) * t)) for i in range(3))


def mul(c, f):
    return tuple(max(0, min(255, int(round(v * f)))) for v in c)


def h32(x, y, s):
    n = (x * 374761393 + y * 668265263 + s * 2147483647) & 0xFFFFFFFF
    n = ((n ^ (n >> 13)) * 1274126177) & 0xFFFFFFFF
    return ((n ^ (n >> 16)) & 0xFFFF) / 65535.0


def vnoise(x, y, sx, sy, seed):
    gx, gy = x / sx, y / sy
    x0, y0 = int(math.floor(gx)), int(math.floor(gy))
    fx, fy = gx - x0, gy - y0
    fx, fy = fx * fx * (3 - 2 * fx), fy * fy * (3 - 2 * fy)
    a, b = h32(x0, y0, seed), h32(x0 + 1, y0, seed)
    c, d = h32(x0, y0 + 1, seed), h32(x0 + 1, y0 + 1, seed)
    return (a + (b - a) * fx) * (1 - fy) + (c + (d - c) * fx) * fy


def block_shade(x, y, seed=7):
    """Deepslate-like pixel texture: 4 discrete shades, streaks stretched sideways, a little per-pixel grain."""
    v = 0.62 * vnoise(x, y, 7.0, 3.0, seed) + 0.38 * h32(x, y, seed + 11)
    q = int(v * 4)                     # 0..3
    return (-1.0, -0.35, 0.35, 1.0)[max(0, min(3, q))]


class Canvas:
    def __init__(self, w, h, style, accent):
        self.w, self.h = w, h
        self.st = STYLES[style]
        self.ac = ACCENTS[accent]
        self.im = Image.new('RGBA', (w, h), (0, 0, 0, 0))
        self.px = self.im.load()

    def put(self, x, y, c, a=255):
        if 0 <= x < self.w and 0 <= y < self.h:
            self.px[x, y] = tuple(c) + (a,)

    def get(self, x, y):
        return self.px[x, y][:3]

    def panel(self):
        st, W, Hh = self.st, self.w, self.h
        for y in range(Hh):
            base = lerp(st['top'], st['bottom'], y / max(1, Hh - 1))
            base = lerp(base, mul(self.ac, 0.45), st['tint'] * (1 - 0.6 * y / Hh))
            g = max(0.0, 1 - y / st['glow_h']) ** 1.6 * st['glow']
            base = lerp(base, self.ac, g)
            for x in range(W):
                s = block_shade(x, y)
                c = mul(base, 1 + st['tex'] * s)
                if st.get('tiles'):
                    # polished-deepslate tiles: 16 px blocks, each a little lighter or darker, a dark seam on the
                    # bottom/right of every block and a light one on its top/left (offset rows like bricks)
                    ty = y // 16
                    ox = 8 if ty % 2 else 0
                    tx = (x + ox) // 16
                    c = mul(c, 1 + 0.06 * (h32(tx, ty, 5) - 0.5) * 2)
                    if (x + ox) % 16 == 15 or y % 16 == 15:
                        c = mul(c, 0.82)
                    elif (x + ox) % 16 == 0 or y % 16 == 0:
                        c = mul(c, 1.08)
                if st.get('vignette'):
                    dx = (x - W / 2) / (W / 2)
                    dy = (y - Hh * 0.35) / Hh
                    c = mul(c, 1 - st['vignette'] * min(1.0, (dx * dx * 0.7 + dy * dy)))
                self.put(x, y, c)
        # outline with vanilla's notched corners + 2 px bevel
        for x in range(W):
            for y in range(Hh):
                edge = x == 0 or y == 0 or x == W - 1 or y == Hh - 1
                corner = (x < 2 or x > W - 3) and (y < 2 or y > Hh - 3)
                if corner and (x in (0, W - 1) or y in (0, Hh - 1)):
                    self.px[x, y] = (0, 0, 0, 0)
                    continue
                if edge:
                    self.put(x, y, st['outline'])
                elif x in (1, 2) and 1 <= y <= Hh - 3 or y in (1, 2) and 1 <= x <= W - 3:
                    self.put(x, y, lerp(self.get(x, y), st['light'], 0.75 if (x == 1 or y == 1) else 0.4))
                elif x in (W - 2, W - 3) and y >= 2 or y in (Hh - 2, Hh - 3) and x >= 2:
                    self.put(x, y, lerp(self.get(x, y), st['dark'], 0.85 if (x == W - 2 or y == Hh - 2) else 0.5))
        for (x, y) in ((1, 1), (W - 2, 1), (1, Hh - 2), (W - 2, Hh - 2)):
            self.put(x, y, st['outline'])

    def hline(self, x0, x1, y, fade=True):
        """Accent divider that fades out to both ends."""
        for x in range(x0, x1):
            t = abs((x - (x0 + x1) / 2) / ((x1 - x0) / 2))
            c = lerp(self.ac, self.get(x, y), t ** 1.4 if fade else 0.0)
            self.put(x, y, c)
            self.put(x, y + 1, lerp(self.get(x, y + 1), self.st['dark'], 0.6))

    def slot(self, x, y, accent=None, strength=0.0):
        """Vanilla inset slot: the item area is x..x+15, the slot is x-1..x+16."""
        st = self.st
        inner = st['slot_in'] if accent is None else lerp(st['slot_in'], accent, strength)
        br = st['slot_br'] if accent is None else lerp(st['slot_br'], accent, 0.55)
        for yy in range(y - 1, y + 17):
            for xx in range(x - 1, x + 17):
                if xx == x - 1 or yy == y - 1:
                    c = st['slot_tl']
                elif xx == x + 16 or yy == y + 16:
                    c = br
                else:
                    c = mul(inner, 1 + st['slot_tex'] * block_shade(xx, yy, 3))
                self.put(xx, yy, c)
        if accent is not None and strength > 0:
            self.put(x + 16, y - 1, lerp(st['slot_tl'], br, 0.5))
            self.put(x - 1, y + 16, lerp(st['slot_tl'], br, 0.5))

    def section(self, x0, y0, x1, y1, accent=None, fill=0.10):
        """Inset panel: darker inside, accent frame (bright on top fading down), 1 px rounded."""
        ac = self.ac if accent is None else accent
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                if (x in (x0, x1)) and (y in (y0, y1)):
                    continue
                if x in (x0, x1) or y in (y0, y1):
                    t = (y - y0) / max(1, y1 - y0)
                    c = lerp(ac, mul(ac, 0.35), t ** 0.8)
                    if y == y1:
                        c = mul(ac, 0.3)
                    self.put(x, y, c)
                else:
                    c = lerp(self.get(x, y), self.st['slot_in'], 0.55)
                    c = lerp(c, ac, fill * (1 - (y - y0) / max(1, y1 - y0)))
                    self.put(x, y, c)

    def player_inventory(self, rows):
        y = 18 + rows * 18 + 13
        self.hline(7, self.w - 7, y - 6)
        for r in range(3):
            for c in range(9):
                self.slot(8 + c * 18, y + r * 18)
        for c in range(9):
            self.slot(8 + c * 18, y + 58)


# ---------------------------------------------------------------- vanilla font

class Font:
    def __init__(self, path=FONT_PNG):
        im = Image.open(path).convert('RGBA')
        self.im = im
        self.w = {}
        for code in range(32, 127):
            cx, cy = (code % 16) * 8, (code // 16) * 8
            wmax = 0
            for x in range(8):
                for y in range(8):
                    if im.getpixel((cx + x, cy + y))[3] > 0:
                        wmax = max(wmax, x + 1)
            self.w[code] = wmax if code != 32 else 3

    def width(self, s):
        return sum(self.w.get(ord(ch), 5) + 1 for ch in s) - 1

    def draw(self, cv, x, y, s, color, shadow=True):
        for pass_ in ((1, mul(color, 0.25)), (0, color)) if shadow else ((0, color),):
            off, col = pass_
            cx = x
            for ch in s:
                code = ord(ch)
                gx, gy = (code % 16) * 8, (code // 16) * 8
                for yy in range(8):
                    for xx in range(8):
                        if self.im.getpixel((gx + xx, gy + yy))[3] > 0:
                            cv.put(cx + xx + off, y + yy + off, col)
                cx += self.w.get(code, 5) + 1


FONT = None


def font():
    global FONT
    if FONT is None:
        FONT = Font()
    return FONT


def label(cv, cx, y, s, color):
    f = font()
    f.draw(cv, cx - f.width(s) // 2, y, s, color)


# ---------------------------------------------------------------- menus

def sx(slot):
    return 8 + (slot % 9) * 18


def sy(slot):
    return 18 + (slot // 9) * 18


def chest(style, rows, accent):
    W, Hh = 176, 114 + rows * 18
    cv = Canvas(W, Hh, style, accent)
    cv.panel()
    cv.hline(6, W - 6, 14)
    for s in range(rows * 9):
        cv.slot(sx(s), sy(s))
    cv.player_inventory(rows)
    return cv


def quests(style, bonus=True):
    """4 rows: DAILY panel (left, 3 quests in row 1) and WEEKLY panel (right), labels in row 0, BONUS in row 3."""
    rows = 4
    W, Hh = 176, 114 + rows * 18
    cv = Canvas(W, Hh, style, 'green')
    cv.panel()
    old_icon(cv, 'menu/bg_quests.png')
    cv.hline(6, W - 6, 14)
    green, cyan, amber = ACCENTS['green'], ACCENTS['cyan'], ACCENTS['amber']
    # daily: slots 10 11 12 (x 26..79), weekly 14 15 16 (x 98..151); panels from row 0 to row 2
    for (s0, ac, word) in ((10, green, 'DAILY'), (14, cyan, 'WEEKLY')):
        x0, x1 = sx(s0) - 4, sx(s0 + 2) + 19
        cv.section(x0, 18, x1, sy(s0) + 21, ac, 0.16)
        label(cv, (x0 + x1) // 2 + 1, 23, word, ac)
        for k in range(3):
            cv.slot(sx(s0 + k), sy(s0), ac, 0.10)
    if bonus:
        # one-time bonus: the same kind of panel, centred - label in row 2, the slot in row 3 (slot 31)
        cx = sx(31) + 8
        cv.section(cx - 22, sy(22) + 2, cx + 22, sy(31) + 21, amber, 0.14)
        label(cv, cx + 1, sy(22) + 7, 'BONUS', amber)
        cv.slot(sx(31), sy(31), amber, 0.16)
    cv.player_inventory(rows)
    return cv


OLD_GUI = os.environ.get('OLD_GUI', '/tmp/claude-0/r48x/assets/starkffa/textures/font/gui')


def old_icon(cv, path):
    """Copy the header icon of the old background (top-left, x 6..21, y 2..13): every pixel that is not the old panel."""
    try:
        im = Image.open(os.path.join(OLD_GUI, path)).convert('RGBA')
    except OSError:
        return
    ref = im.getpixel((30, 8))[:3]
    for y in range(2, 14):
        for x in range(5, 22):
            c = im.getpixel((x, y))
            if c[3] > 0 and sum(abs(c[i] - ref[i]) for i in range(3)) > 40:
                cv.put(x, y, c[:3])


def ender(style):
    """Ender chest: rows 0-1 storage, row 2 = the vault pages (purple)."""
    rows = 3
    cv = Canvas(176, 114 + rows * 18, style, 'purple')
    cv.panel()
    old_icon(cv, 'menu/bg_ender.png')
    cv.hline(6, 170, 14)
    for s_ in range(18):
        cv.slot(sx(s_), sy(s_))
    cv.section(5, sy(18) - 3, 170, sy(18) + 18, ACCENTS['purple'], 0.14)
    for s_ in range(18, 27):
        cv.slot(sx(s_), sy(s_), ACCENTS['purple'], 0.12)
    cv.player_inventory(rows)
    return cv


def vault(style):
    rows = 6
    cv = Canvas(176, 114 + rows * 18, style, 'purple')
    cv.panel()
    old_icon(cv, 'menu/bg_vault.png')
    cv.hline(6, 170, 14)
    for s_ in range(54):
        cv.slot(sx(s_), sy(s_))
    cv.player_inventory(rows)
    return cv


SETTINGS_LABELS = ['PRO HUD', 'SIDEBAR', 'KILL FEED', 'JOINS', 'MESSAGES', 'MENTIONS', 'LOW HP', 'READY SFX']


def settings(style):
    """Two list panels: icon (col 0 / col 5) | label | live switch (overlay glyph at x 63 / 153)."""
    rows = 4
    cv = Canvas(176, 114 + rows * 18, style, 'cyan')
    cv.panel()
    old_icon(cv, 'menu/bg_settings.png')
    cv.hline(6, 170, 14)
    cyan = ACCENTS['cyan']
    for col, x0, x1 in ((0, 5, 84), (5, 95, 172)):
        cv.section(x0, 16, x1, sy(27) + 19, cyan, 0.08)
        for r in range(4):
            slot = r * 9 + col
            cv.slot(sx(slot), sy(slot), cyan, 0.08)
            # r141: no words here - the vanilla font does not fit between icon and switch, the item names say it
            # (the chest version is only the fallback of the /settings dialog)
    cv.player_inventory(rows)
    return cv


def gemshop(style, rows, tiers=False):
    """Gem shop: an open panel (the items get rarity tiles as overlays), pink accent; tiers = rarity bars on the left."""
    cv = Canvas(176, 114 + rows * 18, style, 'pink')
    cv.panel()
    cv.hline(6, 170, 14)
    if tiers:
        cols = [H('#8A96A8'), H('#3FE0FF'), H('#AC74FF'), H('#FFB547'), H('#FF4D5E')]
        for r in range(1, 6):
            c = cols[r - 1]
            for y in range(sy(r * 9), sy(r * 9) + 16):
                for x in (3, 4):
                    cv.put(x, y, lerp(c, cv.get(x, y), 0.15 if x == 3 else 0.45))
    cv.player_inventory(rows)
    return cv


RARITY = {'common': H('#9AA6B8'), 'rare': H('#3FB4FF'), 'epic': H('#AC74FF'), 'legendary': H('#FFB547'),
          'mythic': H('#FF4D5E'), 'exclusive': H('#3DFFA2'), 'gem': H('#F47FFF')}


def tile(style, kind):
    """18 x 18 rarity tile under a gem shop item: a slot inset tinted in the rarity colour with the block texture,
    dark rim top-left, bright rim bottom-right (vanilla's inset light), notched corners; mythic gets a gold rim."""
    st = STYLES[style]
    c = RARITY[kind]
    cv = Canvas(18, 18, style, 'cyan')
    for y in range(18):
        for x in range(18):
            if (x in (0, 17)) and (y in (0, 17)):
                continue
            inner = lerp(st['slot_in'], c, 0.42 - 0.16 * y / 17)
            col = mul(inner, 1 + 0.10 * block_shade(x + 3, y + 5, 9))
            if x == 0 or y == 0:
                col = lerp(st['slot_tl'], c, 0.25)
            elif x == 17 or y == 17:
                col = lerp(c, (255, 255, 255), 0.15)
            elif x == 1 or y == 1:
                col = mul(col, 0.8)
            if kind == 'mythic' and (x in (0, 17) or y in (0, 17)):
                col = H('#FFD24D') if (x + y) % 2 == 0 or x in (0, 17) and y in (1, 16) else H('#E0A93A')
            cv.put(x, y, col)
    return cv


MENUS = {
    'chest3_cyan.png': lambda st: chest(st, 3, 'cyan'), 'chest3_amber.png': lambda st: chest(st, 3, 'amber'),
    'chest4_cyan.png': lambda st: chest(st, 4, 'cyan'), 'chest4_amber.png': lambda st: chest(st, 4, 'amber'),
    'chest5_cyan.png': lambda st: chest(st, 5, 'cyan'), 'chest5_amber.png': lambda st: chest(st, 5, 'amber'),
    'chest6_cyan.png': lambda st: chest(st, 6, 'cyan'), 'chest6_amber.png': lambda st: chest(st, 6, 'amber'),
    'menu/bg_quests.png': lambda st: quests(st, True), 'menu/bg_quests_nb.png': lambda st: quests(st, False),
    'menu/bg_ender.png': ender, 'menu/bg_vault.png': vault, 'menu/bg_settings.png': settings,
    'shop/bg5.png': lambda st: gemshop(st, 5), 'shop/bg6.png': lambda st: gemshop(st, 6),
    'shop/bg6t.png': lambda st: gemshop(st, 6, True),
}
for _k in RARITY:
    MENUS['shop/tile_' + _k + '.png'] = (lambda kind: (lambda st: tile(st, kind)))(_k)


if __name__ == '__main__':
    style, out = sys.argv[1], sys.argv[2]
    for name in (sys.argv[3:] or MENUS.keys()):
        cv = MENUS[name](style)
        dest = os.path.join(out, name)
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        cv.im.save(dest)
        print(name, cv.im.size)
