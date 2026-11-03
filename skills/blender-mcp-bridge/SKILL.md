---
name: blender-mcp-bridge
description: "接线 mcp-for-blender（uvx mcp-for-blender + 5.2 插件）：连接前提、真实工具名对齐（非旧版 blender-mcp）、连接证明、按需加载。让工作室能真正操控 Blender。"
whenToUse: "Blender 建模 / 渲染 / 导出 / 排障 / MCP 接线 时"
license: MIT
---

# Blender MCP 接线（blender-mcp-bridge）

让团队能**在运行中的 Blender 5.2 内**被智能体驱动。本机操控层是增强版 **mcp-for-blender**（经 `uvx mcp-for-blender` 安装，工具命名空间 `mcp__blender__*`），**不是**社区基础版 `blender-mcp`（ahujasid）。

## 配置现状（本机已就绪）

- **MCP 配置**：`~/.workbuddy/mcp.json` 的 `blender` 节点：`command: uvx mcp-for-blender`，`BLENDER_PORT=9876`，`disabled:false`。
- **本地插件**：`uvx mcp-for-blender install-addon` 自动装到 Blender 的 addons 目录；`uvx mcp-for-blender addon-paths` 可查实际路径。插件与服务端的协议版本必须一致，不一致时连接报错很含糊——这是首跑失败最常见的原因。
- **连接前提**：Blender 必须**开着**且插件服务端**已启动**（N 面板 → `MCP for Blender`（旧版显示为 BlenderMCP）→ Start MCP Server）。当前没开 → 实测 `get_addon_status` 返回「Could not connect to Blender」。这不是「没有 MCP」，而是操控层已经存在、只差用户先把软件开起来。
- **没有**编辑器自动拉起这回事；Blender MCP 需用户在 Blender 内手动点启动（或后续研究能否 CLI 拉起 + 触发服务端）。

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
| `import_asset` | 把 `search_assets` 搜到的资产下载并**导入**当前场景 | 资产落进场景 |
| `disable_telemetry` | 关掉 prompt/代码/截图/场景数据的采集 | 隐私合规 |
| `record_trajectory_feedback` | 对某一轨迹步记录评价反馈 | 团队自查 |

**上表即全部 9 个工具，一个不多一个不少**（2026-10-22 实机 `tools/list` 核验：PyPI 最新 `mcp-for-blender` 2.2.2，`serverInfo` 自报 `1.30.0`）。

> 🔴 **没有独立的 export 工具，也没有 import 工具之外的任何「文件转换」工具。**
> 导出 glTF/GLB/FBX/OBJ/STL/USD/ABC/PLY 一律由 `execute_blender_code` 调 `bpy.ops.export_scene.*` 完成，
> 格式能不能出取决于你的 Blender 装没装对应插件（glTF/USD 内置，FBX/OBJ/STL 内置，ABC/PLY 多数版本内置）。
> **别去找 `export_gltf` / `export` / `（导出/导入）` 这种工具，它不存在。** 照着不存在的工具写脚本，买家只会拿到一句「工具不存在」。

> ⚠️ **与旧基础版 blender-mcp 的工具名差异**（建脚本/技能时务必对齐本表）：
> 旧 `get_viewport_screenshot` → 现 `look`；旧 `get_polyhaven_assets` → 现 `search_assets`；旧 `generate_hyper3d_model` → 现 `generate_3d`。直接照搬旧名会调不到工具。

## 每成员工具配方

| 成员 | 常用工具 |
|---|---|
| blender-tech-mcp | get_addon_status / execute_blender_code（导出全系走这里）/ search_assets / import_asset / generate_3d |
| blender-modeling | execute_blender_code（导出 glTF 走这里）/ get_scene_info / look / generate_3d |
| blender-shading | execute_blender_code / get_scene_info / look / search_assets |
| blender-rig-anim | execute_blender_code / get_scene_info / look |
| blender-light-render | execute_blender_code / get_scene_info / look |
| blender-sim-vfx | execute_blender_code / get_scene_info / look |

## 按需加载（对抗小模型幻觉）

- 只亮少量核心工具（get_addon_status / get_scene_info / execute_blender_code / look），重工具经 `search_assets` / `generate_3d` 调用。
- 经验上，工具数多的 MCP server 会做「按需加载」来控制上下文，本团不照搬其工具数。
- 工具全量注入会显著抬高小模型幻觉率：只亮核心几个，重工具按需取。本团照此执行。

## 可复用 helper

`scripts/blender_mcp_exec.py` — 读 .py 或 stdin，经 `uvx mcp-for-blender` 桥在 Blender 内执行并返回输出：`python3 scripts/blender_mcp_exec.py script.py`。可作团队脚本资源（注意：需 Blender 已开 + 插件服务端已启动）。

**输出落盘约定（审计/验证命令必做）**：凡用该 helper 跑审计、验证、对比类命令，输出原文必须重定向落盘，例：`python3 scripts/blender_mcp_exec.py script.py > 派单/回执_01_audit.log 2>&1`；回执正文只报「做了什么 + 产物路径」，**不许把输出转述/摘要进正文充当证据**——证据必须可复查（带路径，可带行号）。

## 红线
- 默认本地优先（127.0.0.1）；云端造模（`generate_3d` / fal.ai）经 `uvx` 运行时，须显式告知用户数据出站。
- 无连接证明不得声称已操控。
- 截图/`look` 仅用于自动化自检，不替代人的视觉终裁。
