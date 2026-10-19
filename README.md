# dsh-blender · JOJO&Adam

Blender 在 DeepSeek Harness 里的生产包：headless 跑 bpy 脚本、渲染、导出 glTF，外加建模技法、5.x 踩坑和程序化资产管线。

不是“教你怎么点 Blender”，是让 agent 真的能把场景建出来、渲染出来、导出成游戏资产。

## 安装

```bash
# 从 npm
dsh plugin --profile web add @jojonadam/dsh-blender        # Web 版
dsh plugin --profile desktop add @jojonadam/dsh-blender    # 桌面版

# 本地开发
dsh plugin --profile desktop add link:/absolute/path/to/dsh-blender
```

## 30 秒上手

前置：本机装有 Blender 5.2 LTS（macOS 默认 `/Applications/Blender.app`）。

```bash
# 1. 体检
python3 skills/blender-studio/scripts/blender_client.py doctor

# 2. 冒烟渲染（默认立方体，256×256）
python3 skills/blender-studio/scripts/blender_client.py smoke --res 256

# 3. 跑示例：参数化地砖 → 渲染 → 保存 .blend → 导出 .glb
python3 skills/blender-studio/scripts/blender_client.py run \
  --script skills/blender-studio/examples/make_tiles.py \
  --outdir outputs/blender/tiles
```

## 包含

| 技能 | 用途 |
|---|---|
| `blender-studio` | 总入口：体检、headless 执行、渲染、导出（含客户端与示例） |
| `blender-env` | 找不到 Blender、版本、METAL、黑图、权限、bpy 报错 |
| `blender-sop` | 5.2 基线、Cycles/EEVEE 抉择、CC0 红线、导出纪律 |
| `blender-modeling-cookbook` | 参数化建模、BMesh、修改器栈、拓扑、UV、选择性 Bevel |
| `blender-5x-pitfalls` | 5.x 的 API 变更与已知坑 |
| `blender-asset-pipeline` | 程序化资产、批量、LOD、glTF 导出、连续网格反模式 |
| `blender-mcp-bridge` | 需要实时操控打开着的 Blender 时接 MCP |

## 设计边界

- 默认 headless：确定性任务（建模/材质/渲染/导出）可复现；
- 雕刻、手动绑定、视觉微调交给 MCP 或人；
- 不代装 Blender、不代下资产（CC0 规则见 SOP）；
- 只在本机执行，不经过云端。

## 验证

```bash
node test/provider.test.mjs
python3 skills/blender-studio/scripts/blender_client.py doctor
```

实机验证：Blender 5.2.1 LTS · macOS · METAL，EEVEE 256×256 冒烟 3.5s；参数化地砖（9 块 + 选择性 Bevel + glTF）3.6s；Cycles 256×256 / 16 采样 CPU 1.3s、Metal 首次 4–5 分钟（kernel 编译，2026-10-19）。

## 品牌

JOJO & Adam · <https://jojo-adam.com>

## License

MIT
