"""低模树（参数化）。调 HEIGHT / TRUNK_COLOR / LEAF_COLOR 即可。
用法: blender -b --python tree.py -- --outdir <dir>
"""
import bpy, sys, os, math, random

HEIGHT = 2.2        # 总高
TRUNK_R = 0.13
LEAF_COLOR = (0.18, 0.42, 0.16, 1)
TRUNK_COLOR = (0.28, 0.18, 0.10, 1)
SEED = 7

outdir = os.environ.get('DSH_BLENDER_OUTDIR', os.getcwd())
argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
if '--outdir' in argv:
    outdir = argv[argv.index('--outdir') + 1]
os.makedirs(outdir, exist_ok=True)
random.seed(SEED)
bpy.ops.wm.read_factory_settings(use_empty=True)


def mat(name, color, rough=0.75):
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = color
    b.inputs['Roughness'].default_value = rough
    return m


trunk_mat = mat('trunk', TRUNK_COLOR, 0.9)
leaf_mat = mat('leaf', LEAF_COLOR, 0.8)

# 树干
bpy.ops.mesh.primitive_cone_add(vertices=7, radius1=TRUNK_R, radius2=TRUNK_R * 0.55,
                                depth=HEIGHT * 0.42, location=(0, 0, HEIGHT * 0.21))
bpy.context.object.data.materials.append(trunk_mat)

# 三层锥形树冠
for i in range(3):
    r = 0.62 - i * 0.14
    z = HEIGHT * (0.40 + i * 0.17)
    bpy.ops.mesh.primitive_cone_add(vertices=8, radius1=r, radius2=0.02,
                                    depth=HEIGHT * 0.26, location=(0, 0, z),
                                    rotation=(0, 0, random.uniform(0, 1)))
    bpy.context.object.data.materials.append(leaf_mat)

# 地面
bpy.ops.mesh.primitive_plane_add(size=8, location=(0, 0, 0))
bpy.context.object.data.materials.append(mat('floor', (0.16, 0.16, 0.17, 1), 0.95))

for loc, energy, size in [((2.6, -2.8, 3.2), 70, 2.5), ((-3.0, -1.4, 2.2), 35, 3.0), ((0.6, 3.2, 2.6), 50, 2.0)]:
    bpy.ops.object.light_add(type='AREA', location=loc)
    bpy.context.object.data.energy = energy
    bpy.context.object.data.size = size

bpy.ops.object.camera_add(location=(2.2, -2.8, 1.9))
cam = bpy.context.object
cam.rotation_euler = (math.radians(63), 0, math.radians(38))
bpy.context.scene.camera = cam

sc = bpy.context.scene
sc.render.engine = 'BLENDER_EEVEE'
sc.view_settings.view_transform = 'Standard'
sc.render.resolution_x = 512
sc.render.resolution_y = 512
sc.render.filepath = os.path.join(outdir, 'tree.png')
bpy.ops.render.render(write_still=True)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(outdir, 'tree.blend'))
bpy.ops.export_scene.gltf(filepath=os.path.join(outdir, 'tree.glb'), export_format='GLB')
print('DONE', outdir)
