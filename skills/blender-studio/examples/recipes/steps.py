"""低模台阶（参数化）：STEPS 级石阶 + 后侧挡墙，踏步带微出檐。
用法: blender -b --python steps.py -- --outdir <dir>
"""
import bpy, sys, os
from mathutils import Vector

STEPS = 5
WIDTH = 1.5
RISER = 0.22
TREAD = 0.34
NOSING = 0.03
COLOR = (0.52, 0.50, 0.47, 1)
SIDE = (0.44, 0.42, 0.40, 1)

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
side = mat('side', SIDE)


def box(size, loc, material):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    o = bpy.context.object
    o.scale = size
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    o.data.materials.append(material)


for i in range(STEPS):
    h = RISER * (i + 1)
    x = TREAD * i + TREAD / 2
    box((TREAD, WIDTH, h), (x, 0, h / 2), stone)
    # 踏步前缘出檐
    box((NOSING, WIDTH, 0.04), (x - TREAD / 2 - NOSING / 2, 0, h - 0.02), side)

# 后侧挡墙（只到顶步高度）
total_h = RISER * STEPS
box((TREAD * 0.6, WIDTH, total_h), (TREAD * STEPS + TREAD * 0.3, 0, total_h / 2), side)

bpy.ops.mesh.primitive_plane_add(size=10, location=(0, 0, 0))
bpy.context.object.data.materials.append(mat('floor', (0.15, 0.15, 0.16, 1), 0.92))

for loc, energy, size in [((3.0, -3.2, 3.4), 170, 2.2), ((-3.0, -1.6, 2.4), 85, 3.0), ((1.2, 3.2, 2.6), 105, 2.0)]:
    bpy.ops.object.light_add(type='AREA', location=loc)
    bpy.context.object.data.energy = energy
    bpy.context.object.data.size = size

bpy.ops.object.camera_add(location=(2.9, -3.3, 1.9))
cam = bpy.context.object
target = Vector((0.75, 0, 0.5))
cam.rotation_euler = (target - cam.location).to_track_quat('-Z', 'Y').to_euler()
cam.data.lens = 48
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
