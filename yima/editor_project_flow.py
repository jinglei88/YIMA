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


def normalize_cursor_index(owner, index_text):
    del owner
    if index_text is None:
        return None
    text = str(index_text).strip()
    if not text or "." not in text:
        return None
    line_text, col_text = text.split(".", 1)
    if not line_text.isdigit() or not col_text.isdigit():
        return None
    line_no = int(line_text)
    col_no = int(col_text)
    if line_no < 1 or col_no < 0:
        return None
    return f"{line_no}.{col_no}"


def normalize_yview(owner, value):
    del owner
    try:
        number = float(value)
    except Exception:
        return None
    if number < 0.0:
        return 0.0
    if number > 1.0:
        return 1.0
    return number


def normalize_xview(owner, value):
    return normalize_yview(owner, value)


def normalize_state_text(owner, value, max_len=200):
    del owner
    if value is None:
        return ""
    text = str(value)
    limit = max(1, int(max_len or 200))
    return text[:limit]


def normalize_fold_line(owner, value):
    del owner
    try:
        line_no = int(str(value).strip())
    except Exception:
        return None
    return line_no if line_no > 0 else None


def _sanitize_fold_lines(owner, raw_lines, max_lines=200):
    if not isinstance(raw_lines, (list, tuple, set)):
        return []
    cleaned = []
    limit = max(1, int(max_lines or 200))
    for item in raw_lines:
        line_no = normalize_fold_line(owner, item)
        if not line_no or line_no in cleaned:
            continue
        cleaned.append(line_no)
        if len(cleaned) >= limit:
            break
    cleaned.sort()
    return cleaned


def _build_normalized_fold_map(owner, raw_folds, max_count=20, max_lines_per_file=200):
    cleaned = {}
    if not isinstance(raw_folds, dict):
        return cleaned
    limit = max(1, int(max_count or 20))
    for filepath, raw_lines in raw_folds.items():
        normalized_path = normalize_file_path(owner, filepath)
        if not normalized_path or normalized_path in cleaned:
            continue
        fold_lines = _sanitize_fold_lines(owner, raw_lines, max_lines=max_lines_per_file)
        if not fold_lines:
            continue
        cleaned[normalized_path] = fold_lines
        if len(cleaned) >= limit:
            break
    return cleaned


def _sanitize_view_state(owner, raw_state):
    if not isinstance(raw_state, dict):
        return None
    cursor = normalize_cursor_index(owner, raw_state.get("cursor"))
    yview = normalize_yview(owner, raw_state.get("yview"))
    xview = normalize_xview(owner, raw_state.get("xview"))
    if cursor is None and yview is None and xview is None:
        return None
    state = {}
    if cursor is not None:
        state["cursor"] = cursor
    if yview is not None:
        state["yview"] = yview
    if xview is not None:
        state["xview"] = xview
    return state


def _build_normalized_view_map(owner, raw_views, max_count=20):
    cleaned = {}
    if not isinstance(raw_views, dict):
        return cleaned
    limit = max(1, int(max_count or 20))
    for filepath, raw_state in raw_views.items():
        normalized_path = normalize_file_path(owner, filepath)
        if not normalized_path or normalized_path in cleaned:
            continue
        state = _sanitize_view_state(owner, raw_state)
        if not state:
            continue
        cleaned[normalized_path] = state
        if len(cleaned) >= limit:
            break
    return cleaned


def normalize_outline_focus_line(owner, value):
    return normalize_fold_line(owner, value)


def _build_normalized_outline_focus_map(owner, raw_focus_map, max_count=20):
    cleaned = {}
    if not isinstance(raw_focus_map, dict):
        return cleaned
    limit = max(1, int(max_count or 20))
    for filepath, raw_line in raw_focus_map.items():
        normalized_path = normalize_file_path(owner, filepath)
        if not normalized_path or normalized_path in cleaned:
            continue
        line_no = normalize_outline_focus_line(owner, raw_line)
        if not line_no:
            continue
        cleaned[normalized_path] = line_no
        if len(cleaned) >= limit:
            break
    return cleaned


def _find_tab_id_by_filepath(owner, filepath):
    if not filepath:
        return None
    target = os.path.normcase(str(filepath))
    for tab_id, data in getattr(owner, "tabs_data", {}).items():
        tab_file = str(data.get("filepath") or "")
        if os.path.normcase(tab_file) == target:
            return tab_id
    return None


def _count_indent_width(line_text):
    width = 0
    for ch in str(line_text or ""):
        if ch == " ":
            width += 1
        elif ch == "\t":
            width += 4
        else:
            break
    return width


def _fallback_block_end_line(editor, start_line):
    try:
        line_count = int(str(editor.index("end-1c")).split(".")[0])
    except Exception:
        return None
    if start_line >= line_count:
        return None

    try:
        start_text = editor.get(f"{start_line}.0", f"{start_line}.end")
    except Exception:
        return None
    if not str(start_text).strip():
        return None

    base_indent = _count_indent_width(start_text)
    end_line = start_line
    has_child = False

    for ln in range(start_line + 1, line_count + 1):
        try:
            text = editor.get(f"{ln}.0", f"{ln}.end")
        except Exception:
            break
        stripped = str(text).strip()
        if not stripped:
            if has_child:
                end_line = ln
            continue

        indent = _count_indent_width(text)
        if indent > base_indent:
            has_child = True
            end_line = ln
            continue
        break

    while end_line > start_line:
        try:
            text = editor.get(f"{end_line}.0", f"{end_line}.end")
        except Exception:
            break
        if str(text).strip():
            break
        end_line -= 1

    if not has_child or end_line <= start_line:
        return None
    return end_line


def _resolve_fold_end_line(owner, editor, start_line):
    resolver = getattr(owner, "_get_block_end_line", None)
    if callable(resolver):
        try:
            end_line = resolver(editor, start_line)
        except Exception:
            end_line = None
        if isinstance(end_line, int) and end_line > start_line:
            return end_line
    return _fallback_block_end_line(editor, start_line)


def _clear_tab_folds(owner, tab_id):
    data = getattr(owner, "tabs_data", {}).get(tab_id, {})
    editor = data.get("editor")
    if editor is None:
        data["folds"] = {}
        return
    folds = data.get("folds", {})
    if isinstance(folds, dict):
        for fold_meta in folds.values():
            if not isinstance(fold_meta, dict):
                continue
            tag = fold_meta.get("tag")
            if not tag:
                continue
            try:
                editor.tag_remove(tag, "1.0", "end")
            except Exception:
                pass
            try:
                editor.tag_configure(tag, elide=False)
            except Exception:
                pass
    data["folds"] = {}


def apply_tab_fold_state(owner, tab_id, fold_lines):
    if not tab_id:
        return 0
    data = getattr(owner, "tabs_data", {}).get(tab_id, {})
    editor = data.get("editor")
    if editor is None:
        data["folds"] = {}
        return 0

    target_lines = _sanitize_fold_lines(owner, fold_lines, max_lines=200)
    _clear_tab_folds(owner, tab_id)
    if not target_lines:
        return 0

    folds = {}
    applied = 0
    for line_no in target_lines:
        end_line = _resolve_fold_end_line(owner, editor, line_no)
        if not end_line:
            continue

        tag_name = f"FoldBlock_{line_no}"
        try:
            editor.tag_configure(tag_name, elide=True)
            editor.tag_remove(tag_name, "1.0", "end")
            editor.tag_add(tag_name, f"{line_no + 1}.0", f"{end_line}.end+1c")
        except Exception:
            continue

        folds[line_no] = {"tag": tag_name, "end_line": end_line, "collapsed": True}
        applied += 1
    data["folds"] = folds

    current_tab_id = None
    getter = getattr(owner, "_get_current_tab_id", None)
    if callable(getter):
        try:
            current_tab_id = getter()
        except Exception:
            current_tab_id = None
    if current_tab_id == tab_id:
        updater = getattr(owner, "_update_line_numbers", None)
        if callable(updater):
            try:
                updater()
            except Exception:
                pass
    return applied


def apply_tab_view_state(owner, tab_id, view_state):
    if not tab_id or not view_state:
        return False
    data = getattr(owner, "tabs_data", {}).get(tab_id, {})
    editor = data.get("editor")
    if editor is None:
        return False

    cursor = normalize_cursor_index(owner, view_state.get("cursor"))
    yview = normalize_yview(owner, view_state.get("yview"))
    xview = normalize_xview(owner, view_state.get("xview"))
    applied = False

    if cursor is not None:
        try:
            editor.mark_set("insert", cursor)
            applied = True
        except Exception:
            pass

    if yview is not None:
        try:
            editor.yview_moveto(yview)
            applied = True
        except Exception:
            pass

    if xview is not None:
        try:
            editor.xview_moveto(xview)
            applied = True
        except Exception:
            pass
    return applied



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


def collect_state_open_views(owner, max_count=20):
    views = {}
    limit = max(1, int(max_count or 20))
    for tab_id in _list_open_tab_ids(owner):
        data = getattr(owner, "tabs_data", {}).get(tab_id, {})
        filepath = normalize_file_path(owner, data.get("filepath"))
        if not filepath or filepath in views:
            continue
        editor = data.get("editor")
        if editor is None:
            continue
        raw_state = {}
        try:
            raw_state["cursor"] = editor.index("insert")
        except Exception:
            pass
        try:
            yview = editor.yview()
            if isinstance(yview, (list, tuple)) and yview:
                raw_state["yview"] = yview[0]
        except Exception:
            pass
        try:
            xview = editor.xview()
            if isinstance(xview, (list, tuple)) and xview:
                raw_state["xview"] = xview[0]
        except Exception:
            pass
        state = _sanitize_view_state(owner, raw_state)
        if not state:
            continue
        views[filepath] = state
        if len(views) >= limit:
            break
    return views


def collect_state_open_folds(owner, max_count=20):
    folds_map = {}
    limit = max(1, int(max_count or 20))
    for tab_id in _list_open_tab_ids(owner):
        data = getattr(owner, "tabs_data", {}).get(tab_id, {})
        filepath = normalize_file_path(owner, data.get("filepath"))
        if not filepath or filepath in folds_map:
            continue
        folds = data.get("folds", {})
        if not isinstance(folds, dict):
            continue
        collapsed_lines = []
        for line_no, fold_meta in folds.items():
            if not isinstance(fold_meta, dict) or not bool(fold_meta.get("collapsed")):
                continue
            normalized_line = normalize_fold_line(owner, line_no)
            if normalized_line:
                collapsed_lines.append(normalized_line)
        collapsed_lines = _sanitize_fold_lines(owner, collapsed_lines, max_lines=200)
        if not collapsed_lines:
            continue
        folds_map[filepath] = collapsed_lines
        if len(folds_map) >= limit:
            break
    return folds_map


def collect_state_open_outline_focus(owner, max_count=20):
    focus_map = {}
    limit = max(1, int(max_count or 20))
    for tab_id in _list_open_tab_ids(owner):
        data = getattr(owner, "tabs_data", {}).get(tab_id, {})
        filepath = normalize_file_path(owner, data.get("filepath"))
        if not filepath or filepath in focus_map:
            continue
        line_no = normalize_outline_focus_line(owner, data.get("outline_focus_line"))
        if not line_no:
            continue
        focus_map[filepath] = line_no
        if len(focus_map) >= limit:
            break
    return focus_map


def load_project_state(owner):
    owner.last_session_files = []
    owner.last_session_views = {}
    owner.last_session_folds = {}
    owner.last_session_outline_focus = {}
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

        owner.last_session_views = _build_normalized_view_map(owner, state.get("open_file_views", {}), max_count=20)
        owner.last_session_folds = _build_normalized_fold_map(owner, state.get("open_file_folds", {}), max_count=20, max_lines_per_file=200)
        owner.last_session_outline_focus = _build_normalized_outline_focus_map(owner, state.get("open_file_outline_focus", {}), max_count=20)

        active_file = normalize_file_path(owner, state.get("active_file"))
        if active_file:
            owner.last_open_file = active_file

        find_var = getattr(owner, "find_var", None)
        if hasattr(find_var, "set"):
            find_var.set(normalize_state_text(owner, state.get("find_query", ""), max_len=300))
        replace_var = getattr(owner, "replace_var", None)
        if hasattr(replace_var, "set"):
            replace_var.set(normalize_state_text(owner, state.get("replace_query", ""), max_len=300))
    except Exception as e:
        print(f"?? ?????????????{e}")

def save_project_state(owner):
    try:
        os.makedirs(owner._state_dir, exist_ok=True)
        open_files = collect_state_open_files(owner, max_count=20)
        open_views = collect_state_open_views(owner, max_count=20)
        open_folds = collect_state_open_folds(owner, max_count=20)
        open_outline_focus = collect_state_open_outline_focus(owner, max_count=20)
        owner.last_session_files = list(open_files)
        owner.last_session_views = dict(open_views)
        owner.last_session_folds = dict(open_folds)
        owner.last_session_outline_focus = dict(open_outline_focus)
        active_file = current_open_file(owner) or owner.last_open_file
        if active_file:
            owner.last_open_file = active_file
        find_var = getattr(owner, "find_var", None)
        replace_var = getattr(owner, "replace_var", None)
        find_query = normalize_state_text(owner, find_var.get() if hasattr(find_var, "get") else "", max_len=300)
        replace_query = normalize_state_text(owner, replace_var.get() if hasattr(replace_var, "get") else "", max_len=300)
        state = {
            "last_project": owner.last_project_dir if owner.last_project_dir else "",
            "last_open_file": owner.last_open_file if owner.last_open_file else "",
            "project_history": owner.recent_projects[:20],
            "open_files": open_files,
            "open_file_views": open_views,
            "open_file_folds": open_folds,
            "open_file_outline_focus": open_outline_focus,
            "active_file": active_file if active_file else "",
            "find_query": find_query,
            "replace_query": replace_query,
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


def restore_project_open_tabs(
    owner,
    project_dir,
    open_files,
    preferred_file=None,
    open_views=None,
    open_folds=None,
    open_outline_focus=None,
):
    root = normalize_project_dir(owner, project_dir)
    if not root:
        return 0

    preferred_abs = normalize_file_path(owner, preferred_file)
    raw_views = open_views if isinstance(open_views, dict) else getattr(owner, "last_session_views", {})
    raw_folds = open_folds if isinstance(open_folds, dict) else getattr(owner, "last_session_folds", {})
    raw_outline_focus = (
        open_outline_focus
        if isinstance(open_outline_focus, dict)
        else getattr(owner, "last_session_outline_focus", {})
    )
    normalized_views = _build_normalized_view_map(owner, raw_views, max_count=20)
    normalized_folds = _build_normalized_fold_map(owner, raw_folds, max_count=20, max_lines_per_file=200)
    normalized_outline_focus = _build_normalized_outline_focus_map(owner, raw_outline_focus, max_count=20)
    views_by_normcase = {os.path.normcase(path): state for path, state in normalized_views.items()}
    folds_by_normcase = {os.path.normcase(path): lines for path, lines in normalized_folds.items()}
    outline_focus_by_normcase = {
        os.path.normcase(path): line_no
        for path, line_no in normalized_outline_focus.items()
    }
    restored = 0
    files = list(open_files or [])

    for filepath in files:
        normalized = normalize_file_path(owner, filepath)
        if not normalized:
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
            tab_id = _find_tab_id_by_filepath(owner, normalized)
            if tab_id:
                data = getattr(owner, "tabs_data", {}).get(tab_id, {})
                focus_line = outline_focus_by_normcase.get(os.path.normcase(normalized))
                if focus_line:
                    data["outline_focus_line"] = focus_line
                apply_tab_fold_state(owner, tab_id, folds_by_normcase.get(os.path.normcase(normalized), []))
                apply_tab_view_state(owner, tab_id, views_by_normcase.get(os.path.normcase(normalized)))
        except Exception as e:
            printer = getattr(owner, "print_output", None)
            if callable(printer):
                printer(f"?? ?????????{normalized}?{e}?")

    if preferred_abs:
        preferred_tab_id = _find_tab_id_by_filepath(owner, preferred_abs)
        if preferred_tab_id:
            preferred_data = getattr(owner, "tabs_data", {}).get(preferred_tab_id, {})
            preferred_focus_line = outline_focus_by_normcase.get(os.path.normcase(preferred_abs))
            if preferred_focus_line:
                preferred_data["outline_focus_line"] = preferred_focus_line
            apply_tab_fold_state(owner, preferred_tab_id, folds_by_normcase.get(os.path.normcase(preferred_abs), []))
            apply_tab_view_state(owner, preferred_tab_id, views_by_normcase.get(os.path.normcase(preferred_abs)))
            try:
                owner.notebook.select(preferred_tab_id)
            except Exception:
                pass

    refresh_outline = getattr(owner, "_refresh_outline", None)
    if callable(refresh_outline):
        try:
            refresh_outline()
        except Exception:
            pass
    return restored

def try_restore_last_project(owner):
    if not owner.last_project_dir or not os.path.isdir(owner.last_project_dir):
        return False
    snapshot_files = list(getattr(owner, "last_session_files", []) or [])
    snapshot_views = dict(getattr(owner, "last_session_views", {}) or {})
    snapshot_folds = dict(getattr(owner, "last_session_folds", {}) or {})
    snapshot_outline_focus = dict(getattr(owner, "last_session_outline_focus", {}) or {})
    preferred_file = owner.last_open_file
    restored = switch_project(
        owner,
        owner.last_project_dir,
        preferred_file=preferred_file,
        create_blank_if_empty=False,
    )
    if not restored:
        return False

    session_files = snapshot_files
    if session_files:
        restore_project_open_tabs(
            owner,
            owner.last_project_dir,
            session_files,
            preferred_file=preferred_file,
            open_views=snapshot_views,
            open_folds=snapshot_folds,
            open_outline_focus=snapshot_outline_focus,
        )
    save_project_state(owner)
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
