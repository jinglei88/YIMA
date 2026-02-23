#!/usr/bin/env python3
"""易码编辑器逻辑回归（无 GUI 交互）。"""

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

import sys
import tempfile
from pathlib import Path
from types import MethodType

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from 易码编辑器 import 易码IDE
from yima.词法分析 import 词法分析器
from yima.语法分析 import 语法分析器


def _assert_true(cond: bool, msg: str) -> None:
    if not cond:
        raise AssertionError(msg)


def _new_harness(workspace: Path):
    """构造轻量 self 对象，复用编辑器核心逻辑方法。"""

    class Harness:
        pass

    h = Harness()
    h.workspace_dir = str(workspace)
    h.tabs_data = {}
    h.autocomplete_fuzzy_enabled = False
    h.builtin_words = 易码IDE._builtin_word_catalog(h)
    h._semantic_module_cache = {}

    # 自动补全 / 导出预检
    h._builtin_module_exports = MethodType(易码IDE._builtin_module_exports, h)
    h._提取引入别名映射 = MethodType(易码IDE._提取引入别名映射, h)
    h._autocomplete_match = MethodType(易码IDE._autocomplete_match, h)
    h._autocomplete_source_priority = MethodType(易码IDE._autocomplete_source_priority, h)
    h._sanitize_export_name = MethodType(易码IDE._sanitize_export_name, h)
    h._导出前置检查 = MethodType(易码IDE._导出前置检查, h)
    h._缩略问题消息 = MethodType(易码IDE._缩略问题消息, h)
    h._格式化问题列表项 = MethodType(易码IDE._格式化问题列表项, h)
    h._目录在工作区内 = MethodType(易码IDE._目录在工作区内, h)
    h._就近主程序入口 = MethodType(易码IDE._就近主程序入口, h)
    h._解析导出入口 = MethodType(易码IDE._解析导出入口, h)

    # 语义分析
    h._默认模块别名 = MethodType(易码IDE._默认模块别名, h)
    h._收集块声明 = MethodType(易码IDE._收集块声明, h)
    h._语义模块搜索路径 = MethodType(易码IDE._语义模块搜索路径, h)
    h._语义定位易码模块 = MethodType(易码IDE._语义定位易码模块, h)
    h._语义正则兜底导出 = MethodType(易码IDE._语义正则兜底导出, h)
    h._语义读取模块导出 = MethodType(易码IDE._语义读取模块导出, h)
    h._语义读取模块导出详情 = MethodType(易码IDE._语义读取模块导出详情, h)
    h._语义读取模块导出签名 = MethodType(易码IDE._语义读取模块导出签名, h)
    h._格式化参数签名 = MethodType(易码IDE._格式化参数签名, h)
    h._语义分析 = MethodType(易码IDE._语义分析, h)
    return h


def _semantic_warnings(h, code: str):
    ast = 语法分析器(词法分析器(code).分析()).解析()
    return h._语义分析(ast)


def check_autocomplete_rules() -> None:
    h = _new_harness(ROOT)

    _assert_true(h._autocomplete_match("系统工具", "系统"), "补全前缀匹配失败")
    _assert_true(not h._autocomplete_match("系统工具", "工具"), "默认不应使用包含匹配")
    h.autocomplete_fuzzy_enabled = True
    _assert_true(h._autocomplete_match("系统工具", "工具"), "开启模糊匹配后应支持包含匹配")

    p = h._autocomplete_source_priority
    _assert_true(p("function") < p("member_func"), "排序优先级应为当前文件优先于已引入")
    _assert_true(p("member_func") < p("builtin_func"), "排序优先级应为已引入优先于内置")
    _assert_true(p("builtin_func") < p("keyword"), "排序优先级应为内置优先于关键字")
    _assert_true(p("keyword") < p("snippet"), "排序优先级应为关键字优先于模板")

    _assert_true(h._sanitize_export_name("  A:B?*  ") == "A_B__", "导出名称清洗规则异常")
    issue_text = h._格式化问题列表项(
        {"level": "warn", "line": 24, "message": "名称【转换数字】在当前上下文可能未定义。", "category": "语义"}
    )
    _assert_true(issue_text.startswith("[提][语义] L24 "), "问题列表格式异常")
    print("[OK] 编辑器补全与排序规则通过")


def check_export_preflight() -> None:
    with tempfile.TemporaryDirectory(prefix="yima_editor_reg_") as td:
        tdir = Path(td)
        h = _new_harness(tdir)

        ok_entry = tdir / "主程序.ym"
        ok_entry.write_text('显示 "ok"\n', encoding="utf-8")
        ok_cfg = {
            "软件名称": "测试软件",
            "输出路径": str(tdir / "dist" / "测试软件.exe"),
            "图标路径": None,
        }
        errs, warns = h._导出前置检查(str(ok_entry), ok_cfg, ok_cfg["输出路径"])
        _assert_true(not errs, f"正常配置不应报错: {errs}")
        _assert_true(isinstance(warns, list), "预检警告返回类型错误")

        bad_entry = tdir / "坏入口.ym"
        bad_entry.write_text('引入 "绝对-非法模块名" 叫做 坏模块\n', encoding="utf-8")
        bad_cfg = {
            "软件名称": "坏软件",
            "输出路径": str(tdir / "dist" / "坏软件.exe"),
            "图标路径": None,
        }
        errs2, _ = h._导出前置检查(str(bad_entry), bad_cfg, bad_cfg["输出路径"])
        _assert_true(any("无法解析的模块" in str(x) for x in errs2), "应拦截不存在模块")
        print("[OK] 导出前置检查规则通过")


def check_semantic_scope_rules() -> None:
    h = _new_harness(ROOT)

    nested_if_code = """
功能 测试(条件)
    如果 条件 就
        如果 对 就
            文本 = "A"
        不然
            文本 = "B"
    不然
        文本 = "C"
    显示 文本
"""
    warns = _semantic_warnings(h, nested_if_code)
    _assert_true(
        not any("文本" in str(w.get("message", "")) and "未定义" in str(w.get("message", "")) for w in warns),
        f"嵌套分支必定赋值被误报: {warns}",
    )
    print("[OK] 语义作用域（嵌套分支赋值）通过")


def check_export_entry_resolution() -> None:
    with tempfile.TemporaryDirectory(prefix="yima_export_entry_") as td:
        root = Path(td)
        sub = root / "示例项目"
        sub.mkdir(parents=True, exist_ok=True)

        (root / "主程序.ym").write_text('显示 "root"\n', encoding="utf-8")
        (sub / "主程序.ym").write_text('显示 "sub"\n', encoding="utf-8")
        当前文件 = sub / "界面层.ym"
        当前文件.write_text('显示 "ui"\n', encoding="utf-8")

        h = _new_harness(root)
        入口, 目录, 软件名 = h._解析导出入口(str(当前文件))
        _assert_true(Path(入口).resolve() == (sub / "主程序.ym").resolve(), "导出入口应优先就近主程序")
        _assert_true(Path(目录).resolve() == sub.resolve(), "源码目录应使用就近项目目录")
        _assert_true(软件名 == "示例项目", "默认软件名应取项目目录名")
    print("[OK] 导出入口就近解析规则通过")


def check_export_entry_not_hijacked_by_workspace_root() -> None:
    with tempfile.TemporaryDirectory(prefix="yima_export_root_hijack_") as td:
        root = Path(td)
        demo = root / "示例"
        demo.mkdir(parents=True, exist_ok=True)

        (root / "主程序.ym").write_text('显示 "root"\n', encoding="utf-8")
        当前文件 = demo / "网图下载器.ym"
        当前文件.write_text('显示 "demo"\n', encoding="utf-8")

        h = _new_harness(root)
        入口, 目录, 软件名 = h._解析导出入口(str(当前文件))
        _assert_true(Path(入口).resolve() == 当前文件.resolve(), "示例文件不应被工作区根主程序劫持")
        _assert_true(Path(目录).resolve() == demo.resolve(), "单文件导出目录应为当前文件目录")
        _assert_true(软件名 == "网图下载器", "单文件导出默认软件名应取当前文件名")
    print("[OK] 导出入口防劫持规则通过")


def main() -> int:
    print("=== 编辑器逻辑回归开始 ===")
    check_autocomplete_rules()
    check_export_preflight()
    check_semantic_scope_rules()
    check_export_entry_resolution()
    check_export_entry_not_hijacked_by_workspace_root()
    print("=== 编辑器逻辑回归完成：全部通过 ===")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as e:
        safe = str(e).encode("unicode_escape", errors="replace").decode("ascii", errors="replace")
        print(f"[FAIL] 编辑器逻辑回归失败: {safe}")
        raise SystemExit(1)
