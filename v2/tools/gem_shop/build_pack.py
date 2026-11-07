import json, os, shutil, subprocess, sys, zipfile, hashlib
R39 = '/home/claude/starkffa-pack/v2/starkffa-pack-r39.zip'
ART = '/home/claude/gemshop/art/out'
SH = '/home/claude/gemshop/shader'
B = '/home/claude/gemshop/pack/build'
OUT = sys.argv[1] if len(sys.argv) > 1 else '/home/claude/gemshop/pack/starkffa-pack-r40.zip'
shutil.rmtree(B, ignore_errors=True); os.makedirs(B)
with zipfile.ZipFile(R39) as z: z.extractall(B)
# shop art
shutil.copytree(os.path.join(ART, 'assets/starkffa/textures/font/gui/shop'), os.path.join(B, 'assets/starkffa/textures/font/gui/shop'))
for f in os.listdir(os.path.join(ART, 'assets/starkffa/font')):
    shutil.copy(os.path.join(ART, 'assets/starkffa/font', f), os.path.join(B, 'assets/starkffa/font', f))
gui = json.load(open(os.path.join(B, 'assets/starkffa/font/gui.json'), encoding='utf-8'))
used = set()
for p in gui['providers']:
    for row in p.get('chars', []): used |= set(row)
    used |= set(p.get('advances', {}).keys())
new = json.load(open(os.path.join(ART, 'gui_providers.json'), encoding='utf-8'))
for p in new:
    for c in ''.join(p['chars']):
        assert c not in used, 'glyph already used: %04X' % ord(c)
gui['providers'] += new
json.dump(gui, open(os.path.join(B, 'assets/starkffa/font/gui.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
# text shader overlays (1.21.11 = format 75, 26.3 = format 97)
for d, src, name in (('stark_text_75', 'rendertype_text_12111.vsh', 'rendertype_text.vsh'), ('stark_text_97', 'text_263.vsh', 'text.vsh')):
    t = os.path.join(B, d, 'assets/minecraft/shaders/core'); os.makedirs(t, exist_ok=True)
    shutil.copy(os.path.join(SH, src), os.path.join(t, name))
m = json.load(open(os.path.join(B, 'pack.mcmeta'), encoding='utf-8'))
m['overlays'] = {'entries': [{'min_format': 75, 'max_format': 75, 'directory': 'stark_text_75'},
                             {'min_format': [97, 0], 'max_format': 97, 'directory': 'stark_text_97'}]}
json.dump(m, open(os.path.join(B, 'pack.mcmeta'), 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
# zip with a fixed timestamp + sorted order (reproducible)
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
