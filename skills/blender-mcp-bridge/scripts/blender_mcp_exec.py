#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
blender_mcp_exec.py — 经 Blender MCP 在运行中的 Blender 里执行任意 bpy 代码
=========================================================================
随包分发版（v1.3.3）。零第三方依赖，只用标准库，macOS / Linux / Windows 通用。

命令面已对上游核实（PyPI mcp-for-blender 2.2.2 的 --help 实测）：
  · `--host` / `--port` 真实存在，且帮助原文写「overrides BLENDER_HOST/BLENDER_PORT」
    → 本脚本显式传 --port 即可，**不需要**再给子进程注入 BLENDER_PORT 环境变量。
  · `install-addon` / `addon-paths` / `setup` / `update` 四个子命令真实存在。

前置：
  1. Blender 已安装并**开着**（建议 5.2 LTS）
  2. 已装 uv（含 uvx）：`pip install uv` 或见 https://docs.astral.sh/uv/
  3. Blender 内 N 面板 → MCP for Blender → **Start MCP Server**（默认端口 9876）
     插件没装/版本过旧 → 先跑 `uvx mcp-for-blender install-addon`

用法：
  python  blender_mcp_exec.py path/to/script.py
  echo "import bpy; print(len(bpy.data.objects))" | python blender_mcp_exec.py
  python  blender_mcp_exec.py script.py --timeout 300     # 重场景/渲染给足时间
  python  blender_mcp_exec.py script.py --port 9877       # Blender 插件换了端口

退出码：0 有输出 / 1 连接或执行失败 / 2 用法错误（stderr 给原因，绝不静默挂死）
  归 2 的具体情形：脚本路径不存在、BLENDER_PORT 填错（非整数 / 空串 / 超 1-65535）、
  找不到 uvx —— 凡是「还没开始连 Blender 就已经确定跑不通」的都算用法错误，方便脚本判错。

--timeout 是**硬超时**：到点无条件退出并给诊断，不等子进程自然返回。
"""
import argparse
import json
import os
import queue
import shutil
import signal
import subprocess
import sys
import threading
import time

DEFAULT_TIMEOUT = 90
DEFAULT_PORT = 9876
# 优先用新包名；blender-mcp 是官方兼容 wrapper，仍可用但会往 stderr 打迁移提示
PKG = "mcp-for-blender"

DIAG = (
    "  1) Blender 是否开着？\n"
    "  2) N 面板 → MCP for Blender → 是否点了 Start MCP Server？\n"
    "  3) 先问一句 `get_addon_status`——它一句话就能说清插件在不在、版本对不对；\n"
    "     版本不一致就 `uvx mcp-for-blender install-addon`，再到 Preferences → Add-ons\n"
    "     里禁用再启用 'Interface: MCP for Blender'\n"
    "  4) 若你改过端口，用 --port 指定实际端口（脚本当前用 {port}）\n"
    "  5) 插件装在哪个目录：`uvx mcp-for-blender addon-paths`"
)


def find_uvx():
    """按 PATH → 常见安装位 → 报错。不写死任何一台机器的路径。"""
    p = shutil.which("uvx")
    if p:
        return p
    cands = [
        os.path.expanduser("~/.local/bin/uvx"),
        os.path.expanduser("~/.cargo/bin/uvx"),
        "/opt/homebrew/bin/uvx",
        "/usr/local/bin/uvx",
        os.path.expanduser("~/AppData/Roaming/Python/Scripts/uvx.exe"),
        os.path.expanduser("~/AppData/Local/Programs/uv/uvx.exe"),
    ]
    for c in cands:
        if os.path.isfile(c):
            return c
    # 走 stderr + 退出码 2（用法/前置条件错），与 docstring 声明的退出码一致。
    # 旧版 sys.exit("字符串") 实际返回 1，买家按 docstring 判码会判错。
    sys.stderr.write(
        "❌ 找不到 uvx。请先安装 uv：\n"
        "   macOS/Linux:  curl -LsSf https://astral.sh/uv/install.sh | sh\n"
        "   Windows:      powershell -c \"irm https://astral.sh/uv/install.ps1 | iex\"\n"
        "   或 pip install uv\n"
        "装完确认 `uvx --version` 可用，再重跑本脚本。\n"
    )
    sys.exit(2)


def _port_from_env():
    """读 BLENDER_PORT 并校验；不设该变量时返回 DEFAULT_PORT。

    v1.3.1 的缺陷：`default=int(os.environ.get("BLENDER_PORT", DEFAULT_PORT))`
    在 argparse 构造期就 int()，环境变量为 `9876abc` 或空串时用户直接吃到
    Python traceback（看不出是自己环境变量填错）。这里改成
    「先取值 → 校验 → 人话报错 + exit 2」。

    刻意**不静默回退默认端口**：静默回退会让用户以为连上了 9876，
    实际 Blender 开在别的端口，症状变成「连不上」而不是「变量填错」，更难查。
    """
    raw = os.environ.get("BLENDER_PORT")
    if raw is None:
        return DEFAULT_PORT
    hint = ("   怎么办：要么删掉这个环境变量（回到默认端口 %d），"
            "要么把它设成正确的整数端口号。\n" % DEFAULT_PORT)
    s = raw.strip()
    if not s:
        sys.stderr.write(
            "❌ 环境变量 BLENDER_PORT 是空字符串，不是端口号。\n" + hint)
        sys.exit(2)
    try:
        v = int(s)
    except ValueError:
        sys.stderr.write(
            "❌ 环境变量 BLENDER_PORT=%r 不是整数。\n" % raw + hint)
        sys.exit(2)
    if not 1 <= v <= 65535:
        sys.stderr.write(
            "❌ 环境变量 BLENDER_PORT=%r 超出端口范围（1-65535）。\n" % raw + hint)
        sys.exit(2)
    return v


class _Reader(threading.Thread):
    """把 stdout 逐行读进队列，让主线程能带超时地等。

    readline 本身是阻塞调用，直接在主线程 readline 会让 --timeout 形同虚设——
    这正是 v1.2 的缺陷：Blender 卡死时脚本无限挂住，外部强杀才结束。
    """

    def __init__(self, stream):
        super().__init__(daemon=True)
        self.stream = stream
        self.q = queue.Queue()

    def run(self):
        try:
            for line in self.stream:
                self.q.put(line)
        except Exception:
            pass
        finally:
            self.q.put(None)  # 哨兵：流结束


class _ErrReader(threading.Thread):
    """stderr 同样必须异步读。若在主线程 read() 到 EOF，而孙进程还握着管道，
    就会二次挂死（v1.3 开发期实测踩到）。这里只累积，永不阻塞主线程。"""

    def __init__(self, stream, limit=400):
        super().__init__(daemon=True)
        self.stream = stream
        self.limit = limit
        self.buf = ""

    def run(self):
        try:
            for line in self.stream:
                if len(self.buf) < self.limit:
                    self.buf += line
        except Exception:
            pass


def _stop(p):
    """整组杀掉。uvx 会再起子进程，只 terminate 直接子进程不足以断开管道。

    分平台：
      · POSIX：run_code 用 start_new_session=True 让 uvx 自成一个进程组，
        这里 killpg 整组收掉，孙进程不会漏。
      · Windows：没有进程组可杀。`p.kill()` 只结束 uvx 本身，uvx 再起的
        python / mcp 子进程会变孤儿并继续握着管道 → 优先 `taskkill /T /F`
        （/T 连子孙进程树一起杀），失败或进程已退才退回 p.kill()。
    """
    try:
        if os.name == "nt":
            try:
                subprocess.run(
                    ["taskkill", "/T", "/F", "/PID", str(p.pid)],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                    timeout=10, check=False,
                )
            except Exception:
                pass
            if p.poll() is None:
                p.kill()
            return
        if hasattr(os, "killpg"):
            os.killpg(os.getpgid(p.pid), signal.SIGKILL)
        else:
            p.kill()
    except Exception:
        try:
            p.kill()
        except Exception:
            pass


def run_code(code, timeout=DEFAULT_TIMEOUT, port=DEFAULT_PORT):
    cmd = [find_uvx(), PKG, "--port", str(port)]
    kw = {}
    if os.name == "posix":
        kw["start_new_session"] = True  # 让 killpg 能收掉 uvx 的整组子进程
    try:
        p = subprocess.Popen(
            cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True, encoding="utf-8", errors="replace", bufsize=1, **kw,
        )
    except FileNotFoundError as e:
        return "ERROR: 无法启动 uvx " + PKG + " → " + str(e), 1

    reader = _Reader(p.stdout)
    ereader = _ErrReader(p.stderr)
    reader.start()
    ereader.start()

    def send(msg):
        try:
            p.stdin.write(json.dumps(msg) + "\n")
            p.stdin.flush()
        except Exception:
            pass

    def read(deadline):
        """硬超时：到点返回 'TIMEOUT'，不等阻塞读自然返回。"""
        while True:
            remain = deadline - time.time()
            if remain <= 0:
                return "TIMEOUT"
            try:
                line = reader.q.get(timeout=remain)
            except queue.Empty:
                return "TIMEOUT"
            if line is None:
                return None  # 子进程已退出
            line = line.strip()
            if not line:
                continue
            try:
                return json.loads(line)
            except Exception:
                continue  # 日志行 / 迁移提示，跳过继续等

    def err_text():
        _stop(p)
        ereader.join(timeout=1.0)
        return (ereader.buf or "").strip()

    deadline = time.time() + timeout

    send({"jsonrpc": "2.0", "id": 1, "method": "initialize",
          "params": {"protocolVersion": "2024-11-05", "capabilities": {},
                     "clientInfo": {"name": "blender-studio-exec", "version": "1.3.3"}}})
    init = read(deadline)
    if init is None or init == "TIMEOUT":
        err = err_text()
        return (f"CONNECT-FAIL（{timeout}s 内没完成 MCP 握手）。逐条诊断：\n"
                + DIAG.format(port=port) + f"\nstderr: {err}"), 1
    if isinstance(init, dict) and "error" in init:
        err_text()
        return "ERROR: 握手失败 → " + json.dumps(init["error"], ensure_ascii=False), 1

    server = (init.get("result", {}).get("serverInfo", {}) or {})
    send({"jsonrpc": "2.0", "method": "notifications/initialized"})
    send({"jsonrpc": "2.0", "id": 2, "method": "tools/call",
          "params": {"name": "execute_blender_code", "arguments": {"code": code}}})
    res = read(deadline)

    if res == "TIMEOUT":
        err = err_text()
        return (f"TIMEOUT（硬超时 {timeout}s，已强制退出）。握手成功"
                f"（{server.get('name', '?')} {server.get('version', '?')}），"
                f"但 execute_blender_code 没在时限内返回。\n"
                f"常见原因：Blender 主线程被模态框/大渲染阻塞、插件服务端卡死，\n"
                f"或脚本本身跑得久 → 渲染/模拟/大场景请加 --timeout 300 以上。\n"
                + DIAG.format(port=port) + f"\nstderr: {err}"), 1
    if res is None:
        err = err_text()
        return ("CONNECT-FAIL：服务进程提前退出。\n" + DIAG.format(port=port)
                + f"\nstderr: {err}"), 1
    if "error" in res:
        err_text()
        return "ERROR: " + json.dumps(res["error"], ensure_ascii=False), 1

    txt = ""
    for part in res.get("result", {}).get("content", []):
        if part.get("type") == "text":
            txt += part.get("text", "")
    err_text()

    # MCP 把「连不上 Blender」包装成正常文本返回，rc 会被误判为 0。
    # 买家看到绿色的“跑完了”其实一次都没连上——必须翻成失败。
    low = txt.lower()
    if "could not connect to blender" in low or low.startswith("error executing code"):
        return (f"CONNECT-FAIL：服务起来了，但连不上 Blender。\n"
                f"服务端原话：{txt.strip()[:300]}\n" + DIAG.format(port=port)), 1
    return txt, 0


def main():
    ap = argparse.ArgumentParser(
        description="经 Blender MCP 在运行中的 Blender 内执行 bpy 代码")
    ap.add_argument("script", nargs="?", help="要执行的 .py 文件；省略则从 stdin 读")
    ap.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT,
                    help=f"硬超时秒数（默认 {DEFAULT_TIMEOUT}；渲染/模拟给 300+）")
    ap.add_argument("--port", type=int, default=None,
                    help=f"Blender MCP 端口（默认 {DEFAULT_PORT}；可用 BLENDER_PORT 环境变量覆盖）")
    a = ap.parse_args()
    # 显式 --port 优先；否则才去校验 BLENDER_PORT（校验失败 → 人话 + exit 2，不是 traceback）
    port = a.port if a.port is not None else _port_from_env()

    if a.script and os.path.exists(a.script):
        with open(a.script, encoding="utf-8") as f:
            code = f.read()
    elif a.script:
        # 走 stderr + 退出码 2（用法错误），与 docstring 一致；旧版 sys.exit(str) 实际返回 1
        sys.stderr.write(
            "❌ 文件不存在: %s\n"
            "   检查路径拼写；或者省略脚本参数，改用 stdin 传代码：\n"
            "   echo \"import bpy; print(len(bpy.data.objects))\" | python blender_mcp_exec.py\n"
            % a.script)
        return 2
    else:
        if sys.stdin.isatty():
            ap.print_help()
            return 2
        code = sys.stdin.read()

    out, rc = run_code(code, a.timeout, port)
    print(out)
    return rc


if __name__ == "__main__":
    sys.exit(main())
