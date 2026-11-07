"""First-person comparison renders (ItemInHandRenderer main hand): T(0.56,-0.52,-0.72) * firstperson_righthand,
camera at the origin looking straight down -Z, vertical FOV 70 (the hand projection ignores the FOV option).
usage (bpy python): fp_compare.py <outdir> <aspect>  -> one png per variant"""
import json, math, os, sys
import numpy as np
sys.path.insert(0, '/home/claude/wpn')
import mcrender as R
R.ROOTS.insert(0, '/tmp/claude-0/mcr/assets/')

OUT = sys.argv[1]
ASPECT = float(sys.argv[2]) if len(sys.argv) > 2 else 16 / 9
H = 640
W = int(round(H * ASPECT))
os.makedirs(OUT, exist_ok=True)
WEAPON = '/home/claude/wpn/out/assets/starkffa/models/item/frost_slam.json'
VARIANTS = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'variants.json')))


def T(x, y, z):
    M = np.eye(4); M[:3, 3] = [x, y, z]; return M


def shot(name, ref, disp):
    R.reset(W, H, bg=(0.55, 0.74, 0.95), samples=10)
    stone = {'textures': {'0': 'minecraft:block/stone_bricks'}, 'elements': [{'from': [0, 0, 0], 'to': [16, 16, 16], 'faces': {
        'up': {'uv': [0, 0, 16, 16], 'texture': '#0'}}}]}
    for x in range(-14, 15):
        for z in range(-26, 1):
            R.build(stone, T(x - 0.5, -2.62, z - 0.5), f'g{x}_{z}')
    M = T(0.56, -0.52, -0.72) @ R.display_matrix(disp)
    R.build(ref, M, 'hand')
    R.camera((0, 0, 0), (0, 0, -1), fov=70)
    R.render(os.path.join(OUT, name + '.png'))


for v in VARIANTS:
    ref = v['ref']
    if ref == 'WEAPON':
        ref = WEAPON
    disp = v.get('display') or R.resolve(ref)['display']['firstperson_righthand']
    shot(v['name'], ref, disp)
    print('rendered', v['name'], disp)
