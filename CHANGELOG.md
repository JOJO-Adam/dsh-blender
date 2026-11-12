# Changelog

## 0.2.1 — 2026-11-12

- 补英文 README（README.en.md）与版本历史；无功能变更。

## 0.2.0 — 2026-11-03

同步专家团 blender-studio v1.3.5 / v1.3.6 的实机测试修复。

- **sop**：新增 §8 六条硬工序（雕刻基底密度、导出前冻结变换、布尔后拓扑卫生、修改器后流形断言、旋成体封口、对称雕刻镜像），每条「为什么→怎么做→断言」；纪律 3 落成可执行步骤（以 asset_list 为基准逐项核七字段），纪律 4 新增共同前提卡（资产名/尺寸/面数预算/导出格式先锁死）。
- **新增 blender-triage**：按症状查的排障表（渲染/模型/材质/导出/性能/绑定），附「本团做不到什么」的诚实清单。
- **blender-mcp-bridge**：补输出落盘约定（审计/验证命令输出必须落文件，回执只报路径），随包 `scripts/blender_mcp_exec.py` 与 `_console.py`。
- **随包资源**：`blender-sop/templates/` 六份交付表与工序单；`blender-sop/scripts/check_table_consistency.py`（跨表咬合，带 `--selftest`）与 `check_templates.py`。
- **5x-pitfalls / asset-pipeline / modeling-cookbook**：同步 v1.3.6 内容（行数 42→197、113→124、68→79）。
- 测试：`test/provider.test.mjs` 覆盖 8 个技能，并断言模板与检查器已随包。

## 0.1.2 — 2026-10-21

- 补市场图标与中英 locale 元数据。

## 0.1.1 — 2026-10-21

- 修复技能发现与打包清单。

## 0.1.0 — 2026-10-21

- 首版：headless runner + 渲染/导出 + 建模/踩坑/资产管线/MCP 接线。
