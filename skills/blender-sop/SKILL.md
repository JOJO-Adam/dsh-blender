---
name: blender-sop
description: "Blender 工作室专业标准大脑：5.2 LTS 基线、Cycles/Eevee 抉择、CC0 资产红线、glTF/USD 导出纪律、Agent+MCP 协作三硬限制。一切管线判断的单一真相源。"
whenToUse: "Blender 建模 / 渲染 / 导出 / 排障 / MCP 接线 时"
license: MIT
---

# Blender 专业标准（blender-sop）

> **DSH 适配**：本技能来自专家团 v1.3.6。文中的「主理人」= 你本人，「成员 / 派单」= 你的子任务或子代理，「回执」= 你的交付记录。单 agent 场景下这些纪律同样成立。


**所有管线判断以此为准。** 本技能是 Blender 工作室的"大脑"，版本/渲染器/资产/导出/协作纪律的单一真相源。

## §0 没有 Blender 时的标准交付（先给东西，再要东西）

**没装 Blender、MCP 连不上、或用户只想先看方案时，本团不是"等环境"，而是先把能用的东西交出去。**

按 `templates/` 下四份表填写，**填完即为可交产物，不需要打开 Blender**：

| 模板 | 填什么 | 交付形态 |
|---|---|---|
| `templates/asset_list.md` | 资产清单：资产名 / 类型 / 用途 / 面数预算 / 命名 | md（可交给建模的人直接开工） |
| `templates/model_spec.md` | 建模参数：尺寸（米）/ 三角面上限 / UV 通道 / 材质槽 / LOD | md |
| `templates/naming_export.md` | 命名前缀 + **glTF 导出参数**（+Y up / 单位 / 三角化 / 切线 / 动画）+ 目录结构 | md |
| `templates/delivery_checklist.md` | 交付检查表：命名 / 面数 / UV / 材质 / **导出可回读** / 预览图 | md |

另有两份**工序单**（做 UV / 布光时照单执行，填写同样不需要 Blender）：

| 模板 | 填什么 | 交付形态 |
|---|---|---|
| `templates/uv_unwrap.md` | UV 展开打包工序：标记缝合边 → 展开 → 打包优化；**打包率验收线 0.75** | md（工序单+实测值） |
| `templates/lighting_exposure.md` | 布光/曝光工序：三点布光 → 曝光校准 → 观感自检（复用 C4 成品渲染配方） | md（工序单+实测值） |

**纪律（四条）**：

1. **不许只回「请先安装 Blender」就结束** —— 那是把工作推回给买家，而他要的是方案。
2. **不许编造"已建模 / 已渲染 / 已导出"** —— 没连上就不说做了，但**方案必须交付**。
3. **四份表跨表咬合检查（交付前必跑，可执行步骤）**：以 `asset_list` 为基准表，与 `model_spec` / `naming_export` / `checklist`（含成员并行产出的表）逐资产核对**七项字段**：资产名（逐字）/ 尺寸（米）/ 面数预算（目标+上限）/ UV 通道 / 材质名 / 导出格式 / 交付形态（主件与备件）。机器检查：`python3 scripts/check_table_consistency.py <表A> <表B>`（exit 0 且无输出 = 咬合；有输出 = 矛盾清单，每条带文件行号）；表单自由到机器查不动时，人肉对同七项。**任何一项不一致 = 不许宣称「表已咬合」**，处置只有两种：改到一致，或标「待拍板」挂给老板拍板。没跑过这项检查，禁止使用「基本咬合」「只剩一处遗留」这类状态词。
4. **共同前提卡（并行派单前必锁）**：并行给两个及以上成员派单前，先发**共同前提卡**锁死 **4 个数字：资产名 / 尺寸（米）/ 面数预算（目标+上限）/ 导出格式**，随派单一起下发。成员回报必须逐项回显这 4 个数字；任何成员想偏离其中任一项，必须先请示主理人转老板拍板，**不许自改**。实机测试（2026-11-02）暴露的教训：无此卡时同批表会出现尺寸 0.6/0.8、上限 ≤800/≤400、UV0/UV0+UV1、材质名带不带 `_01`、FBX/GLB 主件各写各的——5 处矛盾全因此而起。

**自检**：`python3 scripts/check_templates.py --selftest`（验四份齐全、表头与示例对齐、顶部声明、SKILL 已引用）。

**装好 Blender + MCP 之后**：这四份表就是施工图 —— 按 `asset_list` 建对象、按 `model_spec` 控参数、
按 `naming_export` 命名与导出、用 `delivery_checklist` 逐项验收。

## §1 版本基线（务必写准版本号）

- **最新稳定**：Blender **5.2 LTS**（2026-09-15 发布，支持到 2028-07）。本机已装 **5.2.1 LTS**（`/Applications/Blender.app`）。
- **次选长期支持**：4.5 LTS（2025-07，支持到 2027-07）。4.2 LTS 已于 2026-07 EOL。
- **结论**：团队默认目标 **5.2 LTS**；兼容下限 4.5 LTS。渲染器 **Cycles（写实）/ Eevee（实时）** 双轨，5.x Eevee 已重写（EEVEE-Next），**不再假设 4.x 旧 Eevee 行为**。
- **红线**：脚本/修改器语法必须锚定 5.x；不假设 4.x。

## §2 渲染器抉择

| 场景 | 选 | 理由 |
|---|---|---|
| 写实 / 离线 / 产品图 | **Cycles** | 路径追踪，物理准确 |
| 实时 / 预览 / 交互 / 风格化 | **Eevee（EEVEE-Next）** | 5.x 重写，快但近似 |
| 动画序列批量出 | Cycles（降采样+降噪）或 Eevee | 看预算 |

⚠️ 不假设 4.x Eevee 行为；5.x 材质/灯光节点有差异。

## §3 资产红线（商用前置）

- 商用前必须 **CC0 或已授权**，禁未授权素材进包。
- `search_assets` 直拉的 **Poly Haven（CC0）/ Poly Pizza（CC0/CC-BY）/ Sketchfab（须看授权）**——CC-BY 须署名，登记来源。
- 用户自有/自建模产可商用；AI 生成（`generate_3d`）须确认生成器授权（tripo/hunyuan3d/hyper3d 商用条款）。

## §4 导出纪律（glTF/USD/FBX）

- **glTF/GLB**：游戏/AR 默认。**顶点色默认导出会降位**（`COLOR_0` 变 ubyte + 多出畸形 `COLOR_1`），根因是顶点色没被材质节点树引用；**解法：把顶点色接进材质（ShaderNodeVertexColor → Base Color）或导出时 `export_vertex_color='ACTIVE'`**。精确控色要求高时，仍可「GLB 只出几何、颜色到引擎侧套」（最稳，非唯一解）。纯色材质实测 `pbrMetallicRoughness` 正常，不受影响。**能不能不自认倒霉请先自测** → `blender-5x-pitfalls` 致命级第 3 条附 10 秒自检脚本。
- **FBX**：Maya/Unity 互通。
- **USD**：Blender→Unreal 一键管线（多 agent 跨软件）。
- **Decimate** 生成 LOD（LOD1=50% / LOD2=75% / LOD3=90% 缩减）。
- 导出参数（5.x）：`export_format='GLB'`、`export_materials='EXPORT'`（**无 `export_colors` 参数**，5.x 已移除）。

## §5 Agent+MCP 协作三硬限制

1. **创意拓扑不是 agent 的活**：概念/大形/风格/轮廓决策由**人**做；agent 只接手可参数化、可验证子任务（blockout / 低模代理）。手动重拓扑/UV/绑定/动画必须人审。
2. **重操作超时 60–120s**：细分/重拓扑/烘焙/模拟 bake 会超时——须拆小步、降分辨率、或交人手动在 Blender 内跑。
3. **agent 无视觉反馈**：agent 看不到渲染结果，靠 `look`/`get_scene_info` 间接判断——**所有"看起来对不对"的终裁必须落回人**（agent 不自认已验证）。

## §6 Blender-MCP 协作铁律

- **连接前提**：Blender 必须开着且插件服务端已启动（N 面板 → `MCP for Blender`（旧版显示为 BlenderMCP）→ Start MCP Server）。无连接证明（如 `get_addon_status` 已连）前，任何成员不得声称能操控 Blender。
- **执行后必 `look` 自检**：`look` 是 agent 唯一视觉通道，是硬限制 #3 的补偿机制。
- **代码即资产**：结构化操作优先落 bpy 脚本（`execute_blender_code`），可版本化、可 diff、可复现；LL3M 自批判循环 = 执行 → 读回 → 修正。
- **工具按需加载**：只亮少量核心工具（get_addon_status / get_scene_info / execute_blender_code / look），重工具经 `search_assets`/`generate_3d` 调用，别全量塞（工具全量注入会显著抬高小模型的幻觉率）。
- **造模上云、精修在本地**：`generate_3d`（tripo/hunyuan3d/hyper3d）云端造模绕开本地重算超时（硬限制 #2）；精修留本地 bpy。
- **隐私**：默认本地优先（127.0.0.1）；云端造模经 `uvx` 运行时，须显式告知用户数据出站。

## §7 修改与同步纪律

本技能为团队标准基线。每次建模/渲染发现的新技法/坑/规范 → 回写本 SKILL.md 对应章节 + MEMORY.md（项目级）。不擅自推翻 §1–§6 级红线；涉及决策变更先与主理人（艾芙琳）对齐。

## §8 工序条目（建模/雕刻/导出前的硬工序）

> 以下工序是**非过不可的步骤**，不是建议。每条都带可断言的验收线——做完必须自检数字，不许「看起来没问题」。

### §8.1 雕刻基底密度门槛

- **雕刻/有机形基底一律高细分球**：`u_segments=128 × v_segments=96`（≈1.2 万顶点），不许用默认球（默认 32×16 只有 2562 顶点，撑不住雕刻级形变）。
- 断言：基底顶点数 **≥1 万**再开始形变。

### §8.2 导出前冻结变换 + 应用修改器

- 导出前必做：`bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)` + `modifier_apply` 逐个应用栈内修改器。
- 断言：回读尺寸差 **= 0.0**（不冻结时实测漂移 8.2%）。

### §8.3 布尔/倒角后拓扑卫生

- `boolean` / `bevel` 后必做三件：`bmesh.ops.remove_doubles(dist=1e-5)` → `bmesh.ops.recalc_face_normals` → **winding 冲突断言 = 0**（两面共享边被同向遍历即冲突）。
- 断言：winding 冲突 0、signed volume > 0。

### §8.4 修改器栈组合后断言流形

- 多修改器（ARRAY/MIRROR 等）组合后，取**求值网格**（`evaluated_depsgraph_get`）断言非流形边 = 0；重叠实例处先焊接（remove_doubles）再断言。
- 重叠缝不焊 → 求值网格非流形边暴涨（实测 1728 条）。

### §8.5 旋成体封口规范

- 旋成（spin）封口用 **spin + merge**（`use_merge=True` + `remove_doubles`），**禁止裸 ngon 封口**——裸 ngon 被细分后在盖面内部产生大价极点。
- 断言：大价极点（价 >8）只允许出现在**旋转轴上**，轴外大价极点 = 0。

### §8.6 对称雕刻镜像约束

- 对称形体的形变权重**只用 `|x|`**（或镜像修改器约束），禁止左右各算一套。
- 断言：镜像配对顶点最大偏差 **< 1e-3**（理想 1e-6）。
