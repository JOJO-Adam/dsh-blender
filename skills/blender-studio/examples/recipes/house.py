"""低模小屋（参数化）：屋身 + 双坡屋顶 + 门窗 + 烟囱。
用法: blender -b --python house.py -- --outdir <dir>
"""
import bpy, sys, os, math
from mathutils import Vector

W, D, H = 1.9, 1.5, 1.2     # 屋身宽/深/高
ROOF_H = 0.62               # 屋顶高
OVERHANG = 0.14             # 屋檐外伸
WALL = (0.62, 0.58, 0.52, 1)
ROOF = (0.38, 0.16, 0.10, 1)
TRIM = (0.28, 0.20, 0.14, 1)
DOOR = (0.24, 0.14, 0.08, 1)
GLASS = (0.80, 0.86, 0.90, 1)

outdir = os.environ.get('DSH_BLENDER_OUTDIR', os.getcwd())
argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
if '--outdir' in argv:
    outdir = argv[argv.index('--outdir') + 1]
os.makedirs(outdir, exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)


def mat(name, color, rough=0.85, emit=None, strength=0.0):
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = color
    b.inputs['Roughness'].default_value = rough
    if emit is not None and 'Emission Color' in b.inputs:
        b.inputs['Emission Color'].default_value = emit
        b.inputs['Emission Strength'].default_value = strength
    return m


wall = mat('wall', WALL)
roof = mat('roof', ROOF, 0.75)
trim = mat('trim', TRIM, 0.8)
door = mat('door', DOOR, 0.85)
glass = mat('glass', GLASS, 0.25, emit=GLASS, strength=1.6)


def box(size, loc, material, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc, rotation=rot)
    o = bpy.context.object
    o.scale = size
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    o.data.materials.append(material)
    return o


# 地基
box((W + 0.12, D + 0.12, 0.14), (0, 0, 0.07), trim)
# 屋身
box((W, D, H), (0, 0, 0.14 + H / 2), wall)
# 屋顶：实心三角棱柱（带出檐）
sw = W / 2 + OVERHANG
sd = D / 2 + OVERHANG
mesh = bpy.data.meshes.new('roof')
verts = [(-sw, -sd, 0), (sw, -sd, 0), (0, -sd, ROOF_H),
         (-sw, sd, 0), (sw, sd, 0), (0, sd, ROOF_H)]
faces = [(0, 1, 2), (3, 5, 4), (0, 3, 4, 1), (1, 4, 5, 2), (2, 5, 3, 0)]
mesh.from_pydata(verts, [], faces)
mesh.update()
roof_obj = bpy.data.objects.new('roof', mesh)
bpy.context.collection.objects.link(roof_obj)
roof_obj.location = (0, 0, 0.14 + H)
roof_obj.data.materials.append(roof)
# 屋脊压条
box((0.10, 2 * sd + 0.02, 0.06), (0, 0, 0.14 + H + ROOF_H - 0.015), trim)

z0 = 0.14
fy = -D / 2 - 0.012
# 门框 + 门
box((0.52, 0.05, 0.80), (0, fy, z0 + 0.40), trim)
box((0.42, 0.05, 0.71), (0, fy - 0.012, z0 + 0.355), door)
# 两扇窗（框 + 发光玻璃）
for x in (-0.60, 0.60):
    box((0.44, 0.05, 0.42), (x, fy, z0 + 0.78), trim)
    box((0.34, 0.05, 0.32), (x, fy - 0.012, z0 + 0.78), glass)
# 侧窗
sx = W / 2 + 0.012
box((0.05, 0.34, 0.36), (sx, 0.10, z0 + 0.80), trim)
box((0.05, 0.26, 0.28), (sx + 0.012, 0.10, z0 + 0.80), glass)
# 烟囱
box((0.20, 0.20, 0.72), (0.62, 0.34, z0 + H + 0.40), trim)
box((0.26, 0.26, 0.07), (0.62, 0.34, z0 + H + 0.78), roof)

bpy.ops.mesh.primitive_plane_add(size=10, location=(0, 0, 0))
bpy.context.object.data.materials.append(mat('floor', (0.16, 0.16, 0.17, 1), 0.92))

for loc, energy, size in [((3.2, -3.6, 3.6), 180, 2.5), ((-3.2, -1.8, 2.6), 90, 3.0), ((1.2, 3.4, 2.8), 120, 2.0)]:
    bpy.ops.object.light_add(type='AREA', location=loc)
    bpy.context.object.data.energy = energy
    bpy.context.object.data.size = size

bpy.ops.object.camera_add(location=(3.1, -4.3, 2.5))
cam = bpy.context.object
target = Vector((0, 0, 0.95))
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
