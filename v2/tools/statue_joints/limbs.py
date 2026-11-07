"""BetterModel 12-limb player geometry, pixel for pixel (DynamicUV layout from BetterModel 3.6.0-534 SkinManagerImpl).

Every skin pixel is one flat quad. Coordinates are limb-local item units (16 = 1 block) relative to the bone origin:
limbs hang down from their origin (top centre), head/torso pieces sit on it (bottom centre). Front = -Z, model right = +X
(the Blockbench orientation of the rig). Tint order = NORTH, SOUTH, EAST, WEST, UP, DOWN; columns outer, rows inner
(derived from the generated item models: tint index i of <limb>_0.json is the i-th RGB pixel in that order).
"""
import json

K = 16 / 17.066668                      # skin pixel -> item units (0.9375)
UV = json.load(open(__import__('os').path.join(__import__('os').path.dirname(__import__('os').path.abspath(__file__)), 'uvmodels.json')))
if len(UV['head']) == 1:                # the regex missed the head base element (typed declaration)
    UV['head'].insert(0, {'size': [8, 8, 8], 'inflate': 0.0, 'offset': [0, 4, 0], 'space': [8, 8, 8], 'color': 'RGB',
                          'faces': {'NORTH': [8, 8], 'SOUTH': [24, 8], 'EAST': [0, 8], 'WEST': [16, 8], 'UP': [8, 0], 'DOWN': [16, 0]}})
FACE_ORDER = ['NORTH', 'SOUTH', 'EAST', 'WEST', 'UP', 'DOWN']

# r73: the side faces (EAST/WEST, perpendicular to the bending axis) of the CHILD piece of every joint move inwards,
# so where a bent joint overlaps its parent piece the parent's face wins the depth test instead of z-fighting.
SIDE_INSET = {
    'right_forearm': 0.02, 'left_forearm': 0.02, 'right_slim_forearm': 0.02, 'left_slim_forearm': 0.02,
    'right_foreleg': 0.02, 'left_foreleg': 0.02, 'waist': 0.02, 'chest': 0.04,
}

# bone -> limb model (classic arms; slim variants by name)
BONE_LIMB = {
    'h_ph_head': 'head', 'pc_chest': 'chest', 'pw_waist': 'waist', 'phip_hip': 'hip',
    'pra_right_arm': 'right_arm', 'prfa_right_forearm': 'right_forearm',
    'pla_left_arm': 'left_arm', 'plfa_left_forearm': 'left_forearm',
    'prl_right_leg': 'right_leg', 'prfl_right_foreleg': 'right_foreleg',
    'pll_left_leg': 'left_leg', 'plfl_left_foreleg': 'left_foreleg',
}


def limb_name(bone, slim=False):
    n = BONE_LIMB[bone]
    if slim and n in ('right_arm', 'right_forearm', 'left_arm', 'left_forearm'):
        n = n.replace('right_', 'right_slim_').replace('left_', 'left_slim_')
    return n


def box(el):
    sx, sy, sz = [s * K for s in el['size']]
    ox, oy, oz = [o * K for o in el['offset']]
    inf = el['inflate']
    return (ox - sx / 2 - inf, ox + sx / 2 + inf), (oy - sy / 2 - inf, oy + sy / 2 + inf), (oz - sz / 2 - inf, oz + sz / 2 + inf)


def face_pixels(el, face, limb=None):
    """Yields (col, row, corners) for one face of one element. corners = 4 points, counter-clockwise seen from outside.
    limb given: EAST/WEST faces of joint child pieces are moved inwards by SIDE_INSET (see above)."""
    (x0, x1), (y0, y1), (z0, z1) = box(el)
    ins = SIDE_INSET.get(limb, 0.0)
    W, H, D = el['space']
    dx, dy, dz = (x1 - x0) / W, (y1 - y0) / H, (z1 - z0) / D
    if face in ('NORTH', 'SOUTH'):
        cols, rows = W, H
    elif face in ('EAST', 'WEST'):
        cols, rows = D, H
    else:
        cols, rows = W, D
    for i in range(cols):
        for j in range(rows):
            if face == 'NORTH':
                xa, xb = x1 - (i + 1) * dx, x1 - i * dx
                ya, yb = y1 - (j + 1) * dy, y1 - j * dy
                c = [(xb, ya, z0), (xa, ya, z0), (xa, yb, z0), (xb, yb, z0)]
            elif face == 'SOUTH':
                xa, xb = x0 + i * dx, x0 + (i + 1) * dx
                ya, yb = y1 - (j + 1) * dy, y1 - j * dy
                c = [(xa, ya, z1), (xb, ya, z1), (xb, yb, z1), (xa, yb, z1)]
            elif face == 'EAST':
                za, zb = z1 - (i + 1) * dz, z1 - i * dz
                ya, yb = y1 - (j + 1) * dy, y1 - j * dy
                xe = x1 - ins
                c = [(xe, ya, zb), (xe, ya, za), (xe, yb, za), (xe, yb, zb)]
            elif face == 'WEST':
                za, zb = z0 + i * dz, z0 + (i + 1) * dz
                ya, yb = y1 - (j + 1) * dy, y1 - j * dy
                xw = x0 + ins
                c = [(xw, ya, za), (xw, ya, zb), (xw, yb, zb), (xw, yb, za)]
            elif face == 'UP':
                xa, xb = x1 - (i + 1) * dx, x1 - i * dx
                za, zb = z1 - (j + 1) * dz, z1 - j * dz
                c = [(xb, y1, za), (xa, y1, za), (xa, y1, zb), (xb, y1, zb)]
            else:  # DOWN
                xa, xb = x1 - (i + 1) * dx, x1 - i * dx
                za, zb = z1 - (j + 1) * dz, z1 - j * dz
                c = [(xb, y0, zb), (xa, y0, zb), (xa, y0, za), (xb, y0, za)]
            yield i, j, c


def quads(limb, skin):
    """All pixel quads of a limb: list of (layer, face, corners, rgba, tint) - layer 0 = base, 1 = overlay.
    skin: 64x64 RGBA PIL image. tint = index into the base model's tints (base layer only)."""
    out = []
    px = skin.load()
    for layer, el in enumerate(UV[limb]):
        tint = 0
        for face in FACE_ORDER:
            if face not in el['faces']:
                continue
            u0, v0 = el['faces'][face]
            for i, j, c in face_pixels(el, face, limb):
                rgba = px[u0 + i, v0 + j]
                if layer == 0:
                    out.append((0, face, c, (rgba[0], rgba[1], rgba[2], 255), tint))
                    tint += 1
                elif rgba[3] > 0:
                    out.append((1, face, c, rgba, None))
    return out


def boundary_pixel(limb, face, col, row, skin=None):
    """(tint index, rgba) of the base pixel at (col, row) of a face."""
    el = UV[limb][0]
    tint = 0
    for f in FACE_ORDER:
        if f not in el['faces']:
            continue
        W, H, D = el['space']
        cols, rows = (W, H) if f in ('NORTH', 'SOUTH') else (D, H) if f in ('EAST', 'WEST') else (W, D)
        if f == face:
            idx = tint + col * rows + row
            rgba = None
            if skin is not None:
                u0, v0 = el['faces'][f]
                rgba = skin.load()[u0 + col, v0 + row]
            return idx, rgba
        tint += cols * rows
    raise KeyError(face)


def legacy_to_64(skin):
    """64x32 legacy skins: left arm/leg mirror the right ones (vanilla behaviour)."""
    from PIL import Image, ImageOps
    if skin.size == (64, 64):
        return skin
    out = Image.new('RGBA', (64, 64), (0, 0, 0, 0))
    out.paste(skin, (0, 0))

    def mirror_limb(sx, sy, dx, dy):
        # box 4x12x4 at (sx,sy) -> (dx,dy) mirrored (swap left/right faces, flip each face)
        def cp(x, y, w, h, tx, ty, flip=True):
            part = skin.crop((x, y, x + w, y + h))
            out.paste(ImageOps.mirror(part) if flip else part, (tx, ty))
        cp(sx + 4, sy, 4, 4, dx + 4, dy)          # top
        cp(sx + 8, sy, 4, 4, dx + 8, dy)          # bottom
        cp(sx + 0, sy + 4, 4, 12, dx + 8, dy + 4)  # right -> left
        cp(sx + 4, sy + 4, 4, 12, dx + 4, dy + 4)  # front
        cp(sx + 8, sy + 4, 4, 12, dx + 0, dy + 4)  # left -> right
        cp(sx + 12, sy + 4, 4, 12, dx + 12, dy + 4)  # back
    mirror_limb(0, 16, 16, 48)
    mirror_limb(40, 16, 32, 48)
    return out
