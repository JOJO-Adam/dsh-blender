#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""跨表咬合检查（sop 纪律 3 的机器侧判据）。

用法：
    python3 scripts/check_table_consistency.py <表A.md> <表B.md>   # 双表对查，有矛盾 exit 1
    python3 scripts/check_table_consistency.py --selftest          # 自测（5 真实矛盾全中 + 正常对 0 误报）

口径（七项字段取六类可机查项）：
    size 尺寸（米）/ tris 面数预算（目标+上限）/ uv UV 通道配置 / mat 材质名 /
    fmt 导出格式（主件）/ asset 资产名
规则：同类字段在两份表里**都有声明**且取值集合完全不相交 → 判矛盾（每条带文件行号）。
范围限制（如实）：自由文本抽取，单主资产/同资产多表场景适用；多资产项目按资产分表分别跑。
本判据的真阳性基准 = 2026-11-02 实机测试 5 处真实矛盾（见 --selftest fixtures 溯源注记）。
"""
import re
import sys
import tempfile
import unicodedata
from pathlib import Path


def norm(s):
    return unicodedata.normalize("NFKC", s)


def num(tok):
    try:
        return str(float(tok)).rstrip("0").rstrip(".") if "." in tok else str(int(tok))
    except ValueError:
        return tok


def lines_of(text):
    return [(i + 1, ln) for i, ln in enumerate(norm(text).splitlines())]


# —— 六类字段抽取器：返回 (value, lineno) 列表 ——————————————————————————

def ex_size(rows):
    out = []
    ctx = re.compile(r"尺寸|外廓|大小|规格|尺度|箱体|尺寸参考")
    tup = re.compile(r"(\d+(?:\.\d+)?)\s*[×xX\*]\s*(\d+(?:\.\d+)?)\s*[×xX\*]\s*(\d+(?:\.\d+)?)")
    bare = re.compile(r"(\d+(?:\.\d+)?)\s*(?:m|米)\b")
    for i, ln in rows:
        if not ctx.search(ln):
            continue
        for m in tup.finditer(ln):
            out.append(("x".join(num(g) for g in m.groups()), i))
        for m in bare.finditer(ln):
            out.append((num(m.group(1)), i))
    return out


def ex_tris(rows):
    out = []
    ctx = re.compile(r"面数|三角面|tri|预算|上限")
    val = re.compile(r"(?:≤|<=|目标|上限)\s*(\d+)|(\d+)\s*tri\b")
    for i, ln in rows:
        if not ctx.search(ln):
            continue
        for m in val.finditer(ln):
            out.append((num(m.group(1) or m.group(2)), i))
    return out


def ex_uv(rows):
    """UV 配置声明：多通道表达式（UV0+UV1）或单通道声明（仅 UV0 / UV0 单通道）。"""
    out = []
    multi = re.compile(r"UV(\d+)\s*\+\s*UV(\d+)")
    single = re.compile(r"仅\s*UV(\d+)|UV(\d+)\s*单通道")
    for i, ln in rows:
        for m in multi.finditer(ln):
            out.append(("UV%s+UV%s" % (m.group(1), m.group(2)), i))
        for m in single.finditer(ln):
            out.append(("UV%s" % (m.group(1) or m.group(2)), i))
    return out


def ex_mat(rows):
    out = []
    ctx = re.compile(r"材质")
    tok = re.compile(r"\bM_\w+")
    for i, ln in rows:
        if not ctx.search(ln):
            continue
        for m in tok.finditer(ln):
            out.append((m.group(0), i))
    return out


def ex_fmt(rows):
    out = []
    ctx = re.compile(r"交付形态|导出格式|export_format|交付件|导出参数")
    tok = re.compile(r"\b(FBX|GLB|glTF|USD|ABC)\b")
    primary = re.compile(r"为主")
    for i, ln in rows:
        if not ctx.search(ln):
            continue
        found = tok.findall(ln)
        if not found:
            continue
        if primary.search(ln):
            out.append((found[0], i))
        else:
            for f in found:
                out.append((f, i))
    return out


def ex_asset(rows):
    out = []
    tok = re.compile(r"\b(SM_\w+|SK_\w+)")
    for i, ln in rows:
        for m in tok.finditer(ln):
            out.append((m.group(0).rstrip("_LOD123456789"), i))
    return out


CATEGORIES = [
    ("size", "尺寸", ex_size),
    ("tris", "面数预算", ex_tris),
    ("uv", "UV 通道", ex_uv),
    ("mat", "材质名", ex_mat),
    ("fmt", "导出格式", ex_fmt),
    ("asset", "资产名", ex_asset),
]


def extract(path):
    rows = lines_of(Path(path).read_text(encoding="utf-8"))
    return {key: fn(rows) for key, _label, fn in CATEGORIES}


def compare(pa, pb, verbose=True):
    """返回矛盾列表 [(category, label, valsA, linesA, valsB, linesB), ...]。"""
    ea, eb = extract(pa), extract(pb)
    bad = []
    for key, label, _fn in CATEGORIES:
        va = sorted(set(v for v, _i in ea[key]))
        vb = sorted(set(v for v, _i in eb[key]))
        if not va or not vb:
            continue
        if set(va).isdisjoint(set(vb)):
            la = sorted(set(i for _v, i in ea[key]))
            lb = sorted(set(i for _v, i in eb[key]))
            bad.append((key, label, va, la, vb, lb))
            if verbose:
                print("[矛盾] %s：%s %s（%s 行 %s）↔ %s %s（%s 行 %s）" % (
                    label, Path(pa).name, "/".join(va), Path(pa).name, ",".join(map(str, la)),
                    Path(pb).name, "/".join(vb), Path(pb).name, ",".join(map(str, lb))))
    return bad


# —— 自测 fixtures：5 处真实矛盾（2026-11-02 实机测试，欧文表 vs 西奥表） ————

FIX_A = """# 自测件 A（溯源：欧文_表格.md 五矛盾缩样）
| 项 | 值 |
|---|---|
| 单位 | 场景单位 1.0 = 1 米；箱子尺寸假设 0.6×0.6×0.6 m |
| 导出参数 export_format | 'GLB' |
| 交付件 | SM_Crate_Wood_01.glb（GLB 自包含） |
| 材质 | `M_Crate_Wood` |
| 面数 | 三角面 ≤ 800（LOD0） |
| UV 通道 | 仅 UV0 单通道 |
| 资产 | SM_Crate_Wood_01 |
"""

FIX_B = """# 自测件 B（溯源：西奥_表格_v2.md 五矛盾缩样）
| 项 | 值 |
|---|---|
| 交付形态 | FBX + 贴图为主（Unity 原生导入）；GLB 备选 |
| 资产清单 | SM_Crate_Wood_01，目标 300 / 上限 400 |
| model_spec | SM_Crate_Wood_01，尺寸 0.80 × 0.80 × 0.80，三角面上限 ≤ 400，UV0 + UV1 |
| 材质槽 | 1（M_Crate_Wood_01） |
| 外廓 | 外廓仍 0.80 m 等边 |
"""

FIX_CLEAN_A = """# 自测件（正常对 A）
| 项 | 值 |
|---|---|
| 资产 | SM_Crate_Wood_01 |
| 尺寸 | 0.8×0.8×0.8 m |
| 面数 | 三角面 ≤ 800 |
| UV | 仅 UV0 单通道 |
| 材质 | M_Crate_Wood_01 |
| 导出 | 导出参数 export_format 'GLB'；交付件 SM_Crate_Wood_01.glb |
"""

FIX_CLEAN_B = """# 自测件（正常对 B）
| 项 | 值 |
|---|---|
| 资产清单 | SM_Crate_Wood_01 |
| 尺寸 | 0.80 × 0.80 × 0.80 |
| 面数 | 目标 600 / 上限 800 |
| UV 通道 | UV0 单通道 |
| 材质槽 | M_Crate_Wood_01 |
| 交付形态 | GLB 为主 |
"""


def selftest():
    d = Path(tempfile.mkdtemp(prefix="xcheck_"))
    a, b = d / "A.md", d / "B.md"
    a.write_text(FIX_A, encoding="utf-8")
    b.write_text(FIX_B, encoding="utf-8")
    bad = compare(str(a), str(b), verbose=True)
    keys = set(k for k, *_ in bad)
    want = {"size", "tris", "uv", "mat", "fmt"}
    ok1 = want <= keys
    print("真阳性（5 真实矛盾）：%s → %s" % (sorted(keys), "全中 ✅" if ok1 else "漏报 ❌"))
    ca, cb = d / "clean_A.md", d / "clean_B.md"
    ca.write_text(FIX_CLEAN_A, encoding="utf-8")
    cb.write_text(FIX_CLEAN_B, encoding="utf-8")
    bad2 = compare(str(ca), str(cb), verbose=False)
    ok2 = not bad2
    print("正常对误报：%d 条 → %s" % (len(bad2), "0 误报 ✅" if ok2 else "误报 ❌ %s" % bad2))
    if ok1 and ok2:
        print("SELFTEST PASS（真阳性全中 + 正常表 0 误报）")
        return 0
    print("SELFTEST FAIL")
    return 1


def main(argv):
    if len(argv) == 2 and argv[1] == "--selftest":
        return selftest()
    if len(argv) != 3:
        print(__doc__)
        return 2
    bad = compare(argv[1], argv[2])
    if bad:
        print("共 %d 处矛盾——不许宣称「表已咬合」；改到一致或标「待拍板」。" % len(bad))
        return 1
    print("咬合 ✅（六类可机查项双方声明一致；七项中的「交付形态主/备件」含在 fmt）")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
