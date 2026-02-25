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
import os
import json
import tkinter as tk
from tkinter import messagebox, simpledialog
from datetime import datetime
from pathlib import Path

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


def _token_identifier_occurrences(owner, code: str, symbol_name: str):
    del owner
    results = []
    if not code or not symbol_name:
        return results
    try:
        tokens = 词法分析器(code).分析()
        for token in tokens:
            if token.类型 == Token类型.标识符 and token.值 == symbol_name:
                results.append((int(token.行号), int(token.列号)))
        return results
    except Exception:
        pass

    pattern = re.compile(rf"(?<![\u4e00-\u9fa5A-Za-z0-9_]){re.escape(symbol_name)}(?![\u4e00-\u9fa5A-Za-z0-9_])")
    for i, line in enumerate(code.splitlines(), start=1):
        for m in pattern.finditer(line):
            results.append((i, int(m.start()) + 1))
    return results


def _definition_line_candidates(owner, code: str, symbol_name: str):
    del owner
    candidates = []
    lines = code.splitlines()
    escaped = re.escape(symbol_name)
    regex_list = [
        re.compile(rf"^\s*功能\s+{escaped}(?:\s*\(|\s|$)"),
        re.compile(rf"^\s*定义图纸\s+{escaped}(?:\s*\(|\s|$)"),
        re.compile(rf"^\s*引入\s+.+\s+叫做\s+{escaped}(?:\s|$)"),
        re.compile(rf"^\s*遍历\s+.+\s+里的每一个\s+叫做\s+{escaped}(?:\s|$)"),
        re.compile(rf"^\s*{escaped}\s*="),
    ]
    for line_no, text in enumerate(lines, start=1):
        stripped = str(text or "")
        for pat in regex_list:
            if pat.search(stripped):
                candidates.append(line_no)
                break
    return candidates


def _iter_project_ym_files(owner, max_files: int = 1200):
    root = str(getattr(owner, "workspace_dir", "") or "").strip()
    if not root or not os.path.isdir(root):
        return []
    skip_dirs = {".git", "__pycache__", ".venv", ".idea", ".vscode"}
    files = []
    for base, dir_names, file_names in os.walk(root):
        dir_names[:] = [d for d in dir_names if d not in skip_dirs]
        for name in file_names:
            if not name.lower().endswith(".ym"):
                continue
            files.append(os.path.join(base, name))
            if len(files) >= max(1, int(max_files)):
                return sorted(files)
    return sorted(files)


def _project_files_snapshot(owner, max_files: int = 1200):
    snapshot = []
    for path in _iter_project_ym_files(owner, max_files=max_files):
        try:
            st = os.stat(path)
        except OSError:
            continue
        snapshot.append((path, int(st.st_mtime_ns), int(st.st_size)))
    return snapshot


def _project_snapshot_key(snapshot):
    total_mtime = 0
    total_size = 0
    for _path, mt, sz in snapshot:
        total_mtime = (total_mtime + int(mt)) % 1000000007
        total_size = (total_size + int(sz)) % 1000000007
    return (len(snapshot), total_mtime, total_size)


def _collect_project_symbol_refs(owner, symbol_name: str):
    symbol = str(symbol_name or "").strip()
    if not symbol:
        return []

    root = str(getattr(owner, "workspace_dir", "") or "")
    cache = getattr(owner, "_project_symbol_query_cache", None)
    if not isinstance(cache, dict):
        cache = {}
        owner._project_symbol_query_cache = cache

    snapshot = _project_files_snapshot(owner)
    snap_key = _project_snapshot_key(snapshot)
    cache_key = (os.path.normcase(root), symbol)
    cached = cache.get(cache_key)
    if isinstance(cached, dict) and cached.get("snap_key") == snap_key:
        return list(cached.get("refs", []))

    refs = []
    for path, _mt, _sz in snapshot:
        code = _read_text(path)
        if not code:
            continue
        lines = code.splitlines()
        rel = os.path.relpath(path, root) if root else path
        for line_no, col_no in _token_identifier_occurrences(owner, code, symbol):
            text = lines[line_no - 1] if 0 <= line_no - 1 < len(lines) else ""
            refs.append(
                {
                    "path": path,
                    "rel": rel,
                    "line": line_no,
                    "col": col_no,
                    "preview": str(text).strip()[:130],
                }
            )
    refs.sort(key=lambda x: (str(x["rel"]), int(x["line"]), int(x["col"])))
    cache[cache_key] = {"snap_key": snap_key, "refs": refs}
    if len(cache) > 80:
        for old_key in list(cache.keys())[:20]:
            cache.pop(old_key, None)
    return list(refs)


def _read_text(path: str) -> str:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception:
        return ""


def _replace_symbol_in_code(owner, code: str, old_name: str, new_name: str):
    if not code or not old_name or old_name == new_name:
        return code, 0

    replaced_code = code
    replaced_count = 0
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
                start = to_abs(int(token.行号), int(token.列号))
                end = start + len(old_name)
                ranges.append((start, end))

        if ranges:
            replaced_count = len(ranges)
            for start, end in reversed(ranges):
                replaced_code = replaced_code[:start] + new_name + replaced_code[end:]
            return replaced_code, replaced_count
    except Exception:
        pass

    pattern = symbol_pattern(owner, old_name)
    return pattern.subn(new_name, code)


def _find_open_tab_by_path(owner, filepath: str):
    target = os.path.normcase(str(filepath or ""))
    if not target:
        return None
    for tab_id, data in getattr(owner, "tabs_data", {}).items():
        path = str(data.get("filepath") or "")
        if os.path.normcase(path) == target:
            return tab_id
    return None


def _collect_project_rename_hits(owner, symbol_name: str):
    results = []
    refs = _collect_project_symbol_refs(owner, symbol_name)
    grouped = {}
    for row in refs:
        path = row["path"]
        item = grouped.get(path)
        if item is None:
            item = {
                "path": path,
                "rel": row["rel"],
                "count": 0,
                "line": row["line"],
                "col": row["col"],
                "preview": row["preview"][:120],
            }
            grouped[path] = item
        item["count"] += 1
    results.extend(grouped.values())
    results.sort(key=lambda x: str(x["rel"]))
    return results


def _find_project_definition(owner, symbol_name: str, prefer_current_file: str = ""):
    refs = _collect_project_symbol_refs(owner, symbol_name)
    if not refs:
        return None
    files = []
    seen = set()
    for row in refs:
        path = row.get("path")
        if not path or path in seen:
            continue
        seen.add(path)
        files.append(path)
    current = os.path.normcase(str(prefer_current_file or ""))
    ordered = list(files)
    if current:
        ordered.sort(key=lambda p: 0 if os.path.normcase(p) == current else 1)

    for path in ordered:
        code = _read_text(path)
        if not code:
            continue
        lines = _definition_line_candidates(owner, code, symbol_name)
        if not lines:
            continue
        occ = _token_identifier_occurrences(owner, code, symbol_name)
        col = 1
        line = lines[0]
        for ln, c in occ:
            if ln == line:
                col = c
                break
        return {"path": path, "line": line, "col": col}
    return None


def _goto_line_col(owner, editor, line_no: int, col_no: int, symbol_name: str = ""):
    line_no = max(1, int(line_no))
    col_no = max(1, int(col_no))
    start = f"{line_no}.{col_no - 1}"
    end = f"{line_no}.{col_no - 1 + max(1, len(str(symbol_name or '')))}"
    try:
        editor.mark_set("insert", start)
        editor.see(start)
        editor.tag_remove("sel", "1.0", "end")
        editor.tag_add("sel", start, end)
        editor.focus_set()
    except Exception:
        return False
    return True


def _open_file_and_goto(owner, filepath: str, line_no: int, col_no: int, symbol_name: str = ""):
    path = str(filepath or "").strip()
    if not path:
        return False
    current_editor = owner._get_current_editor()
    current_file = owner._current_open_file()
    if current_editor is not None and current_file and os.path.normcase(current_file) == os.path.normcase(path):
        return _goto_line_col(owner, current_editor, line_no, col_no, symbol_name)

    code = _read_text(path)
    if code == "" and not os.path.isfile(path):
        return False
    owner._create_editor_tab(path, code)
    target_editor = owner._get_current_editor()
    if target_editor is None:
        return False
    return _goto_line_col(owner, target_editor, line_no, col_no, symbol_name)


def goto_symbol_definition(owner, event=None):
    del event
    editor = owner._get_current_editor()
    if not editor:
        return "break"

    symbol_name = owner._get_symbol_near_cursor(editor)
    if not symbol_name:
        messagebox.showinfo("跳转定义", "请先把光标放到一个符号上。", parent=owner.root)
        return "break"

    code = editor.get("1.0", "end-1c")
    occurrences = _token_identifier_occurrences(owner, code, symbol_name)
    if not occurrences:
        owner.status_main_var.set(f"未找到符号：{symbol_name}")
        return "break"

    candidates = _definition_line_candidates(owner, code, symbol_name)
    current_line = int(editor.index("insert").split(".")[0])
    chosen = None
    for line_no in candidates:
        if line_no != current_line:
            chosen = line_no
            break
    if chosen is None and candidates:
        chosen = candidates[0]
    if chosen is None:
        current_file = owner._current_open_file()
        project_hit = _find_project_definition(owner, symbol_name, prefer_current_file=current_file or "")
        if project_hit and str(project_hit.get("path") or ""):
            ok = _open_file_and_goto(
                owner,
                project_hit["path"],
                int(project_hit.get("line") or 1),
                int(project_hit.get("col") or 1),
                symbol_name,
            )
            if ok:
                rel = os.path.relpath(project_hit["path"], str(getattr(owner, "workspace_dir", "") or project_hit["path"]))
                owner.status_main_var.set(f"已跳转定义：{symbol_name}（{rel}:L{project_hit['line']}）")
                return "break"
        chosen = occurrences[0][0]

    col_no = 1
    for ln, col in occurrences:
        if ln == chosen:
            col_no = col
            break
    ok = _goto_line_col(owner, editor, chosen, col_no, symbol_name)
    if ok:
        owner.status_main_var.set(f"已跳转定义：{symbol_name}（L{chosen}）")
    else:
        owner.status_main_var.set("跳转定义失败")
    return "break"


def find_symbol_references(owner, event=None):
    del event
    editor = owner._get_current_editor()
    if not editor:
        return "break"

    symbol_name = owner._get_symbol_near_cursor(editor)
    if not symbol_name:
        messagebox.showinfo("查找引用", "请先把光标放到一个符号上。", parent=owner.root)
        return "break"

    code = editor.get("1.0", "end-1c")
    lines = code.splitlines()
    refs = []
    for line_no, col_no in _token_identifier_occurrences(owner, code, symbol_name):
        text = lines[line_no - 1] if 0 <= line_no - 1 < len(lines) else ""
        refs.append({
            "line": line_no,
            "col": col_no,
            "preview": str(text).strip()[:140],
        })

    if not refs:
        owner.status_main_var.set(f"未找到符号引用：{symbol_name}")
        return "break"

    dialog = tk.Toplevel(owner.root)
    dialog.title(f"引用列表 - {symbol_name}")
    dialog.configure(bg=owner.theme_sidebar_bg)
    dialog.transient(owner.root)
    try:
        dialog.resizable(True, True)
    except tk.TclError:
        pass

    width = int(760 * owner.dpi_scale)
    height = int(420 * owner.dpi_scale)
    x = owner.root.winfo_x() + int(40 * owner.dpi_scale)
    y = owner.root.winfo_y() + int(60 * owner.dpi_scale)
    dialog.geometry(f"{max(620, width)}x{max(360, height)}+{x}+{y}")

    body = tk.Frame(dialog, bg=owner.theme_sidebar_bg, padx=12, pady=10)
    body.pack(fill=tk.BOTH, expand=True)

    tk.Label(
        body,
        text=f"符号【{symbol_name}】共 {len(refs)} 处引用（当前文件）",
        bg=owner.theme_sidebar_bg,
        fg=owner.theme_fg,
        font=owner.font_ui_bold,
        anchor="w",
    ).pack(fill=tk.X, pady=(0, 8))

    listbox = tk.Listbox(
        body,
        bg=owner.theme_bg,
        fg=owner.theme_fg,
        selectbackground="#264F78",
        selectforeground="#FFFFFF",
        font=owner.font_code,
        activestyle="none",
    )
    listbox.pack(fill=tk.BOTH, expand=True)

    for idx, row in enumerate(refs, start=1):
        line_no = row["line"]
        col_no = row["col"]
        preview = row["preview"]
        listbox.insert(tk.END, f"{idx:02d}. L{line_no}:{col_no}    {preview}")

    if refs:
        listbox.selection_set(0)

    def _jump_selected(_event=None):
        sel = listbox.curselection()
        if not sel:
            return
        row = refs[int(sel[0])]
        _goto_line_col(owner, editor, row["line"], row["col"], symbol_name)
        owner.status_main_var.set(f"已定位引用：{symbol_name}（L{row['line']}）")
        try:
            dialog.destroy()
        except tk.TclError:
            pass

    btn_row = tk.Frame(body, bg=owner.theme_sidebar_bg)
    btn_row.pack(fill=tk.X, pady=(8, 0))
    tk.Button(
        btn_row,
        text="跳转",
        command=_jump_selected,
        font=owner.font_ui,
        bg=owner.theme_toolbar_bg,
        fg=owner.theme_fg,
        activebackground="#505050",
        activeforeground="#FFFFFF",
        relief="flat",
        borderwidth=0,
        padx=10,
        pady=4,
        cursor="hand2",
    ).pack(side=tk.LEFT)
    tk.Button(
        btn_row,
        text="关闭",
        command=dialog.destroy,
        font=owner.font_ui,
        bg=owner.theme_toolbar_bg,
        fg=owner.theme_fg,
        activebackground="#505050",
        activeforeground="#FFFFFF",
        relief="flat",
        borderwidth=0,
        padx=10,
        pady=4,
        cursor="hand2",
    ).pack(side=tk.RIGHT)

    listbox.bind("<Double-Button-1>", _jump_selected)
    dialog.bind("<Return>", _jump_selected)
    dialog.bind("<Escape>", lambda _e: dialog.destroy())
    try:
        dialog.grab_set()
    except tk.TclError:
        pass
    return "break"


def find_symbol_references_project(owner, event=None):
    del event
    editor = owner._get_current_editor()
    if not editor:
        return "break"

    symbol_name = owner._get_symbol_near_cursor(editor)
    if not symbol_name:
        messagebox.showinfo("全局查找引用", "请先把光标放到一个符号上。", parent=owner.root)
        return "break"

    refs = _collect_project_symbol_refs(owner, symbol_name)

    if not refs:
        owner.status_main_var.set(f"全局未找到符号引用：{symbol_name}")
        return "break"

    dialog = tk.Toplevel(owner.root)
    dialog.title(f"全局引用 - {symbol_name}")
    dialog.configure(bg=owner.theme_sidebar_bg)
    dialog.transient(owner.root)
    try:
        dialog.resizable(True, True)
    except tk.TclError:
        pass

    width = int(920 * owner.dpi_scale)
    height = int(520 * owner.dpi_scale)
    x = owner.root.winfo_x() + int(36 * owner.dpi_scale)
    y = owner.root.winfo_y() + int(50 * owner.dpi_scale)
    dialog.geometry(f"{max(700, width)}x{max(420, height)}+{x}+{y}")

    body = tk.Frame(dialog, bg=owner.theme_sidebar_bg, padx=12, pady=10)
    body.pack(fill=tk.BOTH, expand=True)

    tk.Label(
        body,
        text=f"符号【{symbol_name}】共 {len(refs)} 处引用（项目范围）",
        bg=owner.theme_sidebar_bg,
        fg=owner.theme_fg,
        font=owner.font_ui_bold,
        anchor="w",
    ).pack(fill=tk.X, pady=(0, 8))

    listbox = tk.Listbox(
        body,
        bg=owner.theme_bg,
        fg=owner.theme_fg,
        selectbackground="#264F78",
        selectforeground="#FFFFFF",
        font=owner.font_code,
        activestyle="none",
    )
    listbox.pack(fill=tk.BOTH, expand=True)

    for idx, row in enumerate(refs, start=1):
        listbox.insert(tk.END, f"{idx:03d}. {row['rel']}:{row['line']}:{row['col']}    {row['preview']}")
    listbox.selection_set(0)

    def _jump_selected(_event=None):
        sel = listbox.curselection()
        if not sel:
            return
        row = refs[int(sel[0])]
        if _open_file_and_goto(owner, row["path"], row["line"], row["col"], symbol_name):
            owner.status_main_var.set(f"已定位全局引用：{row['rel']}:{row['line']}")
            try:
                dialog.destroy()
            except tk.TclError:
                pass

    btn_row = tk.Frame(body, bg=owner.theme_sidebar_bg)
    btn_row.pack(fill=tk.X, pady=(8, 0))
    tk.Button(
        btn_row,
        text="跳转",
        command=_jump_selected,
        font=owner.font_ui,
        bg=owner.theme_toolbar_bg,
        fg=owner.theme_fg,
        activebackground="#505050",
        activeforeground="#FFFFFF",
        relief="flat",
        borderwidth=0,
        padx=10,
        pady=4,
        cursor="hand2",
    ).pack(side=tk.LEFT)
    tk.Button(
        btn_row,
        text="关闭",
        command=dialog.destroy,
        font=owner.font_ui,
        bg=owner.theme_toolbar_bg,
        fg=owner.theme_fg,
        activebackground="#505050",
        activeforeground="#FFFFFF",
        relief="flat",
        borderwidth=0,
        padx=10,
        pady=4,
        cursor="hand2",
    ).pack(side=tk.RIGHT)

    listbox.bind("<Double-Button-1>", _jump_selected)
    dialog.bind("<Return>", _jump_selected)
    dialog.bind("<Escape>", lambda _e: dialog.destroy())
    try:
        dialog.grab_set()
    except tk.TclError:
        pass
    return "break"


def _choose_project_rename_targets(owner, hits, old_name: str, new_name: str):
    dialog = tk.Toplevel(owner.root)
    dialog.title("全局重命名预览")
    dialog.configure(bg=owner.theme_sidebar_bg)
    dialog.transient(owner.root)
    try:
        dialog.resizable(True, True)
    except tk.TclError:
        pass

    width = int(900 * owner.dpi_scale)
    height = int(560 * owner.dpi_scale)
    x = owner.root.winfo_x() + int(30 * owner.dpi_scale)
    y = owner.root.winfo_y() + int(44 * owner.dpi_scale)
    dialog.geometry(f"{max(720, width)}x{max(460, height)}+{x}+{y}")

    state = {"confirmed": False, "selected_paths": set()}

    body = tk.Frame(dialog, bg=owner.theme_sidebar_bg, padx=12, pady=10)
    body.pack(fill=tk.BOTH, expand=True)

    total_refs = sum(int(x.get("count", 0)) for x in hits)
    header = tk.Label(
        body,
        text=f"符号【{old_name}】 -> 【{new_name}】\n命中文件 {len(hits)} 个，预计替换 {total_refs} 处",
        bg=owner.theme_sidebar_bg,
        fg=owner.theme_fg,
        font=owner.font_ui_bold,
        anchor="w",
        justify="left",
    )
    header.pack(fill=tk.X, pady=(0, 8))

    tip = tk.Label(
        body,
        text="请勾选要执行重命名的文件（默认全选）。",
        bg=owner.theme_sidebar_bg,
        fg="#AFC3DA",
        font=owner.font_ui,
        anchor="w",
    )
    tip.pack(fill=tk.X, pady=(0, 6))

    listbox = tk.Listbox(
        body,
        bg=owner.theme_bg,
        fg=owner.theme_fg,
        selectbackground="#264F78",
        selectforeground="#FFFFFF",
        font=owner.font_code,
        activestyle="none",
        selectmode=tk.EXTENDED,
    )
    listbox.pack(fill=tk.BOTH, expand=True)

    for idx, row in enumerate(hits, start=1):
        listbox.insert(
            tk.END,
            f"{idx:03d}. {row['rel']}  ({row['count']}处)  例如 L{row['line']}:{row['col']}  {row['preview']}",
        )
    if hits:
        listbox.selection_set(0, tk.END)

    def _select_all():
        listbox.selection_set(0, tk.END)

    def _invert():
        selected = set(int(i) for i in listbox.curselection())
        listbox.selection_clear(0, tk.END)
        for i in range(len(hits)):
            if i not in selected:
                listbox.selection_set(i)

    def _confirm(_event=None):
        selected_idx = [int(i) for i in listbox.curselection()]
        if not selected_idx:
            messagebox.showwarning("全局重命名", "请至少选择一个文件。", parent=dialog)
            return
        state["selected_paths"] = {hits[i]["path"] for i in selected_idx if 0 <= i < len(hits)}
        state["confirmed"] = True
        dialog.destroy()

    def _cancel(_event=None):
        state["confirmed"] = False
        dialog.destroy()

    btn_row = tk.Frame(body, bg=owner.theme_sidebar_bg)
    btn_row.pack(fill=tk.X, pady=(8, 0))
    tk.Button(
        btn_row,
        text="全选",
        command=_select_all,
        font=owner.font_ui,
        bg=owner.theme_toolbar_bg,
        fg=owner.theme_fg,
        relief="flat",
        borderwidth=0,
        padx=10,
        pady=4,
        cursor="hand2",
    ).pack(side=tk.LEFT, padx=(0, 6))
    tk.Button(
        btn_row,
        text="反选",
        command=_invert,
        font=owner.font_ui,
        bg=owner.theme_toolbar_bg,
        fg=owner.theme_fg,
        relief="flat",
        borderwidth=0,
        padx=10,
        pady=4,
        cursor="hand2",
    ).pack(side=tk.LEFT)
    tk.Button(
        btn_row,
        text="执行重命名",
        command=_confirm,
        font=owner.font_ui_bold,
        bg="#2E7D32",
        fg="#FFFFFF",
        activebackground="#3D9742",
        activeforeground="#FFFFFF",
        relief="flat",
        borderwidth=0,
        padx=12,
        pady=5,
        cursor="hand2",
    ).pack(side=tk.RIGHT)
    tk.Button(
        btn_row,
        text="取消",
        command=_cancel,
        font=owner.font_ui,
        bg=owner.theme_toolbar_bg,
        fg=owner.theme_fg,
        relief="flat",
        borderwidth=0,
        padx=10,
        pady=4,
        cursor="hand2",
    ).pack(side=tk.RIGHT, padx=(0, 8))

    listbox.bind("<Return>", _confirm)
    dialog.bind("<Escape>", _cancel)
    dialog.protocol("WM_DELETE_WINDOW", _cancel)
    try:
        dialog.grab_set()
    except tk.TclError:
        pass
    owner.root.wait_window(dialog)
    return state["confirmed"], set(state["selected_paths"])


def _write_rename_backup_snapshot(owner, old_name: str, new_name: str, selected_rows):
    state_dir = str(getattr(owner, "_state_dir", "") or "").strip()
    if not state_dir:
        return ""
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    target = Path(state_dir) / "rename_backups" / f"rename_{stamp}_{old_name}_to_{new_name}"
    target.mkdir(parents=True, exist_ok=True)
    files_dir = target / "files"
    files_dir.mkdir(parents=True, exist_ok=True)

    manifest = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "old_name": old_name,
        "new_name": new_name,
        "workspace_dir": str(getattr(owner, "workspace_dir", "") or ""),
        "files": [],
    }

    for idx, row in enumerate(selected_rows, start=1):
        path = str(row.get("path") or "")
        if not path:
            continue
        src = Path(path)
        if not src.is_file():
            continue
        backup_name = f"{idx:03d}_{src.name}.bak"
        backup_path = files_dir / backup_name
        try:
            backup_path.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")
            manifest["files"].append(
                {
                    "source": path,
                    "relative": row.get("rel", path),
                    "backup": str(backup_path),
                    "count": int(row.get("count", 0)),
                }
            )
        except Exception:
            continue

    (target / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return str(target)


def _append_editor_audit(owner, event_type: str, payload: dict | None = None):
    state_dir = str(getattr(owner, "_state_dir", "") or "").strip()
    if not state_dir:
        return
    audit_dir = Path(state_dir) / "audit"
    audit_dir.mkdir(parents=True, exist_ok=True)
    row = {
        "time": datetime.now().isoformat(timespec="seconds"),
        "event": str(event_type or "unknown"),
        "workspace_dir": str(getattr(owner, "workspace_dir", "") or ""),
        "payload": payload if isinstance(payload, dict) else {},
    }
    try:
        with open(audit_dir / "editor_audit.jsonl", "a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    except Exception:
        pass


def rename_symbol_project(owner, event=None):
    del event
    editor = owner._get_current_editor()
    if not editor:
        return "break"

    old_name = owner._get_symbol_near_cursor(editor)
    if not old_name:
        messagebox.showinfo("全局重命名", "请先把光标放到一个符号上。", parent=owner.root)
        return "break"

    new_name = simpledialog.askstring(
        "全局重命名",
        f"将项目内符号【{old_name}】重命名为：",
        initialvalue=old_name,
        parent=owner.root,
    )
    if new_name is None:
        return "break"
    new_name = str(new_name).strip()
    if not new_name:
        messagebox.showwarning("重命名失败", "新名称不能为空。", parent=owner.root)
        return "break"
    if new_name == old_name:
        owner.status_main_var.set("全局重命名取消：新旧名称相同")
        return "break"
    if not owner._is_valid_symbol_name(new_name):
        messagebox.showwarning("重命名失败", "名称仅支持中文、英文字母、数字和下划线，且不能以数字开头。", parent=owner.root)
        return "break"

    hits = _collect_project_rename_hits(owner, old_name)
    if not hits:
        owner.status_main_var.set(f"全局未找到可重命名项：{old_name}")
        return "break"

    confirmed, selected_paths = _choose_project_rename_targets(owner, hits, old_name, new_name)
    if not confirmed:
        owner.status_main_var.set("全局重命名已取消")
        return "break"

    selected_rows = [row for row in hits if row.get("path") in selected_paths]
    if not selected_rows:
        owner.status_main_var.set("全局重命名已取消：未选择文件")
        return "break"

    backup_dir = _write_rename_backup_snapshot(owner, old_name, new_name, selected_rows)

    changed_files = 0
    changed_refs = 0
    failed = []
    for row in selected_rows:
        path = row["path"]
        code = _read_text(path)
        if not code:
            continue
        new_code, count = _replace_symbol_in_code(owner, code, old_name, new_name)
        if count <= 0 or new_code == code:
            continue
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(new_code)
            changed_files += 1
            changed_refs += int(count)

            tab_id = _find_open_tab_by_path(owner, path)
            if tab_id and tab_id in owner.tabs_data:
                tab_data = owner.tabs_data[tab_id]
                tab_editor = tab_data.get("editor")
                if tab_editor is not None:
                    tab_editor.delete("1.0", "end")
                    tab_editor.insert("1.0", new_code)
                    tab_editor.edit_modified(False)
                tab_data["dirty"] = False
                owner._update_tab_title(tab_id)
        except Exception as e:
            failed.append(f"{row['rel']}：{e}")

    owner.refresh_file_tree()
    owner._update_status_main()
    owner._schedule_diagnose()
    owner._schedule_outline_update()
    owner._project_symbol_query_cache = {}

    msg = f"全局重命名完成：{old_name} -> {new_name}，共修改 {changed_files} 个文件 / {changed_refs} 处"
    if backup_dir:
        msg += f"\n备份已保存：{backup_dir}"
    if failed:
        msg += f"\n失败 {len(failed)} 个文件（见控制台）"
        for line in failed[:12]:
            owner.print_output(f"⚠️ 全局重命名失败：{line}", is_error=True)
    _append_editor_audit(
        owner,
        "project_rename",
        {
            "old_name": old_name,
            "new_name": new_name,
            "selected_files": len(selected_rows),
            "changed_files": changed_files,
            "changed_refs": changed_refs,
            "failed_files": len(failed),
            "backup_dir": backup_dir,
        },
    )
    owner.status_main_var.set(msg)
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
