"""Search/replace and rename flow helpers extracted from 易码编辑器.py."""

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
from tkinter import messagebox, simpledialog

from yima.词法分析 import 词法分析器, Token类型


def symbol_pattern(owner, name):
    escaped = re.escape(name)
    return re.compile(rf"(?<![\u4e00-\u9fa5A-Za-z0-9_]){escaped}(?![\u4e00-\u9fa5A-Za-z0-9_])")


def is_valid_symbol_name(owner, name):
    return bool(re.fullmatch(r"[\u4e00-\u9fa5A-Za-z_][\u4e00-\u9fa5A-Za-z0-9_]*", name))


def get_symbol_near_cursor(owner, editor):
    try:
        selected = editor.get(tk.SEL_FIRST, tk.SEL_LAST).strip()
        if is_valid_symbol_name(owner, selected):
            return selected
    except tk.TclError:
        pass

    insert_idx = editor.index("insert")
    line_no_str, col_str = insert_idx.split(".")
    line_no = int(line_no_str)
    col = int(col_str)
    line_text = editor.get(f"{line_no}.0", f"{line_no}.end")

    for match in re.finditer(r"[\u4e00-\u9fa5A-Za-z_][\u4e00-\u9fa5A-Za-z0-9_]*", line_text):
        if match.start() <= col <= match.end():
            return match.group(0)
    return ""


def rename_symbol(owner, event=None):
    editor = owner._get_current_editor()
    tab_id = owner._get_current_tab_id()
    if not editor or not tab_id or tab_id not in owner.tabs_data:
        return "break"
    owner._clear_multi_cursor_mode(tab_id)

    old_name = get_symbol_near_cursor(owner, editor)
    if not old_name:
        messagebox.showinfo("重命名符号", "请先把光标放到一个变量/功能/图纸名称上，或先选中一个名称。")
        return "break"

    new_name = simpledialog.askstring(
        "批量重命名",
        f"将符号【{old_name}】重命名为：",
        initialvalue=old_name,
        parent=owner.root,
    )
    if new_name is None:
        return "break"

    new_name = new_name.strip()
    if not new_name:
        messagebox.showwarning("重命名失败", "新名称不能为空。")
        return "break"
    if new_name == old_name:
        owner.status_main_var.set("重命名取消：新旧名称相同")
        return "break"
    if not is_valid_symbol_name(owner, new_name):
        messagebox.showwarning("重命名失败", "名称仅支持中文、英文字母、数字和下划线，且不能以数字开头。")
        return "break"

    code = editor.get("1.0", "end-1c")
    replaced_code = code
    replaced_count = 0

    # 优先走词法 token 精准改名：仅重命名标识符，不触碰字符串和注释
    try:
        tokens = 词法分析器(code).分析()
        line_offsets = []
        cursor = 0
        for line in code.splitlines(keepends=True):
            line_offsets.append(cursor)
            cursor += len(line)
        if not line_offsets:
            line_offsets = [0]

        def to_abs(line_no, col_no):
            if line_no <= 0:
                return 0
            line_idx = min(line_no - 1, len(line_offsets) - 1)
            return line_offsets[line_idx] + max(0, col_no - 1)

        ranges = []
        for token in tokens:
            if token.类型 == Token类型.标识符 and token.值 == old_name:
                start = to_abs(token.行号, token.列号)
                end = start + len(old_name)
                ranges.append((start, end))

        if ranges:
            replaced_count = len(ranges)
            if not messagebox.askyesno(
                "确认重命名",
                f"将在当前文件把【{old_name}】替换为【{new_name}】\n预计影响 {replaced_count} 处，是否继续？",
            ):
                owner.status_main_var.set("重命名已取消")
                return "break"
            for start, end in reversed(ranges):
                replaced_code = replaced_code[:start] + new_name + replaced_code[end:]
    except Exception:
        # 文件暂时不合法时，回退到整词替换模式
        pass

    if replaced_count <= 0:
        pattern = symbol_pattern(owner, old_name)
        matches = list(pattern.finditer(code))
        count = len(matches)
        if count == 0:
            owner.status_main_var.set(f"未找到可重命名项：{old_name}")
            return "break"
        if not messagebox.askyesno(
            "确认重命名",
            f"当前文件存在语法问题，将使用整词模式重命名。\n【{old_name}】 -> 【{new_name}】\n预计影响 {count} 处，是否继续？",
        ):
            owner.status_main_var.set("重命名已取消")
            return "break"
        replaced_code, replaced_count = pattern.subn(new_name, code)
        if replaced_count <= 0:
            owner.status_main_var.set("重命名未产生修改")
            return "break"

    editor.edit_separator()
    editor.delete("1.0", "end")
    editor.insert("1.0", replaced_code)
    editor.edit_separator()

    owner.tabs_data[tab_id]["dirty"] = True
    owner._update_tab_title(tab_id)
    owner._update_status_main()
    owner.highlight()
    owner._schedule_diagnose()
    owner._schedule_outline_update()
    owner._update_line_numbers()
    owner.status_main_var.set(f"重命名完成：{old_name} -> {new_name}（共 {replaced_count} 处）")
    return "break"


def clear_find_marks(owner, editor=None):
    target = editor if editor else owner._get_current_editor()
    if not target:
        return
    target.tag_remove("SearchMatch", "1.0", "end")
    target.tag_remove("SearchCurrent", "1.0", "end")


def highlight_find_matches(owner, event=None):
    editor = owner._get_current_editor()
    if not editor:
        return 0

    query = owner.find_var.get()
    clear_find_marks(owner, editor)
    if not query:
        return 0

    idx = "1.0"
    count = 0
    while True:
        idx = editor.search(query, idx, stopindex="end")
        if not idx:
            break
        end = f"{idx}+{len(query)}c"
        editor.tag_add("SearchMatch", idx, end)
        idx = end
        count += 1
    return count


def focus_find_result(owner, start_idx, end_idx, query):
    editor = owner._get_current_editor()
    if not editor:
        return
    editor.tag_remove("SearchCurrent", "1.0", "end")
    editor.tag_add("SearchCurrent", start_idx, end_idx)
    editor.tag_remove("sel", "1.0", "end")
    editor.tag_add("sel", start_idx, end_idx)
    editor.mark_set("insert", end_idx)
    editor.see(start_idx)
    owner.status_main_var.set(f"查找：已定位“{query}”")


def find_next(owner, event=None):
    editor = owner._get_current_editor()
    if not editor:
        return "break"
    query = owner.find_var.get()
    if not query:
        return "break"

    highlight_find_matches(owner)
    start = editor.index("insert+1c")
    idx = editor.search(query, start, stopindex="end")
    if not idx:
        idx = editor.search(query, "1.0", stopindex=start)

    if idx:
        end = f"{idx}+{len(query)}c"
        focus_find_result(owner, idx, end, query)
    else:
        owner.status_main_var.set(f"查找：未找到“{query}”")
    return "break"


def find_prev(owner, event=None):
    editor = owner._get_current_editor()
    if not editor:
        return "break"
    query = owner.find_var.get()
    if not query:
        return "break"

    highlight_find_matches(owner)
    start = editor.index("insert-1c")
    idx = editor.search(query, start, stopindex="1.0", backwards=True)
    if not idx:
        idx = editor.search(query, "end-1c", stopindex=start, backwards=True)

    if idx:
        end = f"{idx}+{len(query)}c"
        focus_find_result(owner, idx, end, query)
    else:
        owner.status_main_var.set(f"查找：未找到“{query}”")
    return "break"


def replace_one(owner, event=None):
    editor = owner._get_current_editor()
    if not editor:
        return "break"
    query = owner.find_var.get()
    replacement = owner.replace_var.get()
    if not query:
        return "break"

    replaced = False
    try:
        sel_start = editor.index(tk.SEL_FIRST)
        sel_end = editor.index(tk.SEL_LAST)
        selected = editor.get(sel_start, sel_end)
        if selected == query:
            editor.delete(sel_start, sel_end)
            editor.insert(sel_start, replacement)
            editor.mark_set("insert", f"{sel_start}+{len(replacement)}c")
            replaced = True
    except tk.TclError:
        pass

    if not replaced:
        find_next(owner)
        try:
            sel_start = editor.index(tk.SEL_FIRST)
            sel_end = editor.index(tk.SEL_LAST)
            selected = editor.get(sel_start, sel_end)
            if selected == query:
                editor.delete(sel_start, sel_end)
                editor.insert(sel_start, replacement)
                editor.mark_set("insert", f"{sel_start}+{len(replacement)}c")
                replaced = True
        except tk.TclError:
            pass

    if replaced:
        owner.status_main_var.set(f"替换：已将“{query}”替换为“{replacement}”")
        highlight_find_matches(owner)
        find_next(owner)
    else:
        owner.status_main_var.set(f"替换：未找到“{query}”")
    return "break"


def replace_all(owner, event=None):
    editor = owner._get_current_editor()
    if not editor:
        return "break"
    query = owner.find_var.get()
    replacement = owner.replace_var.get()
    if not query:
        return "break"

    count = 0
    idx = "1.0"
    while True:
        idx = editor.search(query, idx, stopindex="end")
        if not idx:
            break
        end = f"{idx}+{len(query)}c"
        editor.delete(idx, end)
        editor.insert(idx, replacement)
        count += 1
        next_step = max(1, len(replacement))
        idx = f"{idx}+{next_step}c"

    highlight_find_matches(owner)
    owner.status_main_var.set(f"替换：共替换 {count} 处")
    return "break"


def open_find_dialog(owner, event=None, focus_replace=False):
    if owner.find_dialog and owner.find_dialog.winfo_exists():
        owner.find_dialog.deiconify()
        owner.find_dialog.lift()
    else:
        owner.find_dialog = tk.Toplevel(owner.root)
        owner.find_dialog.title("查找与替换")
        owner.find_dialog.configure(bg=owner.theme_sidebar_bg)
        owner.find_dialog.resizable(False, False)
        owner.find_dialog.transient(owner.root)

        width = int(430 * owner.dpi_scale)
        height = int(150 * owner.dpi_scale)
        x = owner.root.winfo_x() + max(30, int(40 * owner.dpi_scale))
        y = owner.root.winfo_y() + max(70, int(80 * owner.dpi_scale))
        owner.find_dialog.geometry(f"{width}x{height}+{x}+{y}")

        container = tk.Frame(owner.find_dialog, bg=owner.theme_sidebar_bg, padx=12, pady=10)
        container.pack(fill=tk.BOTH, expand=True)

        row1 = tk.Frame(container, bg=owner.theme_sidebar_bg)
        row1.pack(fill=tk.X, pady=(0, 8))
        tk.Label(row1, text="查找：", font=owner.font_ui, bg=owner.theme_sidebar_bg, fg=owner.theme_fg, width=6, anchor="e").pack(side=tk.LEFT)
        owner.find_entry = tk.Entry(
            row1,
            textvariable=owner.find_var,
            font=owner.font_code,
            bg=owner.theme_bg,
            fg=owner.theme_fg,
            insertbackground="#FFFFFF",
            relief="flat",
            highlightthickness=1,
            highlightbackground=owner.theme_sash,
            highlightcolor="#0E639C",
        )
        owner.find_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=3)
        owner.find_entry.bind("<Return>", owner._find_next)
        owner.find_entry.bind("<KeyRelease>", owner._highlight_find_matches)

        row2 = tk.Frame(container, bg=owner.theme_sidebar_bg)
        row2.pack(fill=tk.X, pady=(0, 8))
        tk.Label(row2, text="替换：", font=owner.font_ui, bg=owner.theme_sidebar_bg, fg=owner.theme_fg, width=6, anchor="e").pack(side=tk.LEFT)
        owner.replace_entry = tk.Entry(
            row2,
            textvariable=owner.replace_var,
            font=owner.font_code,
            bg=owner.theme_bg,
            fg=owner.theme_fg,
            insertbackground="#FFFFFF",
            relief="flat",
            highlightthickness=1,
            highlightbackground=owner.theme_sash,
            highlightcolor="#0E639C",
        )
        owner.replace_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=3)
        owner.replace_entry.bind("<Return>", owner._replace_one)

        btn_row = tk.Frame(container, bg=owner.theme_sidebar_bg)
        btn_row.pack(fill=tk.X)

        def _btn(text, cmd):
            return tk.Button(
                btn_row,
                text=text,
                command=cmd,
                font=owner.font_ui,
                bg=owner.theme_toolbar_bg,
                fg=owner.theme_fg,
                activebackground="#505050",
                activeforeground="#FFFFFF",
                relief="flat",
                borderwidth=0,
                padx=8,
                pady=4,
                cursor="hand2",
            )

        _btn("上一个", owner._find_prev).pack(side=tk.LEFT, padx=(0, 6))
        _btn("下一个", owner._find_next).pack(side=tk.LEFT, padx=(0, 6))
        _btn("替换", owner._replace_one).pack(side=tk.LEFT, padx=(0, 6))
        _btn("全部替换", owner._replace_all).pack(side=tk.LEFT, padx=(0, 6))
        _btn("关闭", lambda: owner.find_dialog.withdraw()).pack(side=tk.RIGHT)

        owner.find_dialog.bind("<Escape>", lambda e: owner.find_dialog.withdraw())
        owner.find_dialog.protocol("WM_DELETE_WINDOW", lambda: owner.find_dialog.withdraw())

    editor = owner._get_current_editor()
    if editor:
        try:
            selected = editor.get(tk.SEL_FIRST, tk.SEL_LAST)
            if selected and "\n" not in selected:
                owner.find_var.set(selected)
        except tk.TclError:
            pass
        highlight_find_matches(owner)

    if focus_replace and hasattr(owner, "replace_entry"):
        owner.replace_entry.focus_set()
        owner.replace_entry.select_range(0, tk.END)
    elif hasattr(owner, "find_entry"):
        owner.find_entry.focus_set()
        owner.find_entry.select_range(0, tk.END)
    return "break"
