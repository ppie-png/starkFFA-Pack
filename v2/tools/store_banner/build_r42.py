"""Pack r42 = r41 + the /store dialog banner (font starkffa:store, U+E000-E003 + spaces U+F801 -1 / U+F802 +1): two product cards like the web store -
RANKS (SPARK/STORM/STARK badges) and GEMS (the pink 3D gem). Texture 564x184 drawn at 2x -> glyph 282x92 GUI px,
ascent 92: the glyph sits on the last of 11 text lines in the dialog (the empty lines above reserve its height)."""
import hashlib, json, os, shutil, sys, zipfile
R41 = '/home/claude/starkffa-pack/v2/starkffa-pack-r41.zip'
B = '/home/claude/gemshop/pack42/build'
OUT = sys.argv[1] if len(sys.argv) > 1 else '/home/claude/gemshop/pack42/starkffa-pack-r42.zip'
BANNER = '/home/claude/storeui/banner_strip.png'
shutil.rmtree(B, ignore_errors=True); os.makedirs(B)
with zipfile.ZipFile(R41) as z: z.extractall(B)
os.makedirs(os.path.join(B, 'assets/starkffa/textures/font/store'), exist_ok=True)
shutil.copy(BANNER, os.path.join(B, 'assets/starkffa/textures/font/store/banner.png'))
font = {'providers': [{'type': 'bitmap', 'file': 'starkffa:font/store/banner.png', 'height': 92, 'ascent': 92,
                       'chars': [''.join(chr(0xE000 + k) for k in range(4))]},
                      {'type': 'space', 'advances': {chr(0xF801): -1, chr(0xF802): 1}}]}
json.dump(font, open(os.path.join(B, 'assets/starkffa/font/store.json'), 'w'), indent=1)
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
