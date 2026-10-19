---
name: blender-env
description: "Blender 环境体检与排障：找不到可执行文件、版本不对、GPU/METAL、EEVEE 黑图、输出目录无权限、bpy 脚本报错、MCP 插件没连上。当 doctor 失败或用户说 Blender 跑不起来时使用。"
whenToUse: "Blender 找不到 / 版本 / METAL / GPU / 黑图 / 权限 / bpy 报错 / 插件连接 时"
license: MIT
---

# Blender 环境体检

> 先 doctor，再怀疑脚本。多数“脚本有问题”最后是路径、版本或 GPU 后端。

## 1. 体检顺序

| 步 | 检查 | 命令 | 失败含义 |
|---|---|---|---|
| 1 | 可执行文件 | `python3 scripts/blender_client.py doctor` | 没装 / 路径不对 |
| 2 | 版本 | 同上，看 `Blender 5.x` | 4.x 的引擎标识不同 |
| 3 | GPU 后端 | 同上，看 `METAL` | 回落到软件渲染，极慢 |
| 4 | 引擎列表 | 同上，应含 `BLENDER_EEVEE` | 版本或构建异常 |
| 5 | 冒烟 | `... smoke --res 256` | 能出图 = 链路通 |

## 2. 常见故障

### 找不到 Blender

- macOS 默认在 `/Applications/Blender.app/Contents/MacOS/Blender`；
- 其他位置：`export BLENDER_BIN=/path/to/Blender`，或每次 `--blender /path/to/Blender`；
- 不要指望 `blender` 在 PATH 里——App 安装通常不会建符号链接。

### 版本不对（4.x vs 5.x）

- 5.x 的 EEVEE 标识是 `BLENDER_EEVEE`（4.2–4.x 曾用 `BLENDER_EEVEE_NEXT`）；
- 部分 API 在 5.x 变更（Bevel、材质节点、`bevel_weight` 移除），见 `blender-5x-pitfalls`；
- 混用版本时，先统一到 5.2 LTS 再排查脚本。

### 渲染黑图 / 全黑

- headless 下 EEVEE 依赖 GPU；先确认 `doctor` 的 GPU 后端是 `METAL`；
- 没有相机 → 黑图；没有灯光 → 暗图（不是黑）；
- 世界背景为纯黑且没有灯光时，默认立方体也会接近黑；
- 先在 `smoke` 上验证，再怀疑场景。

### 输出目录无权限

- 错误形如 `Permission denied` / `Operation not permitted` 写 PNG；
- 用 `--outdir` / `--out` 指到可写目录（工作区内最稳）；
- 受限进程启动的 Blender 也受同样限制——必要时用可写目录重启。

### bpy 脚本报错

- 先看完整 traceback：客户端失败时会打印最后 25 行；
- 常见：API 名称在 5.x 改名、上下文对象为空（headless 没有 UI 上下文）、`bpy.ops` 需要正确的 active object；
- headless 下避免依赖 `screen`/`area` 的操作。

### MCP 连不上（交互模式）

- 需要 Blender 正在运行 + 装好 addon + `uvx blender-mcp`；
- headless 不需要 MCP；只有“实时操控打开着的 Blender”才需要；
- 详见 `blender-mcp-bridge`。

## 3. 体检输出怎么读

```
✅ Blender: Blender 5.2.1 LTS
   路径: /Applications/Blender.app/Contents/MacOS/Blender
   GPU 后端: METAL
   引擎: BLENDER_EEVEE
```

- 版本不是 5.x → 先对齐版本或接受差异；
- GPU 不是 METAL → 检查是否被 `--factory-startup` 之外的配置改过；
- 引擎列表缺 EEVEE → 构建异常，重装。

## 4. 边界

- 不代装 Blender、不改系统级配置；
- 不承诺渲染耗时——同一场景在不同 GPU 上差异很大；
- 环境修不好时，明确告诉用户卡在哪一步，而不是继续调脚本。
