"""控制台编码兜底（v1.5.8）。

## 为什么需要这个

README 写着**支持 Windows**（Python 3.9+，官网安装包）。但中文 Windows 的控制台默认代码页是
**cp936（GBK）**，而 GBK **不含** `✅`(U+2705) / `❌`(U+274C) —— 于是第一句
`print("  ✅ ...")` 就抛：

```
UnicodeEncodeError: 'gbk' codec can't encode character '\u2705' in position 2
```

**表现不是"符号显示成方块"，是脚本当场崩、一条断言都没跑。**
本机用 `PYTHONIOENCODING=gbk` 复现过：自检第一条就炸。

## 做法

把 stdout / stderr 切成 UTF-8（`errors="replace"` 兜底）。三件事要说清：

1. `reconfigure` 是 3.7+ 的方法，本产品要求 3.9+，可用
2. 切的是**输出流编码**，不改文件读写（文件本来都是显式 `encoding="utf-8"`）
3. 万一环境不支持（老版本 / 被重定向成非 TextIOWrapper），**静默跳过**——
   宁可符号显示异常，也不能因此让出稿失败

## 为什么放在 import 处而不是 `main()`

有些脚本的主要输出在 `selftest()` 或模块级代码里（比如四份样本的基线打印），
放在 `main()` 会漏掉。放在 import 处是幂等的，被当库导入时也无害。
"""
import sys


def ensure_utf8() -> None:
    """把 stdout/stderr 切到 UTF-8（失败则忽略）。可重复调用。"""
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError, OSError):
            # 老版本没有 reconfigure / 流被重定向成非文本流 —— 跳过，不影响出稿
            pass
