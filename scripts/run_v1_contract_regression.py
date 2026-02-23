#!/usr/bin/env python3
"""易码 v1 契约回归脚本。"""

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


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def check_version() -> str:
    version_file = ROOT / "VERSION"
    if not version_file.exists():
        raise AssertionError("缺少 VERSION 文件。")
    version = read_text(version_file).strip()
    if not re.fullmatch(r"1\.\d+\.\d+", version):
        raise AssertionError(f"VERSION 不符合 v1 规则：{version}")
    return version


def check_keyword_contract() -> None:
    from yima.词法分析 import 多字词典

    keyword_set = set(多字词典.keys())
    required = {
        "显示",
        "输入",
        "功能",
        "返回",
        "引入",
        "叫做",
        "如果",
        "否则如果",
        "不然",
        "尝试",
        "如果出错",
        "当",
        "的时候",
        "重复",
        "次",
        "遍历",
        "里的每一个",
        "停下",
        "略过",
        "定义图纸",
        "造一个",
        "它的",
        "并且",
        "或者",
        "取反",
        "对",
        "错",
        "空",
    }
    missing = sorted(required - keyword_set)
    if missing:
        raise AssertionError(f"v1 关键字缺失：{', '.join(missing)}")

    # 历史写法已废弃，不应再回流到词法入口
    banned_legacy = {"排列", "是一份清单", "函数", "类"}
    leaked = sorted(banned_legacy & keyword_set)
    if leaked:
        raise AssertionError(f"检测到历史写法回流到词法层：{', '.join(leaked)}")


def check_docs_contract(version: str) -> None:
    readme = read_text(ROOT / "README.md")
    lang_spec = read_text(ROOT / "文档/语言规范.md")
    freeze_doc = read_text(ROOT / "文档/v1.0冻结与回归策略.md")

    if ("v1.0" not in readme) or ("冻结" not in readme):
        raise AssertionError("README 缺少 v1.0 冻结说明。")
    if "当前版本不维护历史同义词兼容层" not in lang_spec:
        raise AssertionError("语言规范缺少“历史同义词不再维护”声明。")
    if version not in freeze_doc and "1.0" not in freeze_doc:
        raise AssertionError("冻结文档缺少版本描述。")


def main() -> int:
    version = check_version()
    check_keyword_contract()
    check_docs_contract(version)
    print(f"[OK] v1 契约回归通过（VERSION={version}）")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as e:
        safe = str(e).encode("unicode_escape", errors="replace").decode("ascii", errors="replace")
        print(f"[FAIL] v1 契约回归失败: {safe}")
        raise SystemExit(1)
