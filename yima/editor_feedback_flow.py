"""Issue list, status bar, and diagnose scheduling helpers."""

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
import tkinter as tk


def set_diagnostic_status(owner, text, level="ok"):
    owner.status_diag_var.set(text)
    color_map = {
        "ok": "#C8E6C9",
        "info": "#9CDCFE",
        "warn": "#FFD27F",
        "error": "#FFAB91",
    }
    try:
        owner.status_diag_label.configure(fg=color_map.get(level, "#D4D4D4"))
    except tk.TclError:
        pass


def jump_to_diagnostic(owner, event=None):
    tab_id = owner._get_current_tab_id()
    editor = owner._get_current_editor()
    if not tab_id or tab_id not in owner.tabs_data or not editor:
        return "break"

    问题列表 = build_issue_items(owner, tab_id)
    if not 问题列表:
        owner.status_main_var.set("当前没有可跳转的语法/语义问题")
        return "break"

    导航索引 = int(owner.tabs_data[tab_id].get("diagnostic_nav_index", 0) or 0)
    目标项 = 问题列表[导航索引 % len(问题列表)]
    owner.tabs_data[tab_id]["diagnostic_nav_index"] = (导航索引 + 1) % len(问题列表)

    line = max(1, int(目标项.get("line") or 1))
    col = 目标项.get("col")
    col_index = max(0, int(col) - 1) if col else 0
    target = f"{line}.{col_index}"

    if hasattr(owner, "issue_listbox"):
        try:
            owner.issue_listbox.selection_clear(0, tk.END)
            owner.issue_listbox.selection_set(导航索引 % len(问题列表))
            owner.issue_listbox.activate(导航索引 % len(问题列表))
            issue_update_status(owner)
        except tk.TclError:
            pass

    try:
        editor.mark_set("insert", target)
        editor.see(target)
        editor.focus_set()
        owner._highlight_current_line()
        owner._update_cursor_status()
        owner.status_main_var.set(
            f"已定位问题（{(导航索引 % len(问题列表)) + 1}/{len(问题列表)}）：第 {line} 行"
            + (f"，第 {col} 列" if col else "")
            + f" - {目标项.get('message', '')}"
        )
    except tk.TclError:
        owner.status_main_var.set("错误位置定位失败（行列已变化）")
    return "break"


def build_issue_items(owner, tab_id):
    if not tab_id or tab_id not in owner.tabs_data:
        return []

    data = owner.tabs_data[tab_id]
    结果 = []
    去重键 = set()

    diagnostic = data.get("diagnostic")
    if diagnostic:
        is_warn = str(diagnostic.get("type", "")) == "语义提示"
        if not is_warn:
            行号 = int(diagnostic.get("line") or 1)
            键 = ("error", 行号, diagnostic.get("col"), diagnostic.get("message", ""), "语法")
            if 键 not in 去重键:
                去重键.add(键)
                结果.append(
                    {
                        "level": "error",
                        "line": 行号,
                        "col": diagnostic.get("col"),
                        "message": diagnostic.get("message", ""),
                        "type": diagnostic.get("type", "语法错误"),
                        "category": "语法",
                    }
                )

    for warn in data.get("semantic_warnings", []) or []:
        行号 = int(warn.get("line") or 1)
        分类 = str(warn.get("category", "语义") or "语义")
        键 = ("warn", 行号, warn.get("col"), warn.get("message", ""), 分类)
        if 键 in 去重键:
            continue
        去重键.add(键)
        结果.append(
            {
                "level": "warn",
                "line": 行号,
                "col": warn.get("col"),
                "message": warn.get("message", ""),
                "type": warn.get("type", "语义提示"),
                "category": 分类,
            }
        )

    return 结果


def truncate_issue_message(owner, 文本, 最大长度=44):
    值 = str(文本 or "").strip().replace("\n", " ")
    if len(值) <= 最大长度:
        return 值
    return 值[: max(1, 最大长度 - 1)] + "…"


def format_issue_item(owner, item):
    级别 = str(item.get("level", "warn"))
    前缀 = "[错]" if 级别 == "error" else "[提]"
    分类 = "语法" if 级别 == "error" else str(item.get("category", "语义") or "语义")
    行号 = int(item.get("line") or 1)
    消息 = truncate_issue_message(owner, item.get("message", ""))
    return f"{前缀}[{分类}] L{行号} {消息}"


def update_issue_detail_wrap(owner, event=None):
    if not hasattr(owner, "issue_detail_label"):
        return
    try:
        宽度 = owner.issue_detail_label.winfo_width()
        if event is not None and hasattr(event, "width"):
            宽度 = int(event.width)
        owner.issue_detail_label.configure(wraplength=max(120, int(宽度) - 16))
    except tk.TclError:
        pass


def set_issue_detail_text(owner, text):
    if not hasattr(owner, "issue_detail_var"):
        return
    owner.issue_detail_var.set(str(text or "").strip() or "（当前无选中问题）")


def refresh_issue_list(owner):
    if not hasattr(owner, "issue_listbox"):
        return
    tab_id = owner._get_current_tab_id()
    if not tab_id or tab_id not in owner.tabs_data:
        try:
            owner.issue_listbox.delete(0, tk.END)
            owner.issue_listbox.insert(tk.END, "(当前文件无语法/语义问题)")
            owner.issue_listbox.itemconfig(0, foreground="#777777")
            owner.issue_count_var.set("0")
            set_issue_detail_text(owner, "（当前文件无语法/语义问题）")
        except tk.TclError:
            pass
        return

    问题列表 = build_issue_items(owner, tab_id)
    owner.tabs_data[tab_id]["issue_items"] = 问题列表
    owner.tabs_data[tab_id]["diagnostic_nav_index"] = 0

    try:
        owner.issue_listbox.delete(0, tk.END)
    except tk.TclError:
        return

    if not 问题列表:
        owner.issue_listbox.insert(tk.END, "(当前文件无语法/语义问题)")
        try:
            owner.issue_listbox.itemconfig(0, foreground="#777777")
        except tk.TclError:
            pass
        owner.issue_count_var.set("0")
        set_issue_detail_text(owner, "（当前文件无语法/语义问题）")
        return

    owner.issue_count_var.set(str(len(问题列表)))
    for i, item in enumerate(问题列表):
        显示文本 = format_issue_item(owner, item)
        owner.issue_listbox.insert(tk.END, 显示文本)
        try:
            颜色 = "#FFAB91" if item["level"] == "error" else "#FFD27F"
            owner.issue_listbox.itemconfig(i, foreground=颜色)
        except tk.TclError:
            pass

    owner.issue_listbox.selection_clear(0, tk.END)
    owner.issue_listbox.selection_set(0)
    owner.issue_listbox.activate(0)
    issue_update_status(owner)


def get_selected_issue_item(owner):
    tab_id = owner._get_current_tab_id()
    if not tab_id or tab_id not in owner.tabs_data:
        return None
    selection = owner.issue_listbox.curselection() if hasattr(owner, "issue_listbox") else ()
    if not selection:
        return None
    idx = selection[0]
    items = owner.tabs_data[tab_id].get("issue_items", [])
    if idx < 0 or idx >= len(items):
        return None
    return items[idx]


def issue_update_status(owner, event=None):
    item = get_selected_issue_item(owner)
    if not item:
        set_issue_detail_text(owner, "（当前无选中问题）")
        return
    级别文本 = "错误" if item.get("level") == "error" else "提示"
    分类文本 = "语法" if item.get("level") == "error" else str(item.get("category", "语义") or "语义")
    行号 = int(item.get("line") or 1)
    列号 = item.get("col")
    消息 = str(item.get("message", "") or "").strip()
    owner.status_main_var.set(f"问题列表：{级别文本}/{分类文本}（第 {item['line']} 行）- {item.get('message', '')}")
    详情文本 = (
        f"级别：{级别文本}    分类：{分类文本}\n"
        f"位置：第 {行号} 行" + (f"，第 {列号} 列" if 列号 else "") + "\n"
        f"详情：{消息 if 消息 else '（无详细信息）'}"
    )
    set_issue_detail_text(owner, 详情文本)


def on_issue_activate(owner, event=None):
    item = get_selected_issue_item(owner)
    editor = owner._get_current_editor()
    if not item or not editor:
        return "break"

    line = max(1, int(item.get("line") or 1))
    col = item.get("col")
    col_index = max(0, int(col) - 1) if col else 0
    target = f"{line}.{col_index}"

    try:
        editor.mark_set("insert", target)
        editor.see(target)
        editor.focus_set()
        owner._highlight_current_line()
        owner._update_cursor_status()
        owner.status_main_var.set(
            f"已定位问题：第 {line} 行" + (f"，第 {col} 列" if col else "") + f" - {item.get('message', '')}"
        )
        issue_update_status(owner)
    except tk.TclError:
        owner.status_main_var.set("问题位置定位失败（行列已变化）")
    return "break"


def update_status_main(owner):
    tab_id = owner._get_current_tab_id()
    if not tab_id or tab_id not in owner.tabs_data:
        owner.status_main_var.set("就绪")
        return
    filepath = owner.tabs_data[tab_id].get("filepath", "未命名代码.ym")
    display_name = os.path.basename(filepath) if filepath != "未命名代码.ym" else "未命名代码.ym"
    dirty_hint = "（未保存）" if owner.tabs_data[tab_id].get("dirty") else "（已保存）"
    owner.status_main_var.set(f"文件：{display_name} {dirty_hint}")


def update_cursor_status(owner, event=None):
    editor = owner._get_current_editor()
    if not editor:
        return
    try:
        line, col = editor.index("insert").split(".")
        owner.status_pos_var.set(f"行 {int(line)}，列 {int(col) + 1}")
    except (ValueError, tk.TclError):
        pass
    update_status_main(owner)


def on_editor_modified(owner, event):
    editor = event.widget
    try:
        if not editor.edit_modified():
            return
    except tk.TclError:
        return

    tab_id = owner._get_tab_id_by_editor(editor)
    if tab_id and tab_id in owner.tabs_data:
        if not owner.tabs_data[tab_id].get("dirty"):
            owner.tabs_data[tab_id]["dirty"] = True
            owner._update_tab_title(tab_id)
            if tab_id == owner._get_current_tab_id():
                owner._update_status_main()
        # 代码发生变更后，旧折叠范围可能失效，自动展开并重算
        if owner.tabs_data[tab_id].get("folds"):
            owner._clear_all_folds(tab_id)
        if tab_id == owner._get_current_tab_id():
            owner._schedule_highlight()
            owner._schedule_diagnose()
            owner._schedule_outline_update()
            owner._update_line_numbers()
            owner._update_cursor_status()
    editor.edit_modified(False)


def schedule_diagnose(owner, event=None):
    if owner._diagnose_after_id:
        try:
            owner.root.after_cancel(owner._diagnose_after_id)
        except tk.TclError:
            pass
    owner._diagnose_after_id = owner.root.after(120, owner._run_live_diagnose)


# ===== merged from yima/editor_diagnose_flow.py =====
import os
import tkinter as tk

from yima.editor_logic_core import (
    collect_block_declarations as core_collect_block_declarations,
    default_module_alias as core_default_module_alias,
    semantic_analyze as core_semantic_analyze,
    semantic_locate_yima_module as core_semantic_locate_yima_module,
    semantic_module_search_paths as core_semantic_module_search_paths,
    semantic_read_module_export_details as core_semantic_read_module_export_details,
    semantic_read_module_export_signatures as core_semantic_read_module_export_signatures,
    semantic_read_module_exports as core_semantic_read_module_exports,
)
from yima.词法分析 import 词法分析器
from yima.语法分析 import 语法分析器
from yima.错误 import 易码错误


def default_module_alias(owner, 模块名):
    return core_default_module_alias(模块名)


def collect_block_declarations(owner, 语句列表):
    return core_collect_block_declarations(语句列表, default_alias_resolver=owner._默认模块别名)


def semantic_module_search_paths(owner, tab_id=None):
    return core_semantic_module_search_paths(
        owner.workspace_dir,
        tabs_data=owner.tabs_data,
        tab_id=tab_id,
        current_workdir=os.getcwd(),
    )


def semantic_locate_yima_module(owner, 模块名, tab_id=None):
    return core_semantic_locate_yima_module(模块名, semantic_module_search_paths(owner, tab_id))


def semantic_read_module_exports(owner, 模块路径):
    return core_semantic_read_module_exports(
        模块路径,
        owner._semantic_module_cache,
        owner._格式化参数签名,
        default_alias_resolver=owner._默认模块别名,
    )


def semantic_read_module_export_details(owner, 模块路径):
    return core_semantic_read_module_export_details(
        模块路径,
        owner._semantic_module_cache,
        owner._格式化参数签名,
        default_alias_resolver=owner._默认模块别名,
    )


def semantic_read_module_export_signatures(owner, 模块路径):
    return core_semantic_read_module_export_signatures(
        模块路径,
        owner._semantic_module_cache,
        owner._格式化参数签名,
        default_alias_resolver=owner._默认模块别名,
    )


def semantic_analyze(owner, 语法树, tab_id=None):
    return core_semantic_analyze(
        语法树,
        owner.builtin_words,
        default_alias_resolver=owner._默认模块别名,
        collect_block_declarations_func=owner._收集块声明,
    )


def run_live_diagnose(owner):
    owner._diagnose_after_id = None
    editor = owner._get_current_editor()
    tab_id = owner._get_current_tab_id()
    if not editor or not tab_id or tab_id not in owner.tabs_data:
        return

    editor.tag_remove("ErrorLine", "1.0", "end")
    editor.tag_remove("WarnLine", "1.0", "end")
    code = editor.get("1.0", "end-1c")
    if not code.strip():
        owner.tabs_data[tab_id]["diagnostic"] = None
        owner.tabs_data[tab_id]["semantic_warnings"] = []
        owner.tabs_data[tab_id]["issue_items"] = []
        owner.tabs_data[tab_id]["diagnostic_nav_index"] = 0
        owner._set_diagnostic_status("语法检查：等待输入", level="info")
        owner._refresh_issue_list()
        return

    try:
        tokens = 词法分析器(code).分析()
        语法树 = 语法分析器(tokens).解析()
        语义警告 = owner._语义分析(语法树, tab_id=tab_id)
        owner.tabs_data[tab_id]["semantic_warnings"] = 语义警告

        if 语义警告:
            首条 = 语义警告[0]
            line = int(首条.get("line") or 1)
            col = 首条.get("col")
            try:
                editor.tag_add("WarnLine", f"{line}.0", f"{line}.end+1c")
            except tk.TclError:
                pass
            owner.tabs_data[tab_id]["diagnostic"] = 首条
            owner._set_diagnostic_status(
                f"语义提示：第 {line} 行" + (f"，列 {col}" if col else "") + f" - {首条.get('message', '')}（共 {len(语义警告)} 处）",
                level="warn",
            )
        else:
            owner.tabs_data[tab_id]["diagnostic"] = None
            owner._set_diagnostic_status("语法检查：通过", level="ok")
        owner._refresh_issue_list()
    except 易码错误 as e:
        line = int(e.行号) if e.行号 else 1
        line = max(1, line)
        col = int(e.列号) if e.列号 else None
        try:
            editor.tag_add("ErrorLine", f"{line}.0", f"{line}.end+1c")
        except tk.TclError:
            pass

        error_text = str(e.消息).replace("\n", " ")
        col_text = f"，列 {col}" if col else ""
        owner.tabs_data[tab_id]["diagnostic"] = {
            "line": line,
            "col": col,
            "message": error_text,
            "type": e.错误类型,
        }
        owner.tabs_data[tab_id]["semantic_warnings"] = []
        owner._set_diagnostic_status(f"{e.错误类型}：第 {line} 行{col_text} - {error_text}", level="error")
        owner._refresh_issue_list()
    except Exception as e:
        owner.tabs_data[tab_id]["diagnostic"] = None
        owner.tabs_data[tab_id]["semantic_warnings"] = []
        owner._set_diagnostic_status(f"语法检查失败：{e}", level="error")
        owner._refresh_issue_list()


# ===== merged from yima/editor_highlight_flow.py =====
import re
import tkinter as tk

from yima.editor_logic_core import extract_import_alias_map as core_extract_import_alias_map


def highlight(owner, event=None):
    editor = owner._get_current_editor()
    if not editor:
        return
    owner._highlight_after_id = None

    code = editor.get("1.0", "end-1c")

    # 先清除所有高亮
    for tag in ["Define", "Keyword", "Operator", "String", "Number", "Comment", "Boolean", "Builtin", "ModuleAlias", "ObjectRef", "MemberName"]:
        editor.tag_remove(tag, "1.0", "end")

    # 1. 高亮数字 (包含小数)
    for match in re.finditer(r"\b\d+(\.\d+)?\b", code):
        start_idx = f"1.0 + {match.start()}c"
        end_idx = f"1.0 + {match.end()}c"
        editor.tag_add("Number", start_idx, end_idx)

    # 2. 高亮字符串 (双引号包含的内容)
    for match in re.finditer(r'"[^"]*"', code):
        start_idx = f"1.0 + {match.start()}c"
        end_idx = f"1.0 + {match.end()}c"
        editor.tag_add("String", start_idx, end_idx)

    # 3. 高亮注释 (# 开始到行尾)
    for match in re.finditer(r"#.*", code):
        start_idx = f"1.0 + {match.start()}c"
        end_idx = f"1.0 + {match.end()}c"
        editor.tag_add("Comment", start_idx, end_idx)

    # 4. 高亮关键字与操作符
    # Define 控制结构定义
    defines = ["功能", "返回", "叫做", "尝试", "如果出错", "定义图纸", "造一个", "它的"]

    # Keyword 流程控制
    keywords = ["如果", "就", "否则如果", "不然", "当", "的时候", "重复", "次", "遍历", "里的每一个", "停下", "略过", "引入"]

    operators = ["而且", "并且", "或者", "取反", "!", "+", "-", "*", "/", "%", "**", "//", "==", "!=", ">", "<", ">=", "<="]

    booleans = ["对", "错", "空"]

    builtins_list = owner.builtin_words

    def apply_tags(word_list, tag_name):
        # 将单词按长度降序排列，保证长词(如有包含关系)优先被匹配
        for kw in sorted(word_list, key=len, reverse=True):
            start = "1.0"
            while True:
                # 使用精确字面量匹配
                start = editor.search(kw, start, stopindex="end")
                if not start:
                    break

                end = f"{start} + {len(kw)}c"

                # ★ 全词边界检测：防止 "长度" 匹配到 "长度值"，"错" 匹配到 "错误信息"
                is_word = True
                # 检查前一个字符
                try:
                    prev_char = editor.get(f"{start} - 1c", start)
                    if prev_char and re.match(r"[\u4e00-\u9fa5a-zA-Z0-9_]", prev_char):
                        is_word = False
                except tk.TclError:
                    pass
                # 检查后一个字符
                if is_word:
                    try:
                        next_char = editor.get(end, f"{end} + 1c")
                        if next_char and re.match(r"[\u4e00-\u9fa5a-zA-Z0-9_]", next_char):
                            # 特殊豁免：操作符后面紧跟中文是允许的（如 "==" 后跟条件）
                            if tag_name != "Operator":
                                is_word = False
                    except tk.TclError:
                        pass

                # 防止破坏已经高亮的字符串、注释，或者已经被标记的更高优先级结构
                existing_tags = editor.tag_names(start)
                conflict_tags = ["String", "Comment", "Define", "Keyword", "Operator", "Boolean", "Builtin"]

                if is_word and not any(t in existing_tags for t in conflict_tags):
                    editor.tag_add(tag_name, start, end)

                start = end

    apply_tags(defines, "Define")
    apply_tags(keywords, "Keyword")
    apply_tags(operators, "Operator")
    apply_tags(booleans, "Boolean")
    apply_tags(builtins_list, "Builtin")

    # 5. 高亮对象成员调用：对象.成员
    #    - 模块别名对象（来自 引入 ... 叫做 ...）用 ModuleAlias
    #    - 其他对象名用 ObjectRef
    #    - 点后的成员名统一用 MemberName
    别名集合 = set(core_extract_import_alias_map(code).keys())
    标识符模式 = r"[\u4e00-\u9fa5A-Za-z_][\u4e00-\u9fa5A-Za-z0-9_]*"

    def 在字符串或注释内(索引):
        标签 = editor.tag_names(索引)
        return ("String" in 标签) or ("Comment" in 标签)

    for match in re.finditer(rf"({标识符模式})\.({标识符模式})", code):
        obj_start = f"1.0 + {match.start(1)}c"
        obj_end = f"1.0 + {match.end(1)}c"
        member_start = f"1.0 + {match.start(2)}c"
        member_end = f"1.0 + {match.end(2)}c"
        if 在字符串或注释内(obj_start):
            continue
        obj_name = match.group(1)
        obj_tag = "ModuleAlias" if obj_name in 别名集合 else "ObjectRef"
        editor.tag_add(obj_tag, obj_start, obj_end)
        editor.tag_add("MemberName", member_start, member_end)

    # 6. 高亮正在输入的对象点号（如 系统.）
    for match in re.finditer(rf"({标识符模式})\.(?=\s|$|[)\],])", code):
        obj_start = f"1.0 + {match.start(1)}c"
        obj_end = f"1.0 + {match.end(1)}c"
        if 在字符串或注释内(obj_start):
            continue
        obj_name = match.group(1)
        obj_tag = "ModuleAlias" if obj_name in 别名集合 else "ObjectRef"
        editor.tag_add(obj_tag, obj_start, obj_end)
