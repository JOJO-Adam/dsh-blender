"""低模木桶（参数化）：旋转体桶身（平滑外鼓）+ 两道细箍 + 桶盖。
用法: blender -b --python barrel.py -- --outdir <dir>
"""
import bpy, sys, os, math, bmesh
from mathutils import Vector

RADIUS = 0.34
HEIGHT = 0.92
BULGE = 0.10       # 外鼓比例（0.10 = 中部外扩 10%）
SEGS = 16
HOOPS = 2
COLOR = (0.36, 0.20, 0.09, 1)
LID = (0.30, 0.17, 0.08, 1)
METAL = (0.15, 0.16, 0.18, 1)

outdir = os.environ.get('DSH_BLENDER_OUTDIR', os.getcwd())
argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
if '--outdir' in argv:
    outdir = argv[argv.index('--outdir') + 1]
os.makedirs(outdir, exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)


def mat(name, color, rough=0.75, metal=0.0):
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = color
    b.inputs['Roughness'].default_value = rough
    if 'Metallic' in b.inputs:
        b.inputs['Metallic'].default_value = metal
    return m


wood = mat('wood', COLOR, 0.8)
lid = mat('lid', LID, 0.85)
metal = mat('metal', METAL, 0.35, 0.8)


def add_mesh(name, verts, faces, material):
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(verts, [], faces); mesh.update()
    bm = bmesh.new(); bm.from_mesh(mesh)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(mesh); bm.free()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(material)
    return obj


def barrel_radius(z):
    t = z / HEIGHT
    return RADIUS * (0.95 + BULGE * math.sin(math.pi * t))


# 桶身：多环旋转体
rings = [0.0, 0.05, 0.14, 0.28, 0.42, 0.50, 0.58, 0.72, 0.86, 0.92]
verts, faces = [], []
for z in rings:
    r = barrel_radius(z)
    for i in range(SEGS):
        a = 2 * math.pi * i / SEGS
        verts.append((r * math.cos(a), r * math.sin(a), z))
for k in range(len(rings) - 1):
    for i in range(SEGS):
        a = k * SEGS + i
        b = k * SEGS + (i + 1) % SEGS
        c = (k + 1) * SEGS + (i + 1) % SEGS
        d = (k + 1) * SEGS + i
        faces.append((a, b, c, d))
# 底面封口
faces.append(tuple(range(SEGS - 1, -1, -1)))
add_mesh('barrel_body', verts, faces, wood)

# 桶盖（略内凹，用薄圆柱近似）
bpy.ops.mesh.primitive_cylinder_add(vertices=SEGS, radius=RADIUS * 0.97, depth=0.04, location=(0, 0, HEIGHT - 0.015))
bpy.context.object.data.materials.append(lid)

# 细铁箍
for i in range(HOOPS):
    zc = HEIGHT * (0.20 + 0.58 * i)
    bpy.ops.mesh.primitive_cylinder_add(vertices=SEGS, radius=barrel_radius(zc) + 0.008, depth=0.035,
                                        location=(0, 0, zc))
    bpy.context.object.data.materials.append(metal)

bpy.ops.mesh.primitive_plane_add(size=8, location=(0, 0, 0))
bpy.context.object.data.materials.append(mat('floor', (0.15, 0.15, 0.16, 1), 0.92))

for loc, energy, size in [((2.6, -3.0, 3.0), 150, 2.2), ((-2.8, -1.6, 2.2), 70, 3.0), ((0.8, 3.0, 2.4), 90, 2.0)]:
    bpy.ops.object.light_add(type='AREA', location=loc)
    bpy.context.object.data.energy = energy
    bpy.context.object.data.size = size

bpy.ops.object.camera_add(location=(1.7, -2.5, 1.45))
cam = bpy.context.object
target = Vector((0, 0, 0.46))
cam.rotation_euler = (target - cam.location).to_track_quat('-Z', 'Y').to_euler()
cam.data.lens = 55
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
