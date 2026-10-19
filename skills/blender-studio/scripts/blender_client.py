#!/usr/bin/env python3
"""
blender_client.py — 零依赖 Blender headless 客户端（仅标准库）。

用法：
  python3 blender_client.py doctor [--blender PATH]
  python3 blender_client.py smoke  [--outdir DIR] [--res 256]
  python3 blender_client.py render --blend SCENE.blend --out PNG [--engine BLENDER_EEVEE]
                                  [--samples 32] [--res 512] [--frame 1] [--timeout 600]
  python3 blender_client.py run --script SCRIPT.py [--blend SCENE.blend] [--outdir DIR]
                               [--timeout 600] [--arg KEY=VALUE ...]

默认自动查找 Blender（BLENDER_BIN 环境变量 → /Applications/Blender.app → PATH）。
退出码：0 成功；2 找不到 Blender；4 Blender 执行失败或超时。
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

CANDIDATES = [
    os.environ.get("BLENDER_BIN"),
    "/Applications/Blender.app/Contents/MacOS/Blender",
    shutil.which("blender"),
]


def fail(message: str, code: int):
    print(message, file=sys.stderr)
    raise SystemExit(code)


def find_blender(explicit: str | None = None) -> str:
    for candidate in ([explicit] if explicit else []) + CANDIDATES:
        if candidate and Path(candidate).exists():
            return candidate
    fail(
        "❌ 找不到 Blender。用 --blender 指定路径，或设置 BLENDER_BIN。\n"
        "   macOS 默认路径：/Applications/Blender.app/Contents/MacOS/Blender",
        2,
    )


def run_blender(cmd: list[str], timeout: float) -> subprocess.CompletedProcess:
    try:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        fail(f"❌ Blender 超时（{timeout}s），已终止。", 4)


def tail(text: str, n: int = 25) -> str:
    lines = [line for line in (text or "").splitlines() if line.strip()]
    return "\n".join(lines[-n:])


def run_expr(blender: str, expr: str, timeout: float = 120) -> subprocess.CompletedProcess:
    return run_blender([blender, "-b", "--factory-startup", "--python-expr", expr], timeout)


def probe(blender: str) -> dict:
    expr = (
        "import bpy, json;"
        "print('DSH_PROBE' + json.dumps({"
        "'version': bpy.app.version_string,"
        "'engines': [e.identifier for e in bpy.types.RenderSettings.bl_rna.properties['engine'].enum_items],"
        "'gpu': bpy.context.preferences.system.gpu_backend"
        "}))"
    )
    result = run_expr(blender, expr, timeout=120)
    for line in (result.stdout or "").splitlines():
        if line.startswith("DSH_PROBE"):
            return json.loads(line[len("DSH_PROBE"):])
    fail("❌ 无法从 Blender 读取环境信息：\n" + tail(result.stdout + result.stderr), 4)


def version_of(blender: str) -> str:
    result = run_blender([blender, "--version"], timeout=60)
    first = (result.stdout or "").splitlines()[0] if result.stdout else ""
    return first.strip() or "?"


def cmd_doctor(args) -> int:
    blender = find_blender(args.blender)
    info = probe(blender)
    print("✅ Blender:", version_of(blender))
    print("   路径:", blender)
    print("   GPU 后端:", info.get("gpu", "?"))
    print("   引擎:", ", ".join(info.get("engines") or []))
    return 0


def resolution(value: str) -> tuple[int, int]:
    match = re.fullmatch(r"(\d+)(?:[xX](\d+))?", value.strip())
    if not match:
        fail(f"❌ 分辨率格式不对：{value}（例：512 或 768x512）", 3)
    w = int(match.group(1))
    h = int(match.group(2) or w)
    return w, h


def run_python_script(blender: str, script_path: Path, blend: str | None, timeout: float, extra: list[str]) -> subprocess.CompletedProcess:
    cmd = [blender, "-b"]
    cmd += [blend] if blend else ["--factory-startup"]
    cmd += ["--python", str(script_path)]
    if extra:
        cmd += ["--"] + extra
    return run_blender(cmd, timeout)


def cmd_smoke(args) -> int:
    blender = find_blender(args.blender)
    outdir = Path(args.outdir).expanduser().resolve()
    outdir.mkdir(parents=True, exist_ok=True)
    out = outdir / "smoke.png"
    w, h = resolution(str(args.res))
    script = f"""
import bpy
scene = bpy.context.scene
scene.render.engine = 'BLENDER_EEVEE'
scene.render.resolution_x = {w}
scene.render.resolution_y = {h}
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = 'PNG'
scene.render.filepath = {str(out)!r}
bpy.ops.render.render(write_still=True)
print('DSH_RENDER_OK')
"""
    started = time.time()
    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False, encoding="utf-8") as tmp:
        tmp.write(script)
        tmp_path = Path(tmp.name)
    try:
        result = run_python_script(blender, tmp_path, None, args.timeout, [])
    finally:
        tmp_path.unlink(missing_ok=True)
    if result.returncode != 0 or not out.exists():
        fail("❌ 冒烟渲染失败：\n" + tail(result.stdout + result.stderr), 4)
    print(f"✅ 冒烟渲染完成（{time.time() - started:.1f}s）")
    print("   ", out)
    return 0


def cmd_render(args) -> int:
    blender = find_blender(args.blender)
    blend = Path(args.blend).expanduser().resolve()
    if not blend.exists():
        fail(f"❌ 找不到 .blend：{blend}", 3)
    out = Path(args.out).expanduser().resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    w, h = resolution(str(args.res))
    script = f"""
import bpy
scene = bpy.context.scene
scene.render.engine = {args.engine!r}
scene.render.resolution_x = {w}
scene.render.resolution_y = {h}
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = 'PNG'
scene.render.filepath = {str(out)!r}
scene.frame_set({int(args.frame)})
try:
    scene.eevee.taa_render_samples = {int(args.samples)}
except Exception:
    pass
bpy.ops.render.render(write_still=True)
print('DSH_RENDER_OK')
"""
    started = time.time()
    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False, encoding="utf-8") as tmp:
        tmp.write(script)
        tmp_path = Path(tmp.name)
    try:
        result = run_python_script(blender, tmp_path, str(blend), args.timeout, [])
    finally:
        tmp_path.unlink(missing_ok=True)
    if result.returncode != 0 or not out.exists():
        fail("❌ 渲染失败：\n" + tail(result.stdout + result.stderr), 4)
    print(f"✅ 渲染完成（{time.time() - started:.1f}s）")
    print("   ", out)
    return 0


def cmd_run(args) -> int:
    blender = find_blender(args.blender)
    script = Path(args.script).expanduser().resolve()
    if not script.exists():
        fail(f"❌ 找不到脚本：{script}", 3)
    blend = str(Path(args.blend).expanduser().resolve()) if args.blend else None
    if blend and not Path(blend).exists():
        fail(f"❌ 找不到 .blend：{blend}", 3)
    if args.outdir:
        os.environ["DSH_BLENDER_OUTDIR"] = str(Path(args.outdir).expanduser().resolve())
    started = time.time()
    result = run_python_script(blender, script, blend, args.timeout, args.arg)
    if result.returncode != 0:
        fail("❌ 脚本执行失败：\n" + tail(result.stdout + result.stderr), 4)
    print(f"✅ 执行完成（{time.time() - started:.1f}s）")
    if args.outdir:
        print("   输出目录:", Path(args.outdir).expanduser().resolve())
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Blender headless 零依赖客户端")
    ap.add_argument("--blender", default=None, help="Blender 可执行文件路径")
    sub = ap.add_subparsers(dest="cmd", required=True)

    sub.add_parser("doctor")

    p_smoke = sub.add_parser("smoke")
    p_smoke.add_argument("--outdir", default="outputs/blender/smoke")
    p_smoke.add_argument("--res", default="256")
    p_smoke.add_argument("--timeout", type=float, default=300)

    p_render = sub.add_parser("render")
    p_render.add_argument("--blend", required=True)
    p_render.add_argument("--out", required=True)
    p_render.add_argument("--engine", default="BLENDER_EEVEE")
    p_render.add_argument("--samples", type=int, default=32)
    p_render.add_argument("--res", default="512")
    p_render.add_argument("--frame", type=int, default=1)
    p_render.add_argument("--timeout", type=float, default=900)

    p_run = sub.add_parser("run")
    p_run.add_argument("--script", required=True)
    p_run.add_argument("--blend", default=None)
    p_run.add_argument("--outdir", default=None)
    p_run.add_argument("--timeout", type=float, default=900)
    p_run.add_argument("--arg", action="append", default=[])

    args = ap.parse_args()
    handlers = {"doctor": cmd_doctor, "smoke": cmd_smoke, "render": cmd_render, "run": cmd_run}
    return handlers[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main())
