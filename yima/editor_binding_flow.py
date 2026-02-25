"""Editor event bindings, tag setup, and small UI helper rendering."""

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
from tkinter import ttk


def style_scrolledtext_vbar(owner, text_widget, parent=None):
    """统一 ScrolledText 滚动条为暗色。"""
    try:
        frame = getattr(text_widget, "frame", None)
        if frame:
            frame.configure(bg=owner.theme_bg, bd=0, highlightthickness=0)
    except tk.TclError:
        pass

    if parent is not None:
        inner = getattr(text_widget, "vbar", None)
        if inner:
            try:
                inner.pack_forget()
            except tk.TclError:
                pass
        outer = ttk.Scrollbar(parent, orient="vertical", command=text_widget.yview)
        outer.pack(side=tk.RIGHT, fill=tk.Y)
        text_widget.configure(yscrollcommand=outer.set)
        text_widget.vbar = outer
        return

    vbar = getattr(text_widget, "vbar", None)
    if not vbar:
        return

    scrollbar_width = max(10, int(11 * owner.dpi_scale))
    style_options = {
        "width": scrollbar_width,
        "bg": "#3A4555",
        "activebackground": "#4C5D73",
        "troughcolor": owner.theme_panel_inner_bg,
        "relief": "flat",
        "borderwidth": 0,
        "highlightthickness": 0,
        "elementborderwidth": 0,
        "highlightbackground": owner.theme_panel_inner_bg,
        "highlightcolor": owner.theme_panel_inner_bg,
    }
    for key, value in style_options.items():
        try:
            vbar.configure(**{key: value})
        except tk.TclError:
            pass


def build_toolbar_icon(owner, kind="run", size=16, color="#FFFFFF"):
    del owner
    size = max(12, int(size))
    img = tk.PhotoImage(width=size, height=size)

    def put_px(x, y):
        if 0 <= x < size and 0 <= y < size:
            img.put(color, (x, y))

    def draw_line(x0, y0, x1, y1, thickness=1):
        x0 = int(x0)
        y0 = int(y0)
        x1 = int(x1)
        y1 = int(y1)
        dx = abs(x1 - x0)
        dy = -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        radius = max(0, int(thickness) - 1)
        while True:
            for oy in range(-radius, radius + 1):
                for ox in range(-radius, radius + 1):
                    put_px(x0 + ox, y0 + oy)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x0 += sx
            if e2 <= dx:
                err += dx
                y0 += sy

    def draw_rect(x, y, w, h, thickness=1):
        left = int(x)
        top = int(y)
        right = int(x + w - 1)
        bottom = int(y + h - 1)
        for t in range(max(1, int(thickness))):
            for px in range(left + t, right - t + 1):
                put_px(px, top + t)
                put_px(px, bottom - t)
            for py in range(top + t, bottom - t + 1):
                put_px(left + t, py)
                put_px(right - t, py)

    if kind == "code":
        # </>：代码图标（更接近 SVG 风格的粗线轮廓）
        margin = int(size * 0.16)
        mid = size // 2
        left_x = margin + 2
        right_x = size - margin - 2
        arm = max(5, int(size * 0.24))
        lift = max(4, int(size * 0.20))
        draw_line(left_x + arm, mid - lift, left_x, mid, thickness=2)
        draw_line(left_x + arm, mid + lift, left_x, mid, thickness=2)
        draw_line(right_x - arm, mid - lift, right_x, mid, thickness=2)
        draw_line(right_x - arm, mid + lift, right_x, mid, thickness=2)
        draw_line(size // 2 + 3, margin + 1, size // 2 - 2, size - margin - 2, thickness=2)
        return img

    if kind == "design":
        # 画板布局图标：左边栏 + 右侧网格块
        inset = 2
        draw_rect(inset, inset, size - inset * 2, size - inset * 2, thickness=2)
        tool_w = max(4, int(size * 0.24))
        draw_line(inset + tool_w, inset + 1, inset + tool_w, size - inset - 1, thickness=2)
        cell = max(3, int((size - tool_w - 8) / 3))
        gx = inset + tool_w + 2
        gy = inset + 2
        for row in range(3):
            for col in range(2):
                draw_rect(gx + col * (cell + 2), gy + row * (cell + 2), cell, cell, thickness=1)
        return img

    if kind == "run":
        # 播放图标做得更内收，避免过尖、过大
        left = int(size * 0.28)
        right = int(size * 0.82)
        top = int(size * 0.20)
        bottom = int(size * 0.80)
        mid = (top + bottom) // 2
        half = max(1, (bottom - top) // 2)
        for y in range(top, bottom + 1):
            t = abs(y - mid) / float(half)
            x_end = int(right - t * (right - left))
            for x in range(left, x_end + 1):
                put_px(x, y)
        return img

    box_l = int(size * 0.15)
    box_r = int(size * 0.60)
    box_t = int(size * 0.18)
    box_b = int(size * 0.82)
    for x in range(box_l, box_r + 1):
        put_px(x, box_t)
        put_px(x, box_b)
    for y in range(box_t, box_b + 1):
        put_px(box_l, y)
        put_px(box_r, y)

    ay = size // 2
    ax0 = int(size * 0.44)
    ax1 = int(size * 0.92)
    for x in range(ax0, ax1 + 1):
        put_px(x, ay)
    put_px(ax1 - 2, ay - 1)
    put_px(ax1 - 2, ay + 1)
    put_px(ax1 - 1, ay - 2)
    put_px(ax1 - 1, ay + 2)
    put_px(ax1, ay)
    return img


def setup_tags(owner, editor=None):
    target_editor = editor if editor else owner._get_current_editor()
    if not target_editor:
        return

    target_editor.tag_configure("Keyword", foreground="#C586C0", font=(owner.font_code[0], owner.font_code[1], "bold"))
    target_editor.tag_configure("Define", foreground="#569CD6", font=(owner.font_code[0], owner.font_code[1], "bold"))
    target_editor.tag_configure("Operator", foreground="#D4D4D4")
    target_editor.tag_configure("String", foreground="#CE9178")
    target_editor.tag_configure("Number", foreground="#B5CEA8")
    target_editor.tag_configure("Comment", foreground="#6A9955", font=(owner.font_code[0], owner.font_code[1], "italic"))
    target_editor.tag_configure("Boolean", foreground="#4FC1FF", font=(owner.font_code[0], owner.font_code[1], "bold"))
    target_editor.tag_configure("Builtin", foreground="#DCDCAA", font=(owner.font_code[0], owner.font_code[1], "bold"))
    target_editor.tag_configure("ModuleAlias", foreground="#4FC1FF", font=(owner.font_code[0], owner.font_code[1], "bold"))
    target_editor.tag_configure("ObjectRef", foreground="#9CDCFE")
    target_editor.tag_configure("MemberName", foreground="#FFD27F", font=(owner.font_code[0], owner.font_code[1], "bold"))
    target_editor.tag_configure("ErrorLine", background="#51222A")
    target_editor.tag_configure("WarnLine", background="#4D4521")
    target_editor.tag_configure("SearchMatch", background="#3B3A1A", foreground="#F3E99A")
    target_editor.tag_configure("SearchCurrent", background="#6A5C1A", foreground="#FFF4AA")
    target_editor.tag_configure("MultiCursorSel", background="#1D4B63", foreground="#FFFFFF")

    owner.output.tag_configure("ConsoleError", foreground="#FF6B6B", font=(owner.output.cget("font"),))

    target_editor.tag_configure("CurrentLine", background=owner.theme_line_bg)
    target_editor.tag_lower("CurrentLine")
    target_editor.tag_raise("ErrorLine")
    target_editor.tag_raise("WarnLine")
    target_editor.tag_raise("SearchMatch")
    target_editor.tag_raise("SearchCurrent")
    target_editor.tag_raise("MultiCursorSel")
    target_editor.tag_raise("ModuleAlias")
    target_editor.tag_raise("ObjectRef")
    target_editor.tag_raise("MemberName")


def bind_events(owner, editor=None):
    target_editor = editor if editor else owner._get_current_editor()
    if not target_editor:
        return

    target_editor.bind("<KeyRelease>", owner._remember_edit_cursor, add="+")
    target_editor.bind("<KeyRelease>", owner._schedule_highlight)
    target_editor.bind("<KeyRelease>", owner._update_line_numbers, add="+")
    target_editor.bind("<KeyRelease>", owner._highlight_current_line, add="+")
    target_editor.bind("<KeyRelease>", owner._schedule_diagnose, add="+")
    target_editor.bind("<KeyRelease>", owner._schedule_outline_update, add="+")
    target_editor.bind("<KeyRelease>", owner._update_cursor_status, add="+")
    target_editor.bind("<ButtonRelease>", owner._highlight_current_line, add="+")
    target_editor.bind("<ButtonRelease>", owner._update_cursor_status, add="+")
    target_editor.bind("<ButtonRelease>", owner._schedule_calltip_update, add="+")
    target_editor.bind("<ButtonRelease>", owner._remember_edit_cursor, add="+")
    target_editor.bind("<ButtonRelease-1>", owner._sync_insert_after_click, add="+")
    target_editor.bind("<MouseWheel>", owner._update_line_numbers, add="+")
    target_editor.bind("<Configure>", owner._update_line_numbers, add="+")
    target_editor.bind("<FocusIn>", owner._update_cursor_status, add="+")
    target_editor.bind("<<Modified>>", owner._on_editor_modified, add="+")
    target_editor.bind("<Alt-Button-1>", owner.multi_cursor_alt_click, add="+")
    target_editor.bind("<KeyPress>", owner._handle_multi_cursor_key, add="+")
    target_editor.bind("<KeyPress>", owner._handle_auto_pairs, add="+")

    target_editor.bind("<Return>", owner._handle_return)
    target_editor.bind("<KP_Enter>", owner._handle_return)

    target_editor.bind("<Tab>", owner._handle_tab)
    target_editor.bind("<Shift-Tab>", owner._handle_shift_tab)

    owner.tree.bind("<Double-1>", owner.on_tree_double_click)
    owner.tree.bind("<Button-3>", owner.popup_tree_menu)
    owner.notebook.bind("<<NotebookTabChanged>>", owner.on_tab_changed)

    target_editor.bind("<KeyRelease>", owner._check_autocomplete, add="+")
    target_editor.bind("<FocusOut>", owner._on_editor_focus_out)
    target_editor.bind("<Button-1>", owner._handle_editor_left_click)
    target_editor.bind("<Up>", owner._handle_autocomplete_nav)
    target_editor.bind("<Down>", owner._handle_autocomplete_nav)
    target_editor.bind("<Prior>", owner._handle_autocomplete_nav)
    target_editor.bind("<Next>", owner._handle_autocomplete_nav)
    target_editor.bind("<Escape>", lambda e: owner._hide_autocomplete())
    target_editor.bind("<Control-space>", owner._trigger_autocomplete)
