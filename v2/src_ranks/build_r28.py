"""Pack r28 = r27 + the new rank badges (src_ranks/badges.py) replacing the r7 pills."""
import zipfile, hashlib, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import badges
V2 = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
src = zipfile.ZipFile(os.path.join(V2, "starkffa-pack-r27.zip"))
new_files, frames = badges.build(None)
out_path = os.path.join(V2, "starkffa-pack-r28.zip")
DT = (2026, 11, 3, 0, 0, 0)
def is_old_rank(name):
    return name == "assets/starkffa/font/ranks.json" or name.startswith("assets/starkffa/textures/font/ranks/")
with zipfile.ZipFile(out_path, "w", zipfile.ZIP_DEFLATED) as out:
    written = set()
    for info in src.infolist():
        if is_old_rank(info.filename): continue
        zi = zipfile.ZipInfo(info.filename, DT); zi.compress_type = zipfile.ZIP_DEFLATED; zi.external_attr = info.external_attr
        out.writestr(zi, src.read(info.filename)); written.add(info.filename)
    for rel in sorted(new_files):
        zi = zipfile.ZipInfo(rel, DT); zi.compress_type = zipfile.ZIP_DEFLATED; zi.external_attr = 0o644 << 16
        out.writestr(zi, new_files[rel]); written.add(rel)
sha1 = hashlib.sha1(open(out_path, "rb").read()).hexdigest()
print(out_path, os.path.getsize(out_path), "bytes,", len(written), "entries, sha1", sha1)
