"""Multi-cursor interaction flow helpers."""

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

import tkinter as tk


def get_multi_state(owner, tab_id=None):
    target_tab_id = tab_id if tab_id else owner._get_current_tab_id()
    if not target_tab_id or target_tab_id not in owner.tabs_data:
        return None, None
    data = owner.tabs_data[target_tab_id]
    state = data.setdefault(
        "multi_cursor",
        {"query": "", "stage": "ranges", "ranges": [], "points": [], "last_abs": -1},
    )
    return target_tab_id, state


def index_to_abs(owner, editor, idx):
    del owner
    try:
        return len(editor.get("1.0", idx))
    except tk.TclError:
        return 0


def sort_unique_indices(owner, editor, indices):
    uniq = {}
    for idx in indices:
        uniq[owner._index_to_abs(editor, idx)] = idx
    return [uniq[k] for k in sorted(uniq.keys())]


def find_all_symbol_ranges(owner, editor, symbol_name):
    code = editor.get("1.0", "end-1c")
    pattern = owner._symbol_pattern(symbol_name)
    ranges = []
    for m in pattern.finditer(code):
        start = f"1.0 + {m.start()}c"
        end = f"1.0 + {m.end()}c"
        ranges.append((start, end))
    return ranges


def convert_ranges_to_points(owner, editor, state, use_end=True):
    points = []
    for start, end in state.get("ranges", []):
        idx = end if use_end else start
        try:
            points.append(editor.index(idx))
        except tk.TclError:
            continue
    state["stage"] = "points"
    state["ranges"] = []
    state["points"] = owner._sort_unique_indices(editor, points)
    return state["points"]


def handle_editor_left_click(owner, event):
    editor = owner._get_current_editor()
    tab_id, state = owner._get_multi_state()
    if not editor or event.widget is not editor or state is None:
        return

    if event.state & 0x0008:
        return

    owner._hide_autocomplete()
    owner._hide_calltip()
    try:
        click_idx = editor.index(f"@{event.x},{event.y}")
        editor.mark_set("insert", click_idx)
        editor.tag_remove("sel", "1.0", "end")
        editor.focus_set()
    except tk.TclError:
        pass

    if state.get("ranges") or state.get("points"):
        owner._clear_multi_cursor_mode(tab_id)
        owner.status_main_var.set("多光标模式已退出")


def sync_insert_after_click(owner, event=None):
    editor = owner._get_current_editor()
    if not editor:
        return
    if event is not None and event.widget is not editor:
        return
    try:
        if event is not None:
            idx = editor.index(f"@{event.x},{event.y}")
            editor.mark_set("insert", idx)
    except tk.TclError:
        pass


def multi_cursor_alt_click(owner, event=None):
    editor = owner._get_current_editor()
    tab_id, state = owner._get_multi_state()
    if not editor or not tab_id or state is None:
        return "break"
    if event is None or event.widget is not editor:
        return "break"

    owner._hide_autocomplete()

    try:
        click_idx = editor.index(f"@{event.x},{event.y}")
    except tk.TclError:
        return "break"

    if state["stage"] == "ranges" and state.get("ranges"):
        owner._convert_ranges_to_points(editor, state, use_end=True)

    points = list(state.get("points", []))
    if not points:
        points = [editor.index("insert")]

    click_abs = owner._index_to_abs(editor, click_idx)
    point_abs = [owner._index_to_abs(editor, p) for p in points]
    if click_abs in point_abs:
        if len(points) > 1:
            points = [p for p in points if owner._index_to_abs(editor, p) != click_abs]
        else:
            points = [click_idx]
    else:
        points.append(click_idx)

    state["query"] = ""
    state["stage"] = "points"
    state["ranges"] = []
    state["points"] = owner._sort_unique_indices(editor, points)
    state["last_abs"] = owner._index_to_abs(editor, state["points"][-1]) if state["points"] else -1

    editor.mark_set("insert", click_idx)
    editor.focus_set()
    owner._render_multi_cursor_state(tab_id)
    owner.status_main_var.set(f"多光标：已放置 {len(state['points'])} 个光标点（Alt+点击继续，Esc退出）")
    return "break"


def render_multi_cursor_state(owner, tab_id=None):
    target_tab_id, state = owner._get_multi_state(tab_id)
    if not target_tab_id or state is None:
        return
    editor = owner.tabs_data[target_tab_id].get("editor")
    if not editor:
        return

    editor.tag_remove("MultiCursorSel", "1.0", "end")
    if state["stage"] == "ranges":
        for start, end in state["ranges"]:
            try:
                editor.tag_add("MultiCursorSel", start, end)
            except tk.TclError:
                continue
    else:
        for point in state["points"]:
            try:
                next_idx = editor.index(f"{point}+1c")
                if next_idx != point:
                    editor.tag_add("MultiCursorSel", point, next_idx)
                else:
                    prev_idx = editor.index(f"{point}-1c")
                    if prev_idx != point:
                        editor.tag_add("MultiCursorSel", prev_idx, point)
            except tk.TclError:
                continue


def clear_multi_cursor_mode(owner, tab_id=None, keep_query=False):
    target_tab_id, state = owner._get_multi_state(tab_id)
    if not target_tab_id or state is None:
        return
    editor = owner.tabs_data[target_tab_id].get("editor")
    if editor:
        editor.tag_remove("MultiCursorSel", "1.0", "end")
    query = state.get("query", "") if keep_query else ""
    state["query"] = query
    state["stage"] = "ranges"
    state["ranges"] = []
    state["points"] = []
    state["last_abs"] = -1


def update_after_multi_edit(owner, tab_id, status_text=""):
    if not tab_id or tab_id not in owner.tabs_data:
        return
    owner.tabs_data[tab_id]["dirty"] = True
    owner._update_tab_title(tab_id)
    owner._update_status_main()
    if status_text:
        owner.status_main_var.set(status_text)
    owner._schedule_highlight()
    owner._schedule_diagnose()
    owner._schedule_outline_update()
    owner._update_line_numbers()
    owner._update_cursor_status()
    owner._render_multi_cursor_state(tab_id)


def multi_cursor_add_next(owner, event=None):
    del event
    editor = owner._get_current_editor()
    tab_id, state = owner._get_multi_state()
    if not editor or not tab_id or state is None:
        return "break"

    if state["stage"] != "ranges":
        owner._clear_multi_cursor_mode(tab_id)
        _, state = owner._get_multi_state(tab_id)

    word = state["query"] or owner._get_symbol_near_cursor(editor)
    if not word:
        owner.status_main_var.set("多光标：请先把光标放在符号上，或先选中一个符号")
        return "break"

    all_ranges = owner._find_all_symbol_ranges(editor, word)
    if not all_ranges:
        owner.status_main_var.set(f"多光标：未找到符号【{word}】")
        return "break"

    state["query"] = word
    selected_start_abs = {owner._index_to_abs(editor, s) for s, _ in state["ranges"]}

    if not state["ranges"]:
        cursor_abs = owner._index_to_abs(editor, "insert")
        chosen = None
        for s, e in all_ranges:
            s_abs = owner._index_to_abs(editor, s)
            e_abs = owner._index_to_abs(editor, e)
            if s_abs <= cursor_abs <= e_abs:
                chosen = (s, e)
                break
        if not chosen:
            for s, e in all_ranges:
                s_abs = owner._index_to_abs(editor, s)
                if s_abs >= cursor_abs:
                    chosen = (s, e)
                    break
        if not chosen:
            chosen = all_ranges[0]
        state["ranges"] = [chosen]
        state["last_abs"] = owner._index_to_abs(editor, chosen[0])
    else:
        candidates = sorted(all_ranges, key=lambda r: owner._index_to_abs(editor, r[0]))
        next_choice = None
        for s, e in candidates:
            s_abs = owner._index_to_abs(editor, s)
            if s_abs > state["last_abs"] and s_abs not in selected_start_abs:
                next_choice = (s, e)
                break
        if not next_choice:
            for s, e in candidates:
                s_abs = owner._index_to_abs(editor, s)
                if s_abs not in selected_start_abs:
                    next_choice = (s, e)
                    break
        if not next_choice:
            owner.status_main_var.set(f"多光标：{word} 已全部选中")
            owner._render_multi_cursor_state(tab_id)
            return "break"
        state["ranges"].append(next_choice)
        state["last_abs"] = owner._index_to_abs(editor, next_choice[0])

    state["ranges"] = sorted(state["ranges"], key=lambda r: owner._index_to_abs(editor, r[0]))
    owner._render_multi_cursor_state(tab_id)
    owner.status_main_var.set(f"多光标：已选中 {len(state['ranges'])} 处【{word}】（Ctrl+D继续，Esc退出）")
    return "break"


def multi_cursor_select_all(owner, event=None):
    del event
    editor = owner._get_current_editor()
    tab_id, state = owner._get_multi_state()
    if not editor or not tab_id or state is None:
        return "break"

    word = owner._get_symbol_near_cursor(editor) or state.get("query", "")
    if not word:
        owner.status_main_var.set("多光标：请先把光标放在符号上，或先选中一个符号")
        return "break"

    all_ranges = owner._find_all_symbol_ranges(editor, word)
    if not all_ranges:
        owner.status_main_var.set(f"多光标：未找到符号【{word}】")
        return "break"

    state["query"] = word
    state["stage"] = "ranges"
    state["ranges"] = sorted(all_ranges, key=lambda r: owner._index_to_abs(editor, r[0]))
    state["points"] = []
    state["last_abs"] = owner._index_to_abs(editor, state["ranges"][-1][0]) if state["ranges"] else -1
    owner._render_multi_cursor_state(tab_id)
    owner.status_main_var.set(f"多光标：已全选 {len(state['ranges'])} 处【{word}】（直接输入可同步编辑）")
    return "break"


def multi_apply_insert_char(owner, ch):
    editor = owner._get_current_editor()
    tab_id, state = owner._get_multi_state()
    if not editor or not tab_id or state is None:
        return

    if state["stage"] == "ranges" and state["ranges"]:
        operations = sorted(
            state["ranges"],
            key=lambda r: owner._index_to_abs(editor, r[0]),
            reverse=True,
        )
        new_points = []
        for start, end in operations:
            try:
                editor.delete(start, end)
                editor.insert(start, ch)
                new_points.append(editor.index(f"{start}+{len(ch)}c"))
            except tk.TclError:
                continue
        state["stage"] = "points"
        state["ranges"] = []
        state["points"] = owner._sort_unique_indices(editor, new_points)
    else:
        points = owner._sort_unique_indices(editor, state["points"])
        new_points = []
        for point in sorted(points, key=lambda p: owner._index_to_abs(editor, p), reverse=True):
            try:
                editor.insert(point, ch)
                new_points.append(editor.index(f"{point}+{len(ch)}c"))
            except tk.TclError:
                continue
        state["stage"] = "points"
        state["points"] = owner._sort_unique_indices(editor, new_points)

    owner._update_after_multi_edit(
        tab_id,
        f"多光标编辑：同步输入 {len(state['points']) or len(state['ranges'])} 处",
    )


def multi_apply_backspace(owner):
    editor = owner._get_current_editor()
    tab_id, state = owner._get_multi_state()
    if not editor or not tab_id or state is None:
        return

    new_points = []
    if state["stage"] == "ranges" and state["ranges"]:
        operations = sorted(
            state["ranges"],
            key=lambda r: owner._index_to_abs(editor, r[0]),
            reverse=True,
        )
        for start, end in operations:
            try:
                editor.delete(start, end)
                new_points.append(start)
            except tk.TclError:
                continue
        state["ranges"] = []
        state["stage"] = "points"
    else:
        points = owner._sort_unique_indices(editor, state["points"])
        for point in sorted(points, key=lambda p: owner._index_to_abs(editor, p), reverse=True):
            try:
                if owner._index_to_abs(editor, point) <= 0:
                    continue
                start = editor.index(f"{point}-1c")
                editor.delete(start, point)
                new_points.append(start)
            except tk.TclError:
                continue
        state["stage"] = "points"

    state["points"] = owner._sort_unique_indices(editor, new_points)
    owner._update_after_multi_edit(tab_id, "多光标编辑：已同步退格")


def multi_apply_delete(owner):
    editor = owner._get_current_editor()
    tab_id, state = owner._get_multi_state()
    if not editor or not tab_id or state is None:
        return

    new_points = []
    if state["stage"] == "ranges" and state["ranges"]:
        operations = sorted(
            state["ranges"],
            key=lambda r: owner._index_to_abs(editor, r[0]),
            reverse=True,
        )
        for start, end in operations:
            try:
                editor.delete(start, end)
                new_points.append(start)
            except tk.TclError:
                continue
        state["ranges"] = []
        state["stage"] = "points"
    else:
        points = owner._sort_unique_indices(editor, state["points"])
        for point in sorted(points, key=lambda p: owner._index_to_abs(editor, p), reverse=True):
            try:
                editor.delete(point, f"{point}+1c")
                new_points.append(point)
            except tk.TclError:
                continue
        state["stage"] = "points"

    state["points"] = owner._sort_unique_indices(editor, new_points)
    owner._update_after_multi_edit(tab_id, "多光标编辑：已同步删除")


def handle_multi_cursor_key(owner, event):
    editor = owner._get_current_editor()
    tab_id, state = owner._get_multi_state()
    if not editor or not tab_id or state is None:
        return
    if event.widget is not editor:
        return

    active = bool(state.get("ranges") or state.get("points"))
    if not active:
        return

    if event.keysym == "Escape":
        owner._clear_multi_cursor_mode(tab_id)
        owner.status_main_var.set("多光标模式已退出")
        return "break"

    if event.keysym in ("Left", "Right", "Up", "Down", "Home", "End", "Prior", "Next"):
        owner._clear_multi_cursor_mode(tab_id)
        return

    if event.state & 0x4:
        return

    if event.keysym == "BackSpace":
        owner._multi_apply_backspace()
        return "break"
    if event.keysym == "Delete":
        owner._multi_apply_delete()
        return "break"
    if event.keysym == "Return":
        owner._multi_apply_insert_char("\n")
        return "break"
    if event.keysym == "Tab":
        owner._multi_apply_insert_char("    ")
        return "break"

    if event.char and ord(event.char) >= 32:
        owner._multi_apply_insert_char(event.char)
        return "break"
