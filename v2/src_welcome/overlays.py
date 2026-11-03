"""Welcome cinematic camera overlays (pack r27, equippable camera_overlay starkffa:misc/welcome/wN, stretched full-screen).
w0 black | w1-w4 fade in from black | w5 letterbox bars + light vignette | w6-w8 white flash (picture area) | w9-w11 bars open."""
import math, numpy as np
from PIL import Image
W, H = 640, 360
BAR = 0.11
OUT = '/tmp/claude-0/work/welcome/ov/'
yy, xx = np.mgrid[0:H, 0:W].astype(np.float64)
nx = (xx / (W - 1) - 0.5) * 2; ny = (yy / (H - 1) - 0.5) * 2
d = np.sqrt((nx * 0.92) ** 2 + ny ** 2)
vig = np.clip((d - 0.66) / 0.78, 0, 1) ** 1.7
dist = np.minimum(yy, H - 1 - yy)
def frame(name, bar=1.0, black=0.0, flash=0.0, vig_k=1.0):
    rgb = np.zeros((H, W, 3)); a = np.zeros((H, W))
    # vignette (slate-black, soft)
    a_v = vig * 0.34 * vig_k
    rgb[:] = (6, 8, 12); a = a_v.copy()
    # white flash in the picture area (slightly ice-tinted)
    if flash > 0:
        fa = flash * (0.92 - 0.25 * np.clip(d - 0.4, 0, 1))
        col = np.array([238, 250, 255.0])
        rgb = rgb * (a / np.maximum(a + fa * (1 - a), 1e-6))[..., None] + col * (fa * (1 - a) / np.maximum(a + fa * (1 - a), 1e-6))[..., None]
        a = a + fa * (1 - a)
    # fade from black over everything
    if black > 0:
        rgb = rgb * (a / np.maximum(a + black * (1 - a), 1e-6))[..., None] + np.array([3, 4, 6.0]) * (black * (1 - a) / np.maximum(a + black * (1 - a), 1e-6))[..., None]
        a = a + black * (1 - a)
    # letterbox bars with a soft 2 px edge and a faint cyan rim
    bh = bar * BAR * H
    if bh > 0:
        inside = dist < bh - 1
        edge = (dist >= bh - 1) & (dist < bh + 1.5)
        rgb[inside] = (4, 5, 8); a[inside] = 1.0
        t = np.clip((dist - (bh - 1)) / 2.5, 0, 1)
        rim = np.array([63, 224, 255.0])
        ec = np.array([4, 5, 8.0]) * 0.7 + rim * 0.3
        rgb[edge] = ec
        a[edge] = np.maximum(a[edge], 1.0 - t[edge] * 0.75)
    img = np.dstack([np.clip(rgb, 0, 255), np.clip(a * 255, 0, 255)]).round().astype(np.uint8)
    Image.fromarray(img, 'RGBA').save(OUT + name + '.png', optimize=True)
    return img
frames = [('w0', dict(bar=1.0, black=1.0)),
          ('w1', dict(bar=1.0, black=0.8)), ('w2', dict(bar=1.0, black=0.58)), ('w3', dict(bar=1.0, black=0.36)), ('w4', dict(bar=1.0, black=0.16)),
          ('w5', dict(bar=1.0)),
          ('w6', dict(bar=1.0, flash=0.9)), ('w7', dict(bar=1.0, flash=0.55)), ('w8', dict(bar=1.0, flash=0.24)),
          ('w9', dict(bar=0.66, vig_k=0.7)), ('w10', dict(bar=0.33, vig_k=0.4)), ('w11', dict(bar=0.1, vig_k=0.15))]
ims = {n: frame(n, **kw) for n, kw in frames}
# preview over a backdrop
bg = Image.new('RGBA', (W, H), (110, 160, 210, 255))
sheet = Image.new('RGBA', (W * 3 + 20, H * 2 + 10), (30, 30, 30, 255))
for i, k in enumerate(['w0', 'w2', 'w5', 'w6', 'w8', 'w10']):
    c = bg.copy(); c.alpha_composite(Image.fromarray(ims[k], 'RGBA'))
    sheet.alpha_composite(c, ((i % 3) * (W + 10), (i // 3) * (H + 10)))
sheet.save('/tmp/claude-0/-home-claude/f196a605-ce72-5550-83a8-35be259707e7/scratchpad/welcome_overlays.png')
print('ok')
