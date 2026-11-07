"""Gap-free joints for BetterModel's 12-limb player model (STARK statues r73).

BetterModel draws every limb piece as a hollow shell of pixel quads: the forearm has no top face, the upper arm no
bottom face, the waist neither - any bend at an elbow, knee or the torso opens a wedge you can see through.
Fix: every lower piece carries an octagonal prism ("rounded joint") around its bending axis (X through the bone
origin = the joint centre). It is (almost) round, so it fills the wedge for ANY bend angle without poking out
(max 0.16 px at 22.5 deg), and it hides inside the limbs while they are straight. Each facet is split into the
limb's pixel columns and tinted with the boundary row of the piece (back facets = SOUTH row, front = NORTH row);
the two octagon end caps are 4 overlapping strips in one colour (same colour = no visible z-fighting).

Coordinates: limb-local item units relative to the bone origin (see limbs.py); MC model space = local + 8.
Limbs hang below the origin -> boundary row = their TOP row; waist/chest sit above it -> their BOTTOM row.
"""
import math
from limbs import UV, box, boundary_pixel

R_INSET = 0.04        # prism radius stays this far inside the limb faces (no z-fighting while straight)
CAP_INSET = 0.06      # end caps this far inside the side faces
T225 = math.tan(math.radians(22.5))

# limb -> (boundary row: 'top' | 'bottom', side whose boundary pixel colours the caps: 'back' | 'front')
JOINT_LIMBS = {
    'right_forearm': ('top', 'back'), 'left_forearm': ('top', 'back'),
    'right_slim_forearm': ('top', 'back'), 'left_slim_forearm': ('top', 'back'),
    'right_foreleg': ('top', 'front'), 'left_foreleg': ('top', 'front'),
    'waist': ('bottom', 'back'), 'chest': ('bottom', 'back'),
}


def _geometry(limb):
    el = UV[limb][0]
    (x0, x1), (y0, y1), (z0, z1) = box(el)
    W, H, D = el['space']
    r = (z1 - z0) / 2 - R_INSET
    s = 2 * r * T225
    return el, (x0, x1), (z0, z1), W, H, D, r, s


def _row(limb):
    el = UV[limb][0]
    return 0 if JOINT_LIMBS[limb][0] == 'top' else el['space'][1] - 1


def facet_tint(limb, phi, col):
    """Tint index for the facet at angle phi (deg, in the z-y plane: 0 = +z back, 90 = +y, 180 = -z front) and pixel
    column col (SOUTH columns run -x -> +x, NORTH columns +x -> -x, see limbs.face_pixels)."""
    el = UV[limb][0]
    W = el['space'][0]
    row = _row(limb)
    front = phi % 360 in (135, 180, 225)
    if front:
        return boundary_pixel(limb, 'NORTH', W - 1 - col, row)[0]   # NORTH col 0 is at +x
    return boundary_pixel(limb, 'SOUTH', col, row)[0]


def cap_tint(limb, east):
    el = UV[limb][0]
    W, H, D = el['space']
    row = _row(limb)
    side = JOINT_LIMBS[limb][1]
    # EAST columns run back(+z) -> front(-z); WEST columns front(-z) -> back(+z)
    if east:
        col = 1 if side == 'back' else D - 2
        return boundary_pixel(limb, 'EAST', col, row)[0]
    col = D - 2 if side == 'back' else 1
    return boundary_pixel(limb, 'WEST', col, row)[0]


def _rot_x(p, deg):
    a = math.radians(deg)
    x, y, z = p
    # rotation about +x, right-handed: y -> z
    return (x, y * math.cos(a) - z * math.sin(a), y * math.sin(a) + z * math.cos(a))


def joint_parts(limb):
    """List of dicts: {'from','to' (local, axis aligned before rotation), 'face', 'tint', 'rot' (deg about x through
    the origin, 0/+45/-45), 'corners' (local, after rotation, CCW from outside)}."""
    el, (x0, x1), (z0, z1), W, H, D, r, s = _geometry(limb)
    dx = (x1 - x0) / W
    parts = []

    def add(frm, to, face, tint, rot):
        # corners of the single face (flat element), counter-clockwise seen from outside
        (ax, ay, az), (bx, by, bz) = frm, to
        if face == 'south':
            c = [(ax, ay, bz), (bx, ay, bz), (bx, by, bz), (ax, by, bz)]
        elif face == 'north':
            c = [(bx, ay, az), (ax, ay, az), (ax, by, az), (bx, by, az)]
        elif face == 'up':
            c = [(bx, by, az), (ax, by, az), (ax, by, bz), (bx, by, bz)]
        elif face == 'down':
            c = [(bx, ay, bz), (ax, ay, bz), (ax, ay, az), (bx, ay, az)]
        elif face == 'east':
            c = [(bx, ay, bz), (bx, ay, az), (bx, by, az), (bx, by, bz)]
        else:  # west
            c = [(ax, ay, az), (ax, ay, bz), (ax, by, bz), (ax, by, az)]
        parts.append({'from': frm, 'to': to, 'face': face, 'tint': tint, 'rot': rot,
                      'corners': [_rot_x(p, rot) for p in c]})

    xa, xb = x0 + CAP_INSET, x1 - CAP_INSET
    for i in range(W):
        cx0 = max(xa, x0 + i * dx)
        cx1 = min(xb, x0 + (i + 1) * dx)
        # back (+z) facet and its two diagonal neighbours
        t = facet_tint(limb, 0, i)
        for rot in (0, 45, -45):
            add((cx0, -s / 2, r), (cx1, s / 2, r), 'south', t, rot)
        # front (-z) facet and its two diagonal neighbours
        t = facet_tint(limb, 180, i)
        for rot in (0, 45, -45):
            add((cx0, -s / 2, -r), (cx1, s / 2, -r), 'north', t, rot)
        # up / down facets (axis aligned)
        t = facet_tint(limb, 90, i)
        add((cx0, r, -s / 2), (cx1, r, s / 2), 'up', t, 0)
        add((cx0, -r, -s / 2), (cx1, -r, s / 2), 'down', t, 0)
    # octagon end caps: vertical strip, horizontal strip, two diagonal strips
    for east in (True, False):
        face = 'east' if east else 'west'
        t = cap_tint(limb, east)
        for k, (lo, hi, rot) in enumerate((((-r, -s / 2), (r, s / 2), 0), ((-s / 2, -r), (s / 2, r), 0),
                                           ((-r, -s / 2), (r, s / 2), 45), ((-r, -s / 2), (r, s / 2), -45))):
            x = (xb - 0.003 * k) if east else (xa + 0.003 * k)
            add((x, lo[0], lo[1]), (x, hi[0], hi[1]), face, t, rot)
    return parts


def mc_elements(limb):
    """The joint as Minecraft model elements (model space = local + 8), single face each, white pixel texture."""
    out = []
    for p in joint_parts(limb):
        frm = [round(v + 8, 5) for v in p['from']]
        to = [round(v + 8, 5) for v in p['to']]
        e = {'from': frm, 'to': to, 'faces': {p['face']: {'uv': [0, 0, 16, 16], 'tintindex': p['tint'], 'texture': '#0'}}}
        if p['rot']:
            e['rotation'] = {'angle': p['rot'], 'axis': 'x', 'origin': [8, 8, 8]}
        out.append(e)
    return out


if __name__ == '__main__':
    for limb in JOINT_LIMBS:
        parts = joint_parts(limb)
        print(limb, len(parts), 'parts; tints', sorted({p['tint'] for p in parts})[:8], '...')
