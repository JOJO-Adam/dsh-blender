---
name: blender-asset-pipeline
description: "Agent 驱动的程序化资产管线：先设计再动手，AI 写参数化 bpy 脚本 + 自检 + glTF 导出，人负责美术方向。覆盖三硬限制、Bevel 圆角、CC0 拉取、LOD 导出与连续网格反模式。"
whenToUse: "Blender 资产管线 / 程序化生成 / 游戏资产 / glTF / LOD / 批量 时"
license: MIT
---


# Blender 资产管线 · 设计优先的协作建模

> DSH 执行层（headless 跑 Blender、渲染、导出）：见 `blender-studio` 技能。


**先设计，再动手；代码即资产表征，用户定美术方向。**

本技能把「Agent 用 Blender 建模」的圈内先进经验固化为可复用流程。核心思想来自 LL3M（arXiv 2508，把 3D 生成重定义为写可解释 bpy 代码）、AAA Blender Modeling Playbook（参数化优先 + 精修循环）、StraySpark（数百小时实战的三条硬限制）。**本版已通用化**：剥离了原 Seele 小岛项目的 6×6 演示夹具、TYPE_MAP/HEIGHT_MAP 硬编码、Godot 侧上色段落与项目红线，仅保留可复用的技法与纪律。

## 适用场景

- 为游戏 / AR 批量生成 low-poly / 圆润风格 3D 模块：地形 tile、props（树/灌丛/礁石/小屋）、角色占位。
- 已接 Blender MCP（mcp-for-blender），想用 agent 脚本化批量建模，而非手动点菜单。
- 要把程序化方块占位升级为圆润 low-poly 视觉（逃离 Minecraft 感）。
- 需要「参考图 → Spec → 参数化生成 → 截图检视 → 导出 → 引擎实测」的闭环。

## 核心原则：先设计，再动手

绝不在没有 brief/spec 的情况下动网格。每个资产走：

```
简报&参考 → Spec 表(锚定数值) → 参数化构建 → 截图检视 → 导出 → 引擎实测 → 修订
```

- **Reference-grounded**：动手前定 1–3 张参考图（动森/朋友生活/GoGoTown 截图，或 Poly Pizza CC0 模型，或用户给的方向）。无参考不建模。
- **Spec 表锚定数值**：尺寸（如 1×1 grid 单位）、三角预算（tile ≤ 200、树 ≤ 1500）、配色、pivot。数值写死 → agent 行为确定、可复现。
- **参数化 > 生成式 > 基元**：优先用参数化库/脚本；外部 AI 生成（`generate_3d` / Hunyuan3D）次之；纯基元 blockout 仅做占位。

## 三条硬限制（必守，来自 StraySpark）

1. **创意拓扑不是 agent 的活**：LLM 出不了生产级拓扑。agent 只出 blockout / 占位 / low-poly 代理；圆润比例、轮廓、配色由用户定。手动重拓扑/UV/绑定/动画必须人审。
2. **重操作会超时**：细分(Subsurf)、重拓扑、纹理烘焙可能超过 MCP 工具超时（通常 60–120s）。大任务拆小步；或手动跑长任务。
3. **agent 视觉反馈有限**：靠 `look` 渲图 / `get_scene_info` 拓扑事实，而非自己"看到"渲染。最终裁判是**用户眼睛 + 游戏引擎实跑**，不是 agent 自认。

## 标准闭环（Phase A–E）

| 阶段 | 做什么 | 谁 | 出口 |
|---|---|---|---|
| A 简报+参考 | 定 1–3 张参考图 + 写 Spec 表（尺寸/三角预算/配色/pivot） | 用户给方向 | Spec 表 |
| B 参数化构建 | bpy + Bevel 生成 low-poly，或 `generate_3d` 拉云端模型进来精修 | agent | .blend |
| C 截图检视 | `look` 渲 turntable/接触表，对照 Spec 自检 3 个最高影响问题 | agent | 截图+缺陷清单 |
| D 导出 | glb → 资产目录，apply transform + 可选 Decimate LOD | agent | .glb（几何-only） |
| E 引擎实测 | 引擎内替换占位、跑场景看比例/锚点/视觉 | 用户+agent | 修订项 |

> ⚠️ 工具名对齐 mcp-for-blender：阶段 C 用 `look`（非旧版 `get_viewport_screenshot`）；阶段 B 云端造模用 `generate_3d`（非旧版 `generate_hyper3d_model`）；CC0 直拉用 `search_assets`（非旧版 `get_polyhaven_assets`）。

## 关键技术（逃离 Minecraft 方块感）

- **Bevel 倒角修改器**给 tile/道具圆角 → 立刻脱离立方体棱角（圆润 low-poly 关键一招）。
- **BMesh `from_pydata`** 从顶点/面数据建网格；`bmesh.ops` 做 extrude/subdivide/translate。改完 `bm.to_mesh()` + `bm.free()`。
- **修改器栈**（脚本化）：Bevel(圆角) / Solidify(厚度) / Subdivision(平滑，省用) / Array(阵列) / Mirror(对称)。
- **fBm/Perlin 噪声**（`mathutils/noise` 或 `noise` 库）做地形起伏；**L-system 思路**做树。
- **glTF 2.0 二进制导出** `bpy.ops.export_scene.gltf(...)`；**Decimate** 生成 LOD 层级（LOD1=50%、LOD2=75%、LOD3=90% 缩减）。
- **Flat shading** 切换可出风格化块面（是「风格化」不是「像素化」）。

## 缝消除 & Blender 5.x 踩坑（实战沉淀 · 高复用）

### 地面/地形必须「合并连续网格」，不能用「一堆独立方块各自做顶点色」
- **反模式（踩过）**：每个格子一个独立 cube mesh，各自 `bevel` + 各自顶点色向邻居渐变。两根打脸：① 每格独立 mesh → 倒角后每格成独立圆枕，枕间露沟槽 → **网格缝更明显**；② 草块贴沙边染向沙、沙块贴草边染向草，两边同染 → 1 格宽沙环被草色吃掉、水边糊成 muddy 窄带。
- **正确架构（对标动森/朋友生活/GoGoTown）**：地面 = **一整张连续网格（heightfield）**，不是一堆独立方块。
  - 平地区域是一张连续平面 → **根本没有网格缝**。
  - 顶点色 splat 混合**只在边界带**做、块中心保持纯色（每格 SUB×SUB 子顶点，中心顶点纯色）→ 沙不被吃、水边干净。
  - 高度差处才生**崖壁/岸壁**（earth 材质，double-sided 免法线朝向烦恼）。
  - 倒角只对**整张合并 mesh** 做且**限角** → 只磨圆崖壁/外缘，平顶 0° 绝不倒角 → 平顶无缝、圆润感留在该在处。
- 同高邻居**共享顶点**（字典 key 复用）→ 顶面对接无缝；只有临不同地形类型（非水）的邻居才 smoothstep 边界带渐变。水作为独立平面，陆地颜色**绝不向水晕染**。

### Blender 5.x 三个必记坑
1. **Bevel 用 `obj.modifiers.new(name="Bevel", type='BEVEL')` 拿回引用**，不用 `bpy.ops.object.modifier_add(type='BEVEL')` 后按名 `obj.modifiers["Bevel"]` 取（5.x 报 `key "Bevel" not found`）。
2. **Bevel 必须 `limit_method='ANGLE'` + `angle_limit`（如 40°）**：默认 `NONE` 会**把所有边（含平顶内部网格线）全倒角** → 平顶重引缝。限角后只磨圆崖壁/外缘（90°），平顶 0° 不动。
3. **5.x 材质/导出**：① 新材质 `node_tree.nodes.clear()` 后显建 Output+BSDF（无自动命名）；② `ColorRamp` element `.color` 需 RGBA 四元组；③ 5.x Principled BSDF **无 `Transmission`** 输入 → 透明水面只调 `blend_method='BLEND'` + Alpha；④ `export_scene.gltf` **无 `export_colors` 参数**（5.x 已移除）→ 直接 `export_format='GLB', export_materials='EXPORT'`。
4. **顶点色连续网格优于逐立方体**：连续网格上 splat 顶点色才能跨边界无缝衔接；逐立方体各自顶点色无法跨 mesh 衔接（同反模式①）。
5. `look`/`get_viewport_screenshot` 在部分环境回传被过滤（"model does not support images"）→ **AI 无法自检视觉**，靠客观 DIAG/PROOF（面法线分布、坐标、渐变顶点数）佐证 + 用户眼睛终审。
6. **`transform_apply(location=True)` 会把 `obj.location` 重置为 0**（位置已烘进顶点数据）。凡在 apply 之后用 `obj.location.x/y` 判定方向（如"哪条竖直棱属于哪一侧"）都会退化：坐标全相对 0 → 符号全为负 → **整块所有竖直棱被误选**。**修复**：方向判定改用网格顶点真实包围盒中心 `ocx=0.5*(min+max x)`, `ocy=0.5*(min+max y)`。强烈建议：倒角/方向相关逻辑一律用顶点包围盒中心，不碰 `obj.location`。

### 选择性倒角实现（实测坑）
- `MeshEdge.bevel_weight` 属性在 5.x **已移除**；改成网格属性 `bevel_weight_edge`，但 Bevel 修改器 `limit_method='WEIGHT'` 实测 `slant=0` 未生效（flaky）。
- **最稳做法**：用 `bmesh.ops.bevel(bm, geom=[选中的竖直棱], affect='EDGES', offset=BEVEL_W, segments=2, profile=0.5, clamp_overlap=True)` 直接对选中棱倒角 → 版本无关、确定性强。倒角后 `bm.to_mesh(mesh)` 回写，按法线重排材质，顶点色在倒角后上色（含新增顶点防黑边）。
- 判竖直棱：两顶点 `abs(x1-x2)<eps and abs(y1-y2)<eps`（忽略 z 差）→ 竖直；其 `xs=sign(x-中心x)`、`ys=sign(y-中心y)` 决定属于哪侧。

### 导出坑（已修）
- **Blender 5.2 glTF 色导出 bug**：顶点色→白色 `COLOR_0`(ubyte)+畸形 `COLOR_1`(ushort)；纯色材质→无 `pbrMetallicRoughness`。**对策：GLB 只出几何，颜色全在下游引擎（Godot/Maya/Unity）侧套** `StandardMaterial3D` / PBR。不要在 Blender 侧烤色。
- bmesh 跨会话 bevel 报 `BMEdge has been removed` → 选中+bevel+to_mesh+free 必须在**单 bmesh 会话内**完成。
- 过渡名无拓扑后缀互相覆盖 → 加 `_inland/_side/_corner` 后缀区分。

## 连接与工具（mcp-for-blender）

- MCP 配置：`~/.workbuddy/mcp.json` 的 `blender` 节点（`command: uvx blender-mcp`, `BLENDER_PORT=9876`）。
- 插件：`~/Library/Application Support/Blender/5.2/scripts/addons/blender_mcp_addon.py`（Blender 内 Edit→Preferences→Add-ons 启用 "Blender MCP"，N 面板 BlenderMCP → Start MCP Server）。
- **可复用 helper**：`/Users/jojo/AI_Projects/Seele/tools/blender_mcp_exec.py` — 读 .py 脚本或 stdin，经 `uvx blender-mcp` 桥在 Blender 内执行并返回输出：`python3 blender_mcp_exec.py script.py`（需 Blender 已开 + 插件服务端已启动）。
- 视觉自检：`look`（rendered 通道，返回场景渲图）替代旧 `get_viewport_screenshot`。

## CC0 素材直拉（mcp-for-blender 内集成）

- **Poly Pizza**：~10,600 免费 low-poly CC0 模型，适合风格化游戏；让 agent 搜索+过滤+直接导入。
- **Poly Haven**：HDRI 环境光照 + PBR 纹理；适合离开 Blender 配光照/材质。
- **Hunyuan3D / Tripo**（经 `generate_3d`，需 API key）：文本/图像生成带贴图 3D 模型，用于素材库没有的独有道具，再进 Blender 精修。
- 策略：AI 生成与 CC0 拉取混合——先拉 CC0 基线对齐视觉语言，再参数化自研专属模块。CC-BY 须署名登记来源（资产红线见 `blender-sop` §3）。

## 迭代完善纪律

本技能 v1.0.0 为通用化初版，使用中逐步修订：
- 每次建模发现的新技法/坑/好用的 Spec 模板 → 回写本 SKILL.md。
- 新资产类别（树/屋/角色）沉淀为可复用 bpy 函数片段，附在本技能或独立参考文件。
- 用户美术方向偏好（配色、轮廓、圆角强度）→ 记入 Spec 表默认模板。
- 不擅自推翻 `blender-sop` 级红线；涉及决策变更先与主理人（艾芙琳）对齐。
