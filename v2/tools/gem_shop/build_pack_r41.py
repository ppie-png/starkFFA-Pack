"""Pack r41 = r40 + (1) every STARK menu background fully opaque (alpha 250 -> 255: the vanilla chest slot grid shone
through the 98 % panels, owner 07.11.: "leicht kariert") + (2) the cosmetics v2 FX sprites (fx_gen.py)."""
import hashlib, os, shutil, sys, zipfile
from PIL import Image
sys.path.insert(0, '/home/claude/gemshop/fx')
import fx_gen

R40 = '/home/claude/starkffa-pack/v2/starkffa-pack-r40.zip'
B = '/home/claude/gemshop/pack41/build'
OUT = sys.argv[1] if len(sys.argv) > 1 else '/home/claude/gemshop/pack41/starkffa-pack-r41.zip'
shutil.rmtree(B, ignore_errors=True); os.makedirs(B)
with zipfile.ZipFile(R40) as z: z.extractall(B)
fixed = 0
gui = os.path.join(B, 'assets/starkffa/textures/font/gui')
for root, dirs, fs in os.walk(gui):
    for f in fs:
        if not f.endswith('.png'): continue
        p = os.path.join(root, f)
        im = Image.open(p).convert('RGBA'); px = im.load(); n = 0
        for y in range(im.height):
            for x in range(im.width):
                r, g, b, a = px[x, y]
                if a == 250:
                    px[x, y] = (r, g, b, 255); n += 1
        if n:
            im.save(p); fixed += 1
print('opaque backgrounds:', fixed)
sprites = fx_gen.write(B)
print('fx sprites:', sprites)
if os.path.exists(OUT): os.remove(OUT)
files = []
for root, dirs, fs in os.walk(B):
    for f in fs: files.append(os.path.relpath(os.path.join(root, f), B))
files.sort()
with zipfile.ZipFile(OUT, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as z:
    for f in files:
        zi = zipfile.ZipInfo(f.replace(os.sep, '/'), date_time=(2026, 11, 7, 0, 0, 0))
        zi.compress_type = zipfile.ZIP_DEFLATED
        z.writestr(zi, open(os.path.join(B, f), 'rb').read())
data = open(OUT, 'rb').read()
print(OUT, len(data), 'sha1', hashlib.sha1(data).hexdigest(), 'sha256', hashlib.sha256(data).hexdigest(), 'files', len(files))
