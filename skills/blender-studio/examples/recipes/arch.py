"""低模拱门（参数化）：两根立柱 + 弧形楔石。调 WIDTH / HEIGHT / BLOCKS。
用法: blender -b --python arch.py -- --outdir <dir>
"""
import bpy, sys, os, math
from mathutils import Vector

WIDTH = 1.7      # 柱外间距
HEIGHT = 1.5     # 柱高
BLOCKS = 7       # 弧上楔石数
COLOR = (0.52, 0.48, 0.42, 1)

outdir = os.environ.get('DSH_BLENDER_OUTDIR', os.getcwd())
argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
if '--outdir' in argv:
    outdir = argv[argv.index('--outdir') + 1]
os.makedirs(outdir, exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)


def mat(name, color, rough=0.8):
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = color
    b.inputs['Roughness'].default_value = rough
    return m


stone = mat('stone', COLOR)
R = WIDTH / 2

for sign in (-1, 1):
    bpy.ops.mesh.primitive_cube_add(size=1, location=(sign * R, 0, HEIGHT / 2))
    o = bpy.context.object
    o.scale = (0.22, 0.34, HEIGHT)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    o.data.materials.append(stone)

for i in range(BLOCKS):
    t = math.pi * (i + 0.5) / BLOCKS
    x = R * math.cos(t)
    z = HEIGHT + R * 0.62 * math.sin(t)
    bpy.ops.mesh.primitive_cube_add(size=1, location=(x, 0, z))
    o = bpy.context.object
    o.scale = (0.24, 0.34, 0.22)
    o.rotation_euler = (0, -t + math.pi / 2, 0)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    o.data.materials.append(stone)

bpy.ops.mesh.primitive_plane_add(size=10, location=(0, 0, 0))
bpy.context.object.data.materials.append(mat('floor', (0.15, 0.15, 0.16, 1), 0.92))

for loc, energy, size in [((3.2, -3.8, 3.8), 180, 2.5), ((-3.4, -2.0, 2.8), 90, 3.0), ((1.2, 3.6, 3.0), 115, 2.0)]:
    bpy.ops.object.light_add(type='AREA', location=loc)
    bpy.context.object.data.energy = energy
    bpy.context.object.data.size = size

bpy.ops.object.camera_add(location=(2.6, -4.6, 2.3))
cam = bpy.context.object
target = Vector((0, 0, 1.1))
cam.rotation_euler = (target - cam.location).to_track_quat('-Z', 'Y').to_euler()
cam.data.lens = 45
bpy.context.scene.camera = cam

sc = bpy.context.scene
sc.render.engine = 'BLENDER_EEVEE'
sc.view_settings.view_transform = 'Standard'
sc.render.resolution_x = 512
sc.render.resolution_y = 512
sc.render.filepath = os.path.join(outdir, 'arch.png')
bpy.ops.render.render(write_still=True)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(outdir, 'arch.blend'))
bpy.ops.export_scene.gltf(filepath=os.path.join(outdir, 'arch.glb'), export_format='GLB')
print('DONE', outdir)
