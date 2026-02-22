#!/usr/bin/env python3
"""易码最小回归脚本。

用途：
1. 编译检查核心 Python 文件；
2. 运行关键示例；
3. 验证本轮关键语义（除零报错、严格局部作用域开关、模块导入缓存）。
"""

from __future__ import annotations

import os
import locale
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PY = sys.executable
SYS_ENCODING = locale.getpreferredencoding(False) or "utf-8"


def run_cmd(args: list[str], *, env: dict[str, str] | None = None) -> str:
    proc = subprocess.run(
        args,
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        encoding=SYS_ENCODING,
        errors="replace",
    )
    output = (proc.stdout or "") + (proc.stderr or "")
    if proc.returncode != 0:
        raise RuntimeError(f"命令失败: {' '.join(args)}\n{output}")
    return output


def assert_contains(text: str, needle: str, label: str) -> None:
    if needle not in text:
        safe = text.encode("unicode_escape", errors="replace").decode("ascii", errors="replace")
        raise AssertionError(f"{label} 失败：未找到【{needle}】\\n实际输出(转义)：\\n{safe}")


def compile_check() -> None:
    files = [
        "易码.py",
        "易码编辑器.py",
        "易码打包工具.py",
        "yima/词法分析.py",
        "yima/语法分析.py",
        "yima/语法树.py",
        "yima/解释器.py",
        "yima/环境.py",
        "yima/错误.py",
        "yima/信号.py",
    ]
    run_cmd([PY, "-m", "py_compile", *files])
    print("[OK] 编译检查通过")


def sample_check() -> None:
    samples = [
        "示例/M10综合测试.ym",
        "示例/M11模块化测试.ym",
        "示例/M12容错测试.ym",
    ]
    for sample in samples:
        run_cmd([PY, "易码.py", sample])
        print(f"[OK] 示例通过: {sample}")


def semantic_check() -> None:
    out = run_cmd([PY, "-c", "from 易码 import 执行源码; 执行源码('显示 1 / 0', interactive=False)"])
    assert_contains(out, "除数不能为 0", "除零报错")
    print("[OK] 除零报错语义通过")

    strict_env = dict(os.environ)
    strict_env["YIMA_STRICT_SCOPE"] = "1"
    out = run_cmd(
        [
            PY,
            "-c",
            "from 易码 import 执行源码; 执行源码('x = 1\\n功能 f()\\n    x = 2\\nf()\\n显示 x', interactive=False)",
        ],
        env=strict_env,
    )
    assert_contains(out, "1", "严格局部作用域")
    print("[OK] 严格局部作用域开关通过")

    with tempfile.TemporaryDirectory(dir=ROOT) as td:
        tdir = Path(td)
        mod = tdir / "_cache_mod.ym"
        main = tdir / "_cache_main.ym"
        mod.write_text('显示 "loaded"\n值 = 1\n', encoding="utf-8")
        main.write_text('引入 "_cache_mod" 叫做 A\n引入 "_cache_mod" 叫做 B\n显示 A.值 + B.值\n', encoding="utf-8")

        out = run_cmd([PY, "易码.py", str(main)])
        if out.count("loaded") != 1:
            raise AssertionError(f"模块缓存验证失败：期望 loaded 出现 1 次，实际 {out.count('loaded')} 次。\n{out}")
        assert_contains(out, "2", "模块缓存结果")
    print("[OK] 模块缓存语义通过")


def error_regression_check() -> None:
    out = run_cmd([PY, "scripts/run_error_regression.py"])
    assert_contains(out, "错误体验回归完成：全部通过", "错误体验回归")
    print("[OK] 错误体验回归通过")


def main() -> int:
    print("=== 易码回归开始 ===")
    compile_check()
    sample_check()
    semantic_check()
    error_regression_check()
    print("=== 易码回归完成：全部通过 ===")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as e:
        safe = str(e).encode("unicode_escape", errors="replace").decode("ascii", errors="replace")
        print(f"[FAIL] 回归失败: {safe}")
        raise SystemExit(1)
