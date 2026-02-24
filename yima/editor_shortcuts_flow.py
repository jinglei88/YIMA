"""Shortcut binding flow helpers extracted from 易码编辑器.py."""

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


def bind_global_shortcuts(owner):
    owner.root.bind("<Control-s>", owner._shortcut_save)
    owner.root.bind("<Control-o>", owner._shortcut_open)
    owner.root.bind("<Control-n>", owner._shortcut_new)
    owner.root.bind("<F1>", owner._shortcut_cheatsheet)
    owner.root.bind("<Control-Shift-K>", owner._shortcut_cheatsheet)
    owner.root.bind("<Control-Shift-k>", owner._shortcut_cheatsheet)
    owner.root.bind("<F5>", owner._shortcut_run)
    owner.root.bind("<Control-d>", owner._shortcut_multi_add_next)
    owner.root.bind("<Control-D>", owner._shortcut_multi_add_next)
    owner.root.bind("<Control-Shift-L>", owner._shortcut_multi_select_all)
    owner.root.bind("<Control-Shift-l>", owner._shortcut_multi_select_all)
    owner.root.bind("<Control-f>", owner._shortcut_find)
    owner.root.bind("<Control-h>", owner._shortcut_replace)
    owner.root.bind("<Control-Shift-R>", owner._shortcut_rename_symbol)
    owner.root.bind("<Control-Shift-r>", owner._shortcut_rename_symbol)
    owner.root.bind("<Control-Shift-Q>", owner._shortcut_quick_view)
    owner.root.bind("<Control-Shift-q>", owner._shortcut_quick_view)
    owner.root.bind("<Control-Tab>", owner._shortcut_next_tab)
    owner.root.bind("<Control-Shift-Tab>", owner._shortcut_prev_tab)
    owner.root.bind("<Control-ISO_Left_Tab>", owner._shortcut_prev_tab)
    owner.root.bind("<Alt-f>", owner._shortcut_toggle_fold)
    owner.root.bind("<Alt-u>", owner._shortcut_unfold_all)


def shortcut_save(owner, event=None):
    owner.save_file(show_message=False)
    return "break"


def shortcut_open(owner, event=None):
    owner.open_file()
    return "break"


def shortcut_new(owner, event=None):
    owner.clear_code()
    return "break"


def shortcut_cheatsheet(owner, event=None):
    return owner.open_cheatsheet(event)


def shortcut_run(owner, event=None):
    owner.run_code()
    return "break"


def shortcut_multi_add_next(owner, event=None):
    return owner.multi_cursor_add_next(event)


def shortcut_multi_select_all(owner, event=None):
    return owner.multi_cursor_select_all(event)


def shortcut_find(owner, event=None):
    owner.open_find_dialog(focus_replace=False)
    return "break"


def shortcut_replace(owner, event=None):
    owner.open_find_dialog(focus_replace=True)
    return "break"


def shortcut_rename_symbol(owner, event=None):
    return owner.rename_symbol(event)


def shortcut_quick_view(owner, event=None):
    owner._refresh_quick_view()
    owner.status_main_var.set("快速查看已刷新")
    return "break"


def _cycle_tab(owner, step):
    tabs = list(owner.notebook.tabs() or [])
    if len(tabs) <= 1:
        return "break"
    current = owner._get_current_tab_id()
    try:
        idx = tabs.index(current)
    except ValueError:
        idx = 0
    target = tabs[(idx + int(step)) % len(tabs)]
    try:
        owner.notebook.select(target)
    except Exception:
        return "break"
    owner.on_tab_changed(None)
    return "break"


def shortcut_next_tab(owner, event=None):
    del event
    return _cycle_tab(owner, 1)


def shortcut_prev_tab(owner, event=None):
    del event
    return _cycle_tab(owner, -1)


def shortcut_toggle_fold(owner, event=None):
    return owner.toggle_fold_current_line(event)


def shortcut_unfold_all(owner, event=None):
    return owner.unfold_all_blocks(event)
