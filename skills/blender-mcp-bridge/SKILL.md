---
name: blender-mcp-bridge
description: "把 mcp-for-blender 接到 DSH：uvx 启动、Blender 5.2 插件、连接前提、真实工具名对齐、连通性验证与按需加载。用于需要实时操控 Blender 的交互场景。"
whenToUse: "Blender MCP / 实时操控 / 交互式 / uvx / 插件 / 连接失败 时"
license: MIT
---


# Blender MCP 接线（blender-mcp-bridge）

> DSH 执行层（headless 跑 Blender、渲染、导出）：见 `blender-studio` 技能。


让团队能**在运行中的 Blender 5.2 内**被智能体驱动。本机操控层是增强版 **mcp-for-blender**（经 `uvx blender-mcp` 安装，工具命名空间 `mcp__blender__*`），**不是**社区基础版 `blender-mcp`（ahujasid）。

## 配置现状（本机已就绪）

- **MCP 配置**：`~/.workbuddy/mcp.json` 的 `blender` 节点：`command: uvx blender-mcp`，`BLENDER_PORT=9876`，`disabled:false`。
- **本地插件**：`~/Library/Application Support/Blender/5.2/scripts/addons/blender_mcp_addon.py`（175KB，2026-09-14）。
- **连接前提**：Blender 必须**开着**且插件服务端**已启动**（N 面板 → BlenderMCP → Start MCP Server）。当前没开 → 实测 `get_addon_status` 返回「Could not connect to Blender」。这与 Godot 当初"误判无 MCP"同一剧本——操控层存在，只是需用户先开软件。
- **没有** Godot 那种编辑器自动拉起；Blender MCP 需用户在 Blender 内手动点启动（或后续研究能否 CLI 拉起 + 触发服务端）。

## 连接证明（Phase 0.5 闸门）

- 先 `get_addon_status` 确认插件/版本匹配、库与生成器开关；返回已连才算"本机 Blender 已接入"。
- 或 `execute_blender_code` 跑 `import bpy; print(bpy.app.version)` 能回显版本即证明通道通。
- **无连接证明前，任何成员不得声称能操控 Blender**——只能输出纯设计/文档产出并显式告知阻塞。

## 真实工具矩阵（对齐 mcp-for-blender，别照基础版写旧名）

| 工具 | 能力 | 团队用途 |
|---|---|---|
| `get_addon_status` | 版本/插件匹配/库与生成器开关/telemetry | **环境审计入口** |
| `get_scene_info` | 场景事实：对象数/位置/尺寸/拓扑健康/权重 | 读回场景树 |
| `execute_blender_code` | 在用户活 Blender 跑 bpy/bmesh/mathutils | **逃逸舱**：一切结构化工具够不到的都写 Python |
| `look` | 渲图看场景：viewport/camera/多角度/帧序列，solid/material/rendered/wireframe/xray | **视觉反馈通道**（替代旧 `get_viewport_screenshot`，更强） |
| `search_assets` | 搜 polyhaven(CC0)/sketchfab/Polypizza(CC0/CC-BY) | CC0 资产直拉 |
| `generate_3d` | 文本/图像→带贴图 3D 模型，tripo/hunyuan3d/hyper3d，Premium 档 | AI 造模（独有道具），再进 Blender 精修 |
| （导出/导入） | glTF/GLB/FBX/OBJ/STL/USD/ABC/PLY | 资产出 Blender → 引擎/AR/打印 |

> ⚠️ **与旧基础版 blender-mcp 的工具名差异**（建脚本/技能时务必对齐本表）：
> 旧 `get_viewport_screenshot` → 现 `look`；旧 `get_polyhaven_assets` → 现 `search_assets`；旧 `generate_hyper3d_model` → 现 `generate_3d`。直接照搬旧名会调不到工具。

## 每成员工具配方

| 成员 | 常用工具 |
|---|---|
| blender-tech-mcp | get_addon_status / execute_blender_code / 导出全系 / search_assets / generate_3d |
| blender-modeling | execute_blender_code / get_scene_info / look / generate_3d / export glTF |
| blender-shading | execute_blender_code / get_scene_info / look / search_assets |
| blender-rig-anim | execute_blender_code / get_scene_info / look |
| blender-light-render | execute_blender_code / get_scene_info / look |
| blender-sim-vfx | execute_blender_code / get_scene_info / look |

## 按需加载（对抗小模型幻觉）

- 只亮少量核心工具（get_addon_status / get_scene_info / execute_blender_code / look），重工具经 `search_assets` / `generate_3d` 调用。
- 范本来例：StraySpark Blender MCP Server v4.0（556 工具/39 类，只开 22 个开门工具，其余经 search 按需加载，上下文压到 9.5K token）。这套技能不照搬其 556 工具，但**同一哲学**：工具多 ≠ 全塞上下文。
- 复用 Godot 团教训：seele-godot 131 工具全量注入小模型 → 幻觉。Blender 团避免。

## 可复用 helper

`/Users/jojo/AI_Projects/Seele/tools/blender_mcp_exec.py` — 读 .py 或 stdin，经 `uvx blender-mcp` 桥在 Blender 内执行并返回输出：`python3 blender_mcp_exec.py script.py`。可作团队脚本资源（注意：需 Blender 已开 + 插件服务端已启动）。

## 红线
- 默认本地优先（127.0.0.1）；云端造模（`generate_3d` / fal.ai）经 `uvx` 运行时，须显式告知用户数据出站。
- 无连接证明不得声称已操控。
- 截图/`look` 仅用于自动化自检，不替代人的视觉终裁。
