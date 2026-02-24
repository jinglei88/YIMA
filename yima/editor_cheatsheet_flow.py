"""Cheatsheet flows: popup viewer + sidebar quick cards."""

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
from pathlib import Path
from tkinter import ttk


ROOT = Path(__file__).resolve().parents[1]
CHEATSHEET_DOC = ROOT / "文档" / "速查表.md"


def _read_doc_text():
    if not CHEATSHEET_DOC.exists():
        return f"未找到速查表文件：{CHEATSHEET_DOC}"
    return CHEATSHEET_DOC.read_text(encoding="utf-8")


def _parse_headings(text):
    items = []
    for line_no, raw in enumerate(str(text or "").splitlines(), start=1):
        m = re.match(r"^\s*(#{1,6})\s+(.+?)\s*$", raw)
        if not m:
            continue
        level = len(m.group(1))
        title = m.group(2).strip()
        if not title:
            continue
        items.append(
            {
                "line_no": line_no,
                "level": level,
                "title": title,
                "display": ("  " * max(0, level - 1)) + title,
            }
        )
    return items


def _strip_md_code(text):
    value = str(text or "").strip()
    if not value:
        return ""
    if value.startswith("`") and value.endswith("`") and len(value) >= 2:
        value = value[1:-1].strip()
    value = re.sub(r"`([^`]+)`", r"\1", value)
    return value.strip()


def _is_table_separator(text):
    compact = str(text or "").replace(" ", "")
    return bool(compact) and all(ch in "-:|." for ch in compact)


def _parse_quick_patterns(text):
    items = []
    for line_no, raw in enumerate(str(text or "").splitlines(), start=1):
        line = raw.strip()
        if not line.startswith("|") or line.count("|") < 3:
            continue
        if _is_table_separator(line):
            continue
        cells = [part.strip() for part in line.strip("|").split("|")]
        if len(cells) < 3:
            continue
        scene = cells[0]
        syntax = _strip_md_code(cells[1])
        example = _strip_md_code(cells[2])
        if scene in ("场景", "---"):
            continue
        if not syntax:
            continue
        label = f"{scene}  |  {syntax}"
        items.append(
            {
                "scene": scene,
                "syntax": syntax,
                "example": example,
                "line_no": line_no,
                "label": label,
            }
        )
    return items


def _preferred_cheatsheet_geometry(owner):
    try:
        owner.root.update_idletasks()
    except Exception:
        pass

    screen_w = max(900, int(owner.root.winfo_screenwidth()))
    screen_h = max(700, int(owner.root.winfo_screenheight()))
    try:
        root_w = int(owner.root.winfo_width() or 0)
        root_h = int(owner.root.winfo_height() or 0)
    except Exception:
        root_w, root_h = 0, 0

    base_w = max(1120, int(root_w * 0.86)) if root_w > 0 else 1220
    base_h = max(760, int(root_h * 0.86)) if root_h > 0 else 820
    width = min(base_w, int(screen_w * 0.94))
    height = min(base_h, int(screen_h * 0.92))
    return max(980, width), max(680, height)


def _center_to_owner(owner, win, width=None, height=None):
    try:
        owner.root.update_idletasks()
        win.update_idletasks()
    except Exception:
        pass

    if width is None:
        try:
            width = int(win.winfo_width() or 0)
        except Exception:
            width = 0
    if height is None:
        try:
            height = int(win.winfo_height() or 0)
        except Exception:
            height = 0
    if width <= 0 or height <= 0:
        width, height = _preferred_cheatsheet_geometry(owner)

    try:
        root_x = int(owner.root.winfo_x() or 0)
        root_y = int(owner.root.winfo_y() or 0)
        root_w = int(owner.root.winfo_width() or 0)
        root_h = int(owner.root.winfo_height() or 0)
    except Exception:
        root_x = root_y = 0
        root_w = width
        root_h = height

    screen_w = max(width, int(owner.root.winfo_screenwidth()))
    screen_h = max(height, int(owner.root.winfo_screenheight()))
    x = root_x + max(0, (root_w - width) // 2)
    y = root_y + max(0, (root_h - height) // 2)
    x = max(0, min(x, screen_w - width))
    y = max(0, min(y, screen_h - height))
    try:
        win.geometry(f"{width}x{height}+{x}+{y}")
    except tk.TclError:
        pass


def _apply_cheatsheet_outline_width(owner, target_width=None):
    body = getattr(owner, "_cheatsheet_body", None)
    if body is None:
        return
    target = int(target_width or getattr(owner, "_cheatsheet_outline_target_w", 360) or 360)
    target = max(300, target)
    try:
        body.update_idletasks()
        body_w = int(body.winfo_width() or 0)
        if body_w > 0:
            # 给右侧正文保留至少 420px，避免挤压阅读区
            target = min(target, max(300, body_w - 420))
        body.sash_place(0, target, 0)
    except tk.TclError:
        pass


def _create_dark_entry(owner, parent, textvariable, width=None):
    entry_kwargs = {
        "master": parent,
        "textvariable": textvariable,
        "font": owner.font_ui,
        "bg": owner.theme_panel_inner_bg,
        "fg": owner.theme_fg,
        "insertbackground": owner.theme_fg,
        "selectbackground": owner.theme_accent,
        "selectforeground": "#FFFFFF",
        "relief": "flat",
        "bd": 0,
        "highlightthickness": 1,
        "highlightbackground": owner.theme_toolbar_border,
        "highlightcolor": owner.theme_accent,
    }
    if width is not None:
        entry_kwargs["width"] = int(width)
    entry = tk.Entry(**entry_kwargs)

    def _on_focus_in(_event):
        try:
            entry.configure(highlightbackground=owner.theme_accent)
        except tk.TclError:
            pass

    def _on_focus_out(_event):
        try:
            entry.configure(highlightbackground=owner.theme_toolbar_border)
        except tk.TclError:
            pass

    entry.bind("<FocusIn>", _on_focus_in, add="+")
    entry.bind("<FocusOut>", _on_focus_out, add="+")
    return entry


def _ensure_cheatsheet_window(owner):
    win = getattr(owner, "_cheatsheet_window", None)
    if win is not None:
        try:
            if win.winfo_exists():
                return win
        except tk.TclError:
            pass

    win = tk.Toplevel(owner.root)
    win.title("易码速查表")
    init_w, init_h = _preferred_cheatsheet_geometry(owner)
    _center_to_owner(owner, win, init_w, init_h)
    win.configure(bg=owner.theme_bg)
    try:
        win.minsize(980, 680)
    except tk.TclError:
        pass
    win.protocol("WM_DELETE_WINDOW", win.withdraw)

    top = tk.Frame(win, bg=owner.theme_toolbar_bg, padx=10, pady=8)
    top.pack(fill=tk.X)

    tk.Label(
        top,
        text="速查表 QUICK REFERENCE",
        font=("Microsoft YaHei", 10, "bold"),
        bg=owner.theme_toolbar_bg,
        fg="#DFE6EE",
    ).pack(side=tk.LEFT)

    owner._cheatsheet_query_var = tk.StringVar(value="")
    search_entry = _create_dark_entry(owner, top, owner._cheatsheet_query_var, width=26)
    search_entry.pack(side=tk.RIGHT, padx=(8, 0))
    owner._cheatsheet_search_entry = search_entry

    refresh_btn = tk.Button(
        top,
        text="刷新",
        command=lambda: refresh_cheatsheet(owner),
        font=("Microsoft YaHei", 8),
        bg=owner.theme_toolbar_group_bg,
        fg=owner.theme_toolbar_fg,
        activebackground=owner.theme_toolbar_hover,
        activeforeground="#FFFFFF",
        relief="flat",
        bd=0,
        padx=8,
        pady=2,
        cursor="hand2",
    )
    refresh_btn.pack(side=tk.RIGHT)

    open_doc_btn = tk.Button(
        top,
        text="在编辑区打开",
        command=lambda: _open_doc_in_editor(owner),
        font=("Microsoft YaHei", 8),
        bg=owner.theme_toolbar_group_bg,
        fg=owner.theme_toolbar_fg,
        activebackground=owner.theme_toolbar_hover,
        activeforeground="#FFFFFF",
        relief="flat",
        bd=0,
        padx=8,
        pady=2,
        cursor="hand2",
    )
    open_doc_btn.pack(side=tk.RIGHT, padx=(0, 6))

    body = tk.PanedWindow(win, orient=tk.HORIZONTAL, sashwidth=5, bg=owner.theme_sash, borderwidth=0)
    body.pack(fill=tk.BOTH, expand=True)

    outline_target_w = min(460, max(340, int(init_w * 0.34)))
    left = tk.Frame(body, bg=owner.theme_panel_bg, width=outline_target_w)
    body.add(left, stretch="never", minsize=max(300, outline_target_w - 40))

    tk.Label(
        left,
        text="章节目录",
        font=("Microsoft YaHei", 9, "bold"),
        bg=owner.theme_panel_bg,
        fg="#9FB0C5",
        anchor="w",
        padx=10,
        pady=6,
    ).pack(fill=tk.X)

    outline_box = tk.Frame(left, bg=owner.theme_panel_bg, padx=8, pady=0)
    outline_box.pack(fill=tk.BOTH, expand=True, pady=(0, 8))

    outline = tk.Listbox(
        outline_box,
        font=("Microsoft YaHei", 9),
        bg=owner.theme_panel_inner_bg,
        fg=owner.theme_fg,
        selectbackground=owner.theme_accent,
        selectforeground="#FFFFFF",
        borderwidth=0,
        highlightthickness=0,
        relief="flat",
    )
    outline_vsb = ttk.Scrollbar(outline_box, orient="vertical", command=outline.yview)
    outline.configure(yscrollcommand=outline_vsb.set)
    outline.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    outline_vsb.pack(side=tk.RIGHT, fill=tk.Y)
    owner._cheatsheet_outline = outline

    right = tk.Frame(body, bg=owner.theme_panel_bg)
    body.add(right, stretch="always", minsize=420)

    tk.Label(
        right,
        text=f"文档：{CHEATSHEET_DOC}",
        font=("Microsoft YaHei", 8),
        bg=owner.theme_panel_bg,
        fg="#8FA1B8",
        anchor="w",
        padx=10,
        pady=6,
    ).pack(fill=tk.X)

    text_box = tk.Frame(right, bg=owner.theme_panel_bg, padx=8, pady=0)
    text_box.pack(fill=tk.BOTH, expand=True, pady=(0, 6))

    text_widget = tk.Text(
        text_box,
        wrap=tk.WORD,
        font=("Microsoft YaHei", 10),
        bg=owner.theme_bg,
        fg="#D7E0EC",
        insertbackground="#D7E0EC",
        borderwidth=0,
        highlightthickness=0,
        relief="flat",
        padx=10,
        pady=8,
    )
    text_vsb = ttk.Scrollbar(text_box, orient="vertical", command=text_widget.yview)
    text_widget.configure(yscrollcommand=text_vsb.set)
    text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    text_vsb.pack(side=tk.RIGHT, fill=tk.Y)
    owner._cheatsheet_text = text_widget

    text_widget.tag_configure("CheatTitle", foreground="#9CDCFE", font=("Microsoft YaHei", 10, "bold"))
    text_widget.tag_configure("CheatSearch", background="#3B3A1A", foreground="#F3E99A")
    text_widget.tag_configure("CheatCurrentHeading", background="#1E4C70", foreground="#FFFFFF")

    owner._cheatsheet_status_var = tk.StringVar(value="可搜索关键字，双击左侧章节可快速定位")
    tk.Label(
        win,
        textvariable=owner._cheatsheet_status_var,
        font=("Microsoft YaHei", 8),
        bg=owner.theme_toolbar_bg,
        fg="#9FB0C5",
        anchor="w",
        padx=10,
        pady=5,
    ).pack(fill=tk.X, side=tk.BOTTOM)

    search_entry.bind("<KeyRelease>", lambda e: _on_query_changed(owner), add="+")
    search_entry.bind("<Return>", lambda e: _jump_first_visible_heading(owner), add="+")
    outline.bind("<Double-Button-1>", lambda e: _on_outline_activate(owner), add="+")
    outline.bind("<Return>", lambda e: _on_outline_activate(owner), add="+")
    win.bind("<Escape>", lambda e: win.withdraw(), add="+")
    win.bind("<Control-f>", lambda e: owner._cheatsheet_search_entry.focus_set(), add="+")

    owner._cheatsheet_window = win
    owner._cheatsheet_body = body
    owner._cheatsheet_outline_target_w = outline_target_w
    owner._cheatsheet_headings_all = []
    owner._cheatsheet_headings_visible = []
    win.after_idle(lambda: _apply_cheatsheet_outline_width(owner))
    return win


def _render_doc_text(owner, text):
    text_widget = owner._cheatsheet_text
    text_widget.configure(state=tk.NORMAL)
    text_widget.delete("1.0", tk.END)
    text_widget.insert("1.0", text or "")
    text_widget.tag_remove("CheatTitle", "1.0", tk.END)
    for idx, raw in enumerate((text or "").splitlines(), start=1):
        if re.match(r"^\s*#{1,6}\s+.+", raw):
            text_widget.tag_add("CheatTitle", f"{idx}.0", f"{idx}.end")
    text_widget.configure(state=tk.DISABLED)


def _render_outline(owner, headings):
    outline = owner._cheatsheet_outline
    outline.delete(0, tk.END)
    owner._cheatsheet_headings_visible = list(headings or [])
    for item in owner._cheatsheet_headings_visible:
        outline.insert(tk.END, item.get("display", item.get("title", "")))
    if owner._cheatsheet_headings_visible:
        outline.selection_clear(0, tk.END)
        outline.selection_set(0)
        outline.activate(0)


def _apply_search_highlight(owner, query):
    text_widget = owner._cheatsheet_text
    text_widget.configure(state=tk.NORMAL)
    text_widget.tag_remove("CheatSearch", "1.0", tk.END)
    if query:
        start = "1.0"
        while True:
            pos = text_widget.search(query, start, stopindex=tk.END, nocase=True)
            if not pos:
                break
            end = f"{pos}+{len(query)}c"
            text_widget.tag_add("CheatSearch", pos, end)
            start = end
    text_widget.configure(state=tk.DISABLED)


def _filter_headings(owner, query):
    q = str(query or "").strip().lower()
    all_items = owner._cheatsheet_headings_all or []
    if not q:
        return all_items
    return [item for item in all_items if q in str(item.get("title", "")).lower()]


def _jump_to_line(owner, line_no, title_hint=""):
    line_no = max(1, int(line_no or 1))
    text_widget = owner._cheatsheet_text
    start = f"{line_no}.0"
    end = f"{line_no}.end"
    text_widget.configure(state=tk.NORMAL)
    text_widget.tag_remove("CheatCurrentHeading", "1.0", tk.END)
    text_widget.tag_add("CheatCurrentHeading", start, end)
    text_widget.configure(state=tk.DISABLED)
    text_widget.see(start)
    if hasattr(owner, "_cheatsheet_status_var"):
        if title_hint:
            owner._cheatsheet_status_var.set(f"已定位：{title_hint}（第 {line_no} 行）")
        else:
            owner._cheatsheet_status_var.set(f"已定位到第 {line_no} 行")


def _jump_to_heading(owner, item):
    if not item:
        return
    _jump_to_line(owner, item.get("line_no"), item.get("title", ""))


def _jump_first_visible_heading(owner):
    if not owner._cheatsheet_headings_visible:
        return "break"
    _jump_to_heading(owner, owner._cheatsheet_headings_visible[0])
    return "break"


def _on_outline_activate(owner):
    outline = owner._cheatsheet_outline
    selection = outline.curselection()
    if not selection:
        return "break"
    idx = selection[0]
    items = owner._cheatsheet_headings_visible or []
    if idx < 0 or idx >= len(items):
        return "break"
    _jump_to_heading(owner, items[idx])
    return "break"


def _on_query_changed(owner):
    query = owner._cheatsheet_query_var.get() if hasattr(owner, "_cheatsheet_query_var") else ""
    filtered = _filter_headings(owner, query)
    fallback_to_all = False
    if query and not filtered and owner._cheatsheet_headings_all:
        # 查询词可能命中文档正文（而非标题）；目录不应因此变空。
        filtered = list(owner._cheatsheet_headings_all)
        fallback_to_all = True
    _render_outline(owner, filtered)
    _apply_search_highlight(owner, query)
    if query:
        if fallback_to_all:
            owner._cheatsheet_status_var.set(
                f"筛选关键字：{query}（标题未命中，已显示全部章节）"
            )
        else:
            owner._cheatsheet_status_var.set(f"筛选关键字：{query}（命中章节 {len(filtered)} 个）")
    else:
        owner._cheatsheet_status_var.set("可搜索关键字，双击左侧章节可快速定位")


def _open_doc_in_editor(owner):
    text = _read_doc_text()
    owner._create_editor_tab(str(CHEATSHEET_DOC), text)
    if hasattr(owner, "status_main_var"):
        owner.status_main_var.set("已在编辑区打开速查表文档")


def refresh_cheatsheet(owner, event=None):
    _ensure_cheatsheet_window(owner)
    text = _read_doc_text()
    owner._cheatsheet_headings_all = _parse_headings(text)
    _render_doc_text(owner, text)
    _on_query_changed(owner)
    if owner._cheatsheet_headings_all and owner._cheatsheet_headings_visible:
        _jump_to_heading(owner, owner._cheatsheet_headings_visible[0])
    elif owner._cheatsheet_headings_all:
        _jump_to_heading(owner, owner._cheatsheet_headings_all[0])
    else:
        owner._cheatsheet_status_var.set("速查表无可用章节标题")
    refresh_cheatsheet_quick_panel(owner)
    return "break" if event is not None else None


def open_cheatsheet(owner, event=None, line_no=None, query=""):
    win = _ensure_cheatsheet_window(owner)
    refresh_cheatsheet(owner)
    if query and hasattr(owner, "_cheatsheet_query_var"):
        owner._cheatsheet_query_var.set(str(query))
        _on_query_changed(owner)
    if line_no:
        _jump_to_line(owner, line_no)
    try:
        cur_w, cur_h = _preferred_cheatsheet_geometry(owner)
        _center_to_owner(owner, win, cur_w, cur_h)
        win.deiconify()
        win.lift()
        win.focus_force()
        owner._cheatsheet_search_entry.focus_set()
        win.after_idle(lambda: _apply_cheatsheet_outline_width(owner))
    except tk.TclError:
        pass
    if hasattr(owner, "status_main_var"):
        owner.status_main_var.set("速查表已打开（F1 / Ctrl+Shift+K）")
    return "break"


def _format_quick_pattern_label(item):
    scene = str(item.get("scene", "")).strip()
    syntax = str(item.get("syntax", "")).strip()
    return f"{scene} · {syntax}" if scene and syntax else (syntax or scene or "（空）")


def _render_quick_patterns(owner, items):
    listbox = getattr(owner, "cheatsheet_quick_listbox", None)
    if listbox is None:
        return
    listbox.delete(0, tk.END)
    owner._cheatsheet_quick_items_visible = list(items or [])
    for item in owner._cheatsheet_quick_items_visible:
        listbox.insert(tk.END, _format_quick_pattern_label(item))
    if owner._cheatsheet_quick_items_visible:
        listbox.selection_clear(0, tk.END)
        listbox.selection_set(0)
        listbox.activate(0)
    _update_quick_pattern_detail(owner)


def _filter_quick_patterns(owner, query):
    all_items = owner._cheatsheet_quick_items_all or []
    q = str(query or "").strip().lower()
    if not q:
        return all_items
    filtered = []
    for item in all_items:
        haystack = " ".join(
            [
                str(item.get("scene", "")),
                str(item.get("syntax", "")),
                str(item.get("example", "")),
            ]
        ).lower()
        if q in haystack:
            filtered.append(item)
    return filtered


def _selected_quick_pattern(owner):
    listbox = getattr(owner, "cheatsheet_quick_listbox", None)
    if listbox is None:
        return None
    selection = listbox.curselection()
    if not selection:
        return None
    idx = int(selection[0])
    visible = owner._cheatsheet_quick_items_visible or []
    if idx < 0 or idx >= len(visible):
        return None
    return visible[idx]


def _update_quick_pattern_detail(owner):
    detail_var = getattr(owner, "cheatsheet_quick_detail_var", None)
    if detail_var is None:
        return
    item = _selected_quick_pattern(owner)
    if not item:
        detail_var.set("推荐：-\n示例：-")
        return
    syntax = str(item.get("syntax", "") or "（无）").replace("\n", " ").replace("\r", " ").strip()
    example = str(item.get("example", "") or "（无）").replace("\n", " ").replace("\r", " ").strip()
    detail_var.set(f"推荐：{syntax}\n示例：{example}")


def setup_cheatsheet_quick_section(owner, sidebar_frame, create_tool_btn):
    section = tk.Frame(
        sidebar_frame,
        bg=owner.theme_panel_bg,
        highlightthickness=1,
        highlightbackground=owner.theme_toolbar_border,
        highlightcolor=owner.theme_toolbar_border,
        bd=0,
    )
    section.pack(fill=tk.X, padx=8, pady=(0, 10))

    top = tk.Frame(section, bg=owner.theme_panel_bg, padx=8, pady=6)
    top.pack(fill=tk.X)

    tk.Label(
        top,
        text="速查卡 CHEAT CARD",
        font=("Microsoft YaHei", 8, "bold"),
        bg=owner.theme_panel_bg,
        fg="#8FA1B8",
        anchor="w",
    ).pack(side=tk.LEFT, fill=tk.X, expand=True)

    create_tool_btn(
        top,
        "展开",
        owner._open_cheatsheet_from_quick,
        variant="subtle",
        compact=True,
        font=("Microsoft YaHei", 8),
    ).pack(side=tk.RIGHT, padx=(4, 0))
    create_tool_btn(
        top,
        "刷新",
        owner._refresh_cheatsheet_quick_panel,
        variant="subtle",
        compact=True,
        font=("Microsoft YaHei", 8),
    ).pack(side=tk.RIGHT)

    body = tk.Frame(section, bg=owner.theme_panel_bg, padx=8)
    body.pack(fill=tk.X, pady=(0, 8))

    owner.cheatsheet_quick_query_var = tk.StringVar(value="")
    entry = _create_dark_entry(owner, body, owner.cheatsheet_quick_query_var)
    entry.pack(fill=tk.X, pady=(0, 6))
    owner.cheatsheet_quick_entry = entry

    list_box_wrap = tk.Frame(body, bg=owner.theme_panel_bg)
    list_box_wrap.pack(fill=tk.X)
    listbox = tk.Listbox(
        list_box_wrap,
        height=5,
        font=owner.font_ui,
        bg=owner.theme_panel_inner_bg,
        fg=owner.theme_fg,
        selectbackground=owner.theme_accent,
        selectforeground="#FFFFFF",
        borderwidth=0,
        highlightthickness=0,
        relief="flat",
    )
    listbox_vsb = ttk.Scrollbar(list_box_wrap, orient="vertical", command=listbox.yview)
    listbox.configure(yscrollcommand=listbox_vsb.set)
    listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    listbox_vsb.pack(side=tk.RIGHT, fill=tk.Y)
    owner.cheatsheet_quick_listbox = listbox

    action_row = tk.Frame(body, bg=owner.theme_panel_bg)
    action_row.pack(fill=tk.X, pady=(6, 0))
    create_tool_btn(
        action_row,
        "插入推荐写法",
        owner._insert_selected_cheatsheet_pattern,
        variant="subtle",
        compact=True,
        font=("Microsoft YaHei", 8),
    ).pack(side=tk.LEFT)
    create_tool_btn(
        action_row,
        "打开全文",
        owner.open_cheatsheet,
        variant="subtle",
        compact=True,
        font=("Microsoft YaHei", 8),
    ).pack(side=tk.LEFT, padx=(4, 0))

    owner.cheatsheet_quick_detail_var = tk.StringVar(value="推荐：-\n示例：-")
    detail_box = tk.Frame(
        body,
        bg=owner.theme_panel_inner_bg,
        highlightthickness=1,
        highlightbackground=owner.theme_toolbar_border,
        highlightcolor=owner.theme_toolbar_border,
        bd=0,
    )
    detail_box.pack(fill=tk.X, pady=(6, 0))
    detail_label = tk.Label(
        detail_box,
        textvariable=owner.cheatsheet_quick_detail_var,
        font=("Microsoft YaHei", 8),
        bg=owner.theme_panel_inner_bg,
        fg="#9FB0C5",
        anchor="nw",
        justify="left",
        padx=6,
        pady=4,
        height=2,
    )
    detail_label.pack(fill=tk.X)
    owner.cheatsheet_quick_detail_label = detail_label

    owner._cheatsheet_quick_items_all = []
    owner._cheatsheet_quick_items_visible = []
    entry.bind("<KeyRelease>", owner._on_cheatsheet_quick_query_changed, add="+")
    entry.bind("<Return>", owner._insert_selected_cheatsheet_pattern, add="+")
    listbox.bind("<<ListboxSelect>>", owner._on_cheatsheet_quick_select, add="+")
    listbox.bind("<Double-Button-1>", owner._insert_selected_cheatsheet_pattern, add="+")
    listbox.bind("<Return>", owner._insert_selected_cheatsheet_pattern, add="+")
    refresh_cheatsheet_quick_panel(owner)


def refresh_cheatsheet_quick_panel(owner, event=None):
    if not hasattr(owner, "cheatsheet_quick_listbox"):
        return "break" if event is not None else None
    text = _read_doc_text()
    owner._cheatsheet_quick_items_all = _parse_quick_patterns(text)
    query = owner.cheatsheet_quick_query_var.get() if hasattr(owner, "cheatsheet_quick_query_var") else ""
    filtered = _filter_quick_patterns(owner, query)
    _render_quick_patterns(owner, filtered)
    return "break" if event is not None else None


def on_cheatsheet_quick_query_changed(owner, event=None):
    if not hasattr(owner, "cheatsheet_quick_query_var"):
        return "break" if event is not None else None
    query = owner.cheatsheet_quick_query_var.get()
    filtered = _filter_quick_patterns(owner, query)
    _render_quick_patterns(owner, filtered)
    if hasattr(owner, "status_main_var"):
        if query:
            owner.status_main_var.set(f"速查卡筛选：{query}（命中 {len(filtered)} 条）")
        else:
            owner.status_main_var.set("速查卡已重置")
    return "break" if event is not None and getattr(event, "keysym", "") == "Return" else None


def on_cheatsheet_quick_select(owner, event=None):
    _update_quick_pattern_detail(owner)
    return "break" if event is not None and getattr(event, "type", "") == "2" else None


def insert_selected_cheatsheet_pattern(owner, event=None):
    item = _selected_quick_pattern(owner)
    if not item:
        if hasattr(owner, "status_main_var"):
            owner.status_main_var.set("请先在速查卡里选一条写法")
        return "break"

    editor = owner._get_current_editor()
    if editor is None:
        if hasattr(owner, "status_main_var"):
            owner.status_main_var.set("当前没有打开代码编辑区，无法插入")
        return "break"

    insert_text = str(item.get("syntax", "")).strip()
    if not insert_text:
        return "break"

    try:
        if editor.tag_ranges("sel"):
            editor.delete("sel.first", "sel.last")
        editor.insert("insert", insert_text)
        editor.focus_set()
        owner._schedule_highlight()
        owner._update_line_numbers()
        owner._update_cursor_status()
        owner._schedule_diagnose()
        if hasattr(owner, "status_main_var"):
            owner.status_main_var.set(f"已插入推荐写法：{item.get('scene', '')}")
    except tk.TclError:
        if hasattr(owner, "status_main_var"):
            owner.status_main_var.set("插入失败：当前编辑器不可用")
    return "break"


def open_cheatsheet_from_quick(owner, event=None):
    item = _selected_quick_pattern(owner)
    line_no = item.get("line_no") if item else None
    query = ""
    open_cheatsheet(owner, line_no=line_no, query=query)
    return "break"
