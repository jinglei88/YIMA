#!/usr/bin/env python3
"""易码最小回归脚本。

用途：
1. 编译检查核心 Python 文件；
2. 运行关键示例；
3. 验证本轮关键语义（除零报错、严格局部作用域开关、模块导入缓存）；
4. 验证 CLI 契约（版本号、-c 执行、严格模式参数覆盖）。
"""

from __future__ import annotations

#
# Ownership Marker (Open Source Prep)
# Author: 景磊 (Jing Lei)
# Copyright (c) 2026 景磊
# Project: 易码 / Yima
# Marker-ID: YIMA-JINGLEI-CORE

__author__ = "景磊"
__copyright__ = "Copyright (c) 2026 景磊"
__marker_id__ = "YIMA-JINGLEI-CORE"


import os
import locale
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PY = sys.executable
SYS_ENCODING = locale.getpreferredencoding(False) or "utf-8"
EXIT_FILE_ERROR = 3
EXIT_LEX_ERROR = 10
EXIT_PARSE_ERROR = 11
EXIT_RUNTIME_ERROR = 12


def run_cmd(
    args: list[str],
    *,
    env: dict[str, str] | None = None,
    cwd: Path | None = None,
) -> str:
    merged_env = dict(os.environ)
    merged_env.setdefault("PYTHONDONTWRITEBYTECODE", "1")
    if env:
        merged_env.update(env)
    proc = subprocess.run(
        args,
        cwd=cwd or ROOT,
        env=merged_env,
        capture_output=True,
        text=True,
        encoding=SYS_ENCODING,
        errors="replace",
    )
    output = (proc.stdout or "") + (proc.stderr or "")
    if proc.returncode != 0:
        raise RuntimeError(f"命令失败: {' '.join(args)}\n{output}")
    return output


def run_cmd_raw(
    args: list[str],
    *,
    env: dict[str, str] | None = None,
    cwd: Path | None = None,
) -> tuple[int, str]:
    merged_env = dict(os.environ)
    merged_env.setdefault("PYTHONDONTWRITEBYTECODE", "1")
    if env:
        merged_env.update(env)
    proc = subprocess.run(
        args,
        cwd=cwd or ROOT,
        env=merged_env,
        capture_output=True,
        text=True,
        encoding=SYS_ENCODING,
        errors="replace",
    )
    output = (proc.stdout or "") + (proc.stderr or "")
    return proc.returncode, output


def assert_contains(text: str, needle: str, label: str) -> None:
    if needle not in text:
        safe = text.encode("unicode_escape", errors="replace").decode("ascii", errors="replace")
        raise AssertionError(f"{label} 失败：未找到【{needle}】\\n实际输出(转义)：\\n{safe}")


def _assert_rc(actual: int, expected: int, label: str) -> None:
    if actual != expected:
        raise AssertionError(f"{label} 失败：期望退出码 {expected}，实际 {actual}")


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
        "yima/editor_cheatsheet_flow.py",
    ]
    with tempfile.TemporaryDirectory(prefix="yima_pycache_", dir=ROOT) as td:
        run_cmd([PY, "-m", "py_compile", *files], env={"PYTHONPYCACHEPREFIX": td})
    print("[OK] 编译检查通过")


def sample_check() -> None:
    samples = [
        "示例/M10综合测试.ym",
        "示例/M11模块化测试.ym",
        "示例/M12容错测试.ym",
        "示例/经典案例_图纸对象入门.ym",
    ]
    for sample in samples:
        run_cmd([PY, "易码.py", sample])
        print(f"[OK] 示例通过: {sample}")

    # 该用例会基于“当前工作目录”创建数据库文件，放到临时目录执行以避免污染仓库。
    auth_sample = ROOT / "示例/经典案例_注册登录_自动测试.ym"
    cli_entry = ROOT / "易码.py"
    with tempfile.TemporaryDirectory(prefix="yima_reg_auth_", dir=ROOT) as td:
        run_cmd([PY, str(cli_entry), str(auth_sample)], cwd=Path(td))
    print("[OK] 示例通过: 示例/经典案例_注册登录_自动测试.ym（隔离目录）")


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

    with tempfile.TemporaryDirectory(dir=ROOT) as td:
        tdir = Path(td)
        mod = tdir / "_scope_mod.ym"
        main = tdir / "_scope_main.ym"
        mod.write_text(
            "计数 = 0\n"
            "功能 增加一次()\n"
            "    计数 = 计数 + 1\n"
            "功能 当前计数()\n"
            "    返回 计数\n",
            encoding="utf-8",
        )
        main.write_text(
            '引入 "_scope_mod" 叫做 库\n'
            "库.增加一次()\n"
            "库.增加一次()\n"
            '引入 "_scope_mod" 叫做 当前计数\n'
            "显示 当前计数()\n",
            encoding="utf-8",
        )

        out = run_cmd([PY, "易码.py", str(main)])
        assert_contains(out, "2", "模块函数作用域与统一引入")
    print("[OK] 模块函数作用域与统一引入通过")

    out = run_cmd(
        [
            PY,
            "-c",
            (
                "from 易码 import 执行源码; "
                "执行源码('功能 继续探索()\\n    返回 \"ok\"\\n显示 \"按钮：【【继续探索】】\"\\n显示 \"按钮2：\\\\【继续探索\\\\】\"', interactive=False)"
            ),
        ]
    )
    assert_contains(out, "按钮：【继续探索】", "模板字面量转义")
    assert_contains(out, "按钮2：【继续探索】", "模板字面量反斜杠转义")
    print("[OK] 模板字面量转义通过")


def cli_contract_check() -> None:
    version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()

    out = run_cmd([PY, "易码.py", "--help"])
    assert_contains(out, "Examples /", "CLI --help 示例块")
    assert_contains(out, "--strict-scope", "CLI --help 参数列表")

    out = run_cmd([PY, "易码.py", "--version"])
    assert_contains(out, version, "CLI 版本号")

    out = run_cmd([PY, "易码.py", "-c", "显示 1 + 1"])
    assert_contains(out, "2", "CLI -c 执行")

    strict_env = dict(os.environ)
    strict_env["YIMA_STRICT_SCOPE"] = "0"
    out = run_cmd(
        [
            PY,
            "易码.py",
            "--strict-scope",
            "-c",
            "x = 1\n功能 f()\n    x = 2\nf()\n显示 x",
        ],
        env=strict_env,
    )
    assert_contains(out, "1", "CLI --strict-scope 覆盖环境变量")

    strict_env["YIMA_STRICT_SCOPE"] = "1"
    out = run_cmd(
        [
            PY,
            "易码.py",
            "--no-strict-scope",
            "-c",
            "x = 1\n功能 f()\n    x = 2\nf()\n显示 x",
        ],
        env=strict_env,
    )
    assert_contains(out, "2", "CLI --no-strict-scope 覆盖环境变量")

    rc, _out = run_cmd_raw([PY, "易码.py", "-c", "显示 @"])
    _assert_rc(rc, EXIT_LEX_ERROR, "CLI 词法错误退出码")

    rc, _out = run_cmd_raw([PY, "易码.py", "-c", "显示 (1 + 2"])
    _assert_rc(rc, EXIT_PARSE_ERROR, "CLI 语法错误退出码")

    rc, _out = run_cmd_raw([PY, "易码.py", "-c", "显示 1 / 0"])
    _assert_rc(rc, EXIT_RUNTIME_ERROR, "CLI 运行错误退出码")

    rc, _out = run_cmd_raw([PY, "易码.py", "_definitely_not_exists_12345.ym"])
    _assert_rc(rc, EXIT_FILE_ERROR, "CLI 文件错误退出码")
    print("[OK] CLI 契约回归通过")


def error_regression_check() -> None:
    out = run_cmd([PY, "scripts/run_error_regression.py"])
    assert_contains(out, "错误体验回归完成：全部通过", "错误体验回归")
    print("[OK] 错误体验回归通过")


def editor_logic_regression_check() -> None:
    out = run_cmd([PY, "scripts/run_editor_logic_regression.py"])
    assert_contains(out, "编辑器逻辑回归完成：全部通过", "编辑器逻辑回归")
    print("[OK] 编辑器逻辑回归通过")


def packaging_regression_check() -> None:
    out = run_cmd([PY, "scripts/run_packaging_regression.py"])
    assert_contains(out, "打包专项回归完成：全部通过", "打包专项回归")
    print("[OK] 打包专项回归通过")


def main() -> int:
    print("=== 易码回归开始 ===")
    compile_check()
    sample_check()
    semantic_check()
    cli_contract_check()
    error_regression_check()
    editor_logic_regression_check()
    packaging_regression_check()
    print("=== 易码回归完成：全部通过 ===")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as e:
        safe = str(e).encode("unicode_escape", errors="replace").decode("ascii", errors="replace")
        print(f"[FAIL] 回归失败: {safe}")
        raise SystemExit(1)

