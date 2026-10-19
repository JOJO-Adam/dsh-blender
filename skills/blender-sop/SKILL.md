---
name: blender-sop
description: "Blender 专业标准：5.2 LTS 基线、Cycles/Eevee 抉择、CC0 资产红线、glTF/USD 导出纪律，以及 agent 驱动 Blender 协作的三条硬限制。所有管线判断的单一真相源。"
whenToUse: "Blender / 渲染器选择 / Cycles / Eevee / CC0 / glTF / USD / 导出规范 时"
license: MIT
---


# Blender 专业标准（blender-sop）

> DSH 执行层（headless 跑 Blender、渲染、导出）：见 `blender-studio` 技能。


**所有管线判断以此为准。** 本技能是 Blender 工作室的"大脑"，版本/渲染器/资产/导出/协作纪律的单一真相源。

## §1 版本基线（务必写准，别犯 Godot 的版本错）

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

- **glTF/GLB**：游戏/AR 默认。本环境 **5.2 glTF 导出器丢色**（顶点色→白色 `COLOR_0`+畸形 `COLOR_1`；纯色材质→无 `pbrMetallicRoughness`）→ **GLB 只出几何，颜色在下游引擎侧套**（Godot/Maya/Unity 建材质）。
- **FBX**：Maya/Unity 互通。
- **USD**：Blender→Unreal 一键管线（多 agent 跨软件）。
- **Decimate** 生成 LOD（LOD1=50% / LOD2=75% / LOD3=90% 缩减）。
- 导出参数（5.x）：`export_format='GLB'`、`export_materials='EXPORT'`（**无 `export_colors` 参数**，5.x 已移除）。

## §5 Agent+MCP 协作三硬限制（StraySpark）

1. **创意拓扑不是 agent 的活**：概念/大形/风格/轮廓决策由**人**做；agent 只接手可参数化、可验证子任务（blockout / 低模代理）。手动重拓扑/UV/绑定/动画必须人审。
2. **重操作超时 60–120s**：细分/重拓扑/烘焙/模拟 bake 会超时——须拆小步、降分辨率、或交人手动在 Blender 内跑。
3. **agent 无视觉反馈**：agent 看不到渲染结果，靠 `look`/`get_scene_info` 间接判断——**所有"看起来对不对"的终裁必须落回人**（agent 不自认已验证）。

## §6 Blender-MCP 协作铁律

- **连接前提**：Blender 必须开着且插件服务端已启动（N 面板 → BlenderMCP → Start MCP Server）。无连接证明（如 `get_addon_status` 已连）前，任何成员不得声称能操控 Blender。
- **执行后必 `look` 自检**：`look` 是 agent 唯一视觉通道，是硬限制 #3 的补偿机制。
- **代码即资产**：结构化操作优先落 bpy 脚本（`execute_blender_code`），可版本化、可 diff、可复现；LL3M 自批判循环 = 执行 → 读回 → 修正。
- **工具按需加载**：只亮少量核心工具（get_addon_status / get_scene_info / execute_blender_code / look），重工具经 `search_assets`/`generate_3d` 调用，别全量塞（复用 Godot 团"131 工具全量注入→幻觉"教训）。
- **造模上云、精修在本地**：`generate_3d`（tripo/hunyuan3d/hyper3d）云端造模绕开本地重算超时（硬限制 #2）；精修留本地 bpy。
- **隐私**：默认本地优先（127.0.0.1）；云端造模经 `uvx` 运行时，须显式告知用户数据出站。

## §7 修改与同步纪律

本技能为团队标准基线。每次建模/渲染发现的新技法/坑/规范 → 回写本 SKILL.md 对应章节 + MEMORY.md（项目级）。不擅自推翻 §1–§6 级红线；涉及决策变更先与主理人（艾芙琳）对齐。
