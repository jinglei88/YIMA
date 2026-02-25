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
import os
from types import MethodType

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))
from _console_utf8 import setup_console_utf8

setup_console_utf8()

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from 易码编辑器 import 易码IDE
from yima.词法分析 import 词法分析器
from yima.语法分析 import 语法分析器


from yima.editor_logic_core import (
    build_advanced_export_config,
    build_export_confirmation_text,
    build_export_defaults,
    build_quick_export_config,
    collect_autocomplete_context,
    collect_context_snippet_hints,
    export_preflight_check,
    extract_call_context,
    first_argument_span_offset,
    extract_member_completion_target,
    extract_word_completion_prefix,
    format_numbered_messages,
    highlight_current_signature_param,
    member_completion_seed,
    merge_member_completion_fallback,
    normalize_export_output_path,
    normalize_completion_signature,
    rank_member_completion_candidates,
    rank_word_completion_candidates,
    resolve_call_expression_signature,
    split_signature_params,
)
from yima.editor_project_flow import (
    load_project_state as flow_load_project_state,
    restore_project_open_tabs as flow_restore_project_open_tabs,
    save_project_state as flow_save_project_state,
    try_restore_last_project as flow_try_restore_last_project,
)


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
    h._autocomplete_match = MethodType(易码IDE._autocomplete_match, h)
    h._autocomplete_source_priority = MethodType(易码IDE._autocomplete_source_priority, h)
    h._sanitize_export_name = MethodType(易码IDE._sanitize_export_name, h)
    h._导出前置检查 = MethodType(易码IDE._导出前置检查, h)
    h._缩略问题消息 = MethodType(易码IDE._缩略问题消息, h)
    h._格式化问题列表项 = MethodType(易码IDE._格式化问题列表项, h)
    h._解析导出入口 = MethodType(易码IDE._解析导出入口, h)

    # 语义分析
    h._默认模块别名 = MethodType(易码IDE._默认模块别名, h)
    h._收集块声明 = MethodType(易码IDE._收集块声明, h)
    h._语义模块搜索路径 = MethodType(易码IDE._语义模块搜索路径, h)
    h._语义定位易码模块 = MethodType(易码IDE._语义定位易码模块, h)
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


def check_core_export_preflight_rules() -> None:
    with tempfile.TemporaryDirectory(prefix="yima_core_export_preflight_") as td:
        root = Path(td)
        workspace = root / "workspace"
        workspace.mkdir(parents=True, exist_ok=True)

        tool_root = root / "tool_root"
        tool_root.mkdir(parents=True, exist_ok=True)
        (tool_root / "易码打包工具.py").write_text("# tool\n", encoding="utf-8")
        (tool_root / "yima").mkdir(parents=True, exist_ok=True)

        entry = workspace / "主程序.ym"
        entry.write_text('引入 "missing_mod" 叫做 缺失\n引入 "json" 叫做 J\n', encoding="utf-8")
        icon_png = workspace / "app.png"
        icon_png.write_text("png", encoding="utf-8")

        config = {
            "软件名称": "坏:名",
            "图标路径": str(icon_png),
        }
        output = str(workspace / "dist" / "坏名.bin")

        errors, warnings = export_preflight_check(
            source_entry=str(entry),
            package_config=config,
            output_path=output,
            workspace_dir=str(workspace),
            tool_root_dir=str(tool_root),
            sanitize_export_name_func=lambda name: str(name).replace(":", "_"),
            builtin_module_names={"系统工具"},
            module_locator=lambda _name: None,
            python_module_exists=lambda name: str(name) == "json",
        )

        _assert_true(any("输出路径必须以 .exe 结尾。" in str(x) for x in errors), f"core export preflight: output suffix check failed: {errors}")
        _assert_true(any("missing_mod" in str(x) and "无法解析的模块" in str(x) for x in errors), f"core export preflight: missing module check failed: {errors}")
        _assert_true(any("软件名称包含非法字符" in str(x) for x in warnings), f"core export preflight: sanitize warning missing: {warnings}")
        _assert_true(any("图标建议使用 .ico 格式" in str(x) for x in warnings), f"core export preflight: icon warning missing: {warnings}")
    print("[OK] core export preflight rules passed")


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


def check_export_config_helper_rules() -> None:
    with tempfile.TemporaryDirectory(prefix="yima_export_cfg_") as td:
        root = Path(td)
        workspace = root / "workspace"
        source = workspace / "demo"
        tool_root = root / "tool"
        output_probe = root / "out"
        custom_dir = root / "custom"
        workspace.mkdir(parents=True, exist_ok=True)
        source.mkdir(parents=True, exist_ok=True)
        tool_root.mkdir(parents=True, exist_ok=True)
        output_probe.mkdir(parents=True, exist_ok=True)
        custom_dir.mkdir(parents=True, exist_ok=True)

        logo = tool_root / "logo.ico"
        logo.write_text("ico", encoding="utf-8")

        defaults = build_export_defaults(str(workspace), str(source), " A:B?* ", str(tool_root))
        _assert_true(defaults["软件名称"] == "A_B__", f"export defaults name mismatch: {defaults}")
        _assert_true(Path(defaults["输出目录"]).resolve() == (source / "易码_成品软件").resolve(), f"export defaults output dir mismatch: {defaults}")
        _assert_true(Path(defaults["输出路径"]).resolve() == (source / "易码_成品软件" / "A_B__.exe").resolve(), f"export defaults output path mismatch: {defaults}")
        _assert_true(Path(defaults["图标路径"]).resolve() == logo.resolve(), f"export defaults icon mismatch: {defaults}")
        _assert_true(defaults["默认软件文件名"] == "A_B__.exe", f"export defaults file name mismatch: {defaults}")

        quick = build_quick_export_config(defaults["软件名称"], defaults["输出路径"], defaults["图标路径"])
        _assert_true(quick["隐藏黑框"] is True and quick["模式标题"] == "一键打包", f"quick export config mismatch: {quick}")

        normalized_empty = normalize_export_output_path("", "新软件", str(output_probe), "A_B__.exe")
        _assert_true(Path(normalized_empty).resolve() == (output_probe / "新软件.exe").resolve(), f"export path normalize empty mismatch: {normalized_empty}")

        normalized_dir = normalize_export_output_path(str(custom_dir), "新软件", str(output_probe), "A_B__.exe")
        _assert_true(Path(normalized_dir).resolve() == (custom_dir / "新软件.exe").resolve(), f"export path normalize dir mismatch: {normalized_dir}")

        normalized_ext = normalize_export_output_path(str(custom_dir / "custom"), "新软件", str(output_probe), "A_B__.exe")
        _assert_true(Path(normalized_ext).resolve() == (custom_dir / "custom.exe").resolve(), f"export path normalize extension mismatch: {normalized_ext}")

        normalized_default_rename = normalize_export_output_path(str(custom_dir / "A_B__.exe"), "重命名", str(output_probe), "A_B__.exe")
        _assert_true(
            Path(normalized_default_rename).resolve() == (custom_dir / "重命名.exe").resolve(),
            f"export path normalize default-name follow mismatch: {normalized_default_rename}",
        )

        advanced = build_advanced_export_config(
            "重命名",
            str(custom_dir / "A_B__.exe"),
            str(logo),
            "console",
            str(output_probe),
            "A_B__.exe",
        )
        _assert_true(advanced["软件名称"] == "重命名", f"advanced export name mismatch: {advanced}")
        _assert_true(Path(advanced["输出路径"]).resolve() == (custom_dir / "重命名.exe").resolve(), f"advanced export output mismatch: {advanced}")
        _assert_true(Path(advanced["图标路径"]).resolve() == logo.resolve(), f"advanced export icon mismatch: {advanced}")
        _assert_true(advanced["隐藏黑框"] is False and advanced["模式标题"] == "高级导出", f"advanced export mode mismatch: {advanced}")

        numbered = format_numbered_messages(["A", "B"])
        _assert_true(numbered == "1. A\n2. B", f"numbered messages mismatch: {numbered}")

        confirm_text = build_export_confirmation_text(quick, str(source / "主程序.ym"), quick["输出路径"])
        _assert_true("模式：一键打包" in confirm_text and "入口：主程序.ym" in confirm_text, f"export confirm text mismatch: {confirm_text}")
    print("[OK] export config helper rules passed")



def check_core_autocomplete_context_rules() -> None:
    kw_import = "\u5f15\u5165"
    kw_alias = "\u53eb\u505a"
    kw_blueprint = "\u5b9a\u4e49\u56fe\u7eb8"
    kw_func = "\u529f\u80fd"
    kw_return = "\u8fd4\u56de"
    kw_show = "\u663e\u793a"
    kw_self = "\u5b83\u7684"
    kw_create = "\u9020\u4e00\u4e2a"

    alias_math = "\u6570\u5b66"
    obj_main = "\u4e3b\u89d2"
    bp_player = "\u73a9\u5bb6"
    name_field = "\u540d\u5b57"
    ask_func = "\u95ee\u5019"
    sum_func = "\u6c42\u548c"
    temp_var = "\u4e34\u65f6"

    code = (
        f'{kw_import} "math" {kw_alias} {alias_math}\n'
        f"{kw_blueprint} {bp_player}({name_field})\n"
        f"    {kw_self} {name_field} = {name_field}\n"
        f"    {kw_func} {ask_func}()\n"
        f"        {kw_return} {name_field}\n"
        f'{obj_main} = {kw_create} {bp_player}("A")\n'
        f"{kw_func} {sum_func}(a, b)\n"
        f"    {temp_var} = a + b\n"
        f"    {kw_return} {temp_var}\n"
        f"{kw_show} {obj_main}.{ask_func}\n"
    )

    def fmt(params):
        values = [str(p).strip() for p in (params or []) if str(p).strip()]
        return f"({', '.join(values)})" if values else "()"

    def details(module_name, _tab_id):
        if str(module_name) == "math":
            return {"sqrt": "function", "pi": "variable"}
        return {}

    def signatures(module_name, _tab_id):
        if str(module_name) == "math":
            return {"sqrt": "(x)"}
        return {}

    def members(_module_name, _tab_id):
        return set()

    context = collect_autocomplete_context(
        code,
        fmt,
        module_member_details_resolver=details,
        module_member_signatures_resolver=signatures,
        module_members_resolver=members,
        tab_id=None,
        cursor_line=9,
    )

    key_import_alias = "\u5f15\u5165\u522b\u540d"
    key_imported_flat = "\u5bfc\u5165\u5bfc\u51fa\u5e73\u94fa"
    key_imported_types = "\u5bfc\u5165\u5bfc\u51fa\u7c7b\u578b"
    key_imported_sigs = "\u5bfc\u5165\u5bfc\u51fa\u7b7e\u540d"
    key_alias_member_map = "\u522b\u540d\u6210\u5458\u6620\u5c04"
    key_scope_locals = "\u5f53\u524d\u5c40\u90e8\u53d8\u91cf"
    key_obj_history = "\u5bf9\u8c61\u6210\u5458\u5386\u53f2"

    _assert_true(context.get(key_import_alias, {}).get(alias_math) == "math", "core context: import alias mapping")
    _assert_true("sqrt" in context.get(key_imported_flat, set()), "core context: imported flatten members")
    _assert_true(context.get(key_imported_types, {}).get("sqrt") == "function", "core context: imported member type")
    _assert_true(context.get(key_imported_sigs, {}).get("sqrt") == "(x)", "core context: imported member signature")
    _assert_true(ask_func in context.get(key_alias_member_map, {}).get(obj_main, set()), "core context: blueprint instance members")
    _assert_true(temp_var in context.get(key_scope_locals, set()), "core context: scope locals")
    _assert_true(ask_func in context.get(key_obj_history, {}).get(obj_main, set()), "core context: object member history")
    print("[OK] editor core context rules passed")


def check_context_snippet_hint_rules() -> None:
    kw_if = "\u5982\u679c"
    kw_then = "\u5c31"
    kw_else_if = "\u5426\u5219\u5982\u679c"
    kw_else = "\u4e0d\u7136"
    kw_try = "\u5c1d\u8bd5"
    kw_catch = "\u5982\u679c\u51fa\u9519"
    kw_show = "\u663e\u793a"

    code_if = (
        f"{kw_if} \u5bf9 {kw_then}\n"
        f"    {kw_show} \"A\"\n"
        f"{kw_show} \"B\"\n"
    )
    hints_if = collect_context_snippet_hints(code_if, 3)
    _assert_true(kw_else_if in hints_if and kw_else in hints_if, f"context snippet if-hints mismatch: {hints_if}")

    code_try = (
        f"{kw_try}\n"
        f"    {kw_show} \"A\"\n"
        f"{kw_show} \"B\"\n"
    )
    hints_try = collect_context_snippet_hints(code_try, 3)
    _assert_true(kw_catch in hints_try, f"context snippet try-hints mismatch: {hints_try}")

    code_other = f"{kw_show} \"A\"\n{kw_show} \"B\"\n"
    hints_other = collect_context_snippet_hints(code_other, 2)
    _assert_true(not hints_other, f"context snippet should be empty: {hints_other}")
    print("[OK] context snippet helper rules passed")


def check_call_context_helper_rules() -> None:
    parsed_simple = extract_call_context("\u663e\u793a \u6c42\u548c(1, 2")
    _assert_true(parsed_simple == {"\u8c03\u7528\u540d": "\u6c42\u548c", "\u53c2\u6570\u5e8f\u53f7": 2}, f"call context simple mismatch: {parsed_simple}")

    parsed_member = extract_call_context("obj.run(a")
    _assert_true(parsed_member == {"\u8c03\u7528\u540d": "obj.run", "\u53c2\u6570\u5e8f\u53f7": 1}, f"call context member mismatch: {parsed_member}")

    parsed_nested_inner = extract_call_context("\u6c42\u548c(\u65b0\u5217\u8868(1, 2), \"a,b\", \u5305\u88c5(3, 4")
    _assert_true(
        parsed_nested_inner == {"\u8c03\u7528\u540d": "\u5305\u88c5", "\u53c2\u6570\u5e8f\u53f7": 2},
        f"call context nested-inner mismatch: {parsed_nested_inner}",
    )

    parsed_nested_outer = extract_call_context("\u6c42\u548c(\u65b0\u5217\u8868(1, 2), \"a,b\", ")
    _assert_true(
        parsed_nested_outer == {"\u8c03\u7528\u540d": "\u6c42\u548c", "\u53c2\u6570\u5e8f\u53f7": 3},
        f"call context nested-outer mismatch: {parsed_nested_outer}",
    )

    _assert_true(extract_call_context("\u6c42\u548c(1, 2)") is None, "call context should be None after closed call")
    _assert_true(extract_call_context("\u663e\u793a \u6570\u503c") is None, "call context should be None without open call")
    print("[OK] call context helper rules passed")


def check_signature_helper_rules() -> None:
    split_basic = split_signature_params("(a, b)")
    _assert_true(split_basic == ["a", "b"], f"signature split basic mismatch: {split_basic}")

    split_nested = split_signature_params("(a, \u8c03\u7528(1, 2), \"x,y\", [1,2], {'k': 1})")
    _assert_true(
        split_nested == ["a", "\u8c03\u7528(1, 2)", "\"x,y\"", "[1,2]", "{'k': 1}"],
        f"signature split nested mismatch: {split_nested}",
    )

    _assert_true(split_signature_params("a, b") == [], "signature split should reject non-parenthesized text")
    _assert_true(split_signature_params("()") == [], "signature split should return empty list for no params")

    highlighted = highlight_current_signature_param("(a, b, c)", 2)
    _assert_true(
        highlighted == ("(a, <<b>>, c)", 2, 3, "b"),
        f"signature highlight mismatch: {highlighted}",
    )

    highlighted_clamped = highlight_current_signature_param("(a, b, c)", 9)
    _assert_true(
        highlighted_clamped == ("(a, b, <<c>>)", 3, 3, "c"),
        f"signature highlight clamp mismatch: {highlighted_clamped}",
    )

    highlighted_empty = highlight_current_signature_param("", 1)
    _assert_true(highlighted_empty == ("()", 0, 0, ""), f"signature highlight empty mismatch: {highlighted_empty}")

    normalized = normalize_completion_signature("(self, a: int, b=1, *args, **kwargs)")
    _assert_true(normalized == "(a, b, args, kwargs)", f"signature normalize mismatch: {normalized}")
    _assert_true(
        normalize_completion_signature("(a, 1b)") == "()",
        "signature normalize should fallback for invalid identifier",
    )

    offset_single = first_argument_span_offset("(arg)")
    _assert_true(offset_single == (1, 4), f"first argument offset single mismatch: {offset_single}")
    offset_multi = first_argument_span_offset("(arg1, arg2)")
    _assert_true(offset_multi == (1, 5), f"first argument offset multi mismatch: {offset_multi}")
    _assert_true(first_argument_span_offset("()") is None, "first argument offset should be None for empty args")
    _assert_true(first_argument_span_offset("arg") is None, "first argument offset should be None for invalid snippet")
    print("[OK] signature helper rules passed")


def check_call_signature_helper_rules() -> None:
    key_func_sigs = "\u529f\u80fd\u7b7e\u540d"
    key_bp_sigs = "\u56fe\u7eb8\u7b7e\u540d"
    key_import_sigs = "\u5bfc\u5165\u5bfc\u51fa\u7b7e\u540d"
    key_alias_member_sig_map = "\u522b\u540d\u6210\u5458\u7b7e\u540d\u6620\u5c04"
    key_import_alias = "\u5f15\u5165\u522b\u540d"

    context = {
        key_func_sigs: {"\u6c42\u548c": "(a, b)"},
        key_bp_sigs: {"\u73a9\u5bb6": "(\u540d\u5b57)"},
        key_import_sigs: {"sqrt": "(x)"},
        key_alias_member_sig_map: {
            "\u6570\u5b66": {"pow": "(x, y)"},
            "obj": {"run": ""},
        },
        key_import_alias: {"\u6570\u5b66": "math"},
    }

    builtin_words = {"\u8bfb\u6587\u4ef6", "\u8f6c\u6570\u5b57"}

    def builtin_sig(name: str) -> str:
        table = {
            "\u8bfb\u6587\u4ef6": "(path)",
            "\u8f6c\u6570\u5b57": "(value)",
        }
        return table.get(str(name), "()")

    def cross_tab_alias(alias: str, _tab_id):
        return {"\u5916\u90e8": "ext.mod"}.get(str(alias))

    def module_sigs(module_name: str, _tab_id):
        if str(module_name) == "ext.mod":
            return {"run": "(payload)"}
        return {}

    _assert_true(
        resolve_call_expression_signature("\u6c42\u548c", context, builtin_words, builtin_sig) == "(a, b)",
        "call signature should prefer local function signature",
    )
    _assert_true(
        resolve_call_expression_signature("\u73a9\u5bb6", context, builtin_words, builtin_sig) == "(\u540d\u5b57)",
        "call signature should resolve blueprint signature",
    )
    _assert_true(
        resolve_call_expression_signature("sqrt", context, builtin_words, builtin_sig) == "(x)",
        "call signature should resolve imported symbol signature",
    )
    _assert_true(
        resolve_call_expression_signature("\u6570\u5b66.pow", context, builtin_words, builtin_sig) == "(x, y)",
        "call signature should resolve alias-member signature",
    )
    _assert_true(
        resolve_call_expression_signature(
            "\u5916\u90e8.run",
            context,
            builtin_words,
            builtin_sig,
            cross_tab_alias_resolver=cross_tab_alias,
            module_member_signature_resolver=module_sigs,
            tab_id="T1",
        ) == "(payload)",
        "call signature should resolve cross-tab module member signature",
    )
    _assert_true(
        resolve_call_expression_signature("obj.run", context, builtin_words, builtin_sig) == "()",
        "empty alias-member signature should fallback to ()",
    )
    _assert_true(
        resolve_call_expression_signature("obj.\u8bfb\u6587\u4ef6", context, builtin_words, builtin_sig) == "(path)",
        "member name should fallback to builtin signature",
    )
    _assert_true(
        resolve_call_expression_signature("\u672a\u77e5", context, builtin_words, builtin_sig) == "",
        "unknown call expression should return empty signature",
    )
    print("[OK] call signature helper rules passed")


def check_member_completion_helper_rules() -> None:
    key_alias_member_map = "\u522b\u540d\u6210\u5458\u6620\u5c04"
    key_alias_member_type_map = "\u522b\u540d\u6210\u5458\u7c7b\u578b\u6620\u5c04"
    key_alias_member_sig_map = "\u522b\u540d\u6210\u5458\u7b7e\u540d\u6620\u5c04"
    key_object_history = "\u5bf9\u8c61\u6210\u5458\u5386\u53f2"

    context = {
        key_alias_member_map: {"obj": {"run"}},
        key_alias_member_type_map: {"obj": {"run": "function"}},
        key_alias_member_sig_map: {"obj": {"run": "()"}},
        key_object_history: {"obj": {"stop"}},
    }

    target = extract_member_completion_target("show obj.r")
    _assert_true(target == ("obj", "r"), f"member target parse mismatch: {target}")
    _assert_true(extract_member_completion_target("show obj.") == ("obj", ""), "member target parse empty prefix failed")
    _assert_true(extract_member_completion_target("show obj") is None, "member target parse should return None")

    members, member_types, member_signatures = member_completion_seed(context, "obj")
    _assert_true(members == {"run", "stop"}, f"member seed set mismatch: {members}")
    _assert_true(member_types.get("run") == "function", f"member seed type mismatch: {member_types}")
    _assert_true(member_signatures.get("run") == "()", f"member seed signature mismatch: {member_signatures}")

    merged_members, merged_types, merged_signatures = merge_member_completion_fallback(
        members,
        member_types,
        member_signatures,
        fallback_details={"sqrt": "function"},
        fallback_signatures={"sqrt": "(x)"},
    )
    _assert_true("sqrt" in merged_members, f"member fallback detail merge mismatch: {merged_members}")
    _assert_true(merged_types.get("sqrt") == "function", f"member fallback type mismatch: {merged_types}")
    _assert_true(merged_signatures.get("sqrt") == "(x)", f"member fallback signature mismatch: {merged_signatures}")

    merged_members2, merged_types2, merged_signatures2 = merge_member_completion_fallback(
        members,
        member_types,
        member_signatures,
        fallback_signatures={"stop": "(s)"},
        fallback_members={"stop", "start"},
    )
    _assert_true("start" in merged_members2, f"member fallback member-set merge mismatch: {merged_members2}")
    _assert_true(merged_types2.get("start") is None, f"member fallback should not add inferred type: {merged_types2}")
    _assert_true(merged_signatures2.get("stop") == "(s)", f"member fallback signature update mismatch: {merged_signatures2}")

    ranked = rank_member_completion_candidates(
        merged_members,
        "s",
        merged_types,
        merged_signatures,
        lambda candidate, prefix: str(candidate).startswith(str(prefix)),
    )
    by_name = {item["insert"]: item for item in ranked}
    _assert_true("sqrt" in by_name, f"member ranking missing sqrt: {ranked}")
    _assert_true(by_name["sqrt"]["source"] == "member_func", f"member ranking source mismatch: {by_name}")
    _assert_true(by_name["sqrt"]["callable"] is True, f"member ranking callable mismatch: {by_name}")
    _assert_true(by_name["sqrt"]["sig"] == "(x)", f"member ranking signature mismatch: {by_name}")
    print("[OK] member completion helper rules passed")


def check_word_completion_helper_rules() -> None:
    key_func_names = "\u529f\u80fd\u540d"
    key_bp_names = "\u56fe\u7eb8\u540d"
    key_var_names = "\u53d8\u91cf\u540d"
    key_scope_locals = "\u5f53\u524d\u5c40\u90e8\u53d8\u91cf"
    key_func_sigs = "\u529f\u80fd\u7b7e\u540d"
    key_bp_sigs = "\u56fe\u7eb8\u7b7e\u540d"
    key_import_alias = "\u5f15\u5165\u522b\u540d"
    key_import_modules = "\u5f15\u5165\u6a21\u5757\u540d"
    key_import_flat = "\u5bfc\u5165\u5bfc\u51fa\u5e73\u94fa"
    key_import_types = "\u5bfc\u5165\u5bfc\u51fa\u7c7b\u578b"
    key_import_sigs = "\u5bfc\u5165\u5bfc\u51fa\u7b7e\u540d"

    context = {
        key_func_names: {"\u8ba1\u7b97"},
        key_bp_names: {"\u73a9\u5bb6"},
        key_var_names: {"\u7ed3\u679c"},
        key_scope_locals: {"\u7ed3\u679c"},
        key_func_sigs: {"\u8ba1\u7b97": "(a, b)"},
        key_bp_sigs: {"\u73a9\u5bb6": "(\u540d\u5b57)"},
        key_import_alias: {"\u6570\u5b66": "math"},
        key_import_modules: {"math"},
        key_import_flat: {"sqrt", "pi"},
        key_import_types: {"sqrt": "function", "pi": "variable"},
        key_import_sigs: {"sqrt": "(x)"},
    }

    _assert_true(extract_word_completion_prefix("show abc") == "abc", "word prefix parse mismatch")
    _assert_true(extract_word_completion_prefix("show abc.") is None, "word prefix parse dot tail should be None")

    autocomplete_words = ["\u663e\u793a", "\u6a21\u677f\u8bcd", "\u8bfb\u6587\u4ef6"]
    snippets = {"\u6a21\u677f\u8bcd": "snippet body"}
    builtin_words = {"\u8bfb\u6587\u4ef6"}

    def builtin_sig(name: str) -> str:
        return "(path)" if str(name) == "\u8bfb\u6587\u4ef6" else ""

    startswith_match = lambda candidate, prefix: str(candidate).startswith(str(prefix))

    ranked_import = rank_word_completion_candidates(
        "s",
        context,
        autocomplete_words,
        snippets,
        builtin_words,
        builtin_sig,
        startswith_match,
    )
    import_map = {item["insert"]: item for item in ranked_import}
    _assert_true("sqrt" in import_map, f"word ranking missing imported function: {ranked_import}")
    _assert_true(import_map["sqrt"]["source"] == "imported_func", f"imported source mismatch: {import_map}")
    _assert_true(import_map["sqrt"]["callable"] is True, f"imported callable mismatch: {import_map}")
    _assert_true(import_map["sqrt"]["sig"] == "(x)", f"imported signature mismatch: {import_map}")

    ranked_builtin = rank_word_completion_candidates(
        "\u8bfb",
        context,
        autocomplete_words,
        snippets,
        builtin_words,
        builtin_sig,
        startswith_match,
    )
    builtin_map = {item["insert"]: item for item in ranked_builtin}
    _assert_true("\u8bfb\u6587\u4ef6" in builtin_map, f"word ranking missing builtin: {ranked_builtin}")
    _assert_true(builtin_map["\u8bfb\u6587\u4ef6"]["source"] == "builtin_func", f"builtin source mismatch: {builtin_map}")
    _assert_true(builtin_map["\u8bfb\u6587\u4ef6"]["callable"] is True, f"builtin callable mismatch: {builtin_map}")
    _assert_true(builtin_map["\u8bfb\u6587\u4ef6"]["sig"] == "(path)", f"builtin signature mismatch: {builtin_map}")

    ranked_snippet = rank_word_completion_candidates(
        "\u6a21",
        context,
        autocomplete_words,
        snippets,
        builtin_words,
        builtin_sig,
        startswith_match,
        context_snippets={"\u6a21\u677f\u8bcd"},
    )
    snippet_map = {item["insert"]: item for item in ranked_snippet}
    _assert_true("\u6a21\u677f\u8bcd" in snippet_map, f"word ranking missing snippet: {ranked_snippet}")
    _assert_true(snippet_map["\u6a21\u677f\u8bcd"]["source"] == "snippet", f"snippet source mismatch: {snippet_map}")

    ranked_local_var = rank_word_completion_candidates(
        "\u7ed3",
        context,
        autocomplete_words,
        snippets,
        builtin_words,
        builtin_sig,
        startswith_match,
    )
    var_map = {item["insert"]: item for item in ranked_local_var}
    _assert_true("\u7ed3\u679c" in var_map, f"word ranking missing local variable: {ranked_local_var}")
    _assert_true(var_map["\u7ed3\u679c"]["source"] == "variable", f"local variable source mismatch: {var_map}")
    print("[OK] word completion helper rules passed")


def check_project_session_state_rules() -> None:
    class NotebookStub:
        def __init__(self):
            self._tabs = []
            self._selected = None

        def tabs(self):
            return list(self._tabs)

        def select(self, tab_id=None):
            if tab_id is None:
                return self._selected
            self._selected = tab_id
            return self._selected

    class EditorStub:
        def __init__(self, cursor="1.0", yview=0.0, xview=0.0, text=""):
            self._cursor = str(cursor)
            try:
                y = float(yview)
            except Exception:
                y = 0.0
            self._yview = max(0.0, min(1.0, y))
            try:
                x = float(xview)
            except Exception:
                x = 0.0
            self._xview = max(0.0, min(1.0, x))
            raw_lines = str(text or "").splitlines()
            self._lines = raw_lines if raw_lines else [""]
            self._tags = {}

        def index(self, name):
            if name == "insert":
                return self._cursor
            if name == "end-1c":
                line_no = len(self._lines)
                col_no = len(self._lines[-1]) if self._lines else 0
                return f"{line_no}.{col_no}"
            return str(name)

        def mark_set(self, name, index):
            if name == "insert":
                self._cursor = str(index)

        def yview(self):
            return (self._yview, min(1.0, self._yview + 0.25))

        def yview_moveto(self, fraction):
            try:
                y = float(fraction)
            except Exception:
                return
            self._yview = max(0.0, min(1.0, y))

        def xview(self):
            return (self._xview, min(1.0, self._xview + 0.25))

        def xview_moveto(self, fraction):
            try:
                x = float(fraction)
            except Exception:
                return
            self._xview = max(0.0, min(1.0, x))

        def _line_of(self, index):
            text = str(index or "1.0")
            line_part = text.split(".", 1)[0]
            try:
                line_no = int(line_part)
            except Exception:
                line_no = 1
            return max(1, min(len(self._lines), line_no))

        def get(self, start, end=None):
            del end
            return self._lines[self._line_of(start) - 1]

        def tag_configure(self, tag_name, **kwargs):
            tag_data = self._tags.setdefault(str(tag_name), {"ranges": []})
            if "elide" in kwargs:
                tag_data["elide"] = bool(kwargs["elide"])

        def tag_remove(self, tag_name, _start, _end):
            tag_data = self._tags.setdefault(str(tag_name), {"ranges": []})
            tag_data["ranges"] = []

        def tag_add(self, tag_name, start, end):
            tag_data = self._tags.setdefault(str(tag_name), {"ranges": []})
            tag_data["ranges"] = [(str(start), str(end))]

    class OwnerStub:
        pass

    with tempfile.TemporaryDirectory(prefix="yima_project_state_") as td:
        root = Path(td)
        project = root / "proj"
        project.mkdir(parents=True, exist_ok=True)
        file_a = project / "a.ym"
        file_b = project / "b.ym"
        file_c = project / "c.ym"
        file_a.write_text("A\n    A1\n    A2\n", encoding="utf-8")
        file_b.write_text("B\n    B1\n", encoding="utf-8")
        file_c.write_text("C\n    C1\n", encoding="utf-8")

        def normcase(path):
            return os.path.normcase(str(Path(path).resolve()))

        def new_owner(initial_views=None, initial_folds=None):
            owner = OwnerStub()
            owner._state_dir = str(root / ".state")
            owner._state_file = str(Path(owner._state_dir) / "editor_state.json")
            owner.workspace_dir = str(project)
            owner.recent_projects = []
            owner.last_project_dir = None
            owner.last_open_file = None
            owner.last_session_files = []
            owner.last_session_views = {}
            owner.last_session_folds = {}
            owner.last_session_outline_focus = {}
            owner.tabs_data = {}
            owner.notebook = NotebookStub()
            owner.print_output = lambda *_args, **_kwargs: None
            owner.refresh_file_tree = lambda: None
            owner._refresh_outline = lambda: None
            owner._update_line_numbers = lambda *_args, **_kwargs: None
            owner._normalize_file_path = lambda p: str(Path(p).resolve()) if Path(p).is_file() else None
            owner._initial_views = {
                normcase(p): dict(v)
                for p, v in (initial_views or {}).items()
                if isinstance(v, dict)
            }
            owner._initial_folds = {
                normcase(p): [int(x) for x in lines]
                for p, lines in (initial_folds or {}).items()
                if isinstance(lines, (list, tuple, set))
            }
            class _StatusVar:
                def __init__(self):
                    self.value = ""
                def set(self, text):
                    self.value = str(text)
            class _TextVar:
                def __init__(self, value=""):
                    self.value = str(value)
                def get(self):
                    return self.value
                def set(self, value):
                    self.value = str(value)

            owner.status_main_var = _StatusVar()
            owner.find_var = _TextVar("")
            owner.replace_var = _TextVar("")

            def _get_current_tab_id():
                return owner.notebook.select()

            owner._get_current_tab_id = _get_current_tab_id

            def _create_editor_tab(filepath, _content=""):
                normalized_file = str(Path(filepath).resolve())
                for tab_id, data in owner.tabs_data.items():
                    if os.path.normcase(str(data.get("filepath") or "")) == os.path.normcase(normalized_file):
                        owner.notebook.select(tab_id)
                        return
                seed = owner._initial_views.get(os.path.normcase(normalized_file), {})
                editor = EditorStub(
                    cursor=seed.get("cursor", "1.0"),
                    yview=seed.get("yview", 0.0),
                    xview=seed.get("xview", 0.0),
                    text=_content,
                )
                tab_id = f"tab-{len(owner.tabs_data) + 1}"
                fold_lines = sorted(set(owner._initial_folds.get(os.path.normcase(normalized_file), [])))
                folds = {
                    int(line_no): {"tag": f"FoldBlock_{int(line_no)}", "end_line": int(line_no) + 1, "collapsed": True}
                    for line_no in fold_lines
                    if int(line_no) > 0
                }
                owner.tabs_data[tab_id] = {"filepath": normalized_file, "editor": editor, "folds": folds}
                owner.notebook._tabs.append(tab_id)
                owner.notebook.select(tab_id)

            owner._create_editor_tab = _create_editor_tab

            def _close_all_tabs_silently():
                owner.tabs_data = {}
                owner.notebook._tabs = []
                owner.notebook._selected = None

            owner._close_all_tabs_silently = _close_all_tabs_silently
            return owner

        def get_tab_id_by_file(owner, filepath):
            target = normcase(filepath)
            for tab_id, data in owner.tabs_data.items():
                current = os.path.normcase(str(data.get("filepath") or ""))
                if current == target:
                    return tab_id
            return None

        def collapsed_fold_lines(tab_data):
            folds = tab_data.get("folds", {}) if isinstance(tab_data, dict) else {}
            rows = []
            for line_no, meta in folds.items():
                if not isinstance(meta, dict) or not bool(meta.get("collapsed")):
                    continue
                rows.append(int(line_no))
            return sorted(rows)

        saved_views = {
            str(file_a): {"cursor": "3.2", "yview": 0.25, "xview": 0.1},
            str(file_b): {"cursor": "7.1", "yview": 0.6, "xview": 0.55},
        }
        saved_folds = {
            str(file_a): [1],
            str(file_b): [1],
        }
        saved_outline_focus = {
            str(file_a): 1,
            str(file_b): 1,
        }

        owner = new_owner(initial_views=saved_views, initial_folds=saved_folds)
        owner.last_project_dir = str(project)
        owner.recent_projects = [str(project)]
        owner.find_var.set("关键字-A")
        owner.replace_var.set("替换-A")
        owner._create_editor_tab(str(file_a), file_a.read_text(encoding="utf-8"))
        owner._create_editor_tab(str(file_b), file_b.read_text(encoding="utf-8"))
        tab_a_seed = get_tab_id_by_file(owner, file_a)
        tab_b_seed = get_tab_id_by_file(owner, file_b)
        owner.tabs_data[tab_a_seed]["outline_focus_line"] = saved_outline_focus[str(file_a)]
        owner.tabs_data[tab_b_seed]["outline_focus_line"] = saved_outline_focus[str(file_b)]
        owner.notebook.select("tab-1")

        flow_save_project_state(owner)

        loaded = new_owner()
        flow_load_project_state(loaded)

        _assert_true(
            os.path.normcase(str(file_a)) == os.path.normcase(str(loaded.last_open_file or "")),
            f"project state active file mismatch: {loaded.last_open_file}",
        )
        _assert_true(
            [os.path.normcase(p) for p in loaded.last_session_files]
            == [os.path.normcase(str(file_a)), os.path.normcase(str(file_b))],
            f"project state open files mismatch: {loaded.last_session_files}",
        )
        path_a = str(file_a.resolve())
        path_b = str(file_b.resolve())
        loaded_view_a = loaded.last_session_views.get(path_a, {})
        loaded_view_b = loaded.last_session_views.get(path_b, {})
        _assert_true(loaded_view_a.get("cursor") == "3.2", f"project state cursor(a) mismatch: {loaded_view_a}")
        _assert_true(loaded_view_b.get("cursor") == "7.1", f"project state cursor(b) mismatch: {loaded_view_b}")
        _assert_true(abs(float(loaded_view_a.get("yview", -1.0)) - 0.25) < 1e-9, f"project state yview(a) mismatch: {loaded_view_a}")
        _assert_true(abs(float(loaded_view_b.get("yview", -1.0)) - 0.6) < 1e-9, f"project state yview(b) mismatch: {loaded_view_b}")
        _assert_true(abs(float(loaded_view_a.get("xview", -1.0)) - 0.1) < 1e-9, f"project state xview(a) mismatch: {loaded_view_a}")
        _assert_true(abs(float(loaded_view_b.get("xview", -1.0)) - 0.55) < 1e-9, f"project state xview(b) mismatch: {loaded_view_b}")
        _assert_true(loaded.last_session_folds.get(path_a) == [1], f"project state folds(a) mismatch: {loaded.last_session_folds}")
        _assert_true(loaded.last_session_folds.get(path_b) == [1], f"project state folds(b) mismatch: {loaded.last_session_folds}")
        _assert_true(loaded.last_session_outline_focus.get(path_a) == 1, f"project state outline focus(a) mismatch: {loaded.last_session_outline_focus}")
        _assert_true(loaded.last_session_outline_focus.get(path_b) == 1, f"project state outline focus(b) mismatch: {loaded.last_session_outline_focus}")
        _assert_true(loaded.find_var.get() == "关键字-A", f"project state find query mismatch: {loaded.find_var.get()}")
        _assert_true(loaded.replace_var.get() == "替换-A", f"project state replace query mismatch: {loaded.replace_var.get()}")

        restore_views = {
            str(file_a): {"cursor": "9.4", "yview": 0.33, "xview": 0.2},
            str(file_b): {"cursor": "2.1", "yview": 0.12, "xview": 0.73},
            str(file_c): {"cursor": "5.0", "yview": 0.88, "xview": 0.45},
        }
        restore_folds = {
            str(file_a): [1],
            str(file_b): [1],
            str(file_c): [1],
        }
        restore_outline_focus = {
            str(file_a): 1,
            str(file_b): 1,
            str(file_c): 1,
        }
        restore_owner = new_owner(initial_views={str(file_a): {"cursor": "1.0", "yview": 0.0, "xview": 0.0}})
        restore_owner._create_editor_tab(str(file_a), file_a.read_text(encoding="utf-8"))
        restored_count = flow_restore_project_open_tabs(
            restore_owner,
            str(project),
            [str(file_a), str(file_b), str(file_c)],
            preferred_file=str(file_a),
            open_views=restore_views,
            open_folds=restore_folds,
            open_outline_focus=restore_outline_focus,
        )
        opened = [os.path.normcase(str(v.get("filepath") or "")) for v in restore_owner.tabs_data.values()]
        _assert_true(
            os.path.normcase(str(file_b)) in opened and os.path.normcase(str(file_c)) in opened,
            f"project session restore should open extra files: {opened}",
        )
        _assert_true(restored_count == 2, f"project session restore count mismatch: {restored_count}")
        selected_tab = restore_owner.notebook.select()
        selected_file = restore_owner.tabs_data.get(selected_tab, {}).get("filepath")
        _assert_true(
            os.path.normcase(str(selected_file or "")) == os.path.normcase(str(file_a)),
            f"project session restore should keep preferred tab active: {selected_file}",
        )

        tab_a = get_tab_id_by_file(restore_owner, file_a)
        tab_b = get_tab_id_by_file(restore_owner, file_b)
        tab_c = get_tab_id_by_file(restore_owner, file_c)
        _assert_true(tab_a and tab_b and tab_c, f"project session restore tabs missing: a={tab_a}, b={tab_b}, c={tab_c}")
        editor_a = restore_owner.tabs_data[tab_a]["editor"]
        editor_b = restore_owner.tabs_data[tab_b]["editor"]
        editor_c = restore_owner.tabs_data[tab_c]["editor"]
        _assert_true(editor_a.index("insert") == "9.4", f"project session cursor(a) mismatch: {editor_a.index('insert')}")
        _assert_true(editor_b.index("insert") == "2.1", f"project session cursor(b) mismatch: {editor_b.index('insert')}")
        _assert_true(editor_c.index("insert") == "5.0", f"project session cursor(c) mismatch: {editor_c.index('insert')}")
        _assert_true(abs(editor_a.yview()[0] - 0.33) < 1e-9, f"project session yview(a) mismatch: {editor_a.yview()}")
        _assert_true(abs(editor_b.yview()[0] - 0.12) < 1e-9, f"project session yview(b) mismatch: {editor_b.yview()}")
        _assert_true(abs(editor_c.yview()[0] - 0.88) < 1e-9, f"project session yview(c) mismatch: {editor_c.yview()}")
        _assert_true(abs(editor_a.xview()[0] - 0.2) < 1e-9, f"project session xview(a) mismatch: {editor_a.xview()}")
        _assert_true(abs(editor_b.xview()[0] - 0.73) < 1e-9, f"project session xview(b) mismatch: {editor_b.xview()}")
        _assert_true(abs(editor_c.xview()[0] - 0.45) < 1e-9, f"project session xview(c) mismatch: {editor_c.xview()}")
        _assert_true(collapsed_fold_lines(restore_owner.tabs_data[tab_a]) == [1], f"project session folds(a) mismatch: {restore_owner.tabs_data[tab_a].get('folds')}")
        _assert_true(collapsed_fold_lines(restore_owner.tabs_data[tab_b]) == [1], f"project session folds(b) mismatch: {restore_owner.tabs_data[tab_b].get('folds')}")
        _assert_true(collapsed_fold_lines(restore_owner.tabs_data[tab_c]) == [1], f"project session folds(c) mismatch: {restore_owner.tabs_data[tab_c].get('folds')}")
        _assert_true(restore_owner.tabs_data[tab_a].get("outline_focus_line") == 1, f"project session outline focus(a) mismatch: {restore_owner.tabs_data[tab_a]}")
        _assert_true(restore_owner.tabs_data[tab_b].get("outline_focus_line") == 1, f"project session outline focus(b) mismatch: {restore_owner.tabs_data[tab_b]}")
        _assert_true(restore_owner.tabs_data[tab_c].get("outline_focus_line") == 1, f"project session outline focus(c) mismatch: {restore_owner.tabs_data[tab_c]}")

        restore_owner2 = new_owner()
        restore_owner2.last_project_dir = str(project)
        restore_owner2.last_open_file = str(file_a)
        restore_owner2.last_session_files = [str(file_a), str(file_b)]
        restore_owner2.last_session_views = {
            str(file_a): {"cursor": "11.0", "yview": 0.41, "xview": 0.17},
            str(file_b): {"cursor": "4.2", "yview": 0.52, "xview": 0.66},
        }
        restore_owner2.last_session_folds = {
            str(file_a): [1],
            str(file_b): [1],
        }
        restore_owner2.last_session_outline_focus = {
            str(file_a): 1,
            str(file_b): 1,
        }
        restore_owner2.find_var.set("关键字-B")
        restore_owner2.replace_var.set("替换-B")
        ok = flow_try_restore_last_project(restore_owner2)
        _assert_true(ok, "try_restore_last_project should return True for valid project dir")
        tab_a2 = get_tab_id_by_file(restore_owner2, file_a)
        tab_b2 = get_tab_id_by_file(restore_owner2, file_b)
        _assert_true(tab_a2 and tab_b2, f"try_restore should reopen session files: a={tab_a2}, b={tab_b2}")
        editor_a2 = restore_owner2.tabs_data[tab_a2]["editor"]
        editor_b2 = restore_owner2.tabs_data[tab_b2]["editor"]
        _assert_true(editor_a2.index("insert") == "11.0", f"try_restore cursor(a) mismatch: {editor_a2.index('insert')}")
        _assert_true(editor_b2.index("insert") == "4.2", f"try_restore cursor(b) mismatch: {editor_b2.index('insert')}")
        _assert_true(abs(editor_a2.yview()[0] - 0.41) < 1e-9, f"try_restore yview(a) mismatch: {editor_a2.yview()}")
        _assert_true(abs(editor_b2.yview()[0] - 0.52) < 1e-9, f"try_restore yview(b) mismatch: {editor_b2.yview()}")
        _assert_true(abs(editor_a2.xview()[0] - 0.17) < 1e-9, f"try_restore xview(a) mismatch: {editor_a2.xview()}")
        _assert_true(abs(editor_b2.xview()[0] - 0.66) < 1e-9, f"try_restore xview(b) mismatch: {editor_b2.xview()}")
        _assert_true(collapsed_fold_lines(restore_owner2.tabs_data[tab_a2]) == [1], f"try_restore folds(a) mismatch: {restore_owner2.tabs_data[tab_a2].get('folds')}")
        _assert_true(collapsed_fold_lines(restore_owner2.tabs_data[tab_b2]) == [1], f"try_restore folds(b) mismatch: {restore_owner2.tabs_data[tab_b2].get('folds')}")
        _assert_true(restore_owner2.tabs_data[tab_a2].get("outline_focus_line") == 1, f"try_restore outline focus(a) mismatch: {restore_owner2.tabs_data[tab_a2]}")
        _assert_true(restore_owner2.tabs_data[tab_b2].get("outline_focus_line") == 1, f"try_restore outline focus(b) mismatch: {restore_owner2.tabs_data[tab_b2]}")
    print("[OK] project session state rules passed")

def main() -> int:
    print("=== 编辑器逻辑回归开始 ===")
    check_autocomplete_rules()
    check_export_preflight()
    check_core_export_preflight_rules()
    check_semantic_scope_rules()
    check_export_entry_resolution()
    check_export_entry_not_hijacked_by_workspace_root()
    check_export_config_helper_rules()
    check_core_autocomplete_context_rules()
    check_context_snippet_hint_rules()
    check_call_context_helper_rules()
    check_signature_helper_rules()
    check_call_signature_helper_rules()
    check_member_completion_helper_rules()
    check_word_completion_helper_rules()
    check_project_session_state_rules()
    print("=== 编辑器逻辑回归完成：全部通过 ===")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as e:
        safe = str(e).encode("unicode_escape", errors="replace").decode("ascii", errors="replace")
        print(f"[FAIL] 编辑器逻辑回归失败: {safe}")
        raise SystemExit(1)
