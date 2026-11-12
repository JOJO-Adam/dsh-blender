"""低模箱子堆（参数化）：多只木箱随机堆叠。调 COUNT / SEED。
用法: blender -b --python stack.py -- --outdir <dir>
"""
import bpy, sys, os, math, random
from mathutils import Vector

COUNT = 5
SEED = 3
BASE = 0.62
COLOR = (0.30, 0.17, 0.07, 1)
EDGE = (0.20, 0.11, 0.05, 1)

outdir = os.environ.get('DSH_BLENDER_OUTDIR', os.getcwd())
argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
if '--outdir' in argv:
    outdir = argv[argv.index('--outdir') + 1]
os.makedirs(outdir, exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)


def mat(name, color, rough=0.75):
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = color
    b.inputs['Roughness'].default_value = rough
    return m


wood = mat('wood', COLOR)
edge = mat('edge', EDGE)

random.seed(SEED)
placements = [
    (0.0, 0.0, 0.31, 0.00),
    (-0.68, 0.22, 0.29, 0.42),
    (0.62, -0.16, 0.27, -0.32),
    (0.06, 0.06, 0.92, 0.16),
    (-0.52, -0.62, 0.25, 0.85),
]
for i, (x, y, z, rot) in enumerate(placements[:COUNT]):
    s = BASE * random.uniform(0.80, 1.12)
    bpy.ops.mesh.primitive_cube_add(size=1, location=(x, y, z), rotation=(0, 0, rot))
    o = bpy.context.object
    o.scale = (s, s, s)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    o.data.materials.append(wood)

bpy.ops.mesh.primitive_plane_add(size=10, location=(0, 0, 0))
bpy.context.object.data.materials.append(mat('floor', (0.15, 0.15, 0.16, 1), 0.92))

for loc, energy, size in [((3.2, -3.6, 3.6), 170, 2.5), ((-3.2, -1.8, 2.6), 85, 3.0), ((1.2, 3.4, 2.8), 110, 2.0)]:
    bpy.ops.object.light_add(type='AREA', location=loc)
    bpy.context.object.data.energy = energy
    bpy.context.object.data.size = size

bpy.ops.object.camera_add(location=(2.6, -3.8, 2.2))
cam = bpy.context.object
target = Vector((0, 0, 0.5))
cam.rotation_euler = (target - cam.location).to_track_quat('-Z', 'Y').to_euler()
cam.data.lens = 50
bpy.context.scene.camera = cam

sc = bpy.context.scene
sc.render.engine = 'BLENDER_EEVEE'
sc.view_settings.view_transform = 'Standard'
sc.render.resolution_x = 512
sc.render.resolution_y = 512
sc.render.filepath = os.path.join(outdir, 'stack.png')
bpy.ops.render.render(write_still=True)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(outdir, 'stack.blend'))
bpy.ops.export_scene.gltf(filepath=os.path.join(outdir, 'stack.glb'), export_format='GLB')
print('DONE', outdir)
