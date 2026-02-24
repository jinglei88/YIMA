"""Project and file flow helpers extracted from 易码编辑器.py."""

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

import json
import os
import tkinter as tk
from tkinter import filedialog, messagebox


def open_file(owner):
    filepath = filedialog.askopenfilename(filetypes=[("易码源代码", "*.ym"), ("所有文件", "*.*")])
    if filepath:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        owner._create_editor_tab(filepath, content)
        owner.refresh_file_tree()


def save_file(owner, event=None, show_message=True):
    editor = owner._get_current_editor()
    tab_id = owner._get_current_tab_id()
    if not editor or not tab_id:
        return False

    current_filepath = owner.tabs_data[tab_id]["filepath"]

    # 如果是未命名或者不存在，则要求另存为
    if current_filepath == "未命名代码.ym" or not os.path.exists(current_filepath):
        filepath = filedialog.asksaveasfilename(defaultextension=".ym", filetypes=[("易码源代码", "*.ym")])
        if not filepath:
            return False
        owner.tabs_data[tab_id]["filepath"] = filepath
        owner._update_tab_title(tab_id)
    else:
        filepath = current_filepath

    try:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(editor.get("1.0", "end-1c"))
        owner.tabs_data[tab_id]["dirty"] = False
        owner._update_tab_title(tab_id)
        editor.edit_modified(False)
        owner._update_status_main()
        if show_message:
            messagebox.showinfo("保存成功", f"代码已经稳稳地保存在：\n{filepath}")
        owner.refresh_file_tree()
        return True
    except Exception as e:
        if show_message:
            messagebox.showerror("保存失败", f"无法保存文件：{e}")
        else:
            owner.status_main_var.set(f"保存失败：{e}")
        return False


def clear_code(owner):
    base_name = "未命名代码"
    ext = ".ym"
    idx = ""
    counter = 1

    # 寻找一个没有被占用的名字（同时检查磁盘和已打开的标签页）
    while True:
        candidate_name = f"{base_name}{idx}{ext}"
        candidate_path = os.path.join(owner.workspace_dir, candidate_name)

        # 检查文件是否已在磁盘上存在或者已被打开
        already_exists = os.path.exists(candidate_path)
        already_open = False
        for data in owner.tabs_data.values():
            if data["filepath"] == candidate_path or data["filepath"] == candidate_name:
                already_open = True
                break

        if not already_exists and not already_open:
            # 在磁盘上创建空文件
            try:
                with open(candidate_path, "w", encoding="utf-8") as f:
                    f.write("")
            except Exception as e:
                owner.print_output(f"❌ 创建文件失败：{e}")
                return
            # 打开这个真实文件的标签页
            owner._create_editor_tab(candidate_path, "")
            # 刷新左侧文件树
            owner.refresh_file_tree()
            break
        idx = f"-{counter}"
        counter += 1


def close_all_tabs_silently(owner):
    # 默默关掉所有的 tab
    tabs = list(owner.notebook.tabs())
    for tab_id in tabs:
        owner.notebook.forget(tab_id)
        if tab_id in owner.tabs_data:
            owner.tabs_data[tab_id]["editor"].destroy()
            owner.tabs_data[tab_id]["line_numbers"].destroy()
            if owner.tabs_data[tab_id].get("guide_canvas"):
                owner.tabs_data[tab_id]["guide_canvas"].destroy()
            del owner.tabs_data[tab_id]


def confirm_close_all_dirty_tabs(owner):
    for tab_id in list(owner.notebook.tabs()):
        if not owner._confirm_tab_close(tab_id):
            return False
    return True


def open_project(owner):
    initial_dir = owner.last_project_dir if owner.last_project_dir and os.path.isdir(owner.last_project_dir) else owner.workspace_dir
    dir_path = filedialog.askdirectory(title="选择易码项目文件夹", initialdir=initial_dir)
    if dir_path:
        if not confirm_close_all_dirty_tabs(owner):
            return
        main_file = os.path.join(dir_path, "主程序.ym")
        if not os.path.isfile(main_file):
            if not messagebox.askyesno(
                "缺少主程序.ym",
                "该目录不符合易码标准项目结构（缺少 主程序.ym）。\n是否立即按标准结构初始化？",
            ):
                return
        owner._switch_project(dir_path, create_blank_if_empty=True)


def new_project(owner):
    initial_dir = owner.last_project_dir if owner.last_project_dir and os.path.isdir(owner.last_project_dir) else owner.workspace_dir
    dir_path = filedialog.askdirectory(title="选择一个空文件夹作为新项目", initialdir=initial_dir)
    if dir_path:
        if not confirm_close_all_dirty_tabs(owner):
            return
        if os.listdir(dir_path):
            if not messagebox.askyesno(
                "确认初始化",
                "这个目录不是空的。\n是否继续初始化标准结构（仅创建缺失文件，不覆盖现有文件）？",
            ):
                return
        if not owner._初始化标准项目结构(dir_path):
            return
        owner._switch_project(dir_path, preferred_file=os.path.join(dir_path, "主程序.ym"), create_blank_if_empty=True)


# ===== merged from editor_project_state_flow.py =====
def normalize_project_dir(owner, path):
    if not path:
        return None
    try:
        normalized = os.path.abspath(os.path.expanduser(str(path).strip()))
    except Exception:
        return None
    return normalized if os.path.isdir(normalized) else None


def normalize_file_path(owner, path):
    if not path:
        return None
    try:
        normalized = os.path.abspath(os.path.expanduser(str(path).strip()))
    except Exception:
        return None
    return normalized if os.path.isfile(normalized) else None



def _list_open_tab_ids(owner):
    notebook = getattr(owner, "notebook", None)
    if notebook is not None:
        try:
            return list(notebook.tabs())
        except Exception:
            pass
    return list(getattr(owner, "tabs_data", {}).keys())


def collect_state_open_files(owner, max_count=20):
    files = []
    for tab_id in _list_open_tab_ids(owner):
        data = getattr(owner, "tabs_data", {}).get(tab_id, {})
        filepath = data.get("filepath")
        normalized = normalize_file_path(owner, filepath)
        if not normalized:
            continue
        if normalized in files:
            continue
        files.append(normalized)
        if len(files) >= max(1, int(max_count or 20)):
            break
    return files

def load_project_state(owner):
    owner.last_session_files = []
    try:
        if not os.path.exists(owner._state_file):
            return
        with open(owner._state_file, "r", encoding="utf-8") as f:
            state = json.load(f)
        if not isinstance(state, dict):
            return

        history = state.get("project_history", [])
        if isinstance(history, list):
            cleaned = []
            for item in history:
                normalized = normalize_project_dir(owner, item)
                if normalized and normalized not in cleaned:
                    cleaned.append(normalized)
            owner.recent_projects = cleaned[:20]

        owner.last_project_dir = normalize_project_dir(owner, state.get("last_project"))
        owner.last_open_file = normalize_file_path(owner, state.get("last_open_file"))

        session_files = state.get("open_files", [])
        if isinstance(session_files, list):
            cleaned_files = []
            for item in session_files:
                normalized = normalize_file_path(owner, item)
                if normalized and normalized not in cleaned_files:
                    cleaned_files.append(normalized)
            owner.last_session_files = cleaned_files[:20]

        active_file = normalize_file_path(owner, state.get("active_file"))
        if active_file:
            owner.last_open_file = active_file
    except Exception as e:
        print(f"?? ?????????????{e}")

def save_project_state(owner):
    try:
        os.makedirs(owner._state_dir, exist_ok=True)
        open_files = collect_state_open_files(owner, max_count=20)
        owner.last_session_files = list(open_files)
        active_file = current_open_file(owner) or owner.last_open_file
        if active_file:
            owner.last_open_file = active_file
        state = {
            "last_project": owner.last_project_dir if owner.last_project_dir else "",
            "last_open_file": owner.last_open_file if owner.last_open_file else "",
            "project_history": owner.recent_projects[:20],
            "open_files": open_files,
            "active_file": active_file if active_file else "",
        }
        with open(owner._state_file, "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"?? ?????????????{e}")

def remember_project(owner, dir_path, active_file=None):
    normalized = normalize_project_dir(owner, dir_path)
    if not normalized:
        return
    owner.last_project_dir = normalized
    if normalized in owner.recent_projects:
        owner.recent_projects.remove(normalized)
    owner.recent_projects.insert(0, normalized)
    owner.recent_projects = owner.recent_projects[:20]

    if active_file:
        file_path = normalize_file_path(owner, active_file)
        if file_path:
            owner.last_open_file = file_path

    save_project_state(owner)


def current_open_file(owner):
    tab_id = owner._get_current_tab_id()
    if not tab_id or tab_id not in owner.tabs_data:
        return None
    filepath = owner.tabs_data[tab_id].get("filepath")
    if not filepath or filepath == "未命名代码.ym":
        return None
    return normalize_file_path(owner, filepath)


def pick_project_entry_file(owner, project_dir, preferred_file=None):
    root = normalize_project_dir(owner, project_dir)
    if not root:
        return None

    if preferred_file:
        preferred_abs = normalize_file_path(owner, preferred_file)
        if preferred_abs:
            try:
                same_tree = os.path.commonpath([root, preferred_abs]) == root
            except ValueError:
                same_tree = False
            if same_tree and os.path.basename(preferred_abs) == "主程序.ym" and os.path.isfile(preferred_abs):
                return preferred_abs

    candidate = os.path.join(root, "主程序.ym")
    return candidate if os.path.isfile(candidate) else None


def init_standard_project_structure(owner, project_dir):
    项目根目录 = normalize_project_dir(owner, project_dir)
    if not 项目根目录:
        return False
    try:
        os.makedirs(项目根目录, exist_ok=True)
        os.makedirs(os.path.join(项目根目录, "界面"), exist_ok=True)
        os.makedirs(os.path.join(项目根目录, "业务"), exist_ok=True)
        os.makedirs(os.path.join(项目根目录, "数据"), exist_ok=True)

        模板文件 = {
            os.path.join(项目根目录, "主程序.ym"): '# 易码标准项目入口\n' '引入 "界面/界面层.ym" 叫做 界面\n' "界面.启动()\n",
            os.path.join(项目根目录, "界面", "界面层.ym"): '# 界面层：只负责展示与交互\n' '引入 "../业务/业务层.ym" 叫做 业务\n\n' "功能 启动()\n" '    显示 "界面层已启动"\n' "    业务.运行()\n",
            os.path.join(项目根目录, "业务", "业务层.ym"): '# 业务层：负责规则与流程\n' '引入 "../数据/数据层.ym" 叫做 数据\n\n' "功能 运行()\n" '    显示 "业务层执行中"\n' "    数据.初始化()\n",
            os.path.join(项目根目录, "数据", "数据层.ym"): '# 数据层：负责存储与读取\n' "功能 初始化()\n" '    显示 "数据层已就绪"\n',
        }

        for 文件路径, 内容 in 模板文件.items():
            if not os.path.exists(文件路径):
                with open(文件路径, "w", encoding="utf-8") as f:
                    f.write(内容)
        return True
    except Exception as e:
        messagebox.showerror("项目初始化失败", f"无法创建标准项目结构：{e}")
        return False


def switch_project(owner, dir_path, preferred_file=None, create_blank_if_empty=True):
    project_dir = normalize_project_dir(owner, dir_path)
    if not project_dir:
        return False

    owner.workspace_dir = project_dir
    owner.refresh_file_tree()
    owner._close_all_tabs_silently()

    entry_file = pick_project_entry_file(owner, project_dir, preferred_file)
    if entry_file:
        try:
            with open(entry_file, "r", encoding="utf-8") as f:
                content = f.read()
            owner._create_editor_tab(entry_file, content)
            remember_project(owner, project_dir, entry_file)
        except Exception as e:
            owner.print_output(f"❌ 打开项目入口文件失败：{e}")
            owner._create_editor_tab("未命名代码.ym", "")
            remember_project(owner, project_dir)
    else:
        if create_blank_if_empty:
            if init_standard_project_structure(owner, project_dir):
                标准入口 = os.path.join(project_dir, "主程序.ym")
                try:
                    with open(标准入口, "r", encoding="utf-8") as f:
                        content = f.read()
                    owner._create_editor_tab(标准入口, content)
                    remember_project(owner, project_dir, 标准入口)
                    owner.status_main_var.set("已按标准结构初始化项目：主程序 + 界面/业务/数据")
                except Exception as e:
                    owner.print_output(f"❌ 打开标准入口失败：{e}")
                    owner._create_editor_tab("未命名代码.ym", "")
                    remember_project(owner, project_dir)
            else:
                owner._create_editor_tab("未命名代码.ym", "")
                remember_project(owner, project_dir)
        else:
            owner._create_editor_tab("未命名代码.ym", "")
            remember_project(owner, project_dir)
    return True


def restore_project_open_tabs(owner, project_dir, open_files, preferred_file=None):
    root = normalize_project_dir(owner, project_dir)
    if not root:
        return 0

    preferred_abs = normalize_file_path(owner, preferred_file)
    restored = 0
    files = list(open_files or [])

    for filepath in files:
        normalized = normalize_file_path(owner, filepath)
        if not normalized:
            continue
        if preferred_abs and os.path.normcase(normalized) == os.path.normcase(preferred_abs):
            continue
        try:
            if os.path.commonpath([root, normalized]) != root:
                continue
        except Exception:
            continue

        try:
            with open(normalized, "r", encoding="utf-8") as f:
                content = f.read()
            before = set(getattr(owner, "tabs_data", {}).keys())
            owner._create_editor_tab(normalized, content)
            after = set(getattr(owner, "tabs_data", {}).keys())
            if after != before:
                restored += 1
        except Exception as e:
            printer = getattr(owner, "print_output", None)
            if callable(printer):
                printer(f"?? ?????????{normalized}?{e}?")

    if preferred_abs:
        for tab_id, data in getattr(owner, "tabs_data", {}).items():
            tab_file = str(data.get("filepath") or "")
            if os.path.normcase(tab_file) == os.path.normcase(preferred_abs):
                try:
                    owner.notebook.select(tab_id)
                except Exception:
                    pass
                break
    return restored

def try_restore_last_project(owner):
    if not owner.last_project_dir or not os.path.isdir(owner.last_project_dir):
        return False
    restored = switch_project(
        owner,
        owner.last_project_dir,
        preferred_file=owner.last_open_file,
        create_blank_if_empty=False,
    )
    if not restored:
        return False

    session_files = list(getattr(owner, "last_session_files", []) or [])
    if session_files:
        restore_project_open_tabs(
            owner,
            owner.last_project_dir,
            session_files,
            preferred_file=owner.last_open_file,
        )
    return True

def open_recent_project_menu(owner):
    menu = tk.Menu(owner.root, tearoff=0, font=owner.font_ui)

    valid_history = []
    for project in owner.recent_projects:
        normalized = normalize_project_dir(owner, project)
        if normalized and normalized not in valid_history:
            valid_history.append(normalized)
    owner.recent_projects = valid_history[:20]

    if not owner.recent_projects:
        menu.add_command(label="（暂无历史项目）", state=tk.DISABLED)
    else:
        for idx, project in enumerate(owner.recent_projects[:12], start=1):
            name = os.path.basename(project) or project
            menu.add_command(
                label=f"{idx}. {name}  -  {project}",
                command=lambda p=project: owner._open_project_from_history(p),
            )
        menu.add_separator()
        menu.add_command(label="🗑️ 清空历史项目记录", command=owner.clear_recent_projects)

    x = owner.root.winfo_pointerx()
    y = owner.root.winfo_pointery()
    try:
        menu.tk_popup(x, y)
    finally:
        menu.grab_release()


def open_project_from_history(owner, project_dir):
    normalized = normalize_project_dir(owner, project_dir)
    if not normalized:
        messagebox.showwarning("项目不存在", "这个历史项目路径已经失效，已自动移除。")
        owner.recent_projects = [p for p in owner.recent_projects if normalize_project_dir(owner, p)]
        save_project_state(owner)
        return
    if not owner._confirm_close_all_dirty_tabs():
        return
    switch_project(owner, normalized, create_blank_if_empty=True)


def clear_recent_projects(owner):
    owner.recent_projects = []
    current_project = normalize_project_dir(owner, owner.workspace_dir)
    if current_project:
        owner.last_project_dir = current_project
    save_project_state(owner)
    owner.status_main_var.set("历史项目记录已清空")
