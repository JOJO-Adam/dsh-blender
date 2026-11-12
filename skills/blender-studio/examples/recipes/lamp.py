"""低模路灯（参数化）：灯杆 + 弯臂 + 发光灯头。调 HEIGHT / GLOW_COLOR。
用法: blender -b --python lamp.py -- --outdir <dir>
"""
import bpy, sys, os, math
from mathutils import Vector

HEIGHT = 2.6
GLOW_COLOR = (1.0, 0.78, 0.42, 1)
METAL = (0.12, 0.13, 0.15, 1)

outdir = os.environ.get('DSH_BLENDER_OUTDIR', os.getcwd())
argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
if '--outdir' in argv:
    outdir = argv[argv.index('--outdir') + 1]
os.makedirs(outdir, exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)


def mat(name, color, rough=0.6, emit=None, strength=0.0):
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = color
    b.inputs['Roughness'].default_value = rough
    if emit is not None and 'Emission Color' in b.inputs:
        b.inputs['Emission Color'].default_value = emit
        b.inputs['Emission Strength'].default_value = strength
    return m


metal = mat('metal', METAL, 0.45)
glow = mat('glow', GLOW_COLOR, 0.4, emit=GLOW_COLOR, strength=6.0)

# 底座 + 灯杆
bpy.ops.mesh.primitive_cylinder_add(vertices=10, radius=0.22, depth=0.08, location=(0, 0, 0.04))
bpy.context.object.data.materials.append(metal)
bpy.ops.mesh.primitive_cylinder_add(vertices=10, radius=0.06, depth=HEIGHT, location=(0, 0, HEIGHT / 2))
bpy.context.object.data.materials.append(metal)

# 弯臂（两段圆柱）
for loc, rot, depth in [((0.25, 0, HEIGHT - 0.05), (0, math.radians(90), 0), 0.5),
                        ((0.5, 0, HEIGHT - 0.22), (0, math.radians(90), 0), 0.2)]:
    bpy.ops.mesh.primitive_cylinder_add(vertices=8, radius=0.045, depth=depth, location=loc, rotation=rot)
    bpy.context.object.data.materials.append(metal)

# 灯头（倒锥 + 发光体）
bpy.ops.mesh.primitive_cone_add(vertices=10, radius1=0.20, radius2=0.09, depth=0.16,
                                location=(0.62, 0, HEIGHT - 0.30))
bpy.context.object.data.materials.append(metal)
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.11, location=(0.62, 0, HEIGHT - 0.40))
bpy.context.object.data.materials.append(glow)

# 灯光：发光球本身 + 地面补光
bpy.ops.object.light_add(type='POINT', location=(0.62, 0, HEIGHT - 0.42))
bpy.context.object.data.energy = 12
bpy.context.object.data.color = GLOW_COLOR[:3]
for loc, energy, size in [((2.6, -3.2, 3.4), 160, 2.5), ((-3.0, -1.6, 2.4), 80, 3.0), ((0.8, 3.0, 2.8), 100, 2.0)]:
    bpy.ops.object.light_add(type='AREA', location=loc)
    bpy.context.object.data.energy = energy
    bpy.context.object.data.size = size

# 地面
bpy.ops.mesh.primitive_plane_add(size=8, location=(0, 0, 0))
bpy.context.object.data.materials.append(mat('floor', (0.10, 0.11, 0.13, 1), 0.9))

bpy.ops.object.camera_add(location=(3.2, -4.0, 2.4))
cam = bpy.context.object
target = Vector((0.25, 0, 1.45))
direction = target - cam.location
cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
cam.data.lens = 50
bpy.context.scene.camera = cam

sc = bpy.context.scene
sc.render.engine = 'BLENDER_EEVEE'
sc.view_settings.view_transform = 'Standard'
sc.render.resolution_x = 512
sc.render.resolution_y = 512
sc.render.filepath = os.path.join(outdir, 'lamp.png')
bpy.ops.render.render(write_still=True)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(outdir, 'lamp.blend'))
bpy.ops.export_scene.gltf(filepath=os.path.join(outdir, 'lamp.glb'), export_format='GLB')
print('DONE', outdir)
