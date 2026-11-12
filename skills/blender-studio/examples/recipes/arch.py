"""低模石拱门（参数化）：柱础 + 立柱 + 柱头 + 半圆券（真梯形楔石）+ 拱心石。
楔石用内外弧边顶点直接建网格，相邻块共享径向边，无缝隙。
用法: blender -b --python arch.py -- --outdir <dir>
"""
import bpy, sys, os, math, bmesh
from mathutils import Vector

RI = 0.60        # 券内半径
RO = 0.86        # 券外半径
H = 1.10         # 起拱高度（柱高）
BLOCKS = 7       # 券上楔石数（奇数）
DEPTH = 0.36     # 进深
STONE = (0.55, 0.52, 0.47, 1)
STONE2 = (0.46, 0.43, 0.39, 1)
TONE = (0.36, 0.34, 0.31, 1)

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


stone = mat('stone', STONE)
stone2 = mat('stone2', STONE2)
tone = mat('tone', TONE)


def box(size, loc, material, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc, rotation=rot)
    o = bpy.context.object
    o.scale = size
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    o.data.materials.append(material)
    return o


def voussoir(t0, t1, ri, ro, depth, material, loc_z=0.0):
    """一块梯形楔石：内外弧边 + 进深方向挤出，面法线统一。"""
    d = depth / 2
    def ring(y):
        return [(ri * math.cos(t0), y, ri * math.sin(t0)),
                (ro * math.cos(t0), y, ro * math.sin(t0)),
                (ro * math.cos(t1), y, ro * math.sin(t1)),
                (ri * math.cos(t1), y, ri * math.sin(t1))]
    verts = ring(-d) + ring(d)
    faces = [(0, 1, 2, 3), (7, 6, 5, 4),
             (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)]
    mesh = bpy.data.meshes.new('voussoir')
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    bm = bmesh.new(); bm.from_mesh(mesh)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(mesh); bm.free()
    obj = bpy.data.objects.new('voussoir', mesh)
    bpy.context.collection.objects.link(obj)
    obj.location = (0, 0, loc_z)
    obj.data.materials.append(material)
    return obj


Rm = (RI + RO) / 2
# 立柱 + 柱础 + 柱头
for sign in (-1, 1):
    x = sign * Rm
    box((0.30, DEPTH, H), (x, 0, H / 2), stone)
    box((0.46, DEPTH + 0.10, 0.10), (x, 0, 0.05), tone)
    box((0.38, DEPTH + 0.06, 0.10), (x, 0, H - 0.05), stone2)

# 半圆券：BLOCKS 块梯形楔石，首尾正好落在柱顶
delta = math.pi / BLOCKS
for i in range(BLOCKS):
    t0 = delta * i
    t1 = delta * (i + 1)
    m = stone if i % 2 == 0 else stone2
    if i == BLOCKS // 2:
        # 拱心石：往外凸一点
        voussoir(t0, t1, RI - 0.02, RO + 0.08, DEPTH + 0.06, stone2, loc_z=H)
    else:
        voussoir(t0, t1, RI, RO, DEPTH, m, loc_z=H)

bpy.ops.mesh.primitive_plane_add(size=10, location=(0, 0, 0))
bpy.context.object.data.materials.append(mat('floor', (0.16, 0.16, 0.17, 1), 0.92))

for loc, energy, size in [((3.2, -3.8, 3.8), 180, 2.5), ((-3.4, -2.0, 2.8), 90, 3.0), ((1.2, 3.6, 3.0), 115, 2.0)]:
    bpy.ops.object.light_add(type='AREA', location=loc)
    bpy.context.object.data.energy = energy
    bpy.context.object.data.size = size

bpy.ops.object.camera_add(location=(2.7, -4.4, 2.2))
cam = bpy.context.object
target = Vector((0, 0, 1.15))
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
