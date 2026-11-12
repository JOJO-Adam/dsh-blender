"""低模木桶（参数化）：三段桶身 + 两道铁箍。
用法: blender -b --python barrel.py -- --outdir <dir>
"""
import bpy, sys, os
from mathutils import Vector

RADIUS = 0.42
HEIGHT = 0.95
BULGE = 1.14       # 中部膨胀系数
HOOPS = 2
COLOR = (0.36, 0.20, 0.09, 1)
METAL = (0.13, 0.14, 0.16, 1)

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
metal = mat('metal', METAL, 0.45)

segs = [(RADIUS * 0.88, HEIGHT * 0.34), (RADIUS * BULGE, HEIGHT * 0.32), (RADIUS * 0.88, HEIGHT * 0.34)]
z = 0.0
for r, h in segs:
    bpy.ops.mesh.primitive_cylinder_add(vertices=12, radius=r, depth=h, location=(0, 0, z + h / 2))
    bpy.context.object.data.materials.append(wood)
    z += h

for i in range(HOOPS):
    zc = HEIGHT * (0.22 + 0.56 * i)
    bpy.ops.mesh.primitive_cylinder_add(vertices=12, radius=RADIUS * BULGE + 0.014, depth=0.07,
                                        location=(0, 0, zc))
    bpy.context.object.data.materials.append(metal)

bpy.ops.mesh.primitive_plane_add(size=8, location=(0, 0, 0))
bpy.context.object.data.materials.append(mat('floor', (0.15, 0.15, 0.16, 1), 0.92))

for loc, energy, size in [((2.8, -3.2, 3.2), 150, 2.5), ((-3.0, -1.6, 2.4), 75, 3.0), ((1.0, 3.2, 2.6), 95, 2.0)]:
    bpy.ops.object.light_add(type='AREA', location=loc)
    bpy.context.object.data.energy = energy
    bpy.context.object.data.size = size

bpy.ops.object.camera_add(location=(2.3, -3.4, 1.8))
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
sc.render.filepath = os.path.join(outdir, 'barrel.png')
bpy.ops.render.render(write_still=True)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(outdir, 'barrel.blend'))
bpy.ops.export_scene.gltf(filepath=os.path.join(outdir, 'barrel.glb'), export_format='GLB')
print('DONE', outdir)
