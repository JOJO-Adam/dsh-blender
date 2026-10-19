---
name: blender-studio
description: "Blender 在 DSH 里的总入口：环境体检、headless 跑 bpy 脚本、渲染 .blend、导出 glTF，以及建模/踩坑/资产管线/MCP 的路由。当用户要建模、渲染、做游戏资产、批量生成或接 Blender 时使用。"
whenToUse: "Blender / bpy / 渲染 / render / glTF / GLB / 建模 / 资产 / headless 时"
license: MIT
---

# Blender × DSH

> 本技能是执行层：怎么在 DSH 里用 headless Blender 跑脚本、渲染、导出。
> 领域知识（SOP、建模、踩坑、资产管线）在另外几个技能里，见第 5 节路由。

## 0. 先决条件

- Blender **5.2 LTS**（本包按 5.2 校准；4.x 的引擎标识与 API 有差异）；
- macOS 默认路径 `/Applications/Blender.app/Contents/MacOS/Blender`；
- 用 `BLENDER_BIN` 或 `--blender` 指定其他路径；
- 客户端零依赖（Python 3.8+），不需要在系统 Python 里装 bpy。

## 1. 30 秒体检

```bash
python3 scripts/blender_client.py doctor
```

输出：版本、可执行文件路径、GPU 后端（macOS 应为 `METAL`）、可用渲染引擎。
连不上/找不到时先看 `blender-env`，不要改脚本。

## 2. 冒烟渲染（证明链路是通的）

```bash
python3 scripts/blender_client.py smoke --outdir outputs/blender/smoke --res 256
```

会新建默认场景、用 EEVEE 渲染一张 256×256 PNG。3–5 秒内出图即正常。

## 3. 跑 bpy 脚本（主要工作方式）

```bash
python3 scripts/blender_client.py run \
  --script skills/blender-studio/examples/make_tiles.py \
  --outdir outputs/blender/tiles
```

- 脚本通过环境变量 `DSH_BLENDER_OUTDIR` 拿到输出目录；
- 需要从已存工程开始时加 `--blend path/to/scene.blend`；
- 额外参数：`--arg key=value`（追加到 `--` 之后，脚本用 `sys.argv` 读）。

示例 `examples/make_tiles.py` 演示了完整闭环：参数化建模 → 选择性 Bevel → 相机灯光 → EEVEE 渲染 → 保存 `.blend` → 导出 `.glb`。

## 4. 渲染已有工程 / 导出

```bash
# EEVEE 单帧（快，适合迭代）
python3 scripts/blender_client.py render \
  --blend outputs/blender/tiles/scene.blend \
  --out outputs/blender/tiles/final.png \
  --samples 64 --res 1024

# Cycles 单帧（真实光影；macOS 用 --device METAL，小场景可先试 CPU）
python3 scripts/blender_client.py render \
  --blend outputs/blender/tiles/scene.blend \
  --out outputs/blender/tiles/final_cycles.png \
  --engine CYCLES --device METAL --samples 32 --res 512

# 更复杂的导出（glTF / USD / FBX）直接在脚本里做，不要在命令行拼
python3 scripts/blender_client.py run --script my_export.py --blend scene.blend
```

输出统一放 `outputs/blender/<主题>/`，文件名带版本或日期；生成后用 `present` 把图片给用户看。

> ⚠️ Cycles 在 macOS 上首次运行要编译 Metal kernel（可能几分钟）。如果进程写不了 kernel 缓存，每次都会重编译——迭代用 EEVEE，定稿再上 Cycles。

## 5. 领域路由

| 用户问题 | 调用技能 |
|---|---|
| 找不到 Blender / 版本不对 / 渲染报错 | `blender-env` |
| 渲染器怎么选、导出规范、CC0 红线 | `blender-sop` |
| 建模、Bevel、修改器、拓扑、UV | `blender-modeling-cookbook` |
| 5.x 的 API 变化与已知坑 | `blender-5x-pitfalls` |
| 程序化资产生成、批量、LOD、glTF | `blender-asset-pipeline` |
| 要实时操控打开着的 Blender | `blender-mcp-bridge` |

## 6. 诚实边界

- **headless 只适合确定性任务**：建模、材质、渲染、导出、批量。雕刻、手动绑定、视觉微调这类交互工作，要么用 MCP 接活着的 Blender，要么交给人。
- 不代装 Blender、不代下资产（CC0 规则见 `blender-sop`）。
- 渲染质量与速度取决于本机 GPU；同一场景的耗时不能直接跨机器比较。
- 所有操作只在本机执行，不经过云端。
