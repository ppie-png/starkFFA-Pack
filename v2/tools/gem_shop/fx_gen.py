"""Pack r41 cosmetic FX sprites (gem shop v2): soft-glow sprites in the style of fx_glow / fx_ring, white +
greyscale so the custom_model_data tint colours them. Vertical planes are drawn camera-facing (billboard), horizontal
ones lie on the ground. Writes textures/item, models/item and items JSON into OUT/assets/starkffa."""
import json, math, os, random, sys
from PIL import Image, ImageDraw, ImageFilter

SS = 4  # supersampling


def canvas(w, h):
    return Image.new('L', (w * SS, h * SS), 0)


def down(mask, w, h):
    return mask.resize((w, h), Image.LANCZOS)


def glow(mask_hi, w, h, radius, strength=1.0):
    """soft halo around a hi-res mask (returned at final size)"""
    m = down(mask_hi, w, h)
    g = m.filter(ImageFilter.GaussianBlur(radius))
    return g.point(lambda v: min(255, int(v * strength)))


def compose(core, halo, w, h, core_grey=255, edge_grey=200, halo_alpha=0.75, shade=None):
    """core (L, final size) = opaque body, halo (L) = glow alpha; grey ramps from edge_grey (outer body) to core_grey"""
    out = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    cp, hp = core.load(), halo.load()
    op = out.load()
    # distance-ish brightness: blur of the core = 1 in the middle, lower at the edges
    inner = core.filter(ImageFilter.GaussianBlur(max(1, w // 32)))
    ip = inner.load()
    for y in range(h):
        for x in range(w):
            c = cp[x, y] / 255.0
            a_h = hp[x, y] / 255.0 * halo_alpha
            t = ip[x, y] / 255.0
            grey = edge_grey + (core_grey - edge_grey) * t
            if shade is not None:
                grey *= shade(x / (w - 1), y / (h - 1))
            a = c + a_h * (1 - c)
            if a <= 0.002:
                continue
            # body grey where the core is, white-ish glow elsewhere
            g = (grey * c + 255 * a_h * (1 - c)) / a
            op[x, y] = (int(min(255, g)),) * 3 + (int(min(255, a * 255)),)
    return out


# ---------------------------------------------------------------------------------------------- sprites
def heart(w=64):
    """bold glowing heart: bright body, a darker rim that defines the silhouette, white highlight, a thin glow"""
    m = canvas(w, w)
    px = m.load()
    S = w * SS
    for yy in range(S):
        for xx in range(S):
            x = (xx / S - 0.5) * 2.5
            y = -(yy / S - 0.53) * 2.5
            if (x * x + y * y - 1) ** 3 - x * x * y ** 3 <= 0:
                px[xx, yy] = 255
    core = down(m, w, w)
    halo = glow(m, w, w, w / 18, 1.3)
    rim = core.filter(ImageFilter.MinFilter(5))            # body without its outer 2 px
    out = Image.new('RGBA', (w, w), (0, 0, 0, 0))
    cp, hp, rp, op = core.load(), halo.load(), rim.load(), out.load()
    for y in range(w):
        for x in range(w):
            c, hh, r = cp[x, y] / 255, hp[x, y] / 255 * 0.45, rp[x, y] / 255
            a = c + hh * (1 - c)
            if a < 0.004:
                continue
            body = 168 + (255 - 168) * r                    # rim 168, inside 255
            body *= 0.90 + 0.10 * (1 - y / w)
            g = (body * c + 255 * hh * (1 - c)) / a
            op[x, y] = (int(min(255, g)),) * 3 + (int(min(255, a * 255)),)
    d = ImageDraw.Draw(out)
    d.ellipse([w * 0.26, w * 0.25, w * 0.39, w * 0.36], fill=(255, 255, 255, 255))
    d.ellipse([w * 0.40, w * 0.27, w * 0.45, w * 0.31], fill=(255, 255, 255, 255))
    return out


def star(w=64, rays=4, long_=0.48, short=0.0, thick=0.075):
    m = canvas(w, w)
    d = ImageDraw.Draw(m)
    S = w * SS
    c = S / 2
    def ray(ang, length, width):
        pts = []
        for k in (-1, 1):
            pts.append((c + math.cos(ang + k * math.pi / 2) * width * S, c + math.sin(ang + k * math.pi / 2) * width * S))
        tip = (c + math.cos(ang) * length * S, c + math.sin(ang) * length * S)
        d.polygon([pts[0], tip, pts[1]], fill=255)
    for i in range(rays):
        ray(i * 2 * math.pi / rays - math.pi / 2, long_, thick)
    if short > 0:
        for i in range(rays):
            ray(i * 2 * math.pi / rays - math.pi / 2 + math.pi / rays, short, thick * 0.7)
    d.ellipse([c - S * 0.07, c - S * 0.07, c + S * 0.07, c + S * 0.07], fill=255)
    core = down(m, w, w)
    halo = glow(m, w, w, w / 9, 2.2)
    return compose(core, halo, w, w, 255, 235, 0.85)


def note(w=64):
    m = canvas(w, w)
    d = ImageDraw.Draw(m)
    S = w * SS
    # tilted oval head
    head = Image.new('L', (S, S), 0)
    hd = ImageDraw.Draw(head)
    hx, hy, rx, ry = S * 0.40, S * 0.72, S * 0.15, S * 0.105
    hd.ellipse([hx - rx, hy - ry, hx + rx, hy + ry], fill=255)
    head = head.rotate(24, center=(hx, hy), resample=Image.BICUBIC)
    m.paste(255, mask=head)
    # stem
    sx = hx + rx * 0.86
    d.rectangle([sx - S * 0.035, S * 0.18, sx + S * 0.035, hy - S * 0.02], fill=255)
    # flag
    d.polygon([(sx, S * 0.18), (sx + S * 0.20, S * 0.33), (sx + S * 0.16, S * 0.46), (sx + S * 0.03, S * 0.33)], fill=255)
    core = down(m, w, w)
    halo = glow(m, w, w, w / 11, 1.8)
    return compose(core, halo, w, w, 255, 205, 0.7)


def splat(w=128, seed=7):
    rnd = random.Random(seed)
    m = canvas(w, w)
    d = ImageDraw.Draw(m)
    S = w * SS
    c = S / 2
    blobs = [(0, 0, 0.30)]
    for i in range(11):
        a = rnd.random() * math.tau
        r = 0.10 + rnd.random() * 0.16
        dist = 0.12 + rnd.random() * 0.16
        blobs.append((math.cos(a) * dist, math.sin(a) * dist, r))
    for i in range(14):  # droplets
        a = rnd.random() * math.tau
        dist = 0.34 + rnd.random() * 0.12
        r = 0.018 + rnd.random() * 0.035
        blobs.append((math.cos(a) * dist, math.sin(a) * dist, r))
    for (bx, by, r) in blobs:
        d.ellipse([c + (bx - r) * S, c + (by - r) * S, c + (bx + r) * S, c + (by + r) * S], fill=255)
    m = m.filter(ImageFilter.GaussianBlur(S / 160)).point(lambda v: 255 if v > 110 else 0)
    core = down(m, w, w)
    halo = glow(m, w, w, w / 60, 1.0)
    def sh(u, v):  # glossy sheen streak
        return 0.78 + 0.22 * max(0.0, 1 - abs((u - v) + 0.18) * 6)
    return compose(core, halo, w, w, 235, 175, 0.35, sh)


def bolt(w=32, h=256, seed=3):
    rnd = random.Random(seed)
    m = Image.new('L', (w * SS, h * SS), 0)
    d = ImageDraw.Draw(m)
    W, H = w * SS, h * SS
    x = W / 2
    pts = [(x, 0)]
    y = 0
    while y < H:
        y += H * (0.05 + rnd.random() * 0.07)
        x = max(W * 0.16, min(W * 0.84, x + (rnd.random() - 0.5) * W * 0.9))
        pts.append((x, min(H, y)))
    d.line(pts, fill=255, width=int(W * 0.15), joint='curve')
    # two small branches
    for k in range(2):
        i = 2 + rnd.randrange(max(1, len(pts) - 4))
        bx, by = pts[i]
        bpts = [(bx, by)]
        for j in range(3):
            bx += (rnd.random() - 0.5) * W * 0.6
            by += H * 0.04
            bpts.append((max(2, min(W - 2, bx)), by))
        d.line(bpts, fill=255, width=int(W * 0.06), joint='curve')
    core = m.resize((w, h), Image.LANCZOS)
    halo = m.resize((w, h), Image.LANCZOS).filter(ImageFilter.GaussianBlur(w / 6)).point(lambda v: min(255, int(v * 2.6)))
    return compose(core, halo, w, h, 255, 240, 0.8)


def scorch(w=128, seed=11):
    rnd = random.Random(seed)
    out = Image.new('RGBA', (w, w), (0, 0, 0, 0))
    px = out.load()
    noise = [[rnd.random() for _ in range(w)] for _ in range(w)]
    for y in range(w):
        for x in range(w):
            u, v = (x - w / 2) / (w / 2), (y - w / 2) / (w / 2)
            r = math.hypot(u, v)
            ang = math.atan2(v, u)
            edge = 0.78 + 0.12 * math.sin(ang * 5 + 1.3) + 0.06 * math.sin(ang * 11)
            if r > edge:
                continue
            t = r / edge
            a = (1 - t ** 2.2) * 0.92
            grey = 60 + 70 * t + noise[y][x] * 18
            # radial cracks (lighter)
            crack = max(0.0, 1 - abs(math.sin(ang * 7 + r * 3)) * 9) * (1 - t) * 0.9
            grey = grey + crack * 120
            px[x, y] = (int(grey),) * 3 + (int(a * 255),)
    return out.filter(ImageFilter.GaussianBlur(0.6))


def wing(w=64):
    """angel wing: smooth upper arm curve, a fan of rounded primary feathers below, separation lines"""
    S = w * SS
    m = canvas(w, w)
    d = ImageDraw.Draw(m)
    def bez(p0, p1, p2, t):
        return ((1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * p1[0] + t * t * p2[0],
                (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * p1[1] + t * t * p2[1])
    k, o = 0.86, 0.07
    P = lambda x, y: (o + x * k, o + y * k)
    root, ctrl, tip = P(0.07, 0.60), P(0.38, 0.00), P(0.97, 0.08)
    top = [bez(root, ctrl, tip, i / 40) for i in range(41)]
    tips = [P(0.95, 0.30), P(0.88, 0.50), P(0.77, 0.67), P(0.63, 0.81), P(0.47, 0.90), P(0.31, 0.90), P(0.18, 0.78)]
    poly = [(x * S, y * S) for x, y in top] + [(x * S, y * S) for x, y in tips] + [(root[0] * S, root[1] * S)]
    d.polygon(poly, fill=255)
    for (x, y) in tips:
        d.ellipse([(x - 0.055) * S, (y - 0.055) * S, (x + 0.055) * S, (y + 0.055) * S], fill=255)
    core = down(m, w, w)
    halo = glow(m, w, w, w / 16, 1.5)
    def sh(u, v):
        return 0.93 + 0.07 * (1 - v)
    im = compose(core, halo, w, w, 255, 238, 0.7, sh)
    # feather separation lines (from the arm down between the tips) + a soft covert line
    lines = canvas(w, w)
    ld = ImageDraw.Draw(lines)
    arm = [bez(root, ctrl, tip, t) for t in (0.30, 0.42, 0.54, 0.66, 0.78, 0.90)]
    gaps = [((tips[i][0] + tips[i + 1][0]) / 2, (tips[i][1] + tips[i + 1][1]) / 2) for i in range(len(tips) - 1)]
    for a, g in zip(reversed(arm), gaps):
        ld.line([(a[0] * S, (a[1] + 0.10) * S), (g[0] * S, (g[1] - 0.02) * S)], fill=255, width=int(0.022 * S))
    cov = [bez(P(0.12, 0.62), P(0.40, 0.22), P(0.86, 0.22), t) for t in [i / 20 for i in range(21)]]
    ld.line([(x * S, y * S) for x, y in cov], fill=255, width=int(0.02 * S))
    lm = down(lines, w, w).load()
    px = im.load()
    for y in range(w):
        for x in range(w):
            r, g, b, a = px[x, y]
            k = lm[x, y] / 255.0
            if k > 0 and a > 0:
                f = 1 - 0.20 * k
                px[x, y] = (int(r * f), int(g * f), int(b * f), a)
    return im


def ghost(w=64):
    """a little ghost sheet that hangs below the head: round shoulders, flaring sides, a wavy hem"""
    m = canvas(w, w)
    d = ImageDraw.Draw(m)
    S = w * SS
    d.ellipse([0.20 * S, 0.02 * S, 0.80 * S, 0.62 * S], fill=255)
    d.polygon([(0.20 * S, 0.32 * S), (0.80 * S, 0.32 * S), (0.88 * S, 0.80 * S), (0.12 * S, 0.80 * S)], fill=255)
    for i in range(4):                                       # wavy hem
        cx = 0.12 + 0.76 * (i + 0.5) / 4
        d.ellipse([(cx - 0.105) * S, 0.70 * S, (cx + 0.105) * S, 0.92 * S], fill=255)
    core = down(m, w, w)
    halo = glow(m, w, w, w / 12, 1.4)
    def sh(u, v):
        return 0.86 + 0.14 * (1 - abs(u - 0.5) * 2)
    im = compose(core, halo, w, w, 255, 226, 0.6, sh)
    px = im.load()
    for y in range(w):
        for x in range(w):
            r, g, b, a = px[x, y]
            if a:
                px[x, y] = (r, g, b, int(a * 0.82))          # a little see-through
    return im


def target(w=128):
    m = canvas(w, w)
    d = ImageDraw.Draw(m)
    S = w * SS
    c = S / 2
    def ring(r, t):
        d.ellipse([c - r * S, c - r * S, c + r * S, c + r * S], outline=255, width=int(t * S))
    ring(0.47, 0.035)
    ring(0.30, 0.018)
    # dashed inner ring
    for i in range(16):
        a0 = i * math.tau / 16
        d.arc([c - 0.38 * S, c - 0.38 * S, c + 0.38 * S, c + 0.38 * S], math.degrees(a0), math.degrees(a0) + 12, fill=255, width=int(0.02 * S))
    for i in range(4):  # tick marks
        a = i * math.pi / 2
        d.line([(c + math.cos(a) * 0.36 * S, c + math.sin(a) * 0.36 * S), (c + math.cos(a) * 0.49 * S, c + math.sin(a) * 0.49 * S)], fill=255, width=int(0.03 * S))
    d.ellipse([c - 0.05 * S, c - 0.05 * S, c + 0.05 * S, c + 0.05 * S], fill=255)
    core = down(m, w, w)
    halo = glow(m, w, w, w / 40, 1.6)
    return compose(core, halo, w, w, 255, 230, 0.7)



def wind(w=128, streaks=5, seed=5):
    """r81b wind ring for the vortex funnel (lies flat like fx_swirl/fx_ring, the code turns it to the camera): five
    tapered, slightly inward-curling streaks round an open middle + a faint base ring - squashed to an ellipse and spun
    it reads as a spinning ring of wind from every side"""
    rnd = random.Random(seed)
    S = w * SS
    m = canvas(w, w)
    d = ImageDraw.Draw(m)
    c = S / 2.0
    # faint full ring so the ellipse stays readable between the streaks
    for i in range(60):
        r = (0.64 + 0.22 * i / 59) * c
        v = int(64 * math.sin(math.pi * i / 59))
        d.ellipse((c - r, c - r, c + r, c + r), outline=v, width=SS)
    gap = 2 * math.pi / streaks
    for k in range(streaks):
        a0 = k * gap + rnd.uniform(-0.12, 0.12)
        length = gap * rnd.uniform(0.78, 0.9)
        r0, r1 = rnd.uniform(0.80, 0.86), rnd.uniform(0.62, 0.68)
        steps = 260
        for s in range(steps):
            u = s / (steps - 1)
            a = a0 - u * length
            r = (r0 + (r1 - r0) * u) * c
            th = (0.095 * (1 - u) ** 0.8 + 0.014) * c
            v = int(255 * (1 - u) ** 1.25)
            x, y = c + math.cos(a) * r, c + math.sin(a) * r
            d.ellipse((x - th, y - th, x + th, y + th), fill=max(v, 0))
    core = down(m, w, w)
    halo = core.filter(ImageFilter.GaussianBlur(2.2))
    out = Image.new('RGBA', (w, w), (0, 0, 0, 0))
    cp, hp, op = core.load(), halo.load(), out.load()
    for y in range(w):
        for x in range(w):
            a = max(cp[x, y], int(hp[x, y] * 0.6))
            if a < 2:
                continue
            g = 255 if cp[x, y] > 90 else 236
            op[x, y] = (g, g, g, min(255, a))
    return out


def funnel(w=64, h=128, seed=9):
    """r81b tornado body for the vortex (camera-facing, VERTICAL billboard): a soft translucent cone, wide at the top,
    a thin neck at the bottom, denser at its edges (a shell of wind), faint diagonal streaks"""
    rnd = random.Random(seed)
    out = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    op = out.load()
    ph = [rnd.uniform(0, math.pi * 2) for _ in range(3)]
    for y in range(h):
        t = y / (h - 1)                      # 0 top .. 1 bottom
        hw = (0.47 - 0.40 * t ** 0.85) * w   # half width
        top = min(1.0, t / 0.16)             # fade in at the top
        bot = min(1.0, (1 - t) / 0.05)       # fade into the ground
        for x in range(w):
            dx = abs(x + 0.5 - w / 2) / max(0.5, hw)
            if dx >= 1.0:
                continue
            edge = 1.0 - max(0.0, (dx - 0.78) / 0.22) ** 1.6   # soft outer edge
            shell = 0.42 + 0.58 * dx ** 2.2                  # denser at the edges
            xs = (x + 0.5 - w / 2) / (w / 2)
            streak = 0.78 + 0.22 * math.sin(xs * 7.0 + t * 15.0 + ph[0]) * math.sin(xs * 3.1 - t * 6.0 + ph[1])
            a = 190 * edge * shell * streak * top * bot
            if a < 2:
                continue
            op[x, y] = (255, 255, 255, int(min(255, a)))
    return out


SPRITES = {
    # id: (builder, orientation)  v = camera-facing plane, h = ground decal
    'fx_heart': (heart, 'v'),
    'fx_star': (lambda: star(64, 4, 0.48, 0.20, 0.07), 'v'),
    'fx_starburst': (lambda: star(64, 8, 0.49, 0.30, 0.05), 'v'),
    'fx_note': (note, 'v'),
    'fx_bolt': (lambda: bolt(32, 256, 3), 'v'),
    'fx_bolt2': (lambda: bolt(32, 256, 19), 'v'),
    'fx_wing': (wing, 'v'),
    'fx_ghost': (ghost, 'v'),
    'fx_splat': (splat, 'h'),
    'fx_scorch': (scorch, 'h'),
    'fx_target': (target, 'h'),
    'fx_wind': (wind, 'h'),
    'fx_funnel': (funnel, 'v'),
}


def model(tex, orient):
    if orient == 'v':
        el = {'from': [0, 0, 8], 'to': [16, 16, 8], 'faces': {
            'north': {'uv': [16, 0, 0, 16], 'texture': '#0', 'tintindex': 0},
            'south': {'uv': [0, 0, 16, 16], 'texture': '#0', 'tintindex': 0}}}
    else:
        el = {'from': [0, 8, 0], 'to': [16, 8, 16], 'faces': {
            'up': {'uv': [0, 0, 16, 16], 'texture': '#0', 'tintindex': 0},
            'down': {'uv': [0, 16, 16, 0], 'texture': '#0', 'tintindex': 0}}}
    return {'textures': {'0': 'starkffa:item/' + tex, 'particle': 'starkffa:item/' + tex}, 'elements': [el]}


def write(out):
    base = os.path.join(out, 'assets/starkffa')
    for sub in ('textures/item', 'models/item', 'items'):
        os.makedirs(os.path.join(base, sub), exist_ok=True)
    for sid, (fn, orient) in SPRITES.items():
        fn().save(os.path.join(base, 'textures/item', sid + '.png'))
        json.dump(model(sid, orient), open(os.path.join(base, 'models/item', sid + '.json'), 'w'), indent=1)
        json.dump({'model': {'type': 'minecraft:model', 'model': 'starkffa:item/' + sid,
                             'tints': [{'type': 'minecraft:custom_model_data', 'index': 0, 'default': 16777215}]}},
                  open(os.path.join(base, 'items', sid + '.json'), 'w'), indent=1)
    return list(SPRITES)


if __name__ == '__main__':
    out = sys.argv[1] if len(sys.argv) > 1 else '/home/claude/gemshop/fx/out'
    print(write(out))
