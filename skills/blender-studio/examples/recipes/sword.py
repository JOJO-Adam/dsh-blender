"""低模道具剑（参数化）：剑身 + 护手 + 剑柄 + 剑首。调 LENGTH / WIDTH。
用法: blender -b --python sword.py -- --outdir <dir>
"""
import bpy, sys, os
from mathutils import Vector

LENGTH = 1.1
WIDTH = 0.10
BLADE = (0.72, 0.74, 0.78, 1)
GUARD = (0.55, 0.42, 0.18, 1)
HANDLE = (0.22, 0.14, 0.08, 1)

outdir = os.environ.get('DSH_BLENDER_OUTDIR', os.getcwd())
argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
if '--outdir' in argv:
    outdir = argv[argv.index('--outdir') + 1]
os.makedirs(outdir, exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)


def mat(name, color, rough=0.6):
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = color
    b.inputs['Roughness'].default_value = rough
    return m


blade = mat('blade', BLADE, 0.35)
guard_m = mat('guard', GUARD, 0.5)
handle_m = mat('handle', HANDLE, 0.8)

bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, LENGTH * 0.42 + 0.12))
o = bpy.context.object
o.scale = (WIDTH * 0.5, 0.03, LENGTH * 0.82)
bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
o.data.materials.append(blade)

bpy.ops.mesh.primitive_cone_add(vertices=4, radius1=WIDTH * 0.5, radius2=0, depth=0.22,
                                location=(0, 0, LENGTH * 0.93 + 0.12))
bpy.context.object.data.materials.append(blade)

bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 0.12))
o = bpy.context.object
o.scale = (0.30, 0.06, 0.07)
bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
o.data.materials.append(guard_m)

bpy.ops.mesh.primitive_cylinder_add(vertices=8, radius=0.035, depth=0.26, location=(0, 0, -0.02))
bpy.context.object.data.materials.append(handle_m)

bpy.ops.mesh.primitive_uv_sphere_add(radius=0.05, location=(0, 0, -0.16))
bpy.context.object.data.materials.append(guard_m)

bpy.ops.mesh.primitive_plane_add(size=6, location=(0, 0, -0.21))
bpy.context.object.data.materials.append(mat('floor', (0.13, 0.13, 0.15, 1), 0.92))

for loc, energy, size in [((2.6, -3.0, 3.2), 150, 2.5), ((-2.8, -1.4, 2.2), 75, 3.0), ((1.0, 3.2, 2.6), 95, 2.0)]:
    bpy.ops.object.light_add(type='AREA', location=loc)
    bpy.context.object.data.energy = energy
    bpy.context.object.data.size = size

bpy.ops.object.camera_add(location=(1.9, -2.6, 1.3))
cam = bpy.context.object
target = Vector((0, 0, 0.5))
cam.rotation_euler = (target - cam.location).to_track_quat('-Z', 'Y').to_euler()
cam.data.lens = 55
bpy.context.scene.camera = cam

sc = bpy.context.scene
sc.render.engine = 'BLENDER_EEVEE'
sc.view_settings.view_transform = 'Standard'
sc.render.resolution_x = 512
sc.render.resolution_y = 512
sc.render.filepath = os.path.join(outdir, 'sword.png')
bpy.ops.render.render(write_still=True)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(outdir, 'sword.blend'))
bpy.ops.export_scene.gltf(filepath=os.path.join(outdir, 'sword.glb'), export_format='GLB')
print('DONE', outdir)
