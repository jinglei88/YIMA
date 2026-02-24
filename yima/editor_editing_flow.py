"""Editor typing/indent/snippet/autopair interactions."""

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
import time
import tkinter as tk


def handle_return(owner, event=None):
    if owner._autocomplete_is_visible():
        owner._accept_autocomplete()
        return "break"
    return owner._auto_indent(event)


def tab_current_word(owner, editor):
    insert_idx = editor.index("insert")
    line_start = editor.index("insert linestart")
    line_text_before = editor.get(line_start, insert_idx)
    match = re.search(r"[\u4e00-\u9fa5a-zA-Z0-9_]+$", line_text_before)
    return insert_idx, line_start, (match.group(0) if match else "")


def tab_selection_info(owner, editor, insert_idx=None):
    del owner
    try:
        sel_start = editor.index(tk.SEL_FIRST)
        sel_end = editor.index(tk.SEL_LAST)
        sel_text = editor.get(sel_start, sel_end)
    except tk.TclError:
        return {
            "start": None,
            "end": None,
            "text": "",
            "contains_cursor": False,
        }
    if insert_idx is None:
        contains_cursor = True
    else:
        try:
            contains_cursor = (
                editor.compare(sel_start, "<=", insert_idx)
                and editor.compare(insert_idx, "<", sel_end)
            )
        except tk.TclError:
            contains_cursor = False
    return {
        "start": sel_start,
        "end": sel_end,
        "text": sel_text,
        "contains_cursor": contains_cursor,
    }


def remember_edit_cursor(owner, event=None):
    editor = None
    if event is not None and hasattr(event, "widget"):
        candidate = getattr(event, "widget", None)
        if isinstance(candidate, tk.Text) and owner._get_tab_id_by_editor(candidate):
            editor = candidate
    if editor is None:
        editor = owner._get_current_editor()
    if not editor:
        return

    tab_id = owner._get_tab_id_by_editor(editor)
    if not tab_id:
        return
    try:
        idx, _, word = owner._tab_current_word(editor)
    except Exception:
        return
    owner._last_edit_tab_id = tab_id
    owner._last_edit_index = idx
    owner._last_edit_word = str(word or "")
    owner._last_edit_ts = time.monotonic()


def tab_jump_to_next_placeholder(owner, editor, from_index):
    del owner
    try:
        search_index = editor.index(from_index or "insert")
    except tk.TclError:
        search_index = editor.index("insert")
    while True:
        start_idx = editor.search("‹", search_index, "end")
        if not start_idx:
            return False
        line_end = editor.index(f"{start_idx} lineend")
        line_rest = editor.get(start_idx, line_end)
        match = re.match(r"‹.+?›", line_rest)
        if not match:
            search_index = editor.index(f"{start_idx}+1c")
            continue
        end_idx = f"{start_idx} + {len(match.group(0))}c"
        editor.tag_remove("sel", "1.0", "end")
        editor.tag_add("sel", start_idx, end_idx)
        editor.mark_set("insert", start_idx)
        editor.see("insert")
        return True


def expand_snippet_at_cursor(owner, editor, snippet_word, typed_word=""):
    snippet_name = str(snippet_word or "").strip()
    snippet_text = owner.snippets.get(snippet_name)
    if not snippet_text:
        return False

    insert_idx = editor.index("insert")
    line_start = editor.index("insert linestart")
    line_before = editor.get(line_start, insert_idx)
    remove_word = str(typed_word or snippet_name).strip()

    if remove_word and line_before.endswith(remove_word):
        del_start = f"insert - {len(remove_word)}c"
    else:
        del_start = "insert"

    del_start = editor.index(del_start)

    base_col = int(del_start.split(".")[1])
    base_indent = " " * base_col
    if base_col > 0:
        lines = snippet_text.split("\n")
        snippet_text = lines[0] + "".join("\n" + base_indent + line for line in lines[1:])

    editor.delete(del_start, "insert")
    editor.insert(del_start, snippet_text)

    try:
        start_line = int(del_start.split(".")[0])
        start_col = int(del_start.split(".")[1])
        缩进文本 = " " * start_col
        行数 = snippet_text.count("\n")
        末行 = start_line + 行数
        editor.mark_set("insert", f"{末行}.end")
        editor.insert("insert", "\n" + 缩进文本)
        editor.tag_remove("sel", "1.0", "end")
    except Exception:
        try:
            editor.mark_set("insert", f"{del_start} + {len(snippet_text)}c")
            editor.tag_remove("sel", "1.0", "end")
        except tk.TclError:
            pass
    owner.highlight()
    return True


def handle_tab(owner, event=None):
    editor = None
    if event is not None and hasattr(event, "widget"):
        candidate = getattr(event, "widget", None)
        if isinstance(candidate, tk.Text) and owner._get_tab_id_by_editor(candidate):
            editor = candidate
    if editor is None:
        editor = owner._get_current_editor()
    if not editor:
        return "break"
    try:
        editor.focus_set()
    except tk.TclError:
        pass

    insert_idx, _, 光标前词 = owner._tab_current_word(editor)

    if 光标前词 and 光标前词 in owner.snippets:
        owner._hide_autocomplete()
        owner._expand_snippet_at_cursor(editor, 光标前词, typed_word=光标前词)
        return "break"

    if owner._autocomplete_is_visible():
        是模板候选 = False
        同行弹窗 = False
        try:
            当前行 = editor.index("insert").split(".")[0]
            同行弹窗 = bool(
                owner._autocomplete_popup_line
                and str(owner._autocomplete_popup_line) == str(当前行)
            )
            idx = owner._autocomplete_current_index()
            if 0 <= idx < len(owner._autocomplete_items):
                当前候选 = owner._autocomplete_items[idx] or {}
                是模板候选 = str(当前候选.get("source", "")).strip() == "snippet"
        except Exception:
            是模板候选 = False
            同行弹窗 = False

        if 是模板候选:
            owner._hide_autocomplete()
            if 同行弹窗 and 光标前词 and (光标前词 in owner.snippets):
                owner._expand_snippet_at_cursor(editor, 光标前词, typed_word=光标前词)
            return "break"
        owner._accept_autocomplete()
        return "break"

    选区 = owner._tab_selection_info(editor, insert_idx)
    sel_start = 选区["start"]
    sel_end = 选区["end"]
    sel_text = 选区["text"]
    sel_contains_cursor = bool(选区["contains_cursor"])
    if sel_start and sel_end and (not sel_contains_cursor):
        sel_start = None
        sel_end = None
        sel_text = ""
        try:
            editor.tag_remove("sel", "1.0", "end")
        except tk.TclError:
            pass

    当前选中占位符 = bool(
        sel_start
        and sel_end
        and sel_contains_cursor
        and sel_text.startswith("‹")
        and sel_text.endswith("›")
    )
    if 当前选中占位符:
        if owner._tab_jump_to_next_placeholder(editor, sel_end):
            return "break"
    elif owner._tab_jump_to_next_placeholder(editor, insert_idx):
        return "break"

    try:
        当前行文本 = editor.get("insert linestart", "insert lineend")
        当前缩进 = len(当前行文本) - len(当前行文本.lstrip())
        if 当前缩进 > 0 or (当前选中占位符 and sel_text):
            当前行号 = int(editor.index("insert").split(".")[0])
            总行数 = int(editor.index("end-1c").split(".")[0])
            目标行 = 当前行号
            for i in range(当前行号, 总行数 + 1):
                行 = editor.get(f"{i}.0", f"{i}.end")
                if 行.strip():
                    行缩进 = len(行) - len(行.lstrip())
                    if 行缩进 >= 当前缩进 or i == 当前行号:
                        目标行 = i
                    else:
                        break
                else:
                    目标行 = i
                    break

            父级缩进 = max(0, 当前缩进 - 4)
            缩进文本 = " " * 父级缩进

            editor.mark_set("insert", f"{目标行}.end")
            editor.insert("insert", "\n" + 缩进文本)
            owner.highlight()
            return "break"
    except Exception:
        pass

    if sel_start and sel_end and sel_contains_cursor and not 当前选中占位符:
        try:
            start_line = int(sel_start.split(".")[0])
            end_line = int(sel_end.split(".")[0])
            if sel_end.split(".")[1] == "0" and start_line != end_line:
                end_line -= 1
            for i in range(start_line, end_line + 1):
                editor.insert(f"{i}.0", "    ")
            return "break"
        except Exception:
            pass

    if sel_start and sel_end and sel_contains_cursor and not 当前选中占位符:
        try:
            editor.delete(sel_start, sel_end)
        except tk.TclError:
            pass
    editor.insert("insert", "    ")
    return "break"


def handle_auto_pairs(owner, event):
    editor = owner._get_current_editor()
    if not editor or event.widget is not editor:
        return

    if event.state & 0x4:
        return

    ch = event.char

    if ch and ord(ch) >= 32 and event.keysym not in ("Return", "Tab", "Escape"):
        try:
            if editor.index(tk.SEL_FIRST) != editor.index(tk.SEL_LAST):
                editor.delete(tk.SEL_FIRST, tk.SEL_LAST)
        except tk.TclError:
            pass

    if ch in ("。", "．", "｡"):
        try:
            prev_tags = editor.tag_names("insert-1c")
        except tk.TclError:
            prev_tags = ()
        try:
            cur_tags = editor.tag_names("insert")
        except tk.TclError:
            cur_tags = ()

        在字符串或注释内 = (
            ("String" in prev_tags)
            or ("Comment" in prev_tags)
            or ("String" in cur_tags)
            or ("Comment" in cur_tags)
        )
        if not 在字符串或注释内:
            try:
                editor.delete(tk.SEL_FIRST, tk.SEL_LAST)
            except tk.TclError:
                pass
            editor.insert("insert", ".")
            try:
                owner.root.after_idle(owner._check_autocomplete)
            except Exception:
                pass
            return "break"

    if ch in owner._pair_map:
        right = owner._pair_map[ch]
        try:
            sel_start = editor.index(tk.SEL_FIRST)
            sel_end = editor.index(tk.SEL_LAST)
            selected = editor.get(sel_start, sel_end)
            editor.delete(sel_start, sel_end)
            editor.insert(sel_start, f"{ch}{selected}{right}")
            editor.mark_set(
                "insert", f"{sel_start} + {len(ch) + len(selected) + len(right)}c"
            )
            return "break"
        except tk.TclError:
            editor.insert("insert", f"{ch}{right}")
            editor.mark_set("insert", "insert-1c")
            return "break"

    if ch and ch in owner._pair_map.values():
        next_char = editor.get("insert", "insert+1c")
        if next_char == ch:
            editor.mark_set("insert", "insert+1c")
            return "break"

    if event.keysym == "BackSpace":
        prev_char = editor.get("insert-1c", "insert")
        next_char = editor.get("insert", "insert+1c")
        if prev_char in owner._pair_map and owner._pair_map[prev_char] == next_char:
            editor.delete("insert-1c", "insert+1c")
            return "break"


def auto_indent(owner, event=None):
    del event
    editor = owner._get_current_editor()
    if not editor:
        return "break"

    line_text = editor.get("insert linestart", "insert lineend")
    editor.insert("insert", "\n")

    indent = ""
    for char in line_text:
        if char in [" ", "\t"]:
            indent += char
        else:
            break

    stripped_prev = line_text.strip()
    indent_triggers = [
        "如果",
        "否则如果",
        "不然",
        "尝试",
        "如果出错",
        "重复",
        "功能",
        "定义图纸",
        "当",
        "遍历",
    ]

    for trigger in indent_triggers:
        if (
            stripped_prev.startswith(trigger)
            or stripped_prev.endswith("的时候")
            or stripped_prev.endswith("就")
        ):
            indent += "    "
            break

    if indent:
        editor.insert("insert", indent)

    editor.see("insert")
    owner._highlight_current_line()
    return "break"


def handle_shift_tab(owner, event=None):
    del event
    editor = owner._get_current_editor()
    if not editor:
        return "break"

    try:
        sel_start = editor.index(tk.SEL_FIRST)
        sel_end = editor.index(tk.SEL_LAST)
        start_line = int(sel_start.split(".")[0])
        end_line = int(sel_end.split(".")[0])
        if sel_end.split(".")[1] == "0" and start_line != end_line:
            end_line -= 1
    except tk.TclError:
        insert_pos = editor.index("insert")
        start_line = int(insert_pos.split(".")[0])
        end_line = start_line

    for i in range(start_line, end_line + 1):
        line_text = editor.get(f"{i}.0", f"{i}.end")
        space_count = 0
        for char in line_text:
            if char == " ":
                space_count += 1
            elif char == "\t":
                space_count += 4
            else:
                break

        remove_count = min(4, space_count)
        if remove_count > 0:
            editor.delete(f"{i}.0", f"{i}.{remove_count}")

    return "break"
