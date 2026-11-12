"""低模台阶（参数化）：STEPS 级石阶。调 STEPS / WIDTH / RISER / TREAD。
用法: blender -b --python steps.py -- --outdir <dir>
"""
import bpy, sys, os
from mathutils import Vector

STEPS = 5
WIDTH = 1.6
RISER = 0.22
TREAD = 0.34
COLOR = (0.50, 0.48, 0.46, 1)

outdir = os.environ.get('DSH_BLENDER_OUTDIR', os.getcwd())
argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
if '--outdir' in argv:
    outdir = argv[argv.index('--outdir') + 1]
os.makedirs(outdir, exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)


def mat(name, color, rough=0.85):
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = color
    b.inputs['Roughness'].default_value = rough
    return m


stone = mat('stone', COLOR)

for i in range(STEPS):
    h = RISER * (i + 1)
    bpy.ops.mesh.primitive_cube_add(size=1, location=(TREAD * i + TREAD / 2, 0, h / 2))
    o = bpy.context.object
    o.scale = (TREAD, WIDTH, h)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    o.data.materials.append(stone)

bpy.ops.mesh.primitive_plane_add(size=10, location=(0, 0, 0))
bpy.context.object.data.materials.append(mat('floor', (0.15, 0.15, 0.16, 1), 0.92))

for loc, energy, size in [((3.4, -3.8, 3.8), 180, 2.5), ((-3.2, -2.0, 2.8), 90, 3.0), ((1.4, 3.6, 3.0), 115, 2.0)]:
    bpy.ops.object.light_add(type='AREA', location=loc)
    bpy.context.object.data.energy = energy
    bpy.context.object.data.size = size

bpy.ops.object.camera_add(location=(3.0, -3.6, 2.1))
cam = bpy.context.object
target = Vector((0.85, 0, 0.55))
cam.rotation_euler = (target - cam.location).to_track_quat('-Z', 'Y').to_euler()
cam.data.lens = 45
bpy.context.scene.camera = cam

sc = bpy.context.scene
sc.render.engine = 'BLENDER_EEVEE'
sc.view_settings.view_transform = 'Standard'
sc.render.resolution_x = 512
sc.render.resolution_y = 512
sc.render.filepath = os.path.join(outdir, 'steps.png')
bpy.ops.render.render(write_still=True)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(outdir, 'steps.blend'))
bpy.ops.export_scene.gltf(filepath=os.path.join(outdir, 'steps.glb'), export_format='GLB')
print('DONE', outdir)
