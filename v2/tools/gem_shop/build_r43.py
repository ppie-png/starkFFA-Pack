"""Pack r43 = r42 + the r86 rank styles in the text shader (13 name styles: + spark_rank (green volt), stark_rank (own
STARK kind: slow gold shine + sparkles), storm_rank (violet -> cyan tide)) in both overlays (stark_text_75 = 1.21.11
rendertype_text.vsh, stark_text_97 = 26.3 text.vsh) + the fx_cloud sprite (thunderstorm kill effect)."""
import hashlib, os, shutil, sys, zipfile
R42 = '/home/claude/starkffa-pack/v2/starkffa-pack-r42.zip'
B = '/home/claude/gemshop/pack43/build'
OUT = sys.argv[1] if len(sys.argv) > 1 else '/home/claude/gemshop/pack43/starkffa-pack-r43.zip'
SH = '/home/claude/gemshop/shader'
FX = '/home/claude/starkffa-pack/v2/src/assets/starkffa'   # fx_cloud from tools/gem_shop/fx_gen.py
shutil.rmtree(B, ignore_errors=True); os.makedirs(B)
with zipfile.ZipFile(R42) as z: z.extractall(B)
shutil.copy(os.path.join(SH, 'text_263.vsh'), os.path.join(B, 'stark_text_97/assets/minecraft/shaders/core/text.vsh'))
shutil.copy(os.path.join(SH, 'rendertype_text_12111.vsh'), os.path.join(B, 'stark_text_75/assets/minecraft/shaders/core/rendertype_text.vsh'))
for sub, name in (('textures/item', 'fx_cloud.png'), ('models/item', 'fx_cloud.json'), ('items', 'fx_cloud.json')):
    dst = os.path.join(B, 'assets/starkffa', sub)
    os.makedirs(dst, exist_ok=True)
    shutil.copy(os.path.join(FX, sub, name), os.path.join(dst, name))
if os.path.exists(OUT): os.remove(OUT)
files = []
for root, dirs, fs in os.walk(B):
    for f in fs: files.append(os.path.relpath(os.path.join(root, f), B))
files.sort()
with zipfile.ZipFile(OUT, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as z:
    for f in files:
        zi = zipfile.ZipInfo(f.replace(os.sep, '/'), date_time=(2026, 11, 8, 0, 0, 0))
        zi.compress_type = zipfile.ZIP_DEFLATED
        z.writestr(zi, open(os.path.join(B, f), 'rb').read())
data = open(OUT, 'rb').read()
print(OUT, len(data), 'sha1', hashlib.sha1(data).hexdigest(), 'sha256', hashlib.sha256(data).hexdigest())
