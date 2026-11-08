"""The pink 3D voxel gem alone (front pose like the store's home card) with floating cube particles - for the /store
dialog banner. Transparent PNG."""
import sys
sys.path.insert(0, '/home/claude/gems2')
import bpy, math, mathutils
import gemlib as g
W, H, S = int(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3])
out = sys.argv[4]
s = g.reset(W, H, S)
me, mat = g.load_gem(1.0)
o = bpy.data.objects.new('gem', me)
o.location = (0, 0, 0)
o.rotation_euler = (0, 0, math.radians(-18))
s.collection.objects.link(o)
g.rig((0, 0, 0), k=0.75, e=0.42)
g.cube_particles(12, (0.0, 0.0, -0.62), 0.78, 21, size=(0.022, 0.042), height=(0.0, 1.25))
g.camera((0, 0, 0.0), 3.15, elev=10, azim=-14, lens=85)
s.render.filepath = out
bpy.ops.render.render(write_still=True)
