#!/usr/bin/env python3
"""易码错误体验回归脚本（高频错误场景）。"""

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


import locale
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PY = sys.executable
SYS_ENCODING = locale.getpreferredencoding(False) or "utf-8"


def decode_output(raw: bytes) -> str:
    for enc in ("utf-8", SYS_ENCODING):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="replace")


def run_yima_code(code: str) -> str:
    with tempfile.NamedTemporaryFile("w", suffix=".ym", encoding="utf-8", delete=False, dir=ROOT) as f:
        f.write(code)
        path = Path(f.name)
    try:
        proc = subprocess.run(
            [PY, "易码.py", str(path)],
            cwd=ROOT,
            capture_output=True,
            text=False,
        )
        return decode_output(proc.stdout or b"") + decode_output(proc.stderr or b"")
    finally:
        try:
            path.unlink(missing_ok=True)
        except Exception:
            pass


def assert_has_error_format(output: str, label: str) -> None:
    if "原因：" not in output:
        safe = output.encode("unicode_escape", errors="replace").decode("ascii", errors="replace")
        raise AssertionError(f"{label} 缺少【原因】字段。\n{safe}")
    if "建议：" not in output:
        safe = output.encode("unicode_escape", errors="replace").decode("ascii", errors="replace")
        raise AssertionError(f"{label} 缺少【建议】字段。\n{safe}")


def assert_contains(output: str, needle: str, label: str) -> None:
    if needle not in output:
        safe = output.encode("unicode_escape", errors="replace").decode("ascii", errors="replace")
        raise AssertionError(f"{label} 未命中关键字【{needle}】。\n{safe}")


def main() -> int:
    cases: list[tuple[str, str, list[str]]] = [
        ("词法-非法字符", "显示 1 @ 2\n", ["词法错误", "不认识这个符号"]),
        ("词法-字符串未闭合", '显示 "你好\n', ["词法错误", "字符串没有闭合"]),
        ("词法-缩进不一致", "如果 对 就\n    显示 1\n  显示 2\n", ["词法错误", "缩进不一致"]),
        ("语法-代码块缺缩进", "如果 对 就\n显示 1\n", ["语法错误", "需要缩进代码块"]),
        ("语法-列表缺逗号", "a = [1 2]\n", ["语法错误", "逗号分隔"]),
        ("语法-字典缺逗号", 'a = {"x": 1 "y": 2}\n', ["语法错误", "逗号分隔"]),
        ("语法-右括号缺失", "显示 (1 + 2\n", ["语法错误", "缺少右括号"]),
        ("语法-表达式起始非法", "显示 )\n", ["语法错误", "需要一个值或表达式"]),
        ("运行-未定义名称", "显示 未定义变量\n", ["运行错误", "未定义名称"]),
        ("运行-除零", "显示 1 / 0\n", ["运行错误", "除数不能为 0"]),
        ("运行-函数参数数量", "功能 加(a, b)\n    返回 a + b\n显示 加(1)\n", ["运行错误", "需要 2 个参数"]),
        ("运行-调用非函数", "a = 1\na()\n", ["运行错误", "不可调用"]),
        ("运行-遍历非可迭代", "遍历 123 里的每一个 叫做 x\n    显示 x\n", ["运行错误", "不可遍历"]),
        ("运行-重复次数非整数", "重复 3.5 次\n    显示 1\n", ["运行错误", "重复次数必须是整数"]),
        ("运行-索引越界", "a = [1]\n显示 a[2]\n", ["运行错误", "索引【2】不存在或越界"]),
        ("运行-不支持索引读取", "a = 1\n显示 a[0]\n", ["运行错误", "不支持方括号取值"]),
        ("运行-模块不存在", '引入 "不存在模块" 叫做 坏模块\n', ["运行错误", "找不到模块"]),
        ("语法-旧引入写法停用", '用 "math" 中的 不存在名称\n', ["语法错误", "已停用"]),
        ("运行-它的超出图纸", "显示 它的 名字\n", ["运行错误", "只能在图纸内部"]),
        (
            "运行-造一个参数不匹配",
            "定义图纸 玩家(名字, 血量)\n"
            "    它的 名字 = 名字\n"
            "    它的 血量 = 血量\n"
            "主角 = 造一个 玩家(\"小白\")\n",
            ["运行错误", "造一个", "参数数量不匹配"],
        ),
        (
            "运行-造一个图纸不存在",
            "主角 = 造一个 不存在图纸(1)\n",
            ["运行错误", "找不到图纸"],
        ),
        ("运行-尝试无捕获不吞错", "尝试\n    显示 1 / 0\n显示 1\n", ["运行错误", "除数不能为 0"]),
    ]

    print("=== 错误体验回归开始 ===")
    for idx, (label, code, needles) in enumerate(cases, start=1):
        out = run_yima_code(code)
        for needle in needles:
            assert_contains(out, needle, label)
        assert_has_error_format(out, label)
        print(f"[OK] {idx:02d}. {label}")
    print("=== 错误体验回归完成：全部通过 ===")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as e:
        safe = str(e).encode("unicode_escape", errors="replace").decode("ascii", errors="replace")
        print(f"[FAIL] 错误体验回归失败: {safe}")
        raise SystemExit(1)

