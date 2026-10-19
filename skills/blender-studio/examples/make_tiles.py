"""
示例：参数化 low-poly 地砖 + 选择性 Bevel + 渲染 + glTF 导出。

在 DSH 里跑：
  python3 skills/blender-studio/scripts/blender_client.py run \
    --script skills/blender-studio/examples/make_tiles.py \
    --outdir outputs/blender/tiles

输出（默认 <outdir>）：
  scene.blend   可继续编辑的场景
  tiles.png     512×512 EEVEE 渲染
  tiles.glb     glTF 导出（游戏资产）
"""
import os
import math

import bpy
from mathutils import Vector

OUTDIR = os.environ.get("DSH_BLENDER_OUTDIR", "outputs/blender/tiles")
os.makedirs(OUTDIR, exist_ok=True)

# 1. 空场景
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene

# 2. 参数：3×3 地砖，间隙与厚度
GRID = 3
SIZE = 1.6
GAP = 0.08
HEIGHT = 0.18
BEVEL = 0.045

mat = bpy.data.materials.new("Tile")
mat.use_nodes = True
bsdf = mat.node_tree.nodes.get("Principled BSDF")
bsdf.inputs["Base Color"].default_value = (0.62, 0.66, 0.72, 1.0)
bsdf.inputs["Roughness"].default_value = 0.55

for ix in range(GRID):
    for iy in range(GRID):
        bpy.ops.mesh.primitive_cube_add(size=1)
        obj = bpy.context.active_object
        obj.name = f"tile_{ix}_{iy}"
        obj.scale = (SIZE / 2, SIZE / 2, HEIGHT / 2)
        obj.location = (
            (ix - (GRID - 1) / 2) * (SIZE + GAP),
            (iy - (GRID - 1) / 2) * (SIZE + GAP),
            HEIGHT / 2,
        )
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        obj.data.materials.append(mat)

        bevel = obj.modifiers.new("Bevel", "BEVEL")
        bevel.width = BEVEL
        bevel.segments = 3
        bevel.limit_method = "ANGLE"

# 3. 相机与灯光
bpy.ops.object.camera_add(location=(4.2, -4.8, 4.0))
cam = bpy.context.active_object
cam.rotation_euler = (math.radians(52), 0, math.radians(42))
scene.camera = cam

bpy.ops.object.light_add(type="SUN", location=(3, -2, 6))
sun = bpy.context.active_object
sun.data.energy = 3.2
sun.rotation_euler = (math.radians(35), 0, math.radians(30))

# 4. 世界背景
world = bpy.data.worlds.new("World")
scene.world = world
world.use_nodes = True
world.node_tree.nodes["Background"].inputs[0].default_value = (0.05, 0.06, 0.08, 1.0)

# 5. 渲染设置（EEVEE + 512）
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x = 512
scene.render.resolution_y = 512
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
scene.eevee.taa_render_samples = 32

# 6. 保存工程 + 渲染
blend_path = os.path.join(OUTDIR, "scene.blend")
bpy.ops.wm.save_as_mainfile(filepath=blend_path)

scene.render.filepath = os.path.join(OUTDIR, "tiles.png")
bpy.ops.render.render(write_still=True)

# 7. 导出 glTF（游戏资产）
bpy.ops.export_scene.gltf(
    filepath=os.path.join(OUTDIR, "tiles.glb"),
    export_format="GLB",
    use_selection=False,
)

print("DSH_EXAMPLE_OK", OUTDIR)
