"""Pack r29 = r28 + rank icons (src_ranks/icons.py) added to font starkffa:ranks (the r28 badges stay for rollback)."""
import zipfile, hashlib, os, sys, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import icons
V2 = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
src = zipfile.ZipFile(os.path.join(V2, "starkffa-pack-r28.zip"))
files, prov, cps = icons.build()
font = json.loads(src.read("assets/starkffa/font/ranks.json"))
font["providers"] = [p for p in font["providers"] if p.get("file") != "starkffa:font/ranks/icons.png"] + prov
files["assets/starkffa/font/ranks.json"] = json.dumps(font, indent=2, ensure_ascii=True).encode("utf-8")
out_path = os.path.join(V2, "starkffa-pack-r29.zip")
DT = (2026, 11, 3, 0, 0, 0)
with zipfile.ZipFile(out_path, "w", zipfile.ZIP_DEFLATED) as out:
    for info in src.infolist():
        if info.filename in files: continue
        zi = zipfile.ZipInfo(info.filename, DT); zi.compress_type = zipfile.ZIP_DEFLATED; zi.external_attr = info.external_attr
        out.writestr(zi, src.read(info.filename))
    for rel in sorted(files):
        zi = zipfile.ZipInfo(rel, DT); zi.compress_type = zipfile.ZIP_DEFLATED; zi.external_attr = 0o644 << 16
        out.writestr(zi, files[rel])
print(out_path, os.path.getsize(out_path), "sha1", hashlib.sha1(open(out_path, "rb").read()).hexdigest())
