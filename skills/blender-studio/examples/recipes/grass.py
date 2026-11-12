"""低模草丛（参数化）：N 片锥形草叶。调 COUNT / HEIGHT / SEED。
用法: blender -b --python grass.py -- --outdir <dir>
"""
import bpy, sys, os, random
from mathutils import Vector

COUNT = 14
HEIGHT = 0.32
SEED = 5
COLOR = (0.20, 0.44, 0.16, 1)

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


green = mat('leaf', COLOR)

random.seed(SEED)
for i in range(COUNT):
    x = random.uniform(-0.42, 0.42)
    y = random.uniform(-0.42, 0.42)
    h = HEIGHT * random.uniform(0.6, 1.25)
    tilt = random.uniform(0, 0.32)
    rot_z = random.uniform(0, 6.283)
    bpy.ops.mesh.primitive_cone_add(vertices=4, radius1=0.048, radius2=0, depth=h,
                                    location=(x, y, h / 2), rotation=(tilt, 0, rot_z))
    bpy.context.object.data.materials.append(green)

bpy.ops.mesh.primitive_plane_add(size=6, location=(0, 0, 0))
bpy.context.object.data.materials.append(mat('floor', (0.16, 0.17, 0.16, 1), 0.92))

for loc, energy, size in [((2.4, -2.8, 3.0), 140, 2.5), ((-2.8, -1.4, 2.2), 70, 3.0), ((0.8, 3.0, 2.4), 90, 2.0)]:
    bpy.ops.object.light_add(type='AREA', location=loc)
    bpy.context.object.data.energy = energy
    bpy.context.object.data.size = size

bpy.ops.object.camera_add(location=(1.6, -2.2, 1.2))
cam = bpy.context.object
target = Vector((0, 0, 0.16))
cam.rotation_euler = (target - cam.location).to_track_quat('-Z', 'Y').to_euler()
cam.data.lens = 55
bpy.context.scene.camera = cam

sc = bpy.context.scene
sc.render.engine = 'BLENDER_EEVEE'
sc.view_settings.view_transform = 'Standard'
sc.render.resolution_x = 512
sc.render.resolution_y = 512
sc.render.filepath = os.path.join(outdir, 'grass.png')
bpy.ops.render.render(write_still=True)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(outdir, 'grass.blend'))
bpy.ops.export_scene.gltf(filepath=os.path.join(outdir, 'grass.glb'), export_format='GLB')
print('DONE', outdir)
