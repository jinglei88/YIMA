"""Workspace domain: tree + tab lifecycle + tab creation."""

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
import shutil
import tkinter as tk
from tkinter import messagebox, scrolledtext, simpledialog
from tkinter import font as tkfont

from yima.editor_runtime_guard import log_owner_event, mark_clean_exit


def _infer_tab_span(owner, index, probe_y):
    """通过坐标扫描推断标签左右边界（规避某些环境下 bbox 恒为 0 的问题）。"""
    nb = owner.notebook
    try:
        idx = int(index)
    except Exception:
        return None
    max_x = max(0, int(nb.winfo_width()) - 1)
    if max_x <= 0:
        return None

    y = max(0, int(probe_y))
    left = None
    for x in range(0, max_x + 1):
        try:
            if int(nb.index(f"@{x},{y}")) == idx:
                left = x
                break
        except Exception:
            continue
    if left is None:
        return None

    right = left
    for x in range(left + 1, max_x + 1):
        try:
            if int(nb.index(f"@{x},{y}")) != idx:
                right = x - 1
                break
            right = x
        except Exception:
            right = x - 1
            break
    return left, right


def on_tab_click(owner, event):
    """处理标签点击：左键优先切换，仅在足够宽且点中最右侧×时关闭。"""
    try:
        index = owner.notebook.index(f"@{event.x},{event.y}")
    except tk.TclError:
        return

    # 左键先切换到点击的标签，保证主交互稳定。
    try:
        tabs = owner.notebook.tabs()
        if 0 <= index < len(tabs):
            owner.notebook.select(tabs[index])
    except tk.TclError:
        pass

    span = _infer_tab_span(owner, index, event.y)
    if not span:
        return
    _left, right = span

    # 右侧关闭热区（仅最右一小段），兼顾可点中与不误触。
    try:
        close_font = tkfont.Font(font=owner.font_ui)
        close_width = max(int(close_font.measure(" × ")), int(12 * owner.dpi_scale))
    except Exception:
        close_width = int(12 * owner.dpi_scale)
    close_width = max(10, int(close_width))
    close_left = right - close_width + 1

    if event.x >= close_left:
        close_tab(owner, index)


def on_tab_middle_click(owner, event):
    """中键关闭标签，避免左键误触。"""
    try:
        index = owner.notebook.index(f"@{event.x},{event.y}")
    except tk.TclError:
        return
    close_tab(owner, index)


def close_tab(owner, index):
    tabs = owner.notebook.tabs()
    if index < 0 or index >= len(tabs):
        return
    tab_id = tabs[index]
    if not confirm_tab_close(owner, tab_id):
        return

    owner.notebook.forget(tab_id)

    if tab_id in owner.tabs_data:
        owner.tabs_data[tab_id]["editor"].destroy()
        owner.tabs_data[tab_id]["line_numbers"].destroy()
        if owner.tabs_data[tab_id].get("guide_canvas"):
            owner.tabs_data[tab_id]["guide_canvas"].destroy()
        del owner.tabs_data[tab_id]

    if not owner.notebook.tabs():
        owner._create_editor_tab("未命名代码.ym", "")
    else:
        owner._update_tab_title(owner.notebook.tabs()[0])


def confirm_tab_close(owner, tab_id):
    if tab_id not in owner.tabs_data:
        return True
    data = owner.tabs_data[tab_id]
    if not data.get("dirty"):
        return True

    filepath = data.get("filepath", "未命名代码.ym")
    display_name = os.path.basename(filepath) if filepath != "未命名代码.ym" else "未命名代码.ym"
    choice = messagebox.askyesnocancel("未保存修改", f"《{display_name}》有未保存内容，是否先保存？")
    if choice is None:
        return False
    if choice:
        current_tab = owner._get_current_tab_id()
        try:
            owner.notebook.select(tab_id)
        except tk.TclError:
            return False

        ok = owner.save_file(show_message=False)
        if current_tab and current_tab in owner.notebook.tabs():
            owner.notebook.select(current_tab)
        return ok
    return True


def on_app_close(owner):
    for tab_id in list(owner.notebook.tabs()):
        if not confirm_tab_close(owner, tab_id):
            return
    current_file = owner._current_open_file()
    owner._remember_project(owner.workspace_dir, current_file)
    try:
        owner._save_project_state()
    except Exception as e:
        log_owner_event(owner, "warning", f"保存项目状态失败（退出阶段）：{e}")
    log_owner_event(owner, "info", "用户关闭编辑器窗口。")
    mark_clean_exit(owner)
    owner.root.destroy()


def on_tab_changed(owner, event):
    del event
    editor = owner._get_current_editor()
    if editor:
        owner.highlight()
        owner._update_line_numbers()
        owner._update_cursor_status()
        owner._run_live_diagnose()
        owner._highlight_find_matches()
        owner._refresh_outline()
        owner._refresh_quick_view()
        owner._render_multi_cursor_state()
        current_file = owner._current_open_file()
        if current_file:
            owner.last_open_file = current_file


def refresh_file_tree(owner):
    for item in owner.tree.get_children():
        owner.tree.delete(item)

    root_title = "📂 易码项目目录"
    root_node = owner.tree.insert("", "end", text=root_title, open=True)
    longest_text = root_title

    try:
        for item in os.listdir(owner.workspace_dir):
            path = os.path.join(owner.workspace_dir, item)
            if os.path.isdir(path) and item not in [".venv", "__pycache__", ".git", ".idea", ".vscode"]:
                folder_name = f"📁 {item}"
                if len(folder_name) > len(longest_text):
                    longest_text = folder_name
                folder_node = owner.tree.insert(root_node, "end", text=folder_name, values=(path, "dir"), open=True)
                for sub_item in os.listdir(path):
                    sub_path = os.path.join(path, sub_item)
                    if sub_path.endswith(".ym"):
                        file_name = f"📄 {sub_item}"
                        if len(file_name) > len(longest_text):
                            longest_text = file_name
                        if owner.icon_file:
                            owner.tree.insert(folder_node, "end", text=f" {sub_item}", image=owner.icon_file, values=(sub_path, "file"))
                        else:
                            owner.tree.insert(folder_node, "end", text=file_name, values=(sub_path, "file"))
            elif item.endswith(".ym"):
                file_name = f"📄 {item}"
                if len(file_name) > len(longest_text):
                    longest_text = file_name
                if owner.icon_file:
                    owner.tree.insert(root_node, "end", text=f" {item}", image=owner.icon_file, values=(path, "file"))
                else:
                    owner.tree.insert(root_node, "end", text=file_name, values=(path, "file"))

        try:
            measure_font = tkfont.Font(font=owner.font_ui)
            max_pixel_width = measure_font.measure(longest_text) + int(50 * owner.dpi_scale)
            owner.tree.column("#0", width=max_pixel_width, minwidth=max_pixel_width, stretch=False)
        except Exception as fe:
            print(f"⚠️ 小提示：字体测量计算失败：{fe}")

    except Exception as e:
        owner.print_output(f"刷新文件树出错: {e}")


def on_tree_double_click(owner, event):
    del event
    item = owner.tree.selection()
    if not item:
        return
    item = item[0]
    values = owner.tree.item(item, "values")

    if values and values[1] == "file":
        filepath = values[0]
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
            owner._create_editor_tab(filepath, content)
        except Exception as e:
            messagebox.showerror("打开失败", f"无法读取文件：{e}")


def popup_tree_menu(owner, event):
    item = owner.tree.identify_row(event.y)
    if item:
        owner.tree.selection_set(item)
    owner.tree_menu.tk_popup(event.x_root, event.y_root)


def get_selected_dir_or_root(owner):
    item = owner.tree.selection()
    if not item:
        return owner.workspace_dir

    item = item[0]
    values = owner.tree.item(item, "values")
    if not values:
        return owner.workspace_dir

    path, node_type = values[0], values[1]
    if node_type == "dir":
        return path
    return os.path.dirname(path)


def create_new_file_in_tree(owner):
    target_dir = get_selected_dir_or_root(owner)
    new_name = simpledialog.askstring("新建代码", "请输入新的易码文件名称（不用写 .ym）：", parent=owner.root)
    if not new_name:
        return

    if not new_name.endswith(".ym"):
        new_name += ".ym"

    new_path = os.path.join(target_dir, new_name)
    if os.path.exists(new_path):
        messagebox.showerror("冲突", "这个名字已经存在了，换一个吧。")
        return

    try:
        with open(new_path, "w", encoding="utf-8") as f:
            f.write("")
        owner.refresh_file_tree()
        owner._create_editor_tab(new_path, "")
    except Exception as e:
        messagebox.showerror("错误", f"创建文件失败: {e}")


def create_new_folder_in_tree(owner):
    target_dir = get_selected_dir_or_root(owner)
    new_name = simpledialog.askstring("新建文件夹", "请输入新的文件夹名称：", parent=owner.root)
    if not new_name:
        return

    new_path = os.path.join(target_dir, new_name)
    if os.path.exists(new_path):
        messagebox.showerror("冲突", "这个文件夹已经存在啦。")
        return

    try:
        os.makedirs(new_path)
        owner.refresh_file_tree()
    except Exception as e:
        messagebox.showerror("错误", f"创建文件夹失败: {e}")


def delete_item_in_tree(owner):
    item = owner.tree.selection()
    if not item:
        return
    item = item[0]
    values = owner.tree.item(item, "values")
    if not values:
        return

    path, node_type = values[0], values[1]
    name = os.path.basename(path)

    if not messagebox.askyesno("确认删除", f"你确定要永久删除《{name}》吗？\n删除后不可恢复！"):
        return

    try:
        if node_type == "dir":
            shutil.rmtree(path)
        else:
            os.remove(path)

        owner.refresh_file_tree()

        tabs_to_close = []
        for tab_id, data in owner.tabs_data.items():
            tab_file = data["filepath"]
            if tab_file == path or tab_file.startswith(path + os.sep):
                tabs_to_close.append(tab_id)

        for tab_id in tabs_to_close:
            tabs_list = owner.notebook.tabs()
            if tab_id in tabs_list:
                idx = tabs_list.index(tab_id)
                owner.close_tab(idx)

    except Exception as e:
        messagebox.showerror("错误", f"删除失败: {e}")


def create_editor_tab(owner, filename, content=""):
    for tab_id, data in owner.tabs_data.items():
        if data["filepath"] == filename:
            owner.notebook.select(tab_id)
            owner._update_cursor_status()
            owner._run_live_diagnose()
            owner._refresh_outline()
            return

    tab_frame = tk.Frame(owner.notebook, bg=owner.theme_bg, borderwidth=0, highlightthickness=0)

    spacing_top = 5
    spacing_mid = 0
    spacing_bottom = 5

    line_numbers = tk.Text(
        tab_frame,
        width=4,
        padx=4,
        pady=10,
        takefocus=0,
        borderwidth=0,
        highlightthickness=0,
        bg=owner.theme_gutter_bg,
        fg=owner.theme_gutter_fg,
        font=owner.font_code,
        spacing1=spacing_top,
        spacing2=spacing_mid,
        spacing3=spacing_bottom,
        state=tk.DISABLED,
    )
    line_numbers.pack(side=tk.LEFT, fill=tk.Y)

    guide_canvas = tk.Canvas(tab_frame, width=44, bg=owner.theme_gutter_bg, highlightthickness=0, borderwidth=0)
    guide_canvas.pack(side=tk.LEFT, fill=tk.Y)

    editor = scrolledtext.ScrolledText(
        tab_frame,
        font=owner.font_code,
        undo=True,
        wrap=tk.NONE,
        bg=owner.theme_bg,
        fg=owner.theme_fg,
        insertbackground="white",
        padx=10,
        pady=10,
        selectbackground="#264F78",
        spacing1=spacing_top,
        spacing2=spacing_mid,
        spacing3=spacing_bottom,
        borderwidth=0,
        highlightthickness=0,
    )
    editor.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    owner._style_scrolledtext_vbar(editor, parent=tab_frame)

    def sync_y_scroll(first, last):
        try:
            line_numbers.yview_moveto(float(first))
        except tk.TclError:
            return
        owner._update_indent_guides()
        if hasattr(editor, "vbar"):
            editor.vbar.set(first, last)

    editor.configure(yscrollcommand=sync_y_scroll)

    def forward_left_wheel(event):
        if hasattr(event, "num") and event.num == 4:
            editor.yview_scroll(-1, "units")
            return "break"
        if hasattr(event, "num") and event.num == 5:
            editor.yview_scroll(1, "units")
            return "break"

        delta = getattr(event, "delta", 0)
        if delta != 0:
            step = int(-delta / 120) if abs(delta) >= 120 else (-1 if delta > 0 else 1)
            editor.yview_scroll(step, "units")
            return "break"
        return None

    def sync_cursor_by_left_click(event):
        try:
            target_index = editor.index(f"@0,{event.y}")
        except tk.TclError:
            return "break"
        try:
            editor.focus_set()
            editor.mark_set("insert", target_index)
            editor.tag_remove("sel", "1.0", "end")
            owner._hide_autocomplete()
            owner._hide_calltip()
            owner._highlight_current_line()
            owner._update_cursor_status()
        except tk.TclError:
            pass
        return "break"

    for left_widget in (line_numbers, guide_canvas):
        left_widget.bind("<MouseWheel>", forward_left_wheel)
        left_widget.bind("<Button-4>", forward_left_wheel)
        left_widget.bind("<Button-5>", forward_left_wheel)

    line_numbers.bind("<Button-1>", sync_cursor_by_left_click)
    line_numbers.bind("<ButtonRelease-1>", sync_cursor_by_left_click, add="+")

    def on_guide_click(event):
        if owner._toggle_fold_by_canvas_hit(event):
            return "break"
        return sync_cursor_by_left_click(event)

    guide_canvas.bind("<Button-1>", on_guide_click)
    guide_canvas.bind("<Motion>", owner._on_guide_canvas_motion, add="+")
    guide_canvas.bind("<Leave>", lambda e: e.widget.configure(cursor=""), add="+")

    editor.insert("1.0", content)

    tab_title = os.path.basename(filename) if filename != "未命名代码.ym" else filename
    owner.notebook.add(tab_frame, text=f" {tab_title}   ✖ ")
    owner.notebook.select(tab_frame)

    tab_id = owner.notebook.select()
    owner.tabs_data[tab_id] = {
        "filepath": filename,
        "editor": editor,
        "line_numbers": line_numbers,
        "guide_canvas": guide_canvas,
        "dirty": False,
        "diagnostic": None,
        "semantic_warnings": [],
        "issue_items": [],
        "diagnostic_nav_index": 0,
        "folds": {},
        "outline_items": [],
        "outline_focus_line": None,
        "multi_cursor": {"query": "", "stage": "ranges", "ranges": [], "points": [], "last_abs": -1},
    }
    owner._update_tab_title(tab_id)
    editor.edit_modified(False)

    owner.bind_events(editor)
    owner.setup_tags(editor)
    owner.highlight(editor)
    owner._update_line_numbers(None)
    owner._update_cursor_status()
    owner._run_live_diagnose()
    owner._refresh_outline()

    real_path = owner._normalize_file_path(filename)
    if real_path:
        owner.last_open_file = real_path
