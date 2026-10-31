"""Voxel weapon pipeline.
Design weapons as voxel grids (1 voxel = 0.5 model px) with named materials, then
  * greedy-mesh them into Minecraft model elements (emissive materials get light_emission 15),
  * texture them from a per-weapon animated atlas (emissive swatches pulse),
  * export a READY variant (bright glow) and a COOLDOWN variant (dimmed, no light emission),
  * render an isometric preview PNG.
Art direction: chunky stylised fantasy-tech. 3-tone shading + dark outline per face, ONE signature glow
colour per weapon, oversized silhouettes that read in a 1-second clip.
"""
import math
import numpy as np
from PIL import Image, ImageDraw

def hx(s):
    s = s.lstrip("#"); return np.array([int(s[i:i + 2], 16) for i in (0, 2, 4)], dtype=float)

class Mat:
    def __init__(self, name, color, glow=False, edge=None):
        self.name, self.color, self.glow = name, hx(color), glow
        self.edge = hx(edge) if edge else None

class Grid:
    def __init__(self, X, Y, Z):
        self.v = np.zeros((X, Y, Z), dtype=np.int16); self.mats = [None]; self.idx = {}
    def m(self, mat):
        if mat.name not in self.idx: self.idx[mat.name] = len(self.mats); self.mats.append(mat)
        return self.idx[mat.name]
    def put(self, x, y, z, mat):
        x, y, z = int(round(x)), int(round(y)), int(round(z))
        X, Y, Z = self.v.shape
        if 0 <= x < X and 0 <= y < Y and 0 <= z < Z: self.v[x, y, z] = self.m(mat)
    # ---- primitives (all coordinates in voxels)
    def box(self, x0, x1, y0, y1, z0, z1, mat):
        X, Y, Z = self.v.shape
        x0, x1 = max(0, int(x0)), min(X, int(x1)); y0, y1 = max(0, int(y0)), min(Y, int(y1)); z0, z1 = max(0, int(z0)), min(Z, int(z1))
        if x0 < x1 and y0 < y1 and z0 < z1: self.v[x0:x1, y0:y1, z0:z1] = self.m(mat)
    def ellipsoid(self, c, r, mat, shell=None):
        X, Y, Z = self.v.shape; i = self.m(mat)
        xs, ys, zs = np.ogrid[0:X, 0:Y, 0:Z]
        d = ((xs + .5 - c[0]) / r[0]) ** 2 + ((ys + .5 - c[1]) / r[1]) ** 2 + ((zs + .5 - c[2]) / r[2]) ** 2
        m = d <= 1 if shell is None else (d <= 1) & (d >= shell)
        self.v[m] = i
    def sphere(self, c, r, mat): self.ellipsoid(c, (r, r, r), mat)
    def cyl_y(self, cx, cz, r, y0, y1, mat_fn):
        """vertical cylinder; mat_fn(y) -> Mat (for bands/wraps)"""
        X, Y, Z = self.v.shape
        for y in range(max(0, int(y0)), min(Y, int(y1))):
            mat = mat_fn(y) if callable(mat_fn) else mat_fn; i = self.m(mat)
            for x in range(int(cx - r - 1), int(cx + r + 2)):
                for z in range(int(cz - r - 1), int(cz + r + 2)):
                    if (x + .5 - cx) ** 2 + (z + .5 - cz) ** 2 <= r * r and 0 <= x < X and 0 <= z < Z: self.v[x, y, z] = i
    def torus(self, c, R, r, mat, tilt_x=0.0, tilt_z=0.0, steps=720):
        """ring of radius R (tube r) around centre c, initially in the XZ plane, then tilted (degrees)."""
        ax, az = math.radians(tilt_x), math.radians(tilt_z)
        for k in range(steps):
            t = 2 * math.pi * k / steps
            n = max(3, int(r * 4) | 1)
            for dr in np.linspace(-r, r, n):
                for dy in np.linspace(-r, r, n):
                    if dr * dr + dy * dy > r * r: continue
                    x, y, z = (R + dr) * math.cos(t), dy, (R + dr) * math.sin(t)
                    y, z = y * math.cos(ax) - z * math.sin(ax), y * math.sin(ax) + z * math.cos(ax)
                    x, y = x * math.cos(az) - y * math.sin(az), x * math.sin(az) + y * math.cos(az)
                    self.put(c[0] + x - .5, c[1] + y - .5, c[2] + z - .5, mat)
    def profile_y(self, y0, y1, cx_fn, half_w_fn, z0, z1, mat_fn):
        """blade-like slab: for each y, x in [cx-w, cx+w]; mat_fn(t, xrel) with t 0..1, xrel -1..1"""
        for y in range(int(y0), int(y1)):
            t = (y - y0) / max(1, (y1 - y0 - 1)); cx, w = cx_fn(t), half_w_fn(t)
            for x in range(int(math.floor(cx - w)), int(math.ceil(cx + w)) + 1):
                if abs(x + .5 - cx) > w + .01: continue
                xrel = (x + .5 - cx) / max(w, .01)
                mat = mat_fn(t, xrel)
                if mat is None: continue
                self.box(x, x + 1, y, y + 1, z0, z1, mat)

# ------------------------------------------------------------------ meshing
def greedy(v):
    """Merge equal-material voxels into boxes. Returns list of (x0,y0,z0,x1,y1,z1,mat_index)."""
    v = v.copy(); X, Y, Z = v.shape; out = []
    for y in range(Y):
        for z in range(Z):
            for x in range(X):
                m = v[x, y, z]
                if m == 0: continue
                x1 = x
                while x1 + 1 < X and v[x1 + 1, y, z] == m: x1 += 1
                z1 = z
                while z1 + 1 < Z and np.all(v[x:x1 + 1, y, z1 + 1] == m): z1 += 1
                y1 = y
                while y1 + 1 < Y and np.all(v[x:x1 + 1, y1 + 1, z:z1 + 1] == m): y1 += 1
                v[x:x1 + 1, y:y1 + 1, z:z1 + 1] = 0
                out.append((x, y, z, x1 + 1, y1 + 1, z1 + 1, m))
    return out

# ------------------------------------------------------------------ atlas
SW = 8          # swatch size in px
FRAMES = 8
def atlas(mats, dim=False):
    """Animated atlas: 4 swatches per row, 8x8 each; glow swatches pulse; returns (image, uv_of[mat_index])."""
    n = len(mats); cols = 4
    if n - 1 > 16: raise ValueError("max 16 materials per weapon")
    size = 32; H = 32
    sheet = Image.new("RGBA", (size, H * FRAMES), (0, 0, 0, 0)); px = sheet.load()
    uv = {}
    rng = np.random.default_rng(3)
    for i, mat in enumerate(mats[1:], start=1):
        k = i - 1; sx, sy = (k % cols) * SW, (k // cols) * SW
        uv[i] = [sx / 2 + .25, sy / 2 + .25, (sx + SW) / 2 - .25, (sy + SW) / 2 - .25]
        noise = rng.normal(0, 4, (SW, SW))
        for f in range(FRAMES):
            pulse = 1.0
            if mat.glow and not dim: pulse = 0.88 + 0.2 * (0.5 + 0.5 * math.sin(2 * math.pi * f / FRAMES))
            if mat.glow and dim: pulse = 0.45
            for y in range(SW):
                for x in range(SW):
                    c = mat.color.copy()
                    c *= 1.12 - 0.22 * (y / (SW - 1))                          # top light -> bottom dark
                    if x == 0 or y == 0: c *= 1.08                                # bevel highlight
                    if x == SW - 1 or y == SW - 1:                                # outline
                        c = mat.edge.copy() if mat.edge is not None else c * 0.62
                    if mat.glow and 2 <= x <= 5 and 2 <= y <= 5 and not dim: c = c * 0.7 + 255 * 0.3   # hot core
                    c = c * pulse + (0 if mat.glow else noise[y, x])
                    px[sx + x, sy + y + f * H] = tuple(int(np.clip(v, 0, 255)) for v in c) + (255,)
    return sheet, uv, H

def to_model(grid, tex, origin=(0, 0, 0), rot=None, dim=False, display=None, parent=None):
    """Elements in model units: model = voxel*0.5 + origin. rot: element rotation dict applied to every element."""
    boxes = greedy(grid.v); _, uv, _ = atlas(grid.mats, dim)
    els = []
    for (x0, y0, z0, x1, y1, z1, m) in boxes:
        mat = grid.mats[m]
        frm = [round(x0 * .5 + origin[0], 3), round(y0 * .5 + origin[1], 3), round(z0 * .5 + origin[2], 3)]
        to = [round(x1 * .5 + origin[0], 3), round(y1 * .5 + origin[1], 3), round(z1 * .5 + origin[2], 3)]
        e = {"from": frm, "to": to,
             "faces": {f: {"uv": uv[m], "texture": "#t"} for f in ("north", "east", "south", "west", "up", "down")}}
        if mat.glow and not dim: e["light_emission"] = 15; e["shade"] = False
        if rot: e["rotation"] = rot
        els.append(e)
    model = {"textures": {"t": tex, "particle": tex}, "elements": els}
    if parent: model["parent"] = parent
    if display: model["display"] = display
    return model

def check_bounds(model):
    for e in model["elements"]:
        for v in e["from"] + e["to"]:
            if v < -16 or v > 32: raise ValueError(f"element out of bounds: {e['from']} {e['to']}")

# ------------------------------------------------------------------ preview
def iso_preview(grid, scale=6, dim=False, bg=(22, 26, 36), rotate_z=0.0):
    """Isometric voxel render (painter's algorithm). rotate_z rotates the design in the XY plane for display."""
    X, Y, Z = grid.v.shape
    pts = np.argwhere(grid.v > 0)
    if len(pts) == 0: return Image.new("RGB", (10, 10))
    a = math.radians(rotate_z); ca, sa = math.cos(a), math.sin(a)
    cx, cy = X / 2, Y / 2
    def proj(x, y, z):
        x, y = (x - cx) * ca - (y - cy) * sa, (x - cx) * sa + (y - cy) * ca
        u = (x - z) * 0.866; w = -y + (x + z) * 0.5
        return u * scale, w * scale
    faces = []
    for (x, y, z) in pts:
        m = grid.mats[grid.v[x, y, z]]; col = m.color * (0.45 if (m.glow and dim) else 1.0)
        if m.glow and not dim: col = col * 0.75 + 255 * 0.25
        for (dx, dy, dz, quad, shade) in (
            (0, 1, 0, [(0, 1, 0), (1, 1, 0), (1, 1, 1), (0, 1, 1)], 1.12),
            (1, 0, 0, [(1, 0, 0), (1, 1, 0), (1, 1, 1), (1, 0, 1)], 0.82),
            (0, 0, 1, [(0, 0, 1), (1, 0, 1), (1, 1, 1), (0, 1, 1)], 0.95)):
            nx, ny, nz = x + dx, y + dy, z + dz
            if 0 <= nx < X and 0 <= ny < Y and 0 <= nz < Z and grid.v[nx, ny, nz] > 0: continue
            poly = [proj(x + qx, y + qy, z + qz) for (qx, qy, qz) in quad]
            depth = (x + dx * .5) + (z + dz * .5) - (y + dy * .5) * 0.01 + y * 0.0
            sh = shade if not m.glow else 1.0
            faces.append((x + z + y * 0.001, poly, tuple(int(np.clip(c * sh, 0, 255)) for c in col)))
    faces.sort(key=lambda f: f[0])
    us = [p[0] for f in faces for p in f[1]]; ws = [p[1] for f in faces for p in f[1]]
    W, H = int(max(us) - min(us)) + 20, int(max(ws) - min(ws)) + 20
    img = Image.new("RGB", (W, H), bg); d = ImageDraw.Draw(img)
    ou, ow = min(us) - 10, min(ws) - 10
    for _, poly, col in faces:
        d.polygon([(p[0] - ou, p[1] - ow) for p in poly], fill=col, outline=tuple(int(c * .7) for c in col))
    return img

# ------------------------------------------------------------------ displays
def handheld_display(k=1.0, gui=0.5):
    """Vanilla handheld transforms, scaled by k (models here are bigger than a 16px sprite)."""
    s3, s1 = round(0.85 * k, 3), round(0.68 * k, 3)
    return {
        "thirdperson_righthand": {"rotation": [0, -90, 55], "translation": [0, 4.0, 0.5], "scale": [s3, s3, s3]},
        "thirdperson_lefthand": {"rotation": [0, 90, -55], "translation": [0, 4.0, 0.5], "scale": [s3, s3, s3]},
        "firstperson_righthand": {"rotation": [0, -90, 25], "translation": [1.13, 3.2, 1.13], "scale": [s1, s1, s1]},
        "firstperson_lefthand": {"rotation": [0, 90, -25], "translation": [1.13, 3.2, 1.13], "scale": [s1, s1, s1]},
        "gui": {"rotation": [0, 0, 0], "translation": [0, 0, 0], "scale": [gui, gui, gui]},
        "ground": {"rotation": [0, 0, 0], "translation": [0, 2, 0], "scale": [0.4 * k, 0.4 * k, 0.4 * k]},
        "fixed": {"rotation": [0, 180, 0], "translation": [0, 0, 0], "scale": [gui * 1.4, gui * 1.4, gui * 1.4]},
        "head": {"rotation": [0, 180, 0], "translation": [0, 13, 7], "scale": [1, 1, 1]},
    }
