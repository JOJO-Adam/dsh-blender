"""低模小屋（参数化）：方体屋身 + 四坡屋顶 + 门窗。
用法: blender -b --python house.py -- --outdir <dir>
"""
import bpy, sys, os, math
from mathutils import Vector

W, D, H = 1.8, 1.4, 1.1
ROOF_H = 0.85
WALL = (0.55, 0.50, 0.45, 1)
ROOF = (0.42, 0.18, 0.12, 1)
DOOR = (0.22, 0.13, 0.07, 1)
WINDOW = (0.72, 0.82, 0.88, 1)

outdir = os.environ.get('DSH_BLENDER_OUTDIR', os.getcwd())
argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
if '--outdir' in argv:
    outdir = argv[argv.index('--outdir') + 1]
os.makedirs(outdir, exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)


def mat(name, color, rough=0.8, emit=None, strength=0.0):
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = color
    b.inputs['Roughness'].default_value = rough
    if emit is not None and 'Emission Color' in b.inputs:
        b.inputs['Emission Color'].default_value = emit
        b.inputs['Emission Strength'].default_value = strength
    return m


wall = mat('wall', WALL)
roof = mat('roof', ROOF, 0.7)
door = mat('door', DOOR, 0.85)
glass = mat('glass', WINDOW, 0.3, emit=WINDOW, strength=1.2)

bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, H / 2))
o = bpy.context.object
o.scale = (W, D, H)
bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
o.data.materials.append(wall)

bpy.ops.mesh.primitive_cone_add(vertices=4, radius1=math.hypot(W / 2, D / 2) * 1.02,
                                radius2=0, depth=ROOF_H, location=(0, 0, H + ROOF_H / 2),
                                rotation=(0, 0, math.radians(45)))
bpy.context.object.data.materials.append(roof)

bpy.ops.mesh.primitive_cube_add(size=1, location=(0, -D / 2 - 0.005, 0.32))
o = bpy.context.object
o.scale = (0.36, 0.03, 0.62)
o.data.materials.append(door)

for x in (-0.62, 0.62):
    bpy.ops.mesh.primitive_cube_add(size=1, location=(x, -D / 2 - 0.006, 0.62))
    o = bpy.context.object
    o.scale = (0.34, 0.02, 0.32)
    o.data.materials.append(glass)

bpy.ops.mesh.primitive_plane_add(size=10, location=(0, 0, 0))
bpy.context.object.data.materials.append(mat('floor', (0.17, 0.17, 0.18, 1), 0.92))

for loc, energy, size in [((3.2, -3.6, 3.6), 170, 2.5), ((-3.2, -1.8, 2.6), 85, 3.0), ((1.2, 3.4, 2.8), 110, 2.0)]:
    bpy.ops.object.light_add(type='AREA', location=loc)
    bpy.context.object.data.energy = energy
    bpy.context.object.data.size = size

bpy.ops.object.camera_add(location=(3.0, -4.2, 2.3))
cam = bpy.context.object
target = Vector((0, 0, 0.7))
cam.rotation_euler = (target - cam.location).to_track_quat('-Z', 'Y').to_euler()
cam.data.lens = 48
bpy.context.scene.camera = cam

sc = bpy.context.scene
sc.render.engine = 'BLENDER_EEVEE'
sc.view_settings.view_transform = 'Standard'
sc.render.resolution_x = 512
sc.render.resolution_y = 512
sc.render.filepath = os.path.join(outdir, 'house.png')
bpy.ops.render.render(write_still=True)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(outdir, 'house.blend'))
bpy.ops.export_scene.gltf(filepath=os.path.join(outdir, 'house.glb'), export_format='GLB')
print('DONE', outdir)
