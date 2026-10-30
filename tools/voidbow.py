"""Black Hole Bow sprites + animated black-hole texture (pixel art drawn by code)."""
import math
from PIL import Image

def hx(s, a=255):
    s = s.lstrip("#"); return (int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16), a)

LIMB, LIMB_HI, GRIP, GEM, GEM_HI, STRING = hx("#3B2466"), hx("#9A6BE0"), hx("#1A1026"), hx("#B07CFF"), hx("#F2E6FF"), hx("#A894CC")
ARROW, TIP = hx("#C9B79C"), hx("#C9A7FF")

def bow(pull):
    """pull: None (standby) or 0..2 (drawing stages)."""
    im = Image.new("RGBA", (16, 16), (0, 0, 0, 0)); px = im.load()
    u = (1 / math.sqrt(2), -1 / math.sqrt(2))      # forward (towards top-right)
    w = (1 / math.sqrt(2), 1 / math.sqrt(2))       # along the limbs
    c = (6.2, 9.0); L, k = 7.4, 4.0
    def put(x, y, col):
        xi, yi = int(round(x)), int(round(y))
        if 0 <= xi < 16 and 0 <= yi < 16: px[xi, yi] = col
    ends = []
    for i in range(241):
        s = -L + 2 * L * i / 240
        b = k * (1 - (s / L) ** 2)
        x = c[0] + w[0] * s + u[0] * b; y = c[1] + w[1] * s + u[1] * b
        put(x, y, LIMB); put(x + u[0] * .6, y + u[1] * .6, LIMB)
        put(x + u[0] * 1.3, y + u[1] * 1.3, LIMB_HI)       # outer highlight
    for s in (-L, L):
        ends.append((c[0] + w[0] * s, c[1] + w[1] * s))
    # string (V when pulled)
    back = [0, 1.8, 2.8, 3.7][0 if pull is None else pull + 1]
    mid = (c[0] - u[0] * back, c[1] - u[1] * back)
    for a, b in ((ends[0], mid), (mid, ends[1])):
        for i in range(60):
            t = i / 59; put(a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t, STRING)
    # grip + gem
    gx, gy = c[0] + u[0] * k, c[1] + u[1] * k
    put(gx, gy, GRIP); put(gx - u[0], gy - u[1], GRIP)
    put(gx + u[0] * 1.6, gy + u[1] * 1.6, GEM)
    if pull is not None:
        # arrow from the string forward, void tip
        for i in range(40):
            t = i / 39 * (6 + back)
            put(mid[0] + u[0] * t, mid[1] + u[1] * t, ARROW)
        tip = (mid[0] + u[0] * (6.6 + back), mid[1] + u[1] * (6.6 + back))
        put(*tip, TIP); put(tip[0] - u[0], tip[1] - u[1], GEM)
        # gem glows brighter while drawing
        put(gx + u[0] * 1.6, gy + u[1] * 1.6, GEM_HI if pull >= 1 else GEM)
    return im

def black_hole(frames=8, size=16):
    """Animated: black core, purple accretion ring with a bright arc that orbits."""
    sheet = Image.new("RGBA", (size, size * frames), (0, 0, 0, 0)); px = sheet.load()
    cx = cy = (size - 1) / 2
    for f in range(frames):
        ang0 = 2 * math.pi * f / frames
        for y in range(size):
            for x in range(size):
                dx, dy = x - cx, y - cy; r = math.hypot(dx, dy); a = math.atan2(dy, dx)
                if r < 3.2:
                    px[x, y + f * size] = (6, 2, 12, 255)
                elif r < 4.3:
                    px[x, y + f * size] = (30, 10, 50, 255)                    # event horizon edge
                elif r < 7.4:
                    spiral = (a - ang0 + (r - 4) * 0.55) % (2 * math.pi)
                    hot = max(0.0, math.cos(spiral)) ** 3
                    base = 1 - (r - 4.3) / 3.1
                    col = tuple(int(v) for v in (
                        60 + 150 * hot + 40 * base, 25 + 90 * hot, 110 + 140 * hot + 30 * base))
                    alpha = int(255 * min(1, base * 1.4 + hot * .5))
                    if alpha > 20: px[x, y + f * size] = col + (alpha,)
    return sheet

def icon():
    rows = ["..#####..", ".##...##.", "##.###.##", "#.#...#.#", "#.#.#.#.#",
            "#.#...#.#", "##.###.##", ".##...##.", "..#####.."]
    im = Image.new("RGBA", (9, 9), (0, 0, 0, 0)); px = im.load()
    for y, r in enumerate(rows):
        for x, ch in enumerate(r):
            if ch == "#":
                d = math.hypot(x - 4, y - 4)
                px[x, y] = hx("#F2E6FF") if d < 1.5 else (hx("#C9A7FF") if d < 3 else hx("#7A4FC9"))
    return im
