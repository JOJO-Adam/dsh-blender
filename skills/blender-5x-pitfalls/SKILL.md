---
name: blender-5x-pitfalls
description: "Blender 5.x 踩坑清单（锚定 5.2 LTS）：Bevel 引用与限角陷阱、bevel_weight 移除、材质节点创建、Principled 无 Transmission、glTF 丢色 bug、transform_apply 方向陷阱。"
whenToUse: "Blender 5.x / 版本升级 / Bevel / 材质 / glTF 导出 / transform_apply 时"
license: MIT
---


# Blender 5.x 踩坑清单（blender-5x-pitfalls）

> DSH 执行层（headless 跑 Blender、渲染、导出）：见 `blender-studio` 技能。


**锚定 5.2 LTS。** 本环境已踩过的真实 bug，建脚本前先查，避免重蹈。详见 `blender-sop` / `blender-asset-pipeline` / `blender-modeling-cookbook`。

## 🔴 致命级（必踩无疑，先读）

1. **Bevel 引用**：用 `obj.modifiers.new(name="Bevel", type='BEVEL')` 拿引用，不用 `bpy.ops.object.modifier_add(type='BEVEL')` 后按名 `obj.modifiers["Bevel"]` 取 —— 5.x 报 `key "Bevel" not found`。
2. **Bevel 必须限角**：`limit_method='ANGLE'` + `angle_limit`（如 40°）。默认 `NONE` 会把**所有边（含平顶内部网格线）全倒角** → 平顶重引缝。限角后只磨圆崖壁/外缘（90°），平顶 0° 不动。
3. **glTF 色导出 bug（5.2）**：顶点色→白色 `COLOR_0`(ubyte)+畸形 `COLOR_1`(ushort)；纯色材质→无 `pbrMetallicRoughness`。**对策：GLB 只出几何，颜色全在下游引擎侧套。** `export_scene.gltf` **无 `export_colors` 参数**（5.x 已移除）→ 用 `export_format='GLB', export_materials='EXPORT'`。
4. **`transform_apply(location=True)` 把 `obj.location` 归零**：apply 之后用 `obj.location.x/y` 判方向会符号全翻 → 整块所有竖直棱被误选。**改用顶点包围盒中心** `0.5*(min+max)` 判方向。

## 🟠 高频级

5. **`MeshEdge.bevel_weight` 已移除**（5.x）：改成网格属性 `bevel_weight_edge`，但 Bevel `limit_method='WEIGHT'` 实测 flaky。最稳 = `bmesh.ops.bevel(geom=[选中棱], affect='EDGES', ...)` 直接倒角，版本无关。
6. **新材质无自动命名**：`node_tree.nodes.clear()` 后显建 Output + BSDF。
7. **`ColorRamp` element `.color` 需 RGBA 四元组**（4 个分量）。
8. **5.x Principled BSDF 无 `Transmission` 输入**：透明水面只调 `blend_method='BLEND'` + Alpha，别找 Transmission 插槽。
9. **Eevee 已重写（EEVEE-Next）**：不假设 4.x 旧 Eevee 行为；灯光/材质节点差异。
10. **`look` 回传被过滤**：部分环境 "model does not support images" → agent 无法视觉自检，靠客观 DIAG/PROOF（法线分布/坐标/渐变顶点数）+ 用户眼睛终审。

## 🟡 架构级（反模式）

11. **逐立方体各自顶点色 = 缝 + 色糊**：地面/地形必须用一整张连续 heightfield，顶点色 splat 只在边界带、块中心纯色。
12. **bmesh 跨会话 bevel 报 `BMEdge has been removed`**：选中+bevel+to_mesh+free 必须在**单 bmesh 会话内**完成。
13. **过渡名无拓扑后缀互相覆盖**：加 `_inland/_side/_corner` 区分。

## 关联

- 版本/渲染器/导出纪律总纲 → `blender-sop` §1/§2/§4。
- 连续网格 + Bevel 算法 + 选择性倒角 → `blender-asset-pipeline` / `blender-modeling-cookbook` §3–§5。
- 工具名对齐（mcp-for-blender vs 旧 blender-mcp）→ `blender-mcp-bridge`。
