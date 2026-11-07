"""Pack r36: BetterModel player limbs with gap-free joints (see joints.py) - post-processes the BetterModel limb models
inside the STARK pack. Run after every BetterModel update that regenerates assets/bettermodel/models/player_limb/.

  python3 pack_joints.py <in.zip> <out.zip>

Changes (only these files): models/player_limb/<limb>_0.json (base layer: joint prism + side-face inset) and
<limb>_<n>.json (overlay pixels: side-face inset) for the joint limbs in joints.JOINT_LIMBS.
"""
import json
import re
import sys
import zipfile

sys.path.insert(0, __import__('os').path.dirname(__import__('os').path.abspath(__file__)))
import joints  # noqa: E402
from limbs import SIDE_INSET  # noqa: E402

BASE = 'assets/bettermodel/models/player_limb/'


def inset_side_faces(model, ins):
    """Moves EAST faces -ins and WEST faces +ins in x (flat single-face elements)."""
    n = 0
    for e in model.get('elements', []):
        faces = e.get('faces', {})
        if len(faces) != 1:
            continue
        f = next(iter(faces))
        if f == 'east':
            e['from'][0] = round(e['from'][0] - ins, 6)
            e['to'][0] = round(e['to'][0] - ins, 6)
            n += 1
        elif f == 'west':
            e['from'][0] = round(e['from'][0] + ins, 6)
            e['to'][0] = round(e['to'][0] + ins, 6)
            n += 1
    return n


def main(src, dst):
    zin = zipfile.ZipFile(src)
    zout = zipfile.ZipFile(dst, 'w', zipfile.ZIP_DEFLATED)
    stats = {}
    pat = re.compile(re.escape(BASE) + r'(' + '|'.join(sorted(joints.JOINT_LIMBS, key=len, reverse=True)) + r')_(\d+)\.json$')
    for info in zin.infolist():
        data = zin.read(info.filename)
        m = pat.match(info.filename)
        if m:
            limb, idx = m.group(1), int(m.group(2))
            model = json.loads(data)
            if idx == 0 and any('rotation' in e for e in model.get('elements', [])):
                raise SystemExit(f'{info.filename} already processed (has rotated elements)')
            moved = inset_side_faces(model, SIDE_INSET.get(limb, 0.0))
            added = 0
            if idx == 0:
                els = joints.mc_elements(limb)
                ntint = max(f['tintindex'] for e in model['elements'] for f in e['faces'].values()) + 1
                assert all(f['tintindex'] < ntint for e in els for f in e['faces'].values()), limb
                model['elements'].extend(els)
                added = len(els)
            data = json.dumps(model, separators=(',', ':')).encode()
            s = stats.setdefault(limb, [0, 0, 0])
            s[0] += 1
            s[1] += moved
            s[2] += added
        zi = zipfile.ZipInfo(info.filename, date_time=info.date_time)
        zi.compress_type = zipfile.ZIP_DEFLATED
        zi.external_attr = info.external_attr
        zout.writestr(zi, data)
    zout.close()
    for limb, (files, moved, added) in sorted(stats.items()):
        print(f'{limb:20s} files {files:4d}  side faces moved {moved:4d}  joint elements {added}')
    missing = set(joints.JOINT_LIMBS) - set(stats)
    if missing:
        raise SystemExit(f'limbs not found in the pack: {missing}')


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
