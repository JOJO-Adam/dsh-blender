---
name: blender-5x-pitfalls
description: "Blender 5.x 踩坑清单（锚定 5.2 LTS）：Bevel 引用/限角陷阱、bevel_weight 移除、材质节点创建、Principled 无 Transmission、glTF 顶点色降位（附买家自检）、连续网格 vs 逐立方体、transform_apply 方向陷阱。快速避坑。"
whenToUse: "Blender 建模 / 渲染 / 导出 / 排障 / MCP 接线 时"
license: MIT
---

# Blender 5.x 踩坑清单（blender-5x-pitfalls）

**锚定 5.2 LTS。** 本环境已踩过的真实 bug，建脚本前先查，避免重蹈。详见 `blender-sop` / `blender-asset-pipeline` / `blender-modeling-cookbook`。

## 🔴 致命级（必踩无疑，先读）

1. **Bevel 引用**：用 `obj.modifiers.new(name="Bevel", type='BEVEL')` 拿引用，不用 `bpy.ops.object.modifier_add(type='BEVEL')` 后按名 `obj.modifiers["Bevel"]` 取 —— 5.x 报 `key "Bevel" not found`。
2. **Bevel 必须限角**：`limit_method='ANGLE'` + `angle_limit`（如 40°）。默认 `NONE` 会把**所有边（含平顶内部网格线）全倒角** → 平顶重引缝。限角后只磨圆崖壁/外缘（90°），平顶 0° 不动。
3. **glTF 顶点色降位（5.2 实测，有解）**：默认参数导出时，顶点色会变成 `COLOR_0`(componentType **5121 / ubyte**)，并额外冒出一个畸形的 `COLOR_1`(5123 / ushort)，精度掉一档，引擎侧看就是偏色发白。
   - **根因不是修不了的 bug**：Blender 导出时会自己打一行警告 `The active Vertex Color will not be exported, as it is not used in the node tree of the material`——**顶点色没被材质节点树引用时，导出器会补一个 ubyte 的 `COLOR_0` 兜底**，把真实顶点色挤到 `COLOR_1`。
   - **解法（实测均有效，二选一）**：① 把顶点色真的接进材质：`ShaderNodeVertexColor`（`layer_name` 填属性名）→ Principled 的 `Base Color`；② 导出时显式 `export_vertex_color='ACTIVE'`。
   - **纯色材质不受影响**：实测 `pbrMetallicRoughness` 与 `baseColorFactor` 正常存在。（此前本文写「纯色材质→无 `pbrMetallicRoughness`」，在 5.2.1 LTS 上**未复现**，已更正。）
   - **保守策略**：若下游需要精确控色，仍可「GLB 只出几何、颜色到引擎侧套」——最稳，但不是唯一解，别为此放弃在 Blender 侧上色。
   - `export_scene.gltf` **无 `export_colors` 参数**（5.x 已移除）→ 用 `export_format='GLB'`、`export_materials='EXPORT'`，顶点色开关走 `export_vertex_color`。
   - 🔍 **你的环境丢不丢，跑下面这段自检就知道**（一次 GLB 导出 + 一次 JSON chunk 解析；跑完按名字还原选择与活动物体）：
   ```python
   # 把这段整体丢给 execute_blender_code 跑。它不会在你的场景里留下任何东西：
   # 只建一个临时四面体、导一个小 GLB、就地解析 JSON chunk，
   # 跑完删掉临时物体/网格/材质与临时文件，并把选择与活动物体按名字还原。
   # 注意：还原做不到的部分它会直说（例如文件被标记「已修改」）。
   def _verify_gltf():
       import bpy, json, struct, os, tempfile
       from contextlib import suppress

       # ① 只在 Object Mode 下跑 —— EDIT/SCULPT 等模式下 select_set 会直接抛异常
       if bpy.context.mode != 'OBJECT':
           print("⚠️ 当前是 %s 模式，本自检未执行、场景未改动。"
                 "请先按 Tab 切到 Object Mode 再跑。" % bpy.context.mode)
           return

       vl = bpy.context.view_layer
       # ② 快照用户的选择与活动物体（存名字，跑完按名字还原）
       #    ⚠️ 这里必须跳过 None：买家场景里可能本来就带失效项（删过物体但槽没清），
       #    不跳过的话会在「还没建任何东西」之前就抛 AttributeError，
       #    等于把下面 ④ 才防住的同一个坑留在了上游。
       sel = [o.name for o in list(vl.objects) if o is not None and o.select_get()]
       act = vl.objects.active.name if vl.objects.active else None
       dirty_before = bpy.data.is_dirty

       p = os.path.join(tempfile.gettempdir(), "_verify_gltf.glb")
       ob = me = mt = None
       try:
           me = bpy.data.meshes.new("_verify_me")
           me.from_pydata(
               [(0,0,0),(1,0,0),(0,1,0),(0,0,1)], [],
               [(0,1,2),(0,1,3),(0,2,3),(1,2,3)])
           me.update()
           ob = bpy.data.objects.new("_verify_ob", me)
           bpy.context.scene.collection.objects.link(ob)
           ca = me.color_attributes.new(name="Col", type='BYTE_COLOR', domain='CORNER')
           for d in ca.data: d.color = (0.1, 0.9, 0.3, 1.0)
           me.color_attributes.active_color = ca
           mt = bpy.data.materials.new("_verify_mat")
           if mt.node_tree is None:        # 5.x 新材质自带节点树 → 正常不会走到这行
               mt.use_nodes = True         # 5.x 直接赋 True 会打 DeprecationWarning，故先判断
           nt = mt.node_tree
           if nt and "Principled BSDF" in nt.nodes:
               nt.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.8,0.2,0.2,1)
           ob.data.materials.append(mt)

           for o in list(vl.objects):
               if o is not None: o.select_set(False)
           ob.select_set(True); vl.objects.active = ob
           # 导出器本身可能不可用（买家把内置 glTF 插件关了，或参数不被当前版本支持）。
           # 这时不能把原始 traceback 甩给买家 —— 场景仍会由 finally 还原，但要让他看懂发生了什么。
           try:
               bpy.ops.export_scene.gltf(
                   filepath=p, export_format='GLB',
                   export_materials='EXPORT', use_selection=True)
           except Exception as e:
               print("⚠️ GLB 导出失败，本自检未完成 —— 卡在导出环节，与颜色是否丢失无关。")
               print("   常见原因：内置 glTF 插件被禁用；或 export_materials 等参数不被当前 Blender 版本支持。")
               print("   你的场景与选择会在本段结束时照常还原。")
               print("   原始错误：%r" % (e,))
               return

           with open(p, "rb") as f:
               f.read(12); clen, _ = struct.unpack("<II", f.read(8))
               g = json.loads(f.read(clen).decode("utf-8"))
           ct = {}
           for pr in g["meshes"][0]["primitives"]:
               for k, v in pr["attributes"].items():
                   if k.startswith("COLOR"): ct[k] = g["accessors"][v]["componentType"]
           NM = {5120:"byte",5121:"ubyte",5122:"short",5123:"ushort",5125:"uint",5126:"float"}
           pbr = any("pbrMetallicRoughness" in (m or {}) for m in g.get("materials", []))
           bad = any(v == 5121 for v in ct.values()) or len(ct) > 1
           print("COLOR 属性:", {k: NM.get(v, v) for k, v in ct.items()})
           print("有 pbrMetallicRoughness:", pbr)
           print("判定:", "🔴 丢色（COLOR_0 被降为 ubyte 或出现多层 COLOR_x）" if bad else "🟢 不丢色")
           print("本次用的临时样本（GLB，跑完即删除，可用 glTF 查看器对照）:", p)
       finally:
           # ③ 清理顺序：物体 → 网格 → 材质
           #   只删物体会让 _verify_me / _verify_mat 变孤儿继续留在 bpy.data
           for db, blk in ((bpy.data.objects, ob), (bpy.data.meshes, me),
                           (bpy.data.materials, mt)):
               if blk is not None:
                   with suppress(Exception): db.remove(blk)
           with suppress(Exception): os.remove(p)
           # ③.5 让 view_layer 重新求值。
           #   背景：`objects.remove()` 只删数据块，`view_layer.objects` 会短暂留一个「死槽」，
           #   此刻遍历会拿到 None（实测：删完 len=1 / list=[None]，update() 后 len=0 / list=[]）。
           #   下面 ④ 已经对 None 做了防御，所以**不调这一行也能跑通**；这里是保险——
           #   让槽真正清掉，而不是只跳过它，避免后续自己遍历时又撞上。
           with suppress(Exception): bpy.context.view_layer.update()
           # ④ 还原选择与活动物体（快照里已被删掉的物体自动跳过）
           #   逐物体 try：一个失败不阻断其余；**失败时绝不打印「已还原」**
           errs = []
           for o in list(vl.objects):
               # 即便上面 update() 已清槽，这里仍保留 None 判断：买家场景可能本就带失效项。
               # 对它调 select_set 会抛，再在 except 里读 o.name 会二次抛，
               # 第二次是从 except 里逃逸的，会带着整个还原段一起中断（早期版本实测踩过）。
               if o is None:
                   continue
               try: o.select_set(False)
               except Exception as e: errs.append("取消选择 %s: %r" % (getattr(o, "name", "失效对象"), e))
           for n in sel:
               o = bpy.data.objects.get(n)
               if o is None or n not in vl.objects:
                   continue
               try: o.select_set(True)
               except Exception as e: errs.append("选中 %s: %r" % (n, e))
           try:
               vl.objects.active = bpy.data.objects.get(act) if act else None
           except Exception as e:
               errs.append("设置 active: %r" % (e,))
           if not errs:
               print("已还原选择与活动物体 —— 原选中:", sel, "原 active:", act)
           else:
               print("⚠️ 还原未完成，选择或活动物体可能已被改动，请手动核对：",
                     "；".join(errs), "｜快照: 原选中", sel, "原 active", act)
           if bpy.data.is_dirty != dirty_before:
               print("⚠️ 本次自检让文件被标记为「已修改」（is_dirty 无法可靠复位，"
                     "不假装能还原）；不想保存就别保存。")

   _verify_gltf()
   ```

   **怎么读结果**：
   - `COLOR_0: ubyte` + 多一个 `COLOR_1: ushort` → 你的环境**复现**该降位，按上面解法 ①/② 处理。
   - `COLOR_0` 是 `ushort` 或 `float` 且只有一层 → 你的环境**不丢色**，可直接在 Blender 侧上色。
   - `有 pbrMetallicRoughness: False` → 纯色材质也被吞了，属另一个问题，把 Blender 版本号与这段输出一起报给技术支持。

4. **`transform_apply(location=True)` 把 `obj.location` 归零**：apply 之后用 `obj.location.x/y` 判方向会符号全翻 → 整块所有竖直棱被误选。**改用顶点包围盒中心** `0.5*(min+max)` 判方向。

## 🟠 高频级

5. **`MeshEdge.bevel_weight` 已移除**（5.x）：改成网格属性 `bevel_weight_edge`，但 Bevel `limit_method='WEIGHT'` 实测 flaky。最稳 = `bmesh.ops.bevel(geom=[选中棱], affect='EDGES', ...)` 直接倒角，版本无关。
6. **新材质无自动命名**：`node_tree.nodes.clear()` 后显建 Output + BSDF。
7. **`ColorRamp` element `.color` 需 RGBA 四元组**（4 个分量）。
8. **5.x Principled BSDF 无 `Transmission` 输入**：透明水面只调 `blend_method='BLEND'` + Alpha，别找 Transmission 插槽。
9. **Eevee 已重写（EEVEE-Next）**：不假设 4.x 旧 Eevee 行为；灯光/材质节点差异。
10. **`look` 回传被过滤**：部分环境 "model does not support images" → agent 无法视觉自检，靠客观 DIAG/PROOF（法线分布/坐标/渐变顶点数）+ 用户眼睛终审。

## 🟠 高频级 · 无头 API 注记（round 2 实机复现，禁删改语义）

10a. **`bpy.ops.mesh.loopcut_slide` 无头 segfault（rc=139）**：try/except 拦不住（进程直接崩）→ 等价 `bmesh.ops.subdivide_edges`。〔无头实测·实录 2.0 候选〕
10b. **`bpy.ops.sculpt.brush_stroke` 无头 `poll() failed`**：需 UI 上下文，拒绝初始化 stroke → 无头用 bmesh 位移（`vert.co += …`）等价。〔无头实测·实录 2.0 候选〕
10c. **`bmesh.ops.smooth_vert` 5.2 无 `iterations` 参数**：传了报错 → 手动循环多次调用。〔无头实测·实录 2.0 候选〕
10d. **glTF/STL 导出自动三角化，FBX 保留四边**：回读判据别拿四边面数直比，按**三角计数**比对（`Σ(len(p.vertices)-2)` 三角化前后不变）。〔无头实测；与评测集 A9 判据呼应〕

## 🟡 架构级（反模式）

11. **逐立方体各自顶点色 = 缝 + 色糊**：地面/地形必须用一整张连续 heightfield，顶点色 splat 只在边界带、块中心纯色。
12. **bmesh 跨会话 bevel 报 `BMEdge has been removed`**：选中+bevel+to_mesh+free 必须在**单 bmesh 会话内**完成。
13. **过渡名无拓扑后缀互相覆盖**：加 `_inland/_side/_corner` 区分。

## 🔵 用户可感知的 5.x 变化（不是脚本坑，是操作差异）

**这几条是用户从 4.x 升上来最常踩的：**

| 变化 | 用户会怎么感觉到 | 怎么办 |
|---|---|---|
| **Eevee 已重写（EEVEE-Next）** | 同样的灯光设置，渲染结果和 4.x 不一样；阴影更实 | 别拿 4.x 经验直接套，重新调一次灯光强度与阴影 |
| **Principled BSDF 无 Transmission** | 做玻璃/水找不到 Transmission 滑块 | 用 Alpha + Blend Mode；或改用 Cycles 折射 |
| **bevel_weight 边权重移除** | 4.x 的按权重倒角教程做不出来 | 用 Bevel 修改器的 Angle 模式 |
| **export_colors 参数移除** | 想控制 glTF 导出颜色，发现没这选项 | 用 `export_vertex_color`（`'ACTIVE'` / `'MATERIAL'` / `'NONE'`）+ `export_materials`；详见致命级第 3 条 |
| **材质面板布局调整** | 找不到某个设置 | 认准 Material Properties 顶部三个 tab：Surface / Volume / Settings |

**升级建议**：4.x 项目迁 5.x，先在副本上跑一遍完整渲染对比，别直接开原文件。

## 关联

- 版本/渲染器/导出纪律总纲 → `blender-sop` §1/§2/§4。
- 连续网格 + Bevel 算法 + 选择性倒角 → `blender-asset-pipeline` / `blender-modeling-cookbook` §3–§5。
- 工具名对齐（mcp-for-blender vs 旧 blender-mcp）→ `blender-mcp-bridge`。
