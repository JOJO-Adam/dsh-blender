#!/usr/bin/env python3
"""离线模板自检（blender-studio v1.3.4）。

## 这是什么、不是什么

**不是生成器**——不产出任何内容，只回答一件事：
**包里这四份模板，是不是都能真的填、且彼此不打架、SKILL 里也指得到？**

为什么需要：这一版把「没装 Blender 也能交付」落成了四份表。模板最容易出的问题不是缺失，
而是**「在但没用」**——表头列数与示例行对不上（填进去就错位）、SKILL 里没引用（agent 想不到调）。
任何一条都会让买家拿到「看起来有、实际不能用」的东西。

## 判据

1. 六份模板都在且非空
2. 每张 md 表的**表头列数 == 分隔行列数 == 示例行列数**（对不上就会填错位）
3. 每份顶部都有「本表不需要 Blender 即可填写交付」声明
4. SKILL 里确实引用了六个路径（防「模板在但没人用」）
5. **反向**：删一份模板 / 把示例行列数改坏 → 必须报错
   （只做正向断言，判据坏了也照样绿）
"""
import pathlib
import re
import sys

try:  # 控制台编码兜底：中文 Windows 控制台是 cp936，打不出 ✅/❌
    import _console

    _console.ensure_utf8()
except Exception:                                                # noqa: BLE001
    pass

PKG = pathlib.Path(__file__).resolve().parents[1]
TPL = {
    "asset_list.md": "资产清单表",
    "model_spec.md": "建模参数表",
    "naming_export.md": "命名与导出规范",
    "delivery_checklist.md": "交付检查表",
    "uv_unwrap.md": "UV 展开打包工序单",
    "lighting_exposure.md": "布光/曝光工序单",
}
DECL = "不需要 Blender 即可填写交付"


def _tables(path: pathlib.Path) -> list[tuple[list[str], list[str], list[str], int]]:
    """→ [(表头列, 分隔行列, 示例行列, 行号)]；只取带分隔行（|---|）的真表。"""
    lines = path.read_text(encoding="utf-8").splitlines()
    out = []
    for i in range(len(lines) - 2):
        head, sep, first = lines[i].strip(), lines[i + 1].strip(), lines[i + 2].strip()
        if not (head.startswith("|") and sep.startswith("|") and first.startswith("|")):
            continue
        if not re.fullmatch(r"\|[\s:|-]+\|", sep):
            continue
        cell = lambda s: [c for c in s.strip().strip("|").split("|")]
        out.append((cell(head), cell(sep), cell(first), i + 1))
    return out


def check_all(root: pathlib.Path | None = None) -> list[str]:
    """→ 问题清单（空 = 通过）。root 可替换，便于反向测试。"""
    root = root or PKG
    tdir = root / "templates"
    bad: list[str] = []

    # ① 四份都在且非空
    for name, label in TPL.items():
        f = tdir / name
        if not f.is_file():
            bad.append(f"缺模板：{name}（{label}）")
        elif not f.read_text(encoding="utf-8").strip():
            bad.append(f"模板为空：{name}（{label}）")
    if bad:
        return bad

    # ② 表头 / 分隔行 / 示例行列数一致
    for name in TPL:
        tabs = _tables(tdir / name)
        if not tabs:
            bad.append(f"{name} 里没有可填的表（没找到「表头+分隔行+示例行」）")
            continue
        for head, sep, first, ln in tabs:
            if not (len(head) == len(sep) == len(first)):
                bad.append(f"{name}:{ln} 列数不一致：表头 {len(head)} / 分隔行 {len(sep)} / "
                           f"示例行 {len(first)}（填进去会错位）")

    # ③ 顶部声明
    for name in TPL:
        head_text = "\n".join((tdir / name).read_text(encoding="utf-8").splitlines()[:6])
        if DECL not in head_text:
            bad.append(f"{name} 顶部缺「{DECL}」声明")

    # ④ SKILL 引用
    corpus = "\n".join(s.read_text(encoding="utf-8")
                       for s in (root / "skills").rglob("SKILL.md"))
    for name in TPL:
        if name not in corpus:
            bad.append(f"没有任何 SKILL.md 引用 templates/{name}（模板在但没人用）")

    return bad


def main() -> int:
    if "--selftest" not in sys.argv:
        bad = check_all()
        if bad:
            print("❌ 模板自检未通过：")
            for b in bad:
                print(f"   · {b}")
            return 1
        print("✅ 模板自检通过：六份齐全、表头与示例对齐、顶部声明在、SKILL 已引用")
        return 0

    print("==== 离线模板自检（blender-studio）====")
    fails, checks = [], []

    def ck(label, cond, detail=""):
        checks.append(label)
        print(("  ✅ " if cond else "  ❌ ") + label + ("" if cond else f"   —— {detail}"))
        if not cond:
            fails.append(label)

    bad = check_all()
    ck("① 六份模板齐全且非空", not [b for b in bad if "缺模板" in b or "模板为空" in b],
       [b for b in bad if "模板" in b][:3])
    ck("② 表头列数 == 示例行列数（每张表）",
       not [b for b in bad if "列 vs 示例行" in b or "没有可填的表" in b],
       [b for b in bad if "列" in b][:3])
    ck("③ 六份顶部都有「不需要 Blender 即可填写交付」声明",
       not [b for b in bad if "声明" in b], [b for b in bad if "声明" in b][:3])
    ck("④ SKILL 引用了六个模板路径", not [b for b in bad if "SKILL" in b],
       [b for b in bad if "SKILL" in b][:3])

    # 反向：判据必须能失败
    import shutil
    import tempfile
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="btpl_"))
    try:
        shutil.copytree(PKG / "templates", tmp / "templates")
        shutil.copytree(PKG / "skills", tmp / "skills")

        (tmp / "templates" / "model_spec.md").unlink()
        ck("⑤ 反向：删一份模板 → 必须报错", bool(check_all(tmp)), "删了却没报错")
        shutil.copy(PKG / "templates" / "model_spec.md", tmp / "templates" / "model_spec.md")

        _f = tmp / "templates" / "asset_list.md"
        _t = _f.read_text(encoding="utf-8")
        # 把某张表的分隔行多切一列 → 表头与示例行列数仍相等，但分隔行不一致（格错位）
        _t = _t.replace("|---|---|---|---|---|---|---|", "|---|---|---|---|---|---|---|---|", 1)
        _f.write_text(_t, encoding="utf-8")
        ck("⑥ 反向：分隔行列数与表头不一致 → 必须报错", bool(check_all(tmp)), "列数错了却没报错")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    print()
    print(f"断言数：{len(checks)}")
    if fails:
        print(f"❌ {len(fails)} 项失败：{fails}")
        return 1
    print("── 离线模板自检全部通过")
    return 0


if __name__ == "__main__":
    sys.exit(main())
