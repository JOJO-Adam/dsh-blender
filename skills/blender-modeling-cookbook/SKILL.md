---
name: blender-modeling-cookbook
description: "Blender 建模技法库：参数化 bpy 构建、BMesh 操作、修改器栈、拓扑规则、UV 展开，以及让 low-poly 资产圆润的选择性 Bevel 配方。"
whenToUse: "Blender 建模 / bpy / BMesh / 修改器 / 拓扑 / UV / Bevel 时"
license: MIT
---


# 建模技法库（blender-modeling-cookbook）

> DSH 执行层（headless 跑 Blender、渲染、导出）：见 `blender-studio` 技能。


**沉淀实战建模技法，供 `blender-modeling` 与全员复用。** 锚定 Blender 5.2 LTS；语法不假设 4.x。

## §1 参数化 bpy 构建范式

- **代码即资产**：优先 bpy 参数化脚本（可版本化、可 diff、可复现）。模板：
  ```python
  import bpy, bmesh, mathutils
  mesh = bpy.data.meshes.new("prop"); obj = bpy.data.objects.new("prop", mesh)
  bpy.context.collection.objects.link(obj)
  bm = bmesh.new(); # ... from_pydata / ops ... ; bm.to_mesh(mesh); bm.free()
  ```
- **LL3M 自批判循环**：生成 → `execute_blender_code` 执行 → `get_scene_info`/`look` 读回 → 修正。结构化操作优先落脚本而非依赖不可控的结构化工具。

## §2 BMesh 操作

- 建网格：`bm.from_mesh(mesh)` 或 `bm.from_pydata(verts, edges, faces)`。
- 常用 ops：`bmesh.ops.create_cube` / `extrude_face_region` / `subdivide_edges` / `translate` / `bevel`（直接对选中几何）。
- 倒角（最稳）：`bmesh.ops.bevel(bm, geom=[选中棱], affect='EDGES', offset=W, segments=2, profile=0.5, clamp_overlap=True)` —— 选中+bevel+to_mesh+free 必须在**单 bmesh 会话内**。
- 判竖直棱：两顶点 `abs(x1-x2)<eps and abs(y1-y2)<eps`；方向用**顶点包围盒中心**（`0.5*(min+max)`），**不碰 `obj.location`**（`transform_apply(location=True)` 会把它归零导致符号全部翻转）。

## §3 修改器栈（脚本化）

| 修改器 | 用途 |
|---|---|
| Bevel | 圆角，逃离方块感（限角 `ANGLE` + `angle_limit`） |
| Solidify | 厚度（墙面/叶片） |
| Subdivision | 平滑（省用，重） |
| Array | 阵列（重复元素） |
| Mirror | 对称（角色/道具） |
| WeightedNormal | 法线平滑（低模关键） |

- 加 Bevel 务必 `obj.modifiers.new(name="Bevel", type='BEVEL')` 拿引用，不用 `bpy.ops.object.modifier_add` 后按名取（5.x `key "Bevel" not found`）。
- Bevel `limit_method='ANGLE'` + `angle_limit`（如 40°）：平顶内部网格线（0°）不倒角，只磨圆崖壁/外缘（90°）。

## §4 拓扑规则

- **连续网格优于逐立方体**：地面/地形用一整张 heightfield，顶点色 splat 只在边界带、块中心纯色 → 无缝、色不糊。逐立方体各自顶点色无法跨 mesh 衔接（缝 + 色糊反模式）。
- **低模代理**：quad 优先、拓扑干净、三角预算写死（tile ≤ 200、树 ≤ 1500）。
- **重拓扑/UV/绑定必须人审**（StraySpark 硬限制 #1）。

## §5 UV 展开

- 智能 UV 投影 / 展 UV（Unwrap）/ 打包（Pack Islands）；命名规范，避免重叠。
- 接缝（seam）沿结构暗线；对称模型用 Mirror 同步 UV。

## §6 LOD 与导出

- Decimate 生成 LOD（LOD1=50% / LOD2=75% / LOD3=90% 缩减）。
- glTF/GLB 只出几何（5.2 丢色），颜色下游引擎套（见 `blender-5x-pitfalls` / `blender-sop` §4）。

## §7 复用资产

- `generate_3d`（tripo/hunyuan3d/hyper3d）云端造模独有道具 → 进 Blender 精修。
- `search_assets` 直拉 Poly Pizza CC0 low-poly 作基线，对齐视觉语言后参数化自研。
- helper：`/Users/jojo/AI_Projects/Seele/tools/blender_mcp_exec.py` 本地执行 bpy 脚本。
