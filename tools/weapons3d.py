"""StarkFFA arsenal v2 - every weapon as a chunky 3D voxel model (1 voxel = 0.5 px).
Each design is built vertically (handle at the bottom, +y = tip) and later tilted onto the sword diagonal."""
import math
from voxels import Grid, Mat

# shared materials
STEEL_D = Mat("steel_d", "#2B3242"); STEEL = Mat("steel", "#5A6577"); STEEL_L = Mat("steel_l", "#A8B4C4")
GOLD = Mat("gold", "#E8B23A"); GOLD_D = Mat("gold_d", "#9C6A12"); LEATHER = Mat("leather", "#3B2A22")
BLACK = Mat("black", "#15161C")

def wrap(a, b, period=4):
    return lambda y: a if (y // period) % 2 == 0 else b

# ---------------------------------------------------------------- W1 Tempest Mace (wind)
def tempest_mace():
    g = Grid(52, 74, 52); cx = cz = 26
    CY = Mat("wind_glow", "#7FF3FF", glow=True); NAVY = Mat("navy", "#1E3A5F"); NAVY_L = Mat("navy_l", "#3E6FA8")
    g.cyl_y(cx, cz, 1.6, 4, 40, wrap(NAVY, STEEL_L, 3))                 # wrapped handle
    g.sphere((cx, 3, cz), 2.8, STEEL); g.sphere((cx, 3, cz), 1.4, CY)   # pommel with glowing core
    g.cyl_y(cx, cz, 3.0, 38, 42, GOLD)                                  # collar
    hc = (cx, 52, cz)
    g.sphere(hc, 8.0, STEEL_D)                                          # head
    for ang in range(0, 360, 60):                                       # 6 flanges
        a = math.radians(ang); dx, dz = math.cos(a), math.sin(a)
        for r in range(6, 13):
            h = 9 - (r - 6) * 0.9
            for y in range(int(hc[1] - h), int(hc[1] + h)):
                for w in (-1, 0, 1):
                    g.put(cx + dx * r - dz * w * .6, y, cz + dz * r + dx * w * .6, NAVY_L if r < 12 else STEEL_L)
    for ang in range(30, 360, 60):                                      # glowing studs between flanges
        a = math.radians(ang); g.sphere((cx + math.cos(a) * 7.4, hc[1], cz + math.sin(a) * 7.4), 1.6, CY)
    g.cyl_y(cx, cz, 1.4, 60, 70, CY); g.sphere((cx, 70, cz), 2.0, CY)  # crown spike
    g.torus(hc, 15.5, 0.5, CY, tilt_x=24, steps=220)                   # two orbiting wind rings
    g.torus(hc, 15.5, 0.5, CY, tilt_x=-24, tilt_z=90, steps=220)
    return g

# ---------------------------------------------------------------- W4 Soul Greatsword
def soul_greatsword(lit=False):
    g = Grid(40, 84, 12); cx, z0, z1 = 20, 4, 8
    TEAL = Mat("soul_glow", "#5CFFD2", glow=True); BLADE = Mat("soul_blade", "#D9FFF6" if lit else "#BFEFE4", glow=lit); EDGE = Mat("soul_edge", "#F2FFFC", glow=lit)
    SPINE = Mat("soul_spine", "#2F7F70"); IRON = Mat("iron", "#2E3A3C")
    def blade(t, xr):
        if abs(xr) > .78: return EDGE
        if abs(xr) < .22: return TEAL if (int(t * 22) % 3 != 0) else SPINE
        return BLADE
    g.profile_y(24, 82, lambda t: cx, lambda t: 6.5 * (1 - t) ** .5 + .6, z0, z1, blade)
    g.profile_y(24, 76, lambda t: cx, lambda t: 1.2, z0 - 1, z0, lambda t, x: TEAL if int(t * 22) % 3 else SPINE)
    g.profile_y(24, 76, lambda t: cx, lambda t: 1.2, z1, z1 + 1, lambda t, x: TEAL if int(t * 22) % 3 else SPINE)
    g.box(cx - 12, cx + 12, 20, 24, z0 - 1, z1 + 1, IRON)              # crossguard
    for s in (-1, 1):                                                   # horns curling up
        g.box(cx + s * 12 - (2 if s > 0 else 0), cx + s * 12 + (0 if s > 0 else 2), 22, 30, z0, z1, IRON)
        g.box(cx + s * 10 - (2 if s > 0 else 0), cx + s * 10 + (0 if s > 0 else 2), 28, 32, z0, z1, TEAL)
    g.sphere((cx, 22, (z0 + z1) / 2), 3.0, TEAL)                       # soul gem
    g.cyl_y(cx, (z0 + z1) / 2, 1.7, 5, 20, wrap(BLACK, SPINE, 3))      # grip
    g.sphere((cx, 4, (z0 + z1) / 2), 3.0, IRON); g.sphere((cx, 4, (z0 + z1) / 2), 1.8, TEAL)
    return g

DESIGNS = {"tempest_mace": tempest_mace, "soul_blade": soul_greatsword}

# ---------------------------------------------------------------- W5 Shadow Kunai
def shadow_kunai():
    g = Grid(36, 64, 10); cx, z0, z1 = 16, 3, 6
    PLUM = Mat("plum_glow", "#C08CFF", glow=True); VOID = Mat("void_black", "#1A1424"); VIO = Mat("violet", "#3D2B5C")
    def blade(t, xr):
        if xr > .45: return PLUM                       # glowing cutting edge on one side
        return VIO if abs(xr) < .25 else VOID
    curve = lambda t: cx + 7 * t ** 2
    g.profile_y(22, 60, curve, lambda t: 5.0 * (1 - t) ** .7 + .5, z0, z1, blade)
    g.profile_y(22, 54, curve, lambda t: .8, z0 - 1, z0, lambda t, x: PLUM if int(t * 10) % 2 else None)
    for i in range(9):                                 # crescent guard
        a = math.radians(200 + i * 17.5); g.box(cx + math.cos(a) * 8 - 1, cx + math.cos(a) * 8 + 1, 20 + math.sin(a) * -3, 22 + math.sin(a) * -3, z0, z1, VIO)
    g.box(cx - 3, cx + 3, 18, 22, z0, z1, VOID)
    g.cyl_y(cx, (z0 + z1) / 2, 1.5, 6, 18, wrap(BLACK, VIO, 2))
    g.torus((cx, 3.5, (z0 + z1) / 2), 3.0, 0.7, PLUM, tilt_x=90, steps=200)   # ring pommel
    return g

# ---------------------------------------------------------------- W6 Blink Katana
def blink_katana():
    g = Grid(40, 92, 12); cx, z0, z1 = 14, 5, 7
    CYAN = Mat("blink_glow", "#8FF0FF", glow=True); ICE = Mat("crystal", "#DDF6FF"); FACET = Mat("facet", "#9FD8F0"); WHITE = Mat("white", "#FFFFFF")
    def blade(t, xr):
        if abs(xr) < .2: return CYAN
        if xr > .6: return WHITE
        return ICE if (int(t * 30) + (1 if xr > 0 else 0)) % 2 else FACET
    curve = lambda t: cx + 6 * t ** 1.6
    g.profile_y(26, 90, curve, lambda t: 3.2 * (1 - t) ** .35 + .3, z0, z1, blade)
    g.ellipsoid((cx, 24, 6), (5.5, 1.5, 5.5), STEEL_D); g.ellipsoid((cx, 24, 6), (5.5, 1.6, 5.5), CYAN, shell=0.75)   # tsuba
    g.cyl_y(cx, 6, 1.6, 4, 23, lambda y: WHITE if y % 4 == 0 else BLACK)
    g.box(cx - 2, cx + 2, 2, 4, 4, 8, STEEL_D)
    for (dx, dy, r) in ((9, 40, 1.6), (12, 52, 1.3), (14, 64, 1.0)):              # floating crystal shards
        g.ellipsoid((cx + dx, dy, 6), (r, r * 2.2, r), CYAN)
    return g

# ---------------------------------------------------------------- W8 Storm Spear
def storm_spear():
    g = Grid(30, 92, 30); cx = cz = 15
    VOLT = Mat("volt_glow", "#7DF9FF", glow=True); SPARK = Mat("spark_glow", "#FFF27A", glow=True); SHAFT = Mat("shaft", "#232A38")
    g.cyl_y(cx, cz, 1.3, 4, 70, lambda y: GOLD if y % 16 < 2 else SHAFT)
    for k in range(0, 66):                                     # spiral energy vein
        a = k * 0.42; g.put(cx + math.cos(a) * 1.8 - .5, 4 + k, cz + math.sin(a) * 1.8 - .5, VOLT)
    g.sphere((cx, 3, cz), 2.2, GOLD_D)
    g.cyl_y(cx, cz, 2.4, 68, 72, GOLD)
    g.profile_y(72, 91, lambda t: cx, lambda t: 5.5 * math.sin(math.pi * min(1, t * 1.15)) ** .7 + .4, cz - 1, cz + 1,
                lambda t, x: SPARK if abs(x) < .35 else VOLT)              # main blade
    for s in (-1, 1):                                          # zig-zag lightning prongs
        pts = [(0, 0), (3, 4), (1, 7), (5, 12), (3, 15)]
        for (a, b), (c, d) in zip(pts, pts[1:]):
            for i in range(9):
                t = i / 8; g.box(cx + s * (4 + a + (c - a) * t) - .5, cx + s * (4 + a + (c - a) * t) + 1, 68 + b + (d - b) * t, 69 + b + (d - b) * t, cz - 1, cz + 1, VOLT)
    return g

# ---------------------------------------------------------------- W9 Frost Hammer
def frost_hammer():
    g = Grid(56, 84, 30); cx, cz = 28, 15
    ICEG = Mat("ice_glow", "#A8F0FF", glow=True); PACK = Mat("packed_ice", "#8FC3EC"); BLUE = Mat("blue_ice", "#4C8FD8")
    FROST = Mat("frost_steel", "#6E7F92"); WRAP = Mat("wrap_blue", "#24476E")
    g.cyl_y(cx, cz, 1.8, 4, 52, wrap(FROST, WRAP, 3))
    g.sphere((cx, 3, cz), 2.6, FROST)
    g.box(cx - 15, cx + 15, 50, 68, cz - 8, cz + 8, PACK)               # head
    g.box(cx - 17, cx - 15, 51, 67, cz - 7, cz + 7, BLUE); g.box(cx + 15, cx + 17, 51, 67, cz - 7, cz + 7, BLUE)
    for bx in (cx - 9, cx + 7):                                          # steel bands
        g.box(bx, bx + 2, 49, 69, cz - 9, cz + 9, FROST)
    for (x, z) in ((cx - 4, cz - 8.5), (cx + 3, cz + 8.5), (cx - 12, cz + 8.5), (cx + 11, cz - 8.5)):   # glowing cracks
        g.box(x, x + 1, 53, 66, z - .5, z + .5, ICEG)
    for (x, z, h, r0) in ((cx - 10, cz - 2, 12, 3.2), (cx - 2, cz + 1, 18, 3.8), (cx + 7, cz - 1, 14, 3.4), (cx + 13, cz + 2, 10, 2.6)):
        g.cyl_y(x, z, r0, 68, 70, PACK)                                     # crystal spikes on top (cones)
        for k in range(h):
            r = r0 * (1 - k / h) + .4; g.cyl_y(x + k * .12, z, r, 70 + k, 71 + k, ICEG if k > 2 else BLUE)
    for s in (-1, 1):                                                    # side crystals
        for k in range(9):
            r = 3.0 * (1 - k / 9) + .4
            g.ellipsoid((cx + s * (17 + k), 59, cz), (.7, r, r), ICEG)
    return g

DESIGNS.update({"shadow_dagger": shadow_kunai, "blink_blade": blink_katana, "storm_spear": storm_spear,
                "frost_hammer": frost_hammer})

# ---------------------------------------------------------------- W3 Void Bow (pull 0..3: 0 = idle)
def void_bow(pull=0):
    """Built with the arrow pointing +y and limbs along x; exported with a +45 deg tilt (vanilla bow orientation)."""
    g = Grid(44, 44, 10); cx, by, cz = 22, 16, 5
    VG = Mat("void_glow", "#C9A7FF", glow=True); CORE = Mat("void_core", "#F2E6FF", glow=True)
    LIMB = Mat("void_limb", "#2A1A48"); LIMB_L = Mat("void_limb_l", "#5B3C96"); STR = Mat("void_string", "#E2CCFF", glow=True)
    span = 19
    ends = []
    for i in range(-span * 4, span * 4 + 1):
        x = i / 4; t = x / span
        y = by + 8 * (1 - t * t)
        g.box(cx + x - .5, cx + x + .5, y - 1, y + 1.5, cz - 1, cz + 1, LIMB)
        g.box(cx + x - .5, cx + x + .5, y + 1.5, y + 2.4, cz - 1, cz + 1, VG if abs(t) > .25 else LIMB_L)
    for s in (-1, 1):                                    # recurve tips
        tx = cx + s * span; g.box(tx - (2 if s > 0 else 0), tx + (0 if s < 0 else 1) + (2 if s < 0 else 0) - (0 if s < 0 else 0), by - 1, by + 3, cz - 1, cz + 1, LIMB_L)
        g.sphere((tx + s * 1.5, by + 3, cz), 1.3, VG); ends.append((tx, by))
    g.box(cx - 2.5, cx + 2.5, by + 5, by + 12, cz - 1.5, cz + 1.5, LIMB)            # grip block
    g.ellipsoid((cx, by + 15, cz), (2.4, 3.2, 2.4), CORE); g.ellipsoid((cx, by + 15, cz), (3.4, 4.2, 3.4), VG, shell=.7)   # void crystal
    back = [0, 3, 5, 7][pull]
    mid = (cx, by - back)
    for (ax, ay) in ends:                                # string (V when drawn)
        for i in range(41):
            t = i / 40; g.put(ax + (mid[0] - ax) * t - .5, ay + (mid[1] - ay) * t - .5, cz - .5, STR)
    if pull:
        ARROW = Mat("arrow", "#C9B79C")
        g.box(cx - .5, cx + .5, mid[1], by + 22, cz - .5, cz + .5, ARROW)
        g.ellipsoid((cx, by + 23, cz), (1.4, 2.2, .8), CORE)
    return g

# ---------------------------------------------------------------- W7 Repulsion Shield (vanilla shield coordinate frame)
def repulsion_shield():
    g = Grid(40, 40, 20); c = (20, 20)
    SH = Mat("shield_face", "#E9E4D4"); SG = Mat("shield_glow", "#FFE08A", glow=True); BOSS = Mat("boss_glow", "#FFF4C8", glow=True)
    X, Y, Z = g.v.shape
    for x in range(X):
        for y in range(Y):
            r = math.hypot(x + .5 - c[0], (y + .5 - c[1]) * 0.92)
            if r > 18.5: continue
            g.box(x, x + 1, y, y + 1, 12, 14, SH)                              # plate (front = +z)
            if r > 16: g.box(x, x + 1, y, y + 1, 11, 15, GOLD if r < 18 else GOLD_D)   # raised rim
            elif 9.8 < r < 11.4: g.box(x, x + 1, y, y + 1, 14, 15, SG)          # glowing rune ring
            else:
                a = (math.degrees(math.atan2(y + .5 - c[1], x + .5 - c[0])) + 360) % 45
                if 4 < r < 16 and (a < 4 or a > 41): g.box(x, x + 1, y, y + 1, 14, 15, GOLD)   # 8 rays
    g.ellipsoid((20, 20, 14), (4, 4, 3.2), BOSS)
    g.box(18, 22, 14, 26, 1, 12, STEEL_D)                                       # handle
    return g

DESIGNS.update({"void_bow": void_bow, "repulsion_shield": repulsion_shield})


# ---------------------------------------------------------------- export
from voxels import to_model, atlas, check_bounds, handheld_display
HANDHELD = {  # id: (design, grip voxel y, target length in px) - only hero items get a custom model
    "wind_mace": (tempest_mace, 16, 30),
}
DIAG = {"angle": -45, "axis": "z", "origin": [8, 8, 8]}

def export_all(w, NS):
    def tex(name, grid, dim):
        img, _, _ = atlas(grid.mats, dim)
        w(f"assets/{NS}/textures/item/v2/{name}.png", img)
        w(f"assets/{NS}/textures/item/v2/{name}.png.mcmeta", {"animation": {"frametime": 3, "interpolate": True}})
        return f"{NS}:item/v2/{name}"
    def item(name):
        w(f"assets/{NS}/items/{name}.json", {"model": {"type": "minecraft:model", "model": f"{NS}:item/{name}"}})
    built = []
    for wid, (fn, grip, target) in HANDHELD.items():
        variants = [(wid, fn(), False), (wid + "_cd", fn(), True)]
        if wid == "soul_blade": variants.append(("soul_blade_lit", soul_greatsword(lit=True), False))
        for name, g, dim in variants:
            X, Y, Z = g.v.shape
            L = Y * .5
            origin = (8 - X / 4, max(-16, 2 - grip * .5), 8 - Z / 4)
            if origin[1] + L > 32: origin = (origin[0], 32 - L, origin[2])
            k = target / L / 0.85 * 0.85
            gui = round(min(1.0, 15.5 / (L * 0.72)), 3)
            m = to_model(g, tex(name, g, dim), origin=origin, rot=DIAG, dim=dim, display=handheld_display(k, gui))
            check_bounds(m); w(f"assets/{NS}/models/item/{name}.json", m); item(name); built.append((name, len(m["elements"])))
    return built
