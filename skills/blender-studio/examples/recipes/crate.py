"""低模木箱（参数化）。参数在文件顶部，改完直接跑。
用法: python this_file.py -- --outdir <dir>   (或交给 blender_client.py run)
"""
import bpy, sys, os, math

SIZE = 0.9          # 箱子边长
PLANK_COUNT = 5     # 每面木板数
COLOR = (0.30, 0.17, 0.07, 1)
EDGE_COLOR = (0.35, 0.22, 0.10, 1)

outdir = os.environ.get('DSH_BLENDER_OUTDIR', os.getcwd())
argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
if '--outdir' in argv:
    outdir = argv[argv.index('--outdir') + 1]
os.makedirs(outdir, exist_ok=True)

bpy.ops.wm.read_factory_settings(use_empty=True)


def mat(name, color, rough=0.7):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes['Principled BSDF']
    bsdf.inputs['Base Color'].default_value = color
    bsdf.inputs['Roughness'].default_value = rough
    return m


wood = mat('wood', COLOR)
edge = mat('edge', EDGE_COLOR, 0.6)
h = SIZE / 2
thick = 0.06
gap = 0.012

# 六面围板（每面由若干条木板组成）
for axis in range(3):
    for sign in (-1, 1):
        for i in range(PLANK_COUNT):
            t = -h + (i + 0.5) * (SIZE / PLANK_COUNT)
            w = SIZE / PLANK_COUNT - gap
            if axis == 0:
                loc, dim = (sign * h, t, 0), (thick, w, SIZE)
            elif axis == 1:
                loc, dim = (t, sign * h, 0), (w, thick, SIZE)
            else:
                loc, dim = (t, 0, sign * h), (w, SIZE, thick)
            bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
            o = bpy.context.object
            o.scale = dim
            bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
            o.data.materials.append(wood)

# 四角立柱
for x in (-h, h):
    for y in (-h, h):
        bpy.ops.mesh.primitive_cube_add(size=1, location=(x, y, 0))
        o = bpy.context.object
        o.scale = (thick * 1.2, thick * 1.2, SIZE)
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        o.data.materials.append(edge)

# 地面
bpy.ops.mesh.primitive_plane_add(size=6, location=(0, 0, -h - 0.001))
bpy.context.object.data.materials.append(mat('floor', (0.15, 0.15, 0.16, 1), 0.9))

# 灯光（主光 + 补光 + 轮廓）
for name, loc, energy, size in [
    ('key', (2.4, -2.6, 3.0), 70, 2.5),
    ('fill', (-2.8, -1.2, 2.0), 35, 3.0),
    ('rim', (0.5, 3.0, 2.4), 50, 2.0),
]:
    bpy.ops.object.light_add(type='AREA', location=loc)
    l = bpy.context.object
    l.data.energy = energy
    l.data.size = size

# 相机（斜 45° 俯视）
bpy.ops.object.camera_add(location=(1.9, -2.3, 1.7))
cam = bpy.context.object
cam.rotation_euler = (math.radians(62), 0, math.radians(40))
bpy.context.scene.camera = cam

sc = bpy.context.scene
sc.render.engine = 'BLENDER_EEVEE'
sc.view_settings.view_transform = 'Standard'
sc.render.resolution_x = 512
sc.render.resolution_y = 512
sc.render.filepath = os.path.join(outdir, 'crate.png')
bpy.ops.render.render(write_still=True)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(outdir, 'crate.blend'))
bpy.ops.export_scene.gltf(filepath=os.path.join(outdir, 'crate.glb'), export_format='GLB')
print('DONE', outdir)
