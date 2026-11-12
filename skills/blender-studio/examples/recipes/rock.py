"""低模石头（参数化）：随机顶点位移的二十面体。调 RADIUS / DISPLACE / SEED。
用法: blender -b --python rock.py -- --outdir <dir>
"""
import bpy, sys, os, random
from mathutils import Vector

RADIUS = 0.55
DISPLACE = 0.26
SEED = 11
COLOR = (0.42, 0.42, 0.44, 1)

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

bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=RADIUS, location=(0, 0, RADIUS * 0.72))
rock = bpy.context.object
random.seed(SEED)
for v in rock.data.vertices:
    v.co += v.normal * random.uniform(-DISPLACE, DISPLACE)
rock.data.update()
rock.data.materials.append(stone)

bpy.ops.mesh.primitive_plane_add(size=8, location=(0, 0, 0))
bpy.context.object.data.materials.append(mat('floor', (0.15, 0.15, 0.16, 1), 0.92))

for loc, energy, size in [((2.8, -3.2, 3.2), 150, 2.5), ((-3.0, -1.6, 2.4), 75, 3.0), ((1.0, 3.2, 2.6), 95, 2.0)]:
    bpy.ops.object.light_add(type='AREA', location=loc)
    bpy.context.object.data.energy = energy
    bpy.context.object.data.size = size

bpy.ops.object.camera_add(location=(2.2, -3.2, 1.9))
cam = bpy.context.object
target = Vector((0, 0, 0.45))
cam.rotation_euler = (target - cam.location).to_track_quat('-Z', 'Y').to_euler()
cam.data.lens = 52
bpy.context.scene.camera = cam

sc = bpy.context.scene
sc.render.engine = 'BLENDER_EEVEE'
sc.view_settings.view_transform = 'Standard'
sc.render.resolution_x = 512
sc.render.resolution_y = 512
sc.render.filepath = os.path.join(outdir, 'rock.png')
bpy.ops.render.render(write_still=True)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(outdir, 'rock.blend'))
bpy.ops.export_scene.gltf(filepath=os.path.join(outdir, 'rock.glb'), export_format='GLB')
print('DONE', outdir)
