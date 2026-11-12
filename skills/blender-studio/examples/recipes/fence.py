"""低模木栅栏（参数化）：立柱 + 两道横栏。
用法: blender -b --python fence.py -- --outdir <dir>
"""
import bpy, sys, os
from mathutils import Vector

POSTS = 6          # 立柱数
HEIGHT = 1.1       # 栅栏高
SPACING = 1.0      # 柱距
RAILS = 2          # 横栏数
COLOR = (0.34, 0.20, 0.10, 1)

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
length = (POSTS - 1) * SPACING
x0 = -length / 2

for i in range(POSTS):
    x = x0 + i * SPACING
    bpy.ops.mesh.primitive_cube_add(size=1, location=(x, 0, HEIGHT / 2))
    o = bpy.context.object
    o.scale = (0.09, 0.09, HEIGHT)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    o.data.materials.append(wood)

for r in range(RAILS):
    z = HEIGHT * (0.36 + 0.46 * r)
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, z))
    o = bpy.context.object
    o.scale = (length + 0.15, 0.06, 0.11)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    o.data.materials.append(wood)

bpy.ops.mesh.primitive_plane_add(size=10, location=(0, 0, 0))
bpy.context.object.data.materials.append(mat('floor', (0.15, 0.15, 0.16, 1), 0.92))

for loc, energy, size in [((3.2, -3.6, 3.4), 160, 2.5), ((-3.2, -1.8, 2.4), 80, 3.0), ((1.0, 3.4, 2.8), 100, 2.0)]:
    bpy.ops.object.light_add(type='AREA', location=loc)
    bpy.context.object.data.energy = energy
    bpy.context.object.data.size = size

bpy.ops.object.camera_add(location=(2.4, -5.0, 2.3))
cam = bpy.context.object
target = Vector((0, 0, 0.55))
cam.rotation_euler = (target - cam.location).to_track_quat('-Z', 'Y').to_euler()
cam.data.lens = 45
bpy.context.scene.camera = cam

sc = bpy.context.scene
sc.render.engine = 'BLENDER_EEVEE'
sc.view_settings.view_transform = 'Standard'
sc.render.resolution_x = 512
sc.render.resolution_y = 512
sc.render.filepath = os.path.join(outdir, 'fence.png')
bpy.ops.render.render(write_still=True)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(outdir, 'fence.blend'))
bpy.ops.export_scene.gltf(filepath=os.path.join(outdir, 'fence.glb'), export_format='GLB')
print('DONE', outdir)
