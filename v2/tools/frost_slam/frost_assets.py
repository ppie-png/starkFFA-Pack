"""STARK pack r38 - Frost Slam assets (cloud-Claude r75).

  starkffa:fx_crystal   3D ice crystal shard (item display FX: slam eruption, freeze cocoon, shatter)
  starkffa:fx_frost     flat frost-crack decal for the ground (tinted by custom_model_data colour)
  starkffa:frost_slam   the weapon: 3D ice-crystal mace (replaces the recoloured vanilla mace)

usage: python3 frost_assets.py <out-dir>      (writes <out>/assets/starkffa/...)
"""
import json
import math
import os
import sys

import numpy as np
from PIL import Image

RNG = np.random.default_rng(75)


def hexc(s, a=255):
    s = s.lstrip('#')
    return (int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16), a)


def lerp(c0, c1, t):
    return tuple(int(round(c0[i] + (c1[i] - c0[i]) * t)) for i in range(4))


def ramp(stops, t):
    """stops: [(t, rgba)], t in 0..1"""
    t = max(0.0, min(1.0, t))
    for (t0, c0), (t1, c1) in zip(stops, stops[1:]):
        if t <= t1:
            return lerp(c0, c1, (t - t0) / max(1e-6, t1 - t0))
    return stops[-1][1]


def shade(c, f):
    return (min(255, int(c[0] * f)), min(255, int(c[1] * f)), min(255, int(c[2] * f)), c[3])


def mix_white(c, t):
    return lerp(c, (255, 255, 255, c[3]), t)


# ---------------------------------------------------------------- fx_crystal (16 x 16)
ICE = [(0.0, hexc('#F2FDFF', 236)), (0.22, hexc('#C4F1FF', 226)), (0.5, hexc('#8AD8F8', 218)),
       (0.78, hexc('#5BB3EC', 222)), (1.0, hexc('#3C8DD8', 232))]


def crystal_texture():
    img = Image.new('RGBA', (16, 16), (0, 0, 0, 0))
    px = img.load()
    for region, (u0, deep) in enumerate([(0, 0.0), (4, 0.06), (8, -0.08)]):
        for v in range(16):
            base = ramp(ICE, v / 15.0 + deep)
            for k in range(4):
                c = base
                if k == 0:
                    c = mix_white(c, 0.35)                 # lit edge of the facet
                elif k == 3:
                    c = shade(c, 0.78)                     # shadow edge
                n = RNG.normal(0, 0.035)
                c = shade(c, 1 + n)
                px[u0 + k, v] = c
        # facet streak: a short white diagonal glint
        y0 = int(RNG.integers(7, 12))
        px[u0, y0] = (255, 255, 255, 250)
        px[u0 + 1, y0 - 1] = mix_white(px[u0 + 1, y0 - 1], 0.6)
    # caps: bright top (v 0..8), deep bottom (v 8..16)
    for v in range(16):
        for u in range(12, 16):
            if v < 8:
                c = mix_white(ramp(ICE, 0.1 + 0.05 * abs(u - 13.5)), 0.25)
            else:
                c = ramp(ICE, 0.85)
            px[u, v] = c
    px[13, 1] = px[14, 2] = (255, 255, 255, 255)
    return img


def box(fr, to, tex, uvs, rot=None, light=None, shade_=True):
    """uvs: dict face -> [u0, v0, u1, v1] (16-unit UV space)"""
    faces = {f: {'uv': [round(x, 3) for x in uv], 'texture': tex} for f, uv in uvs.items()}
    e = {'from': [round(x, 4) for x in fr], 'to': [round(x, 4) for x in to], 'faces': faces}
    if rot:
        e['rotation'] = {'origin': [round(x, 4) for x in rot[0]], 'axis': rot[1], 'angle': rot[2]}
    if light:
        e['light_emission'] = light
    if not shade_:
        e['shade'] = False
    return e


def sides(uv, alt=None):
    alt = alt or uv
    return {'north': uv, 'south': alt, 'east': alt, 'west': uv}


def crystal_model():
    """5 tapering tiers, alternately turned 45 / 22.5 deg: reads as a faceted ice crystal, not a stepped tower"""
    T = '#0'
    tiers = [  # (y0, y1, half width, uv column, rotation)
        (0.0, 8.2, 2.0, 0, 45), (6.4, 11.2, 1.55, 4, 22.5), (10.2, 13.6, 1.12, 8, 45),
        (12.9, 15.0, 0.7, 12, 22.5), (14.6, 16.0, 0.32, 12, 45)]
    els = []
    for k, (y0, y1, hw, u, ang) in enumerate(tiers):
        v0 = 16 - y1
        v1 = 16 - y0
        w = 2 * hw
        uv = [u, v0, min(16, u + w), v1]
        uv2 = [u, v0, min(16, u + w * 0.9), v1]
        faces = {**sides(uv, uv2), 'up': [12, 0, 12 + min(4, w), min(4, w)]}
        if k == 0:
            faces['down'] = [12, 12, 16, 16]
        els.append(box([8 - hw, y0, 8 - hw], [8 + hw, y1, 8 + hw], T, faces, rot=([8, 0, 8], 'y', ang)))
    return {'textures': {'0': 'starkffa:item/fx_crystal', 'particle': 'starkffa:item/fx_crystal'}, 'elements': els}


# ---------------------------------------------------------------- fx_frost decal (128 x 128)
def frost_texture(S=128):
    a = np.zeros((S, S), np.float32)
    c = (S - 1) / 2.0
    yy, xx = np.mgrid[0:S, 0:S]
    r = np.hypot(xx - c, yy - c)

    def stamp(x, y, w, alpha):
        x0, x1 = int(max(0, x - w - 1)), int(min(S, x + w + 2))
        y0, y1 = int(max(0, y - w - 1)), int(min(S, y + w + 2))
        if x0 >= x1 or y0 >= y1:
            return
        sub = np.hypot(xx[y0:y1, x0:x1] - x, yy[y0:y1, x0:x1] - y)
        val = np.clip(1.0 - (sub - w * 0.5) / 0.9, 0, 1) * alpha
        a[y0:y1, x0:x1] = np.maximum(a[y0:y1, x0:x1], val)

    def crack(x, y, ang, length, w0, alpha0, depth):
        """straight crystalline segments; frost ferns branch off at about 60 degrees"""
        steps = int(length / 1.2)
        for i in range(steps):
            t = i / max(1, steps - 1)
            w = w0 * (1 - 0.6 * t)
            stamp(x, y, w, alpha0 * (1 - 0.3 * t))
            if i % 7 == 6:
                ang += RNG.normal(0, 0.12)         # small kinks, no wobble
            x += math.cos(ang) * 1.2
            y += math.sin(ang) * 1.2
            if math.hypot(x - c, y - c) > c - 2:
                return
            if depth < 2 and i > 5 and i % 5 == 0 and RNG.random() < 0.55:
                side = 1 if RNG.random() < 0.5 else -1
                crack(x, y, ang + side * RNG.uniform(0.95, 1.12), length * RNG.uniform(0.16, 0.3), max(0.7, w * 0.62), alpha0 * 0.8, depth + 1)

    n = 12
    angs = [k * 2 * math.pi / n + RNG.uniform(-0.12, 0.12) for k in range(n)]
    for k, ang in enumerate(angs):
        L = RNG.uniform(50, 61) if k % 2 == 0 else RNG.uniform(34, 48)
        crack(c + math.cos(ang) * 6, c + math.sin(ang) * 6, ang, L, RNG.uniform(2.3, 3.0) if k % 2 == 0 else 1.7, 1.0, 0)
    # impact rings: concentric arc pieces between neighbouring cracks (how ice breaks around an impact)
    for ring_r, alpha in ((19, 0.85), (33, 0.6)):
        for k in range(n):
            if RNG.random() < 0.3:
                continue
            a0, a1 = angs[k], angs[(k + 1) % n] + (2 * math.pi if k == n - 1 else 0)
            rr = ring_r + RNG.uniform(-2.5, 2.5)
            steps = int((a1 - a0) * rr / 1.1)
            for s in range(steps + 1):
                th = a0 + (a1 - a0) * s / max(1, steps)
                rk = rr + 1.2 * math.sin(s * 0.9)
                stamp(c + math.cos(th) * rk, c + math.sin(th) * rk, 1.0, alpha)
    # inner frost bloom + a faint rime ring with specks
    a = np.maximum(a, np.clip(1 - r / 13.0, 0, 1) ** 1.4 * 0.95)
    ring = np.exp(-((r - 47) / 5.5) ** 2) * 0.22
    a = np.maximum(a, ring * (RNG.random((S, S)) > 0.55))
    for _ in range(34):
        rr, th = RNG.uniform(16, 56), RNG.uniform(0, 2 * math.pi)
        x, y = c + rr * math.cos(th), c + rr * math.sin(th)
        al = RNG.uniform(0.5, 0.9)
        for dx, dy in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)):
            xi, yi = int(round(x + dx)), int(round(y + dy))
            if 0 <= xi < S and 0 <= yi < S:
                a[yi, xi] = max(a[yi, xi], al * (1.0 if (dx, dy) == (0, 0) else 0.6))
    edge = np.clip((c - 1 - r) / 7.0, 0, 1)
    a = a * edge
    rgba = np.zeros((S, S, 4), np.uint8)
    rgba[..., :3] = 255
    rgba[..., 3] = np.clip(a * 255, 0, 255).astype(np.uint8)
    return Image.fromarray(rgba, 'RGBA')


def flat_model(tex):
    return {'textures': {'0': tex, 'particle': tex}, 'elements': [{
        'from': [0, 8, 0], 'to': [16, 8, 16],
        'faces': {'up': {'uv': [0, 0, 16, 16], 'texture': '#0', 'tintindex': 0},
                  'down': {'uv': [0, 16, 16, 0], 'texture': '#0', 'tintindex': 0}}}]}


# ---------------------------------------------------------------- the weapon (32 x 32 texture, 2 px per UV unit)
STEEL = [(0.0, hexc('#3C4F78')), (0.5, hexc('#243252')), (1.0, hexc('#151E33'))]
SILVER = [(0.0, hexc('#F4F8FC')), (0.45, hexc('#C6D2E4')), (1.0, hexc('#7F8EA8'))]
SPIKE = [(0.0, hexc('#FFFFFF', 245)), (0.2, hexc('#DDF8FF', 236)), (0.55, hexc('#9FE3FB', 226)), (1.0, hexc('#5FB8EE', 230))]


def weapon_texture():
    img = Image.new('RGBA', (32, 32), (0, 0, 0, 0))
    px = img.load()
    # steel shaft: x 0..4, y 0..16 (cylinder shading across x)
    for y in range(16):
        for x in range(4):
            px[x, y] = shade(ramp(STEEL, [0.15, 0.35, 0.65, 0.95][x]), 1 + RNG.normal(0, 0.03))
    # grip wrap: x 4..8, y 0..16 - diagonal cyan / white bands on navy
    for y in range(16):
        for x in range(4):
            band = (x + y) % 6
            if band in (0, 1):
                c = hexc('#8BF0FF')
            elif band == 2:
                c = hexc('#E9FBFF')
            else:
                c = ramp(STEEL, 0.55 + 0.1 * (x / 3))
            px[4 + x, y] = shade(c, [1.08, 1.0, 0.9, 0.8][x])
    # silver collar: x 8..16, y 0..4
    for y in range(4):
        for x in range(8):
            px[8 + x, y] = ramp(SILVER, y / 3.0)
    # rune glow line on the collar
    for x in range(8, 16, 2):
        px[x, 1] = hexc('#6FF0FF')
    # core glow: x 16..20, y 0..4
    for y in range(4):
        for x in range(4):
            d = math.hypot(x - 1.5, y - 1.5) / 2.1
            px[16 + x, y] = lerp(hexc('#FFFFFF'), hexc('#3FE0FF'), min(1, d))
    # head ice: x 0..16, y 16..32 (vertical gradient + facet edges + glints)
    for y in range(16):
        for x in range(16):
            c = ramp(ICE, 0.12 + 0.8 * y / 15.0)
            k = x % 4
            if k == 0:
                c = mix_white(c, 0.3)
            elif k == 3:
                c = shade(c, 0.8)
            px[x, 16 + y] = shade(c, 1 + RNG.normal(0, 0.03))
    for gx, gy in ((1, 20), (2, 19), (5, 25), (9, 21), (10, 20), (13, 27)):
        px[gx, gy] = (255, 255, 255, 252)
    # spikes: x 16..32, y 16..32 (lighter, white tips at the top rows)
    for y in range(16):
        for x in range(16):
            c = ramp(SPIKE, y / 15.0)
            k = x % 4
            if k == 0:
                c = mix_white(c, 0.25)
            elif k == 3:
                c = shade(c, 0.84)
            px[16 + x, 16 + y] = c
    # pommel + small frost: x 20..32, y 0..8 = bright ice
    for y in range(8):
        for x in range(12):
            px[20 + x, y] = mix_white(ramp(ICE, 0.2 + y / 10.0), 0.15 if x % 3 == 0 else 0.0)
    return img


def weapon_model():
    T = '#0'
    DY = -2.2       # whole model down: the grip sits where the vanilla mace grip sits

    def B(fr, to, uvs, rot=None, light=None):
        fr = [fr[0], fr[1] + DY, fr[2]]
        to = [to[0], to[1] + DY, to[2]]
        if rot:
            rot = ([rot[0][0], rot[0][1] + DY, rot[0][2]], rot[1], rot[2])
        return box(fr, to, T, uvs, rot, light)

    # UV regions (16-unit space = texture px / 2)
    steel = [0, 0, 2, 8]
    wrap = [2, 0, 4, 8]
    silver = [4, 0, 8, 2]
    core = [8, 0, 10, 2]
    ice = lambda u: [u, 8, u + 2, 16]            # noqa: E731  head body columns
    spike = lambda u, v0=8, v1=16: [8 + u, v0, 8 + u + 2, v1]   # noqa: E731
    pom = [10, 0, 16, 4]
    els = []
    # pommel crystal + collar
    els.append(B([7.1, -1.4, 7.1], [8.9, 1.0, 8.9], {**sides([10, 0, 11, 2], [11, 0, 12, 2]), 'down': [10, 2, 11, 3]}, rot=([8, 0, 8], 'y', 45)))
    els.append(B([6.9, 0.6, 6.9], [9.1, 1.6, 9.1], {**sides(silver), 'up': silver, 'down': silver}))
    # grip + cap + shaft
    els.append(B([7.25, 1.6, 7.25], [8.75, 7.4, 8.75], sides(wrap)))
    els.append(B([7.05, 7.2, 7.05], [8.95, 7.9, 8.95], {**sides(silver), 'up': silver, 'down': silver}))
    els.append(B([7.35, 7.9, 7.35], [8.65, 10.7, 8.65], sides(steel)))
    # head collar (silver ring with glowing runes)
    els.append(B([6.5, 10.4, 6.5], [9.5, 11.5, 9.5], {**sides([4, 0, 8, 1.1]), 'up': silver, 'down': silver}))
    # head body: big diamond crystal + a cross block for volume
    HB = ([8, 13, 8], 'y', 45)
    els.append(B([5.7, 11.2, 5.7], [10.3, 15.9, 10.3], {**sides(ice(0), ice(4)), 'up': [0, 8, 4, 10], 'down': [8, 12, 12, 16]}, rot=HB))
    els.append(B([6.4, 11.6, 6.4], [9.6, 15.5, 9.6], {**sides(ice(2), ice(6)), 'up': [2, 8, 5, 11], 'down': [2, 13, 5, 16]}))
    # glowing core band around the crystal (one continuous belt - no "eyes" from any side)
    els.append(B([5.52, 13.0, 5.52], [10.48, 13.75, 10.48], {**sides([8, 0, 10, 0.6]), 'up': core, 'down': core}, rot=HB, light=15))
    els.append(B([6.25, 13.0, 6.25], [9.75, 13.75, 9.75], {**sides([8, 0, 10, 0.6]), 'up': core, 'down': core}, light=15))

    def taper_y(tiers, x=8.0, z=8.0, uvx=0):
        for k, (y0, y1, hw) in enumerate(tiers):
            ang = 45 if k % 2 == 0 else 22.5
            els.append(B([x - hw, y0, z - hw], [x + hw, y1, z + hw], {**sides(spike(uvx, 8 + k * 1.5, 16), spike(uvx + 2, 8 + k * 1.5, 16)),
                                                                       'up': spike(uvx, 8, 9), 'down': spike(uvx + 2, 15, 16)},
                         rot=([x, y0, z], 'y', ang)))

    # crown spike on top: 4 tapering tiers, alternately turned
    taper_y([(15.4, 17.5, 1.05), (17.2, 19.0, 0.74), (18.7, 19.9, 0.46), (19.6, 20.5, 0.2)])
    # icicles hanging under the head at the diamond corners
    for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        cx, cz = 8 + dx * 2.55, 8 + dz * 2.55
        els.append(B([cx - 0.42, 10.0, cz - 0.42], [cx + 0.42, 11.6, cz + 0.42], sides(spike(4, 11, 14)), rot=([cx, 11, cz], 'y', 45)))
        els.append(B([cx - 0.2, 9.1, cz - 0.2], [cx + 0.2, 10.2, cz + 0.2], sides(spike(0, 8, 10)), rot=([cx, 11, cz], 'y', 45)))
    # four side spikes from the diamond corners, tilted up 22.5 deg, tapering in 3 tiers
    for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        root = 2.5
        tiers = [(0.0, 1.9, 0.78), (1.7, 3.1, 0.52), (2.9, 3.9, 0.26)]
        for k, (l0, l1, hw) in enumerate(tiers):
            uv = spike(4 + 2 * (k % 2), 10 + k, 16)
            if dx:
                x0, x1 = (8 + root + l0, 8 + root + l1) if dx > 0 else (8 - root - l1, 8 - root - l0)
                fr, to = [x0, 13.6 - hw, 8 - hw], [x1, 13.6 + hw, 8 + hw]
                rot = ([8 + dx * root, 13.6, 8], 'z', 22.5 if dx > 0 else -22.5)
            else:
                z0, z1 = (8 + root + l0, 8 + root + l1) if dz > 0 else (8 - root - l1, 8 - root - l0)
                fr, to = [8 - hw, 13.6 - hw, z0], [8 + hw, 13.6 + hw, z1]
                rot = ([8, 13.6, 8 + dz * root], 'x', -22.5 if dz > 0 else 22.5)
            els.append(B(fr, to, {**sides(uv), 'up': uv, 'down': spike(6, 15, 16)}, rot=rot))
    disp = {
        # vanilla handheld_mace with the z angle reduced by 45 deg: the model stands upright, vanilla's flat mace is diagonal
        'thirdperson_righthand': {'rotation': [0, -90, 10], 'translation': [0, 4.0, 1], 'scale': [1, 1, 1]},
        'thirdperson_lefthand': {'rotation': [0, 90, -10], 'translation': [0, 4.0, 1], 'scale': [1, 1, 1]},
        # r39 (Lunar test 07.11.): the r38 pose ([0,-90,-20], [0,3,0.8], 0.9 = vanilla handheld_mace size) filled the right
        # third of the screen and covered the scoreboard - smaller, lower, more upright; 4 poses compared in the real client
        'firstperson_righthand': {'rotation': [0, -90, -5], 'translation': [0.5, 1.0, -0.6], 'scale': [0.75, 0.75, 0.75]},
        'firstperson_lefthand': {'rotation': [0, 90, 5], 'translation': [0.5, 1.0, -0.6], 'scale': [0.75, 0.75, 0.75]},
        'gui': {'rotation': [0, 0, -45], 'translation': [0.3, 0.6, 0], 'scale': [0.84, 0.84, 0.84]},
        'ground': {'rotation': [0, 0, -45], 'translation': [0, 2, 0], 'scale': [0.42, 0.42, 0.42]},
        'fixed': {'rotation': [0, 180, -45], 'translation': [0, 0, 0], 'scale': [0.7, 0.7, 0.7]},
        'head': {'rotation': [0, 180, 0], 'translation': [0, 10, 0], 'scale': [0.8, 0.8, 0.8]},
    }
    return {'textures': {'0': 'starkffa:item/frost_slam_3d', 'particle': 'starkffa:item/frost_slam_3d'},
            'elements': els, 'display': disp}


def write(out):
    A = os.path.join(out, 'assets', 'starkffa')
    for d in ('models/item', 'items', 'textures/item'):
        os.makedirs(os.path.join(A, d), exist_ok=True)

    def js(path, obj):
        with open(os.path.join(A, path), 'w') as f:
            json.dump(obj, f, indent=1)

    crystal_texture().save(os.path.join(A, 'textures/item/fx_crystal.png'))
    js('models/item/fx_crystal.json', crystal_model())
    js('items/fx_crystal.json', {'model': {'type': 'minecraft:model', 'model': 'starkffa:item/fx_crystal'}})
    frost_texture().save(os.path.join(A, 'textures/item/fx_frost.png'))
    js('models/item/fx_frost.json', flat_model('starkffa:item/fx_frost'))
    js('items/fx_frost.json', {'model': {'type': 'minecraft:model', 'model': 'starkffa:item/fx_frost',
                                         'tints': [{'type': 'minecraft:custom_model_data', 'index': 0, 'default': 16777215}]}})
    weapon_texture().save(os.path.join(A, 'textures/item/frost_slam_3d.png'))
    js('models/item/frost_slam.json', weapon_model())
    js('items/frost_slam.json', {'model': {'type': 'minecraft:model', 'model': 'starkffa:item/frost_slam'}})
    print('written to', A)


if __name__ == '__main__':
    write(sys.argv[1] if len(sys.argv) > 1 else '/home/claude/wpn/out')
