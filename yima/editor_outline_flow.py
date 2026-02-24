"""Outline, fold, line-number, and indent-guide interaction helpers."""

from __future__ import annotations

#
# Ownership Marker (Open Source Prep)
# Author: 景磊 (Jing Lei)
# Copyright (c) 2026 景磊
# Project: 易码 / Yima
# Marker-ID: YIMA-JINGLEI-CORE

__author__ = "\u666f\u78ca"
__copyright__ = "Copyright (c) 2026 \u666f\u78ca"
__marker_id__ = "YIMA-JINGLEI-CORE"

import re
import tkinter as tk


def count_indent_width(owner, line_text):
    del owner
    width = 0
    for ch in line_text:
        if ch == " ":
            width += 1
        elif ch == "\t":
            width += 4
        else:
            break
    return width


def get_block_end_line(owner, editor, start_line):
    line_count = int(editor.index("end-1c").split(".")[0])
    if start_line >= line_count:
        return None

    start_text = editor.get(f"{start_line}.0", f"{start_line}.end")
    if not start_text.strip():
        return None

    base_indent = owner._count_indent_width(start_text)
    end_line = start_line
    has_child = False

    for ln in range(start_line + 1, line_count + 1):
        text = editor.get(f"{ln}.0", f"{ln}.end")
        stripped = text.strip()
        if not stripped:
            if has_child:
                end_line = ln
            continue

        indent = owner._count_indent_width(text)
        if indent > base_indent:
            has_child = True
            end_line = ln
            continue
        break

    while end_line > start_line and not editor.get(f"{end_line}.0", f"{end_line}.end").strip():
        end_line -= 1

    if not has_child or end_line <= start_line:
        return None
    return end_line


def schedule_outline_update(owner, event=None):
    del event
    if owner._outline_after_id:
        try:
            owner.root.after_cancel(owner._outline_after_id)
        except tk.TclError:
            pass
    owner._outline_after_id = owner.root.after(260, owner._refresh_outline)


def refresh_outline(owner):
    owner._outline_after_id = None
    if not hasattr(owner, "outline_listbox"):
        return

    editor = owner._get_current_editor()
    tab_id = owner._get_current_tab_id()
    if not editor or not tab_id or tab_id not in owner.tabs_data:
        owner.outline_listbox.delete(0, tk.END)
        return

    previous_selected_line = owner.tabs_data[tab_id].get("outline_focus_line")
    try:
        if not previous_selected_line:
            prev_idx = owner.outline_listbox.curselection()
            if prev_idx:
                prev_item = owner.tabs_data[tab_id].get("outline_items", [])[prev_idx[0]]
                previous_selected_line = prev_item.get("line")
    except Exception:
        pass

    owner.outline_listbox.delete(0, tk.END)
    code_lines = editor.get("1.0", "end-1c").splitlines()
    folds = owner.tabs_data[tab_id].setdefault("folds", {})
    items = []

    for line_no, line_text in enumerate(code_lines, start=1):
        stripped = line_text.strip()
        if not stripped or stripped.startswith("#"):
            continue

        kind = None
        name = None
        m_func = re.match(r"^\s*\u529f\u80fd\s+([^\s(\uff08]+)", line_text)
        if m_func:
            kind = "\u529f\u80fd"
            name = m_func.group(1)
        else:
            m_class = re.match(r"^\s*\u5b9a\u4e49\u56fe\u7eb8\s+([^\s(\uff08]+)", line_text)
            if m_class:
                kind = "\u56fe\u7eb8"
                name = m_class.group(1)

        if not kind or not name:
            continue

        indent_level = owner._count_indent_width(line_text) // 4
        collapsed = bool(folds.get(line_no, {}).get("collapsed"))
        marker = "[+]" if collapsed else "[-]"
        kind_mark = "\u529f\u80fd" if kind == "\u529f\u80fd" else "\u56fe\u7eb8"
        indent_prefix = "  " * min(indent_level, 6)
        display_text = f"{indent_prefix}{marker} {kind_mark} {name}  (L{line_no})"

        items.append({
            "line": line_no,
            "kind": kind,
            "name": name,
            "indent_level": indent_level,
            "display_text": display_text,
        })
        owner.outline_listbox.insert(tk.END, display_text)

    owner.tabs_data[tab_id]["outline_items"] = items

    if not items:
        owner.outline_listbox.insert(tk.END, "(\u5f53\u524d\u6587\u4ef6\u6682\u65e0\u529f\u80fd/\u56fe\u7eb8\u7ed3\u6784)")
        try:
            owner.outline_listbox.itemconfig(0, foreground="#777777")
        except tk.TclError:
            pass
        return

    selected_idx = 0
    if previous_selected_line:
        for i, item in enumerate(items):
            if item["line"] == previous_selected_line:
                selected_idx = i
                break
    owner.outline_listbox.selection_clear(0, tk.END)
    owner.outline_listbox.selection_set(selected_idx)
    owner.outline_listbox.activate(selected_idx)
    owner.tabs_data[tab_id]["outline_focus_line"] = items[selected_idx].get("line")


def get_selected_outline_item(owner):
    tab_id = owner._get_current_tab_id()
    if not tab_id or tab_id not in owner.tabs_data:
        return None
    selection = owner.outline_listbox.curselection()
    if not selection:
        return None
    idx = selection[0]
    items = owner.tabs_data[tab_id].get("outline_items", [])
    if idx < 0 or idx >= len(items):
        return None
    return items[idx]


def outline_update_status(owner, event=None):
    del event
    tab_id = owner._get_current_tab_id()
    if not tab_id or tab_id not in owner.tabs_data:
        return
    item = owner._get_selected_outline_item()
    if not item:
        return
    owner.tabs_data[tab_id]["outline_focus_line"] = item.get("line")
    owner.status_main_var.set("大纲项已选中")


def on_outline_activate(owner, event=None):
    del event
    tab_id = owner._get_current_tab_id()
    if not tab_id or tab_id not in owner.tabs_data:
        return "break"
    item = owner._get_selected_outline_item()
    if not item:
        return "break"
    editor = owner._get_current_editor()
    if not editor:
        return "break"

    target = f"{item.get('line')}.0"
    editor.mark_set("insert", target)
    editor.see(target)
    editor.focus_set()
    owner._highlight_current_line()
    owner._update_cursor_status()
    owner.tabs_data[tab_id]["outline_focus_line"] = item.get("line")
    owner.status_main_var.set("已根据大纲定位")
    return "break"


def toggle_fold_by_line(owner, line_no):
    editor = owner._get_current_editor()
    tab_id = owner._get_current_tab_id()
    if not editor or not tab_id or tab_id not in owner.tabs_data:
        return False

    folds = owner.tabs_data[tab_id].setdefault("folds", {})
    fold_meta = folds.get(line_no)

    if fold_meta and fold_meta.get("collapsed"):
        tag = fold_meta.get("tag")
        if tag:
            editor.tag_remove(tag, "1.0", "end")
            try:
                editor.tag_configure(tag, elide=False)
            except tk.TclError:
                pass
        fold_meta["collapsed"] = False
        owner._update_line_numbers()
        return True

    end_line = owner._get_block_end_line(editor, line_no)
    if not end_line:
        return False

    tag_name = fold_meta.get("tag") if fold_meta else f"FoldBlock_{line_no}"
    editor.tag_configure(tag_name, elide=True)
    editor.tag_remove(tag_name, "1.0", "end")
    editor.tag_add(tag_name, f"{line_no + 1}.0", f"{end_line}.end+1c")
    folds[line_no] = {"tag": tag_name, "end_line": end_line, "collapsed": True}
    owner._update_line_numbers()
    return True


def clear_all_folds(owner, tab_id=None):
    target_tab_id = tab_id if tab_id else owner._get_current_tab_id()
    if not target_tab_id or target_tab_id not in owner.tabs_data:
        return

    editor = owner.tabs_data[target_tab_id].get("editor")
    if not editor:
        return

    folds = owner.tabs_data[target_tab_id].get("folds", {})
    for fold_meta in folds.values():
        tag = fold_meta.get("tag")
        if not tag:
            continue
        editor.tag_remove(tag, "1.0", "end")
        try:
            editor.tag_configure(tag, elide=False)
        except tk.TclError:
            pass
    owner.tabs_data[target_tab_id]["folds"] = {}


def toggle_fold_from_outline(owner, event=None):
    del event
    item = owner._get_selected_outline_item()
    if not item:
        return owner.toggle_fold_current_line(None)

    ok = owner._toggle_fold_by_line(item["line"])
    if ok:
        owner._refresh_outline()
        owner.status_main_var.set(f"\u5df2\u5207\u6362\u6298\u53e0\uff1a{item['kind']} {item['name']}")
    else:
        owner.status_main_var.set("\u5f53\u524d\u4f4d\u7f6e\u6ca1\u6709\u53ef\u6298\u53e0\u4ee3\u7801\u5757")
    return "break"


def toggle_fold_current_line(owner, event=None):
    del event
    editor = owner._get_current_editor()
    if not editor:
        return "break"
    line_no = int(editor.index("insert").split(".")[0])
    ok = owner._toggle_fold_by_line(line_no)
    if ok:
        owner._refresh_outline()
        owner.status_main_var.set(f"\u5df2\u5207\u6362\u7b2c {line_no} \u884c\u4ee3\u7801\u5757\u6298\u53e0")
    else:
        owner.status_main_var.set("\u5f53\u524d\u4f4d\u7f6e\u6ca1\u6709\u53ef\u6298\u53e0\u4ee3\u7801\u5757")
    return "break"


def unfold_all_blocks(owner, event=None):
    del event
    owner._clear_all_folds()
    owner._refresh_outline()
    owner.status_main_var.set("已展开当前文件全部折叠块")
    return "break"


def extract_fold_line_from_canvas_hit(owner, canvas, x, y):
    del owner
    try:
        hit_items = canvas.find_overlapping(x - 1, y - 1, x + 1, y + 1)
    except tk.TclError:
        return None
    for item_id in reversed(hit_items):
        try:
            tags = canvas.gettags(item_id)
        except tk.TclError:
            continue
        for tag in tags:
            if str(tag).startswith("fold_line_"):
                try:
                    return int(str(tag).split("_")[-1])
                except (TypeError, ValueError):
                    return None
    return None


def toggle_fold_by_canvas_hit(owner, event):
    canvas = event.widget if event else None
    if canvas is None:
        return False
    line_no = owner._extract_fold_line_from_canvas_hit(canvas, event.x, event.y)
    if not line_no:
        return False
    ok = owner._toggle_fold_by_line(line_no)
    if ok:
        owner._refresh_outline()
        owner.status_main_var.set(f"\u5df2\u5207\u6362\u7b2c {line_no} \u884c\u4ee3\u7801\u5757\u6298\u53e0")
        return True
    return False


def on_guide_canvas_motion(owner, event):
    canvas = event.widget if event else None
    if canvas is None:
        return
    line_no = owner._extract_fold_line_from_canvas_hit(canvas, event.x, event.y)
    try:
        canvas.configure(cursor="hand2" if line_no else "")
    except tk.TclError:
        pass


def update_line_numbers(owner, event=None):
    del event
    editor = owner._get_current_editor()
    line_numbers = owner._get_current_line_numbers()
    if not editor or not line_numbers:
        return

    line_numbers.config(state=tk.NORMAL)
    line_numbers.delete("1.0", tk.END)
    line_count = editor.index("end-1c").split(".")[0]
    line_numbers_string = "\n".join(str(i) for i in range(1, int(line_count) + 1))
    line_numbers.insert("1.0", line_numbers_string)

    line_numbers.tag_configure("right", justify="right")
    line_numbers.tag_add("right", "1.0", "end")

    line_numbers.config(state=tk.DISABLED)
    line_numbers.yview_moveto(editor.yview()[0])
    owner._update_indent_guides()


def update_indent_guides(owner, event=None):
    del event
    tab_id = owner._get_current_tab_id()
    if not tab_id or tab_id not in owner.tabs_data:
        return

    editor = owner.tabs_data[tab_id]["editor"]
    canvas = owner.tabs_data[tab_id].get("guide_canvas")
    if not canvas:
        return

    canvas.delete("all")

    guide_colors = ["#333333", "#3B3B5A", "#333333", "#3B3B5A"]
    func_pattern = re.compile(r"^\s*\u529f\u80fd\s+([^\s(\uff08]+)")
    blueprint_pattern = re.compile(r"^\s*\u5b9a\u4e49\u56fe\u7eb8\s+([^\s(\uff08]+)")

    try:
        first_line = int(editor.index("@0,0").split(".")[0])
        last_line = int(editor.index(f"@0,{editor.winfo_height()}").split(".")[0])
    except Exception:
        return

    line_data = []
    for line_num in range(first_line, last_line + 1):
        line_text = editor.get(f"{line_num}.0", f"{line_num}.end")
        bbox = editor.bbox(f"{line_num}.0")
        if not bbox:
            continue

        stripped = line_text.lstrip()
        decl_kind = None
        if func_pattern.match(line_text):
            decl_kind = "\u529f\u80fd"
        elif blueprint_pattern.match(line_text):
            decl_kind = "\u56fe\u7eb8"

        if stripped:
            indent = len(line_text) - len(stripped)
            levels = indent // 4
        else:
            levels = 0

        line_data.append({
            "line": line_num,
            "levels": levels,
            "bbox": bbox,
            "text": line_text,
            "kind": decl_kind,
        })

    for i in range(len(line_data)):
        if line_data[i]["levels"] == 0 and i > 0:
            prev_levels = line_data[i - 1]["levels"]
            next_levels = 0
            for j in range(i + 1, len(line_data)):
                if line_data[j]["levels"] > 0:
                    next_levels = line_data[j]["levels"]
                    break
            inherited = min(prev_levels, next_levels) if next_levels > 0 else 0
            if inherited > 0:
                line_data[i]["levels"] = inherited

    canvas_width = int(canvas.cget("width"))
    for row in line_data:
        levels = row["levels"]
        if levels == 0:
            continue
        _, y, _, h = row["bbox"]
        for lvl in range(levels):
            x = 24 + lvl * 6
            if x >= canvas_width - 2:
                break
            color = guide_colors[lvl % len(guide_colors)]
            canvas.create_line(x, y, x, y + h, fill=color, width=1)

    folds = owner.tabs_data[tab_id].setdefault("folds", {})
    for row in line_data:
        line_num = row["line"]
        decl_kind = row["kind"]
        if decl_kind not in ("\u529f\u80fd", "\u56fe\u7eb8"):
            continue

        end_line = owner._get_block_end_line(editor, line_num)
        if not end_line:
            continue

        _, y, _, h = row["bbox"]
        y_center = int(y + h / 2)
        collapsed = bool(folds.get(line_num, {}).get("collapsed"))
        symbol = "▸" if collapsed else "▾"

        if decl_kind == "\u529f\u80fd":
            base_fill = "#2A5A41"
            base_outline = "#3C7A5A"
            label_fg = "#8CE3B4"
            label_text = "功"
        else:
            base_fill = "#304A76"
            base_outline = "#41659F"
            label_fg = "#A8C8FF"
            label_text = "图"

        if collapsed:
            base_fill = "#6A4A2B"
            base_outline = "#9B6A3C"

        x_center = 10
        radius = 7
        tags = ("fold_marker", f"fold_line_{line_num}", f"fold_kind_{decl_kind}")

        canvas.create_oval(
            x_center - radius,
            y_center - radius,
            x_center + radius,
            y_center + radius,
            fill=base_fill,
            outline=base_outline,
            width=1,
            tags=tags,
        )
        canvas.create_text(
            x_center,
            y_center,
            text=symbol,
            fill="#E8F2FF",
            font=("Microsoft YaHei", 8, "bold"),
            tags=tags,
        )
        canvas.create_text(
            20,
            y_center,
            text=label_text,
            fill=label_fg,
            font=("Microsoft YaHei", 8, "bold"),
            anchor="w",
            tags=tags,
        )


def highlight_current_line(owner, event=None):
    del event
    editor = owner._get_current_editor()
    if not editor:
        return
    editor.tag_remove("CurrentLine", "1.0", "end")
    editor.tag_add("CurrentLine", "insert linestart", "insert lineend+1c")
