#!/usr/bin/env python3
"""易码文档一致性回归脚本。"""

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


import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def runtime_builtin_count() -> int:
    from yima.解释器 import 解释器

    it = 解释器()
    return sum(1 for v in it.全局环境.记录本.values() if callable(v))


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def assert_count_mark(path: Path, expected: int, patterns: list[str]) -> None:
    text = read_text(path)
    found_any = False
    for pattern in patterns:
        for m in re.finditer(pattern, text):
            found_any = True
            found = int(m.group(1))
            if found != expected:
                raise AssertionError(
                    f"{path} 数量标注不一致：写的是 {found}，实际应为 {expected}。"
                )
    if not found_any:
        joined = " / ".join(patterns)
        raise AssertionError(f"{path} 未找到数量标注（模式：{joined}）。")


def assert_no_legacy_alias_claim(path: Path) -> None:
    text = read_text(path)
    banned = [
        "兼容别名",
        "排列`（`新列表`兼容别名）",
        "是一份清单`（`新列表`兼容别名）",
    ]
    for needle in banned:
        if needle in text:
            raise AssertionError(f"{path} 仍包含过期兼容描述：{needle}")


def main() -> int:
    expected = runtime_builtin_count()

    # 1) 检查核心文档中的函数数量标注
    assert_count_mark(
        ROOT / "README.md",
        expected,
        [r"内置函数清单（(\d+) 个）"],
    )
    assert_count_mark(
        ROOT / "文档/速查表.md",
        expected,
        [r"内置函数清单（(\d+) 个）"],
    )
    assert_count_mark(
        ROOT / "文档/开发指南.md",
        expected,
        [r"内置函数清单（(\d+) 个）"],
    )
    assert_count_mark(
        ROOT / "文档/语言规范.md",
        expected,
        [r"全量清单（(\d+) 个）"],
    )

    # 2) 防止旧兼容别名描述回流
    assert_no_legacy_alias_claim(ROOT / "文档/语言规范.md")

    print(f"[OK] 文档一致性通过（内置函数 {expected} 个）")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as e:
        safe = str(e).encode("unicode_escape", errors="replace").decode("ascii", errors="replace")
        print(f"[FAIL] 文档一致性失败: {safe}")
        raise SystemExit(1)
