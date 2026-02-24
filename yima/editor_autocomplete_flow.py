"""Autocomplete interaction flow helpers extracted from 易码编辑器.py."""

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
import tkinter as tk

from yima.editor_logic_core import (
    collect_context_snippet_hints as core_collect_context_snippet_hints,
    extract_member_completion_target as core_extract_member_completion_target,
    extract_word_completion_prefix as core_extract_word_completion_prefix,
    first_argument_span_offset as core_first_argument_span_offset,
    member_completion_seed as core_member_completion_seed,
    merge_member_completion_fallback as core_merge_member_completion_fallback,
    normalize_completion_signature as core_normalize_completion_signature,
    rank_member_completion_candidates as core_rank_member_completion_candidates,
    rank_word_completion_candidates as core_rank_word_completion_candidates,
)


def trigger_autocomplete(owner, event=None):
    owner._check_autocomplete(event=None)
    return "break"


def schedule_calltip_update(owner, event=None):
    try:
        owner.root.after_idle(owner._update_calltip)
    except Exception:
        pass


def autocomplete_is_visible(owner):
    try:
        return bool(owner.autocomplete_popup.winfo_ismapped())
    except Exception:
        return False


def is_autocomplete_widget(owner, 控件):
    当前 = 控件
    for _ in range(8):
        if 当前 is None:
            return False
        if 当前 is owner.autocomplete_popup or 当前 is owner.autocomplete_tree:
            return True
        当前 = getattr(当前, "master", None)
    return False


def autocomplete_select_index(owner, 索引):
    总数 = len(owner._autocomplete_row_ids)
    if 总数 <= 0:
        return
    idx = max(0, min(总数 - 1, int(索引)))
    行id = owner._autocomplete_row_ids[idx]
    try:
        owner.autocomplete_tree.selection_set(行id)
        owner.autocomplete_tree.focus(行id)
        owner.autocomplete_tree.see(行id)
    except tk.TclError:
        pass


def autocomplete_current_index(owner):
    if not owner._autocomplete_row_ids:
        return 0
    try:
        选择项 = owner.autocomplete_tree.selection()
        if 选择项:
            return max(0, owner._autocomplete_row_ids.index(选择项[0]))
        焦点项 = owner.autocomplete_tree.focus()
        if 焦点项:
            return max(0, owner._autocomplete_row_ids.index(焦点项))
    except Exception:
        pass
    return 0


def autocomplete_index_from_event(owner, event=None):
    if event is None or not hasattr(event, "y"):
        return None
    try:
        行id = owner.autocomplete_tree.identify_row(event.y)
        if not 行id:
            return None
        return owner._autocomplete_row_ids.index(行id)
    except Exception:
        return None


def on_autocomplete_mouse_press(owner, event=None):
    idx = autocomplete_index_from_event(owner, event)
    if idx is None:
        # 点击分组标题或空白时，不改变当前可插入候选。
        return "break"
    owner._autocomplete_mouse_down = True
    autocomplete_select_index(owner, idx)
    try:
        owner.autocomplete_tree.focus_set()
    except tk.TclError:
        pass
    return None


def on_editor_focus_out(owner, event=None):
    # 点击补全列表时，编辑器会先失焦；延后判断可避免误隐藏
    owner.root.after(20, owner._hide_autocomplete_if_focus_lost)


def hide_autocomplete_if_focus_lost(owner):
    if not autocomplete_is_visible(owner):
        return
    if owner._autocomplete_mouse_down:
        try:
            鼠标控件 = owner.root.winfo_containing(owner.root.winfo_pointerx(), owner.root.winfo_pointery())
        except tk.TclError:
            鼠标控件 = None
        if is_autocomplete_widget(owner, 鼠标控件):
            return
        owner._autocomplete_mouse_down = False
    焦点控件 = owner.root.focus_get()
    if is_autocomplete_widget(owner, 焦点控件):
        return
    try:
        鼠标控件 = owner.root.winfo_containing(owner.root.winfo_pointerx(), owner.root.winfo_pointery())
        if is_autocomplete_widget(owner, 鼠标控件):
            return
    except tk.TclError:
        pass
    owner._hide_autocomplete()
    owner._hide_calltip()


def hide_autocomplete(owner):
    try:
        owner.autocomplete_popup.place_forget()
    except tk.TclError:
        pass
    try:
        for 行id in owner.autocomplete_tree.get_children():
            owner.autocomplete_tree.delete(行id)
    except tk.TclError:
        pass
    owner._autocomplete_items = []
    owner._autocomplete_row_ids = []
    owner._autocomplete_replace_start = None
    owner._autocomplete_replace_end = None
    owner._autocomplete_popup_line = None
    owner._autocomplete_mouse_down = False


def hide_calltip(owner):
    try:
        owner.calltip_popup.place_forget()
    except tk.TclError:
        pass


def check_autocomplete(owner, event=None):
    # 排除 Ctrl 组合键（手动触发除外）
    if event and (event.state & 0x4):
        owner._hide_autocomplete()
        owner._hide_calltip()
        return
    if event and event.keysym in ("Up", "Down", "Left", "Right", "Prior", "Next", "Return", "KP_Enter", "Tab", "Escape"):
        if event.keysym == "Escape":
            owner._hide_autocomplete()
            owner._hide_calltip()
        elif event.keysym in ("Left", "Right", "Up", "Down", "Prior", "Next"):
            owner._schedule_calltip_update()
        elif event.keysym in ("Return", "KP_Enter", "Tab"):
            owner._schedule_calltip_update()
        return

    editor = owner._get_current_editor()
    tab_id = owner._get_current_tab_id()
    if not editor:
        return

    全文 = editor.get("1.0", "end-1c")
    行前文本 = editor.get("insert linestart", "insert")
    try:
        光标行 = int(editor.index("insert").split(".")[0])
    except Exception:
        光标行 = 1
    上下文 = owner._收集补全上下文(全文, tab_id=tab_id, 光标行=光标行)
    owner._update_calltip(editor=editor, tab_id=tab_id, 全文=全文, 行前文本=行前文本, 上下文=上下文)

    点号匹配 = core_extract_member_completion_target(行前文本)
    if 点号匹配:
        对象名, 成员前缀 = 点号匹配
        成员候选集合, 成员类型映射, 成员签名映射 = core_member_completion_seed(上下文, 对象名)

        if not 成员候选集合:
            跨标签模块 = owner._跨标签查别名模块(对象名, 当前tab_id=tab_id)
            if 跨标签模块:
                跨标签详情 = owner._获取模块补全成员详情(跨标签模块, tab_id=tab_id)
                跨标签签名 = owner._获取模块补全成员签名(跨标签模块, tab_id=tab_id)
                跨标签成员 = set()
                if not 跨标签详情:
                    跨标签成员 = set(owner._获取模块补全成员(跨标签模块, tab_id=tab_id))
                成员候选集合, 成员类型映射, 成员签名映射 = core_merge_member_completion_fallback(
                    成员候选集合,
                    成员类型映射,
                    成员签名映射,
                    fallback_details=跨标签详情,
                    fallback_signatures=跨标签签名,
                    fallback_members=跨标签成员,
                )

        排名列表 = core_rank_member_completion_candidates(
            成员候选集合,
            成员前缀,
            成员类型映射,
            成员签名映射,
            owner._autocomplete_match,
        )
        if not 排名列表:
            owner._hide_autocomplete()
            return

        owner._autocomplete_replace_start = "insert" if not 成员前缀 else f"insert - {len(成员前缀)}c"
        owner._autocomplete_replace_end = "insert"
        owner._展示自动补全候选(editor, owner._sort_autocomplete_candidates(排名列表))
        return

    当前词 = core_extract_word_completion_prefix(行前文本)
    if not 当前词:
        owner._hide_autocomplete()
        return

    上下文建议 = core_collect_context_snippet_hints(全文, 光标行)
    排名列表 = core_rank_word_completion_candidates(
        当前词,
        上下文,
        owner.autocomplete_words,
        owner.snippets,
        owner.builtin_words,
        owner._builtin_signature_of,
        owner._autocomplete_match,
        context_snippets=上下文建议,
    )
    # 关闭“上下文自由词”补全：避免把注释/随手文本当成候选，确保补全结果更真实可用。

    if not 排名列表:
        owner._hide_autocomplete()
        return

    owner._autocomplete_replace_start = f"insert - {len(当前词)}c"
    owner._autocomplete_replace_end = "insert"
    排序后 = owner._sort_autocomplete_candidates(排名列表)
    owner._展示自动补全候选(editor, 排序后)


def handle_autocomplete_nav(owner, event):
    if not autocomplete_is_visible(owner):
        return  # 交给系统默认处理

    总数 = len(owner._autocomplete_row_ids)
    if 总数 <= 0:
        return "break"

    idx = autocomplete_current_index(owner)

    if event.keysym == "Up":
        idx = max(0, idx - 1)
    elif event.keysym == "Down":
        idx = min(总数 - 1, idx + 1)
    elif event.keysym == "Prior":
        idx = max(0, idx - 8)
    elif event.keysym == "Next":
        idx = min(总数 - 1, idx + 8)

    autocomplete_select_index(owner, idx)
    return "break"  # 阻止光标移动


def accept_autocomplete(owner, event=None):
    if not autocomplete_is_visible(owner):
        return "break"
    owner._autocomplete_mouse_down = False

    idx = autocomplete_index_from_event(owner, event)
    if event is not None and hasattr(event, "y") and idx is None:
        # 鼠标点在分组标题/空白时，不执行插入。
        return "break"
    if idx is None:
        idx = autocomplete_current_index(owner)

    if idx < 0 or idx >= len(owner._autocomplete_items):
        owner._hide_autocomplete()
        return "break"

    当前候选 = owner._autocomplete_items[idx]
    selected_word = str(当前候选.get("insert", "")).strip()
    selected_source = str(当前候选.get("source", "")).strip()
    selected_sig = str(当前候选.get("sig", "") or "").strip()
    selected_callable = bool(当前候选.get("callable", False))
    if not selected_word:
        owner._hide_autocomplete()
        return "break"

    editor = owner._get_current_editor()
    if not editor:
        owner._hide_autocomplete()
        return "break"

    start_index = owner._autocomplete_replace_start
    end_index = owner._autocomplete_replace_end or "insert"
    if not start_index:
        line_text = editor.get("insert linestart", "insert")
        match = re.search(r"([\u4e00-\u9fa5A-Za-z0-9_]+)$", line_text)
        if match:
            start_index = f"insert - {len(match.group(1))}c"
        else:
            start_index = "insert"

    try:
        insert_pos = editor.index("insert")
        start_pos = editor.index(start_index)
        end_pos = editor.index(end_index)

        当前行 = insert_pos.split(".")[0]
        起始行 = start_pos.split(".")[0]
        结束行 = end_pos.split(".")[0]
        跨行或错序 = 起始行 != 当前行 or 结束行 != 当前行 or editor.compare(start_pos, ">", end_pos)
        if 跨行或错序:
            line_text = editor.get("insert linestart", "insert")
            match = re.search(r"([\u4e00-\u9fa5A-Za-z0-9_]+)$", line_text)
            if match:
                start_pos = editor.index(f"insert - {len(match.group(1))}c")
            else:
                start_pos = insert_pos
            end_pos = insert_pos

        editor.delete(start_pos, end_pos)
        editor.insert(start_pos, selected_word)
        末尾位置 = editor.index(f"{start_pos} + {len(selected_word)}c")

        自动补括号来源 = {"function", "member", "member_func", "imported", "imported_func", "builtin_func", "member_class", "imported_class"}
        需要参数提示强调 = False
        if selected_callable or (selected_source in 自动补括号来源):
            前瞻文本 = editor.get(末尾位置, f"{末尾位置}+6c")
            if not re.match(r"^\s*[\(（]", 前瞻文本 or ""):
                调用片段 = core_normalize_completion_signature(selected_sig)
                editor.insert(末尾位置, 调用片段)
                占位偏移 = core_first_argument_span_offset(调用片段)
                if 占位偏移:
                    起偏移, 止偏移 = 占位偏移
                    sel_start = editor.index(f"{末尾位置}+{起偏移}c")
                    sel_end = editor.index(f"{末尾位置}+{止偏移}c")
                    editor.tag_remove("sel", "1.0", "end")
                    editor.tag_add("sel", sel_start, sel_end)
                    editor.mark_set("insert", sel_end)
                else:
                    editor.mark_set("insert", f"{末尾位置}+1c")
            else:
                # 已手动输入括号时，光标跳到括号内
                括号匹配 = re.search(r"[\(（]", 前瞻文本 or "")
                偏移 = (括号匹配.start() + 1) if 括号匹配 else 1
                editor.mark_set("insert", f"{末尾位置}+{偏移}c")
            需要参数提示强调 = True
        else:
            editor.mark_set("insert", 末尾位置)

        editor.focus_set()
        owner.highlight()
        if 需要参数提示强调:
            owner._update_calltip(editor=editor, tab_id=owner._get_current_tab_id(), emphasize=True)
    except tk.TclError:
        pass

    owner._hide_autocomplete()
    owner._schedule_calltip_update()
    return "break"


# ===== merged from yima/editor_autocomplete_render_flow.py =====
import tkinter as tk
from tkinter import font as tkfont

from yima.editor_logic_core import (
    autocomplete_match as core_autocomplete_match,
    autocomplete_source_group as core_autocomplete_source_group,
    autocomplete_source_priority as core_autocomplete_source_priority,
)


def autocomplete_match(owner, 候选词, 前缀):
    return core_autocomplete_match(候选词, 前缀, fuzzy_enabled=owner.autocomplete_fuzzy_enabled)


def autocomplete_source_priority(owner, 来源):
    return core_autocomplete_source_priority(来源)


def autocomplete_source_group(owner, 来源):
    return core_autocomplete_source_group(来源)


def sort_autocomplete_candidates(owner, 候选列表):
    def 排序键(候选):
        词 = str((候选 or {}).get("insert", "") or "")
        来源 = str((候选 or {}).get("source", "") or "")
        分数 = float((候选 or {}).get("score", 0.0) or 0.0)
        return (
            owner._autocomplete_source_priority(来源),
            分数,
            len(词),
            词,
        )

    return sorted(list(候选列表 or []), key=排序键)


def show_autocomplete_candidates(owner, editor, 排序候选):
    owner._autocomplete_items = []
    owner._autocomplete_row_ids = []
    try:
        for 行id in owner.autocomplete_tree.get_children():
            owner.autocomplete_tree.delete(行id)
    except tk.TclError:
        pass
    显示内容列表 = []
    显示标签列表 = []

    标签映射 = {
        "snippet": "模板",
        "builtin": "内置能力",
        "builtin_func": "内置功能",
        "keyword": "关键字",
        "function": "功能",
        "blueprint": "图纸",
        "alias": "模块别名",
        "module": "模块名",
        "member": "模块成员",
        "member_func": "模块功能",
        "member_blueprint": "模块图纸",
        "member_class": "模块类",
        "member_var": "模块变量",
        "member_alias": "模块别名",
        "imported": "已引入",
        "imported_func": "已引入功能",
        "imported_blueprint": "已引入图纸",
        "imported_class": "已引入类",
        "imported_var": "已引入变量",
        "imported_alias": "已引入别名",
        "variable": "变量",
        "local_word": "上下文词",
    }
    颜色映射 = {
        "snippet": "#9CDCFE",
        "builtin": "#DCDCAA",
        "builtin_func": "#DCDCAA",
        "keyword": "#C586C0",
        "function": "#4FC1FF",
        "blueprint": "#C586C0",
        "alias": "#B5CEA8",
        "module": "#CE9178",
        "member": "#E8E8E8",
        "member_func": "#4FC1FF",
        "member_blueprint": "#C586C0",
        "member_class": "#FFB86C",
        "member_var": "#7BD88F",
        "member_alias": "#B5CEA8",
        "imported": "#FFD27F",
        "imported_func": "#4FC1FF",
        "imported_blueprint": "#C586C0",
        "imported_class": "#FFB86C",
        "imported_var": "#7BD88F",
        "imported_alias": "#B5CEA8",
        "variable": "#7BD88F",
        "local_word": "#9AA6B2",
    }
    分组标题颜色 = "#8FA1B8"
    分组标题字体 = ("Microsoft YaHei", 9, "bold")
    try:
        owner.autocomplete_tree.tag_configure("group_header", foreground=分组标题颜色, font=分组标题字体)
    except tk.TclError:
        pass

    最大候选数 = max(8, int(getattr(owner, "autocomplete_max_items", 16) or 16))
    当前分组键 = None
    分组序号 = 0
    for _, 候选 in enumerate(排序候选[:最大候选数]):
        if isinstance(候选, dict):
            来源 = str(候选.get("source", "")).strip()
            词 = str(候选.get("insert", "")).strip()
            签名 = str(候选.get("sig", "")).strip()
            可调用 = bool(候选.get("callable", False))
        else:
            来源 = str(候选[1] if len(候选) > 1 else "").strip()
            词 = str(候选[2] if len(候选) > 2 else "").strip()
            签名 = str(候选[3] if len(候选) > 3 else "").strip()
            可调用 = bool(候选[4]) if len(候选) > 4 else False
        if not 词:
            continue
        分组键, 分组标题 = owner._autocomplete_source_group(来源)
        if 分组键 != 当前分组键:
            当前分组键 = 分组键
            分组序号 += 1
            try:
                分组id = f"ac_group_{分组键}_{分组序号}"
                owner.autocomplete_tree.insert("", "end", iid=分组id, values=(f"【{分组标题}】", ""), tags=("group_header",))
            except tk.TclError:
                pass
        标签 = 标签映射.get(来源, "上下文")
        显示内容 = f"{词}{签名}" if 签名 else 词
        owner._autocomplete_items.append(
            {
                "insert": 词,
                "source": 来源,
                "sig": 签名,
                "callable": 可调用,
            }
        )
        显示标签列表.append(标签)
        显示内容列表.append(显示内容)
        try:
            行id = f"ac_{len(owner._autocomplete_row_ids)}"
            标签名 = f"src_{来源}" if 来源 else "src_default"
            owner.autocomplete_tree.insert("", "end", iid=行id, values=(标签, 显示内容), tags=(标签名,))
            owner._autocomplete_row_ids.append(行id)
            owner.autocomplete_tree.tag_configure(标签名, foreground=颜色映射.get(来源, owner.theme_fg))
        except tk.TclError:
            pass

    if not owner._autocomplete_items:
        owner._hide_autocomplete()
        return

    owner._autocomplete_select_index(0)
    try:
        owner._autocomplete_popup_line = editor.index("insert").split(".")[0]
    except Exception:
        owner._autocomplete_popup_line = None

    bbox = editor.bbox("insert")
    if not bbox:
        owner._hide_autocomplete()
        return
    x, y, _, height = bbox
    root_x = editor.winfo_rootx() - owner.root.winfo_rootx() + x + 5
    root_y = editor.winfo_rooty() - owner.root.winfo_rooty() + y + height + 5

    try:
        owner.root.update_idletasks()
        字体对象 = tkfont.Font(font=owner.font_code)
        最大标签宽 = max((字体对象.measure(t) for t in 显示标签列表), default=80)
        最大内容宽 = max((字体对象.measure(t) for t in 显示内容列表), default=260)
        类型列宽 = max(92, min(180, 最大标签宽 + 28))
        内容列宽 = max(260, 最大内容宽 + 28)
        根宽度 = max(420, int(owner.root.winfo_width()))
        目标宽度 = max(420, 类型列宽 + 内容列宽 + 26)
        可用最大宽度 = max(320, 根宽度 - 16)
        列表宽度 = min(目标宽度, 可用最大宽度)
        if root_x + 列表宽度 > 根宽度 - 8:
            root_x = max(8, 根宽度 - 列表宽度 - 8)

        行高 = max(20, 字体对象.metrics("linespace") + 6)
        try:
            总可见项 = len(owner.autocomplete_tree.get_children())
        except tk.TclError:
            总可见项 = len(owner._autocomplete_items)
        可见行数 = min(max(4, 总可见项), 12)
        标题高度 = 26
        水平滚动条高度 = max(12, int(16 * owner.dpi_scale))
        列表高度 = max(140, 标题高度 + 行高 * 可见行数 + 水平滚动条高度 + 8)

        最终内容列宽 = max(180, 列表宽度 - 类型列宽 - 20)
        owner.autocomplete_tree.column("kind", width=类型列宽, minwidth=88, stretch=False)
        owner.autocomplete_tree.column("item", width=最终内容列宽, minwidth=180, stretch=True)
        owner.autocomplete_popup.place(x=root_x, y=root_y, width=列表宽度, height=列表高度)
    except Exception:
        owner.autocomplete_popup.place(x=root_x, y=root_y)
    owner.autocomplete_popup.lift()


# ===== merged from yima/editor_calltip_flow.py =====
import tkinter as tk
from tkinter import font as tkfont

from yima.editor_logic_core import (
    extract_call_context as core_extract_call_context,
    highlight_current_signature_param as core_highlight_current_signature_param,
    resolve_call_expression_signature as core_resolve_call_expression_signature,
)
from yima.解释器 import 解释器


def flash_calltip(owner):
    try:
        if owner._calltip_flash_after_id:
            try:
                owner.root.after_cancel(owner._calltip_flash_after_id)
            except tk.TclError:
                pass
            owner._calltip_flash_after_id = None
        owner.calltip_popup.configure(
            bg="#16304A",
            highlightbackground="#6CB2FF",
            highlightcolor="#6CB2FF",
        )
        owner.calltip_label.configure(bg="#16304A", fg="#FFFFFF")

        def _恢复():
            try:
                owner.calltip_popup.configure(
                    bg="#0F1B2B",
                    highlightbackground="#2B4664",
                    highlightcolor="#2B4664",
                )
                owner.calltip_label.configure(bg="#0F1B2B", fg="#DCEBFF")
            except tk.TclError:
                pass
            owner._calltip_flash_after_id = None

        owner._calltip_flash_after_id = owner.root.after(260, _恢复)
    except tk.TclError:
        owner._calltip_flash_after_id = None


def show_calltip(owner, editor, 文本, emphasize=False):
    if not editor:
        owner._hide_calltip()
        return
    内容文本 = str(文本 or "").strip()
    if not 内容文本:
        owner._hide_calltip()
        return

    bbox = editor.bbox("insert")
    if not bbox:
        owner._hide_calltip()
        return

    try:
        owner.calltip_label.configure(text=内容文本)
        owner.root.update_idletasks()
        字体对象 = tkfont.Font(font=owner.calltip_label.cget("font"))
        文本行列表 = [行 for 行 in 内容文本.splitlines() if 行] or [内容文本]
        最大行宽 = max((字体对象.measure(行) for 行 in 文本行列表), default=200)
        文字宽度 = max(220, 最大行宽 + 20)
        根宽度 = max(420, int(owner.root.winfo_width()))
        最大宽度 = max(260, 根宽度 - 16)
        提示宽度 = min(文字宽度, 最大宽度)
        行高 = max(16, 字体对象.metrics("linespace"))
        提示高度 = max(30, 行高 * len(文本行列表) + 14)

        x, y, _, 行高 = bbox
        root_x = editor.winfo_rootx() - owner.root.winfo_rootx() + x + 4
        root_y = editor.winfo_rooty() - owner.root.winfo_rooty() + y - 提示高度 - 6
        if root_y < 8:
            root_y = editor.winfo_rooty() - owner.root.winfo_rooty() + y + 行高 + 4
        if root_x + 提示宽度 > 根宽度 - 8:
            root_x = max(8, 根宽度 - 提示宽度 - 8)

        owner.calltip_popup.place(x=root_x, y=root_y, width=提示宽度, height=提示高度)
        owner.calltip_popup.lift()
        if emphasize:
            flash_calltip(owner)
    except Exception:
        owner._hide_calltip()


def ensure_runtime_builtin_signatures(owner):
    if owner._runtime_builtin_signature_loaded:
        return
    owner._runtime_builtin_signature_loaded = True
    try:
        临时解释器 = 解释器()
        记录本 = dict(getattr(临时解释器.全局环境, "记录本", {}) or {})
        for 名称, 对象 in 记录本.items():
            if not callable(对象):
                continue
            owner._runtime_builtin_signature_cache[str(名称)] = owner._安全签名文本(对象)
    except Exception:
        owner._runtime_builtin_signature_cache = {}


def builtin_signature_of(owner, 名称):
    ensure_runtime_builtin_signatures(owner)
    return str(owner._runtime_builtin_signature_cache.get(str(名称), "()") or "()")


def update_calltip(owner, editor=None, tab_id=None, 全文=None, 行前文本=None, 上下文=None, emphasize=False):
    编辑器 = editor if editor else owner._get_current_editor()
    if not 编辑器:
        owner._hide_calltip()
        return
    当前tab = tab_id if tab_id else owner._get_current_tab_id()
    try:
        if 全文 is None:
            全文 = 编辑器.get("1.0", "end-1c")
        if 行前文本 is None:
            行前文本 = 编辑器.get("insert linestart", "insert")
    except tk.TclError:
        owner._hide_calltip()
        return

    调用上下文 = core_extract_call_context(行前文本)
    if not 调用上下文:
        owner._hide_calltip()
        return

    try:
        光标行 = int(编辑器.index("insert").split(".")[0])
    except Exception:
        光标行 = 1
    调用上下文数据 = 上下文 if 上下文 is not None else owner._收集补全上下文(全文 or "", tab_id=当前tab, 光标行=光标行)
    签名 = core_resolve_call_expression_signature(
        调用上下文["调用名"],
        调用上下文数据,
        owner.builtin_words,
        owner._builtin_signature_of,
        cross_tab_alias_resolver=lambda 别名, 当前tab: owner._跨标签查别名模块(别名, 当前tab_id=当前tab),
        module_member_signature_resolver=lambda 模块名, 当前tab: owner._获取模块补全成员签名(模块名, tab_id=当前tab),
        tab_id=当前tab,
    )
    if not 签名:
        owner._hide_calltip()
        return

    高亮签名, 参数位次, 参数总数, 当前参数名 = core_highlight_current_signature_param(
        签名,
        调用上下文["参数序号"],
    )
    if 参数总数 > 0:
        参数说明 = f"当前参数：第 {参数位次}/{参数总数} 个"
        if 当前参数名:
            参数说明 += f"（{当前参数名}）"
    else:
        参数说明 = f"当前参数：第 {调用上下文['参数序号']} 个"
    提示文本 = f"参数提示：{调用上下文['调用名']}{高亮签名}\n{参数说明}"
    show_calltip(owner, 编辑器, 提示文本, emphasize=bool(emphasize))


# ===== merged from yima/editor_module_completion_flow.py =====
import importlib
import inspect
import tkinter as tk

from yima.editor_logic_core import (
    collect_autocomplete_context as core_collect_autocomplete_context,
    extract_import_alias_map as core_extract_import_alias_map,
)


def format_param_signature(owner, 参数列表):
    参数 = [str(p).strip() for p in (参数列表 or []) if str(p).strip()]
    return f"({', '.join(参数)})" if 参数 else "()"


def safe_signature_text(owner, 可调用对象):
    try:
        签名 = str(inspect.signature(可调用对象))
    except Exception:
        return "()"
    if not 签名:
        return "()"
    if len(签名) > 44:
        return f"{签名[:41]}...)"
    return 签名


def cross_tab_alias_module(owner, 别名, 当前tab_id=None):
    目标别名 = str(别名 or "").strip()
    if not 目标别名:
        return None
    for tab_id, 数据 in owner.tabs_data.items():
        if 当前tab_id and tab_id == 当前tab_id:
            continue
        编辑器 = 数据.get("editor")
        if not 编辑器:
            continue
        try:
            文本 = 编辑器.get("1.0", "end-1c")
        except tk.TclError:
            continue
        映射 = core_extract_import_alias_map(文本)
        if 目标别名 in 映射:
            return 映射[目标别名]
    return None


def get_module_completion_members(owner, 模块名, tab_id=None):
    名称 = str(模块名 or "").strip()
    if not 名称:
        return set()

    内置导出 = owner._builtin_module_exports()
    if 名称 in 内置导出:
        return set(内置导出.get(名称, []))

    if 名称 == "魔法生态库":
        return set(owner.builtin_words)

    本地路径 = owner._语义定位易码模块(名称, tab_id=tab_id)
    if 本地路径:
        导出符号, _ = owner._语义读取模块导出(本地路径)
        return set(导出符号 or set())

    if 名称 in owner._py_module_member_cache:
        return set(owner._py_module_member_cache.get(名称, []))

    try:
        模块对象 = importlib.import_module(名称)
        成员 = {名字 for 名字 in dir(模块对象) if 名字 and not str(名字).startswith("_")}
    except Exception:
        成员 = set()
    owner._py_module_member_cache[名称] = sorted(成员)
    return 成员


def get_module_completion_member_details(owner, 模块名, tab_id=None):
    名称 = str(模块名 or "").strip()
    if not 名称:
        return {}

    内置导出 = owner._builtin_module_exports()
    if 名称 in 内置导出:
        return {成员名: "function" for 成员名 in 内置导出.get(名称, [])}

    if 名称 == "魔法生态库":
        return {词: "builtin" for 词 in owner.builtin_words}

    本地路径 = owner._语义定位易码模块(名称, tab_id=tab_id)
    if 本地路径:
        类型表, _ = owner._语义读取模块导出详情(本地路径)
        return dict(类型表 or {})

    if 名称 in owner._py_module_member_detail_cache:
        return dict(owner._py_module_member_detail_cache.get(名称, {}))

    详情 = {}
    签名详情 = {}
    try:
        模块对象 = importlib.import_module(名称)
        for 成员名 in dir(模块对象):
            成员名 = str(成员名)
            if not 成员名 or 成员名.startswith("_"):
                continue
            类型 = "member"
            try:
                值 = getattr(模块对象, 成员名)
                if inspect.isclass(值):
                    类型 = "class"
                    签名详情[成员名] = owner._安全签名文本(值)
                elif callable(值):
                    类型 = "function"
                    签名详情[成员名] = owner._安全签名文本(值)
            except Exception:
                pass
            详情[成员名] = 类型
    except Exception:
        详情 = {}
        签名详情 = {}

    owner._py_module_member_detail_cache[名称] = dict(详情)
    owner._py_module_member_signature_cache[名称] = dict(签名详情)
    return 详情


def get_module_completion_member_signatures(owner, 模块名, tab_id=None):
    名称 = str(模块名 or "").strip()
    if not 名称:
        return {}

    内置导出 = owner._builtin_module_exports()
    if 名称 in 内置导出:
        return {成员名: owner._builtin_signature_of(成员名) for 成员名 in 内置导出.get(名称, [])}

    if 名称 == "魔法生态库":
        return {词: owner._builtin_signature_of(词) for 词 in owner.builtin_words}

    本地路径 = owner._语义定位易码模块(名称, tab_id=tab_id)
    if 本地路径:
        签名表, _ = owner._语义读取模块导出签名(本地路径)
        return dict(签名表 or {})

    if 名称 in owner._py_module_member_signature_cache:
        return dict(owner._py_module_member_signature_cache.get(名称, {}))

    签名详情 = {}
    try:
        模块对象 = importlib.import_module(名称)
        for 成员名 in dir(模块对象):
            成员名 = str(成员名)
            if not 成员名 or 成员名.startswith("_"):
                continue
            try:
                值 = getattr(模块对象, 成员名)
            except Exception:
                continue
            if callable(值):
                签名详情[成员名] = owner._安全签名文本(值)
    except Exception:
        签名详情 = {}

    owner._py_module_member_signature_cache[名称] = dict(签名详情)
    return 签名详情


def collect_completion_context(owner, 全文, tab_id=None, 光标行=None):
    return core_collect_autocomplete_context(
        全文,
        owner._格式化参数签名,
        module_member_details_resolver=lambda 模块名, 当前tab: owner._获取模块补全成员详情(模块名, tab_id=当前tab),
        module_member_signatures_resolver=lambda 模块名, 当前tab: owner._获取模块补全成员签名(模块名, tab_id=当前tab),
        module_members_resolver=lambda 模块名, 当前tab: owner._获取模块补全成员(模块名, tab_id=当前tab),
        tab_id=tab_id,
        cursor_line=光标行,
    )
