"""Visual UI designer flow: free drag layout + code export."""

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
import re
import tkinter as tk
from tkinter import ttk


CANVAS_REGION_W = 2200
CANVAS_REGION_H = 1400
CANVAS_GRID = 20


COMPONENT_CATALOG = [
    ("文字", {"w": 180, "h": 34, "text": "文字内容"}),
    ("输入框", {"w": 240, "h": 36, "text": "输入框"}),
    ("按钮", {"w": 140, "h": 40, "text": "按钮", "event": "处理点击"}),
    ("表格", {"w": 400, "h": 220, "text": "表格", "columns": "列1,列2,列3", "rows": 8}),
    ("卡片", {"w": 420, "h": 260, "text": "卡片标题"}),
]
COMPONENT_KIND_SET = {item[0] for item in COMPONENT_CATALOG}


def _tool_button(owner, parent, text, cmd):
    btn = tk.Button(
        parent,
        text=text,
        command=cmd,
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
    btn.pack(side=tk.RIGHT, padx=(6, 0))
    return btn


def _center_window(owner, win, width=1320, height=820):
    try:
        owner.root.update_idletasks()
        x = int(owner.root.winfo_x() + max(0, (owner.root.winfo_width() - width) / 2))
        y = int(owner.root.winfo_y() + max(0, (owner.root.winfo_height() - height) / 2))
        win.geometry(f"{width}x{height}+{x}+{y}")
    except Exception:
        try:
            win.geometry(f"{width}x{height}")
        except Exception:
            pass


def _ensure_state(owner):
    if not hasattr(owner, "_ui_designer_components"):
        owner._ui_designer_components = []
    if not hasattr(owner, "_ui_designer_next_uid"):
        owner._ui_designer_next_uid = 1
    if not hasattr(owner, "_ui_designer_selected_uid"):
        owner._ui_designer_selected_uid = None
    if not hasattr(owner, "_ui_designer_drag"):
        owner._ui_designer_drag = {"uid": None, "start_x": 0, "start_y": 0}


def _next_uid(owner):
    _ensure_state(owner)
    uid = int(getattr(owner, "_ui_designer_next_uid", 1) or 1)
    owner._ui_designer_next_uid = uid + 1
    return uid


def _clamp(value, low, high):
    return max(low, min(high, value))


def _to_int(value, default=0):
    try:
        return int(float(value))
    except Exception:
        return int(default)


def _new_component(owner, kind, x=120, y=90):
    if kind not in COMPONENT_KIND_SET:
        kind = "文字"
    catalog_map = {k: dict(v) for k, v in COMPONENT_CATALOG}
    base = catalog_map.get(kind, {"w": 180, "h": 34, "text": kind})
    uid = _next_uid(owner)
    name = f"{kind}{uid}"
    return {
        "uid": uid,
        "kind": kind,
        "name": name,
        "text": str(base.get("text", kind)),
        "x": _to_int(x, 120),
        "y": _to_int(y, 90),
        "w": max(80, _to_int(base.get("w", 180), 180)),
        "h": max(28, _to_int(base.get("h", 34), 34)),
        "event": str(base.get("event", "")),
        "columns": str(base.get("columns", "列1,列2")),
        "rows": max(3, _to_int(base.get("rows", 8), 8)),
    }


def _find_component(owner, uid):
    _ensure_state(owner)
    for item in owner._ui_designer_components:
        if int(item.get("uid", -1)) == int(uid):
            return item
    return None


def _selected_component(owner):
    uid = getattr(owner, "_ui_designer_selected_uid", None)
    if uid is None:
        return None
    return _find_component(owner, uid)


def _draw_grid(owner):
    canvas = getattr(owner, "_ui_designer_canvas", None)
    if canvas is None:
        return
    canvas.delete("grid")
    try:
        for x in range(0, CANVAS_REGION_W + 1, CANVAS_GRID):
            color = "#283547" if x % (CANVAS_GRID * 5) == 0 else "#1B2533"
            canvas.create_line(x, 0, x, CANVAS_REGION_H, fill=color, width=1, tags=("grid",))
        for y in range(0, CANVAS_REGION_H + 1, CANVAS_GRID):
            color = "#283547" if y % (CANVAS_GRID * 5) == 0 else "#1B2533"
            canvas.create_line(0, y, CANVAS_REGION_W, y, fill=color, width=1, tags=("grid",))
    except tk.TclError:
        return
    canvas.lower("grid")


def _component_colors(kind):
    if kind == "按钮":
        return {"fill": "#154E7A", "text": "#FFFFFF"}
    if kind == "输入框":
        return {"fill": "#1A2433", "text": "#D8E0EA"}
    if kind == "表格":
        return {"fill": "#1D2A3C", "text": "#DCE7F5"}
    if kind == "卡片":
        return {"fill": "#1A2230", "text": "#DCE7F5"}
    return {"fill": "#223144", "text": "#DCE7F5"}


def _render_canvas(owner):
    canvas = getattr(owner, "_ui_designer_canvas", None)
    if canvas is None:
        return
    _draw_grid(owner)
    canvas.delete("component")
    selected_uid = getattr(owner, "_ui_designer_selected_uid", None)

    for comp in getattr(owner, "_ui_designer_components", []):
        uid = int(comp.get("uid", 0))
        tag = f"comp_{uid}"
        x = _clamp(_to_int(comp.get("x", 0), 0), 0, CANVAS_REGION_W - 20)
        y = _clamp(_to_int(comp.get("y", 0), 0), 0, CANVAS_REGION_H - 20)
        w = _clamp(_to_int(comp.get("w", 180), 180), 60, CANVAS_REGION_W)
        h = _clamp(_to_int(comp.get("h", 36), 36), 24, CANVAS_REGION_H)
        x2 = min(CANVAS_REGION_W, x + w)
        y2 = min(CANVAS_REGION_H, y + h)
        kind = str(comp.get("kind", "文字"))
        text = str(comp.get("text", "")).strip() or kind
        colors = _component_colors(kind)
        selected = uid == selected_uid
        outline = "#4CA8FF" if selected else "#3B4C62"
        border_w = 2 if selected else 1

        rect_id = canvas.create_rectangle(
            x,
            y,
            x2,
            y2,
            fill=colors["fill"],
            outline=outline,
            width=border_w,
            tags=("component", tag),
        )
        kind_badge = canvas.create_text(
            x + 8,
            y + 8,
            text=kind,
            fill="#8FC5FF",
            anchor="nw",
            font=("Microsoft YaHei", 8, "bold"),
            tags=("component", tag),
        )
        text_id = canvas.create_text(
            x + 10,
            y + max(20, int(h / 2)),
            text=text,
            fill=colors["text"],
            anchor="w",
            font=("Microsoft YaHei", 9),
            tags=("component", tag),
        )
        name_id = canvas.create_text(
            x2 - 8,
            y2 - 8,
            text=str(comp.get("name", f"控件{uid}")),
            fill="#8FA1B8",
            anchor="se",
            font=("Microsoft YaHei", 8),
            tags=("component", tag),
        )
        for item_id in (rect_id, kind_badge, text_id, name_id):
            canvas.tag_bind(item_id, "<ButtonPress-1>", lambda e, target_uid=uid: _on_canvas_press(owner, e, target_uid))
            canvas.tag_bind(item_id, "<B1-Motion>", lambda e, target_uid=uid: _on_canvas_drag(owner, e, target_uid))
            canvas.tag_bind(item_id, "<ButtonRelease-1>", lambda e: _on_canvas_release(owner, e))


def _refresh_property_panel(owner):
    comp = _selected_component(owner)
    info_var = getattr(owner, "_ui_designer_info_var", None)
    vars_map = getattr(owner, "_ui_designer_prop_vars", None)
    if info_var is None or not isinstance(vars_map, dict):
        return
    if comp is None:
        info_var.set("未选中组件")
        for key in ("name", "kind", "text", "event", "columns", "rows", "x", "y", "w", "h"):
            if key in vars_map:
                vars_map[key].set("")
        return

    info_var.set(f"已选中：{comp.get('name', '')} ({comp.get('kind', '')})")
    vars_map["name"].set(str(comp.get("name", "")))
    vars_map["kind"].set(str(comp.get("kind", "")))
    vars_map["text"].set(str(comp.get("text", "")))
    vars_map["event"].set(str(comp.get("event", "")))
    vars_map["columns"].set(str(comp.get("columns", "")))
    vars_map["rows"].set(str(comp.get("rows", 8)))
    vars_map["x"].set(str(comp.get("x", 0)))
    vars_map["y"].set(str(comp.get("y", 0)))
    vars_map["w"].set(str(comp.get("w", 180)))
    vars_map["h"].set(str(comp.get("h", 36)))


def _select_component(owner, uid):
    owner._ui_designer_selected_uid = int(uid)
    _render_canvas(owner)
    _refresh_property_panel(owner)


def _on_canvas_press(owner, event, uid):
    canvas = getattr(owner, "_ui_designer_canvas", None)
    if canvas is None:
        return "break"
    cx = _to_int(canvas.canvasx(event.x), 0)
    cy = _to_int(canvas.canvasy(event.y), 0)
    owner._ui_designer_drag = {"uid": int(uid), "start_x": cx, "start_y": cy}
    _select_component(owner, uid)
    return "break"


def _on_canvas_drag(owner, event, uid):
    canvas = getattr(owner, "_ui_designer_canvas", None)
    comp = _find_component(owner, uid)
    drag = getattr(owner, "_ui_designer_drag", {}) or {}
    if canvas is None or comp is None or int(drag.get("uid", -1)) != int(uid):
        return "break"
    cx = _to_int(canvas.canvasx(event.x), comp.get("x", 0))
    cy = _to_int(canvas.canvasy(event.y), comp.get("y", 0))
    dx = cx - _to_int(drag.get("start_x", cx), cx)
    dy = cy - _to_int(drag.get("start_y", cy), cy)
    comp["x"] = _clamp(_to_int(comp.get("x", 0)) + dx, 0, CANVAS_REGION_W - 20)
    comp["y"] = _clamp(_to_int(comp.get("y", 0)) + dy, 0, CANVAS_REGION_H - 20)
    owner._ui_designer_drag = {"uid": int(uid), "start_x": cx, "start_y": cy}
    _render_canvas(owner)
    _refresh_property_panel(owner)
    return "break"


def _on_canvas_release(owner, event=None):
    del event
    owner._ui_designer_drag = {"uid": None, "start_x": 0, "start_y": 0}
    return "break"


def _add_component(owner, kind=None):
    _ensure_state(owner)
    if kind not in COMPONENT_KIND_SET:
        kind = "文字"
        listbox = getattr(owner, "_ui_designer_palette", None)
        if listbox is not None:
            try:
                selection = listbox.curselection()
                if selection:
                    idx = int(selection[0])
                    kind = COMPONENT_CATALOG[idx][0]
            except Exception:
                kind = "文字"

    offset = len(owner._ui_designer_components) * 16
    comp = _new_component(owner, kind, x=120 + offset, y=90 + offset)
    owner._ui_designer_components.append(comp)
    _select_component(owner, comp["uid"])
    if hasattr(owner, "status_main_var"):
        owner.status_main_var.set(f"界面设计器：已添加组件 {kind}")
    return "break"


def _delete_selected_component(owner):
    comp = _selected_component(owner)
    if comp is None:
        return "break"
    owner._ui_designer_components = [item for item in owner._ui_designer_components if int(item.get("uid", -1)) != int(comp["uid"])]
    owner._ui_designer_selected_uid = None
    _render_canvas(owner)
    _refresh_property_panel(owner)
    if hasattr(owner, "status_main_var"):
        owner.status_main_var.set("界面设计器：已删除选中组件")
    return "break"


def _clear_components(owner):
    owner._ui_designer_components = []
    owner._ui_designer_selected_uid = None
    _render_canvas(owner)
    _refresh_property_panel(owner)
    if hasattr(owner, "status_main_var"):
        owner.status_main_var.set("界面设计器：画布已清空")
    return "break"


def _apply_properties(owner):
    comp = _selected_component(owner)
    vars_map = getattr(owner, "_ui_designer_prop_vars", None)
    if comp is None or not isinstance(vars_map, dict):
        return "break"

    comp["text"] = str(vars_map["text"].get() or "").strip()
    comp["event"] = str(vars_map["event"].get() or "").strip()
    comp["columns"] = str(vars_map["columns"].get() or "").strip()
    comp["rows"] = max(3, _to_int(vars_map["rows"].get(), comp.get("rows", 8)))
    comp["x"] = _clamp(_to_int(vars_map["x"].get(), comp.get("x", 0)), 0, CANVAS_REGION_W - 20)
    comp["y"] = _clamp(_to_int(vars_map["y"].get(), comp.get("y", 0)), 0, CANVAS_REGION_H - 20)
    comp["w"] = _clamp(_to_int(vars_map["w"].get(), comp.get("w", 180)), 60, CANVAS_REGION_W)
    comp["h"] = _clamp(_to_int(vars_map["h"].get(), comp.get("h", 36)), 24, CANVAS_REGION_H)

    _render_canvas(owner)
    _refresh_property_panel(owner)
    if hasattr(owner, "status_main_var"):
        owner.status_main_var.set(f"界面设计器：已更新 {comp.get('name', '')}")
    return "break"


def _sanitize_identifier(text, fallback):
    value = re.sub(r"[^\u4e00-\u9fa5A-Za-z0-9_]", "", str(text or ""))
    if not value:
        value = fallback
    if value[0].isdigit():
        value = f"控件_{value}"
    return value


def _sanitize_function_name(text, fallback):
    name = _sanitize_identifier(text, fallback)
    if not name.startswith("功能") and name in {"显示", "输入", "如果", "功能", "返回"}:
        return f"{fallback}"
    return name


def _normalize_columns(raw_columns):
    text = str(raw_columns or "").strip()
    if not text:
        return ["列1", "列2"]
    sep = None
    for candidate in [",", "，", "|", "｜", ";", "；"]:
        if candidate in text:
            sep = candidate
            break
    if sep is None:
        return [text]
    cols = [item.strip() for item in text.split(sep) if item.strip()]
    return cols or ["列1", "列2"]


def _generate_ym_code(owner):
    comps = list(getattr(owner, "_ui_designer_components", []) or [])
    comps.sort(key=lambda item: (_to_int(item.get("y", 0)), _to_int(item.get("x", 0)), _to_int(item.get("uid", 0))))

    lines = [
        "# --- 可视化界面设计器导出 ---",
        "窗口 = 建窗口(\"可视化界面\", 960, 640)",
        "",
    ]
    used_names = set()
    generated_events = []

    for index, comp in enumerate(comps, start=1):
        kind = str(comp.get("kind", "文字"))
        base_name = _sanitize_identifier(comp.get("name", ""), f"控件{index}")
        name = base_name
        n = 2
        while name in used_names:
            name = f"{base_name}_{n}"
            n += 1
        used_names.add(name)

        x = _to_int(comp.get("x", 0), 0)
        y = _to_int(comp.get("y", 0), 0)
        w = max(60, _to_int(comp.get("w", 160), 160))
        h = max(24, _to_int(comp.get("h", 34), 34))
        text = str(comp.get("text", "")).strip() or kind

        if kind == "文字":
            lines.append(f"{name} = 加文字(窗口, {json.dumps(text, ensure_ascii=False)})")
            lines.append(f"设位置({name}, {x}, {y}, {w}, {h})")
        elif kind == "输入框":
            lines.append(f"{name} = 加输入框(窗口)")
            lines.append(f"设位置({name}, {x}, {y}, {w}, {h})")
        elif kind == "按钮":
            fallback_fn = f"处理点击_{index}"
            fn_name = _sanitize_function_name(comp.get("event", ""), fallback_fn)
            lines.append(f"{name} = 加按钮(窗口, {json.dumps(text, ensure_ascii=False)}, {json.dumps(fn_name, ensure_ascii=False)})")
            lines.append(f"设位置({name}, {x}, {y}, {w}, {h})")
            generated_events.append(fn_name)
        elif kind == "表格":
            columns = _normalize_columns(comp.get("columns", "列1,列2"))
            rows = max(3, _to_int(comp.get("rows", 8), 8))
            lines.append(f"{name} = 加表格(窗口, {json.dumps(columns, ensure_ascii=False)}, {rows})")
            lines.append(f"设位置({name}, {x}, {y}, {w}, {h})")
        elif kind == "卡片":
            lines.append(f"{name} = 加卡片(窗口, {json.dumps(text, ensure_ascii=False)})")
            lines.append(f"设位置({name}, {x}, {y}, {w}, {h})")
        else:
            lines.append(f"# 未识别组件：{json.dumps(kind, ensure_ascii=False)}")
        lines.append("")

    generated_events = sorted(set(generated_events))
    for fn_name in generated_events:
        lines.append(f"功能 {fn_name}")
        lines.append(f"    弹窗(\"提示\", \"触发：{fn_name}\")")
        lines.append("")

    lines.append("打开界面(窗口)")
    return "\n".join(lines).rstrip() + "\n"


def _insert_code_to_editor(owner, code):
    editor = owner._get_current_editor()
    if editor is None:
        try:
            owner._create_editor_tab("界面设计导出.ym", "")
            editor = owner._get_current_editor()
        except Exception:
            editor = None
    if editor is None:
        if hasattr(owner, "status_main_var"):
            owner.status_main_var.set("界面设计器：没有可写入的编辑区")
        return False
    try:
        if editor.tag_ranges("sel"):
            editor.delete("sel.first", "sel.last")
        editor.insert("insert", code)
        editor.focus_set()
        owner._schedule_highlight()
        owner._update_line_numbers()
        owner._update_cursor_status()
        owner._schedule_diagnose()
        return True
    except tk.TclError:
        if hasattr(owner, "status_main_var"):
            owner.status_main_var.set("界面设计器：插入代码失败")
        return False


def export_ui_design_to_editor(owner):
    code = _generate_ym_code(owner)
    ok = _insert_code_to_editor(owner, code)
    if ok and hasattr(owner, "status_main_var"):
        owner.status_main_var.set("界面设计器：已导出到编辑区")
    return "break"


def copy_ui_design_code(owner):
    code = _generate_ym_code(owner)
    try:
        owner.root.clipboard_clear()
        owner.root.clipboard_append(code)
        owner.root.update_idletasks()
        if hasattr(owner, "status_main_var"):
            owner.status_main_var.set("界面设计器：代码已复制到剪贴板")
    except tk.TclError:
        if hasattr(owner, "status_main_var"):
            owner.status_main_var.set("界面设计器：复制失败")
    return "break"


def _ensure_window(owner):
    _ensure_state(owner)
    win = getattr(owner, "_ui_designer_window", None)
    if win is not None:
        try:
            if win.winfo_exists():
                return win
        except tk.TclError:
            pass

    win = tk.Toplevel(owner.root)
    win.title("易码界面设计器")
    _center_window(owner, win, 1320, 820)
    try:
        win.minsize(1080, 680)
    except tk.TclError:
        pass
    win.configure(bg=owner.theme_bg)
    win.protocol("WM_DELETE_WINDOW", win.withdraw)

    top = tk.Frame(win, bg=owner.theme_toolbar_bg, padx=10, pady=8)
    top.pack(fill=tk.X)

    tk.Label(
        top,
        text="界面设计器 UI DESIGNER",
        font=("Microsoft YaHei", 10, "bold"),
        bg=owner.theme_toolbar_bg,
        fg="#DFE6EE",
    ).pack(side=tk.LEFT)

    def _tool_btn(text, cmd):
        btn = tk.Button(
            top,
            text=text,
            command=cmd,
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
        btn.pack(side=tk.RIGHT, padx=(6, 0))
        return btn

    _tool_btn("复制代码", lambda: copy_ui_design_code(owner))
    _tool_btn("导出到编辑区", lambda: export_ui_design_to_editor(owner))
    _tool_btn("清空画布", lambda: _clear_components(owner))
    _tool_btn("删除选中", lambda: _delete_selected_component(owner))

    body = tk.PanedWindow(win, orient=tk.HORIZONTAL, sashwidth=4, bg=owner.theme_sash, borderwidth=0)
    body.pack(fill=tk.BOTH, expand=True)

    # 左：组件面板
    left = tk.Frame(body, bg=owner.theme_panel_bg, width=190)
    body.add(left, stretch="never", minsize=170)
    tk.Label(
        left,
        text="组件列表",
        font=("Microsoft YaHei", 9, "bold"),
        bg=owner.theme_panel_bg,
        fg="#9FB0C5",
        anchor="w",
        padx=10,
        pady=8,
    ).pack(fill=tk.X)

    palette_wrap = tk.Frame(left, bg=owner.theme_panel_bg, padx=8, pady=0)
    palette_wrap.pack(fill=tk.BOTH, expand=True)
    palette = tk.Listbox(
        palette_wrap,
        font=("Microsoft YaHei", 9),
        bg=owner.theme_panel_inner_bg,
        fg=owner.theme_fg,
        selectbackground=owner.theme_accent,
        selectforeground="#FFFFFF",
        borderwidth=0,
        highlightthickness=0,
        relief="flat",
        height=8,
    )
    palette_vsb = ttk.Scrollbar(palette_wrap, orient="vertical", command=palette.yview)
    palette.configure(yscrollcommand=palette_vsb.set)
    palette.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    palette_vsb.pack(side=tk.RIGHT, fill=tk.Y)
    for kind, _ in COMPONENT_CATALOG:
        palette.insert(tk.END, kind)
    palette.selection_set(0)
    owner._ui_designer_palette = palette

    action_left = tk.Frame(left, bg=owner.theme_panel_bg, padx=8, pady=8)
    action_left.pack(fill=tk.X)
    tk.Button(
        action_left,
        text="添加组件",
        command=lambda: _add_component(owner),
        font=("Microsoft YaHei", 8),
        bg=owner.theme_toolbar_group_bg,
        fg=owner.theme_toolbar_fg,
        activebackground=owner.theme_toolbar_hover,
        activeforeground="#FFFFFF",
        relief="flat",
        bd=0,
        padx=8,
        pady=3,
        cursor="hand2",
    ).pack(side=tk.LEFT)
    palette.bind("<Double-Button-1>", lambda e: _add_component(owner), add="+")
    palette.bind("<Return>", lambda e: _add_component(owner), add="+")

    # 中：画布
    center = tk.Frame(body, bg=owner.theme_panel_bg)
    body.add(center, stretch="always", minsize=520)
    center_top = tk.Frame(center, bg=owner.theme_panel_bg, padx=10, pady=6)
    center_top.pack(fill=tk.X)
    tk.Label(
        center_top,
        text="自由画布（拖拽组件自由排版，支持绝对位置导出）",
        font=("Microsoft YaHei", 8),
        bg=owner.theme_panel_bg,
        fg="#8FA1B8",
        anchor="w",
    ).pack(side=tk.LEFT, fill=tk.X, expand=True)

    canvas_wrap = tk.Frame(center, bg=owner.theme_panel_bg, padx=8, pady=0)
    canvas_wrap.pack(fill=tk.BOTH, expand=True, pady=(0, 8))
    canvas = tk.Canvas(
        canvas_wrap,
        bg="#101723",
        highlightthickness=0,
        borderwidth=0,
        relief="flat",
        scrollregion=(0, 0, CANVAS_REGION_W, CANVAS_REGION_H),
    )
    canvas_x = ttk.Scrollbar(canvas_wrap, orient="horizontal", command=canvas.xview)
    canvas_y = ttk.Scrollbar(canvas_wrap, orient="vertical", command=canvas.yview)
    canvas.configure(xscrollcommand=canvas_x.set, yscrollcommand=canvas_y.set)
    canvas.grid(row=0, column=0, sticky="nsew")
    canvas_y.grid(row=0, column=1, sticky="ns")
    canvas_x.grid(row=1, column=0, sticky="ew")
    canvas_wrap.grid_rowconfigure(0, weight=1)
    canvas_wrap.grid_columnconfigure(0, weight=1)
    owner._ui_designer_canvas = canvas
    canvas.bind("<ButtonPress-1>", lambda e: _on_canvas_release(owner, e), add="+")

    # 右：属性面板
    right = tk.Frame(body, bg=owner.theme_panel_bg, width=300)
    body.add(right, stretch="never", minsize=260)
    tk.Label(
        right,
        text="属性",
        font=("Microsoft YaHei", 9, "bold"),
        bg=owner.theme_panel_bg,
        fg="#9FB0C5",
        anchor="w",
        padx=10,
        pady=8,
    ).pack(fill=tk.X)

    owner._ui_designer_info_var = tk.StringVar(value="未选中组件")
    tk.Label(
        right,
        textvariable=owner._ui_designer_info_var,
        font=("Microsoft YaHei", 8),
        bg=owner.theme_panel_bg,
        fg="#D1DDEA",
        anchor="w",
        padx=10,
        pady=2,
    ).pack(fill=tk.X)

    prop_body = tk.Frame(right, bg=owner.theme_panel_bg, padx=10, pady=8)
    prop_body.pack(fill=tk.BOTH, expand=True)

    owner._ui_designer_prop_vars = {
        "name": tk.StringVar(value=""),
        "kind": tk.StringVar(value=""),
        "text": tk.StringVar(value=""),
        "event": tk.StringVar(value=""),
        "columns": tk.StringVar(value=""),
        "rows": tk.StringVar(value=""),
        "x": tk.StringVar(value=""),
        "y": tk.StringVar(value=""),
        "w": tk.StringVar(value=""),
        "h": tk.StringVar(value=""),
    }

    def _row(label, key, readonly=False):
        row = tk.Frame(prop_body, bg=owner.theme_panel_bg)
        row.pack(fill=tk.X, pady=(0, 6))
        tk.Label(
            row,
            text=label,
            width=8,
            font=("Microsoft YaHei", 8),
            bg=owner.theme_panel_bg,
            fg="#8FA1B8",
            anchor="w",
        ).pack(side=tk.LEFT)
        entry = tk.Entry(
            row,
            textvariable=owner._ui_designer_prop_vars[key],
            font=("Microsoft YaHei", 8),
            bg=owner.theme_panel_inner_bg,
            fg=owner.theme_fg,
            insertbackground=owner.theme_fg,
            relief="flat",
            bd=0,
            highlightthickness=1,
            highlightbackground=owner.theme_toolbar_border,
            highlightcolor=owner.theme_accent,
        )
        if readonly:
            entry.configure(state="readonly")
        entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        if not readonly:
            entry.bind("<Return>", lambda e: _apply_properties(owner), add="+")
        return entry

    _row("标识", "name", readonly=True)
    _row("类型", "kind", readonly=True)
    _row("文本", "text")
    _row("函数", "event")
    _row("列定义", "columns")
    _row("行数", "rows")
    _row("X", "x")
    _row("Y", "y")
    _row("宽", "w")
    _row("高", "h")

    tk.Button(
        prop_body,
        text="应用属性",
        command=lambda: _apply_properties(owner),
        font=("Microsoft YaHei", 8),
        bg=owner.theme_toolbar_group_bg,
        fg=owner.theme_toolbar_fg,
        activebackground=owner.theme_toolbar_hover,
        activeforeground="#FFFFFF",
        relief="flat",
        bd=0,
        padx=8,
        pady=3,
        cursor="hand2",
    ).pack(anchor="w", pady=(4, 0))

    hint = tk.Label(
        right,
        text="提示：\n1. 左侧添加组件\n2. 中间拖拽排版\n3. 右侧改属性\n4. 导出到编辑区",
        font=("Microsoft YaHei", 8),
        bg=owner.theme_panel_bg,
        fg="#8FA1B8",
        justify="left",
        anchor="w",
        padx=10,
        pady=8,
    )
    hint.pack(fill=tk.X, side=tk.BOTTOM)

    owner._ui_designer_window = win
    _render_canvas(owner)
    _refresh_property_panel(owner)
    return win


def open_ui_designer(owner, event=None):
    del event
    _ensure_state(owner)
    win = _ensure_window(owner)
    try:
        win.deiconify()
        win.lift()
        win.focus_force()
    except tk.TclError:
        pass
    if hasattr(owner, "status_main_var"):
        owner.status_main_var.set("界面设计器已打开（组件化 + 自由拖拽 + 代码导出）")
    return "break"


def _build_designer_panel(owner, parent, title_text="可视化界面设计 UI DESIGNER"):
    panel = tk.Frame(parent, bg=owner.theme_bg)

    top = tk.Frame(panel, bg=owner.theme_toolbar_bg, padx=10, pady=8)
    top.pack(fill=tk.X)
    tk.Label(
        top,
        text=title_text,
        font=("Microsoft YaHei", 10, "bold"),
        bg=owner.theme_toolbar_bg,
        fg="#DFE6EE",
    ).pack(side=tk.LEFT)

    _tool_button(owner, top, "复制代码", lambda: copy_ui_design_code(owner))
    _tool_button(owner, top, "导出到编辑区", lambda: export_ui_design_to_editor(owner))
    _tool_button(owner, top, "清空画布", lambda: _clear_components(owner))
    _tool_button(owner, top, "删除选中", lambda: _delete_selected_component(owner))

    body = tk.PanedWindow(panel, orient=tk.HORIZONTAL, sashwidth=4, bg=owner.theme_sash, borderwidth=0)
    body.pack(fill=tk.BOTH, expand=True)

    left = tk.Frame(body, bg=owner.theme_panel_bg, width=190)
    body.add(left, stretch="never", minsize=170)
    tk.Label(
        left,
        text="组件列表",
        font=("Microsoft YaHei", 9, "bold"),
        bg=owner.theme_panel_bg,
        fg="#9FB0C5",
        anchor="w",
        padx=10,
        pady=8,
    ).pack(fill=tk.X)

    palette_wrap = tk.Frame(left, bg=owner.theme_panel_bg, padx=8, pady=0)
    palette_wrap.pack(fill=tk.BOTH, expand=True)
    palette = tk.Listbox(
        palette_wrap,
        font=("Microsoft YaHei", 9),
        bg=owner.theme_panel_inner_bg,
        fg=owner.theme_fg,
        selectbackground=owner.theme_accent,
        selectforeground="#FFFFFF",
        borderwidth=0,
        highlightthickness=0,
        relief="flat",
        height=8,
    )
    palette_vsb = ttk.Scrollbar(palette_wrap, orient="vertical", command=palette.yview)
    palette.configure(yscrollcommand=palette_vsb.set)
    palette.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    palette_vsb.pack(side=tk.RIGHT, fill=tk.Y)
    for kind, _ in COMPONENT_CATALOG:
        palette.insert(tk.END, kind)
    palette.selection_set(0)
    owner._ui_designer_palette = palette

    action_left = tk.Frame(left, bg=owner.theme_panel_bg, padx=8, pady=8)
    action_left.pack(fill=tk.X)
    tk.Button(
        action_left,
        text="添加组件",
        command=lambda: _add_component(owner),
        font=("Microsoft YaHei", 8),
        bg=owner.theme_toolbar_group_bg,
        fg=owner.theme_toolbar_fg,
        activebackground=owner.theme_toolbar_hover,
        activeforeground="#FFFFFF",
        relief="flat",
        bd=0,
        padx=8,
        pady=3,
        cursor="hand2",
    ).pack(side=tk.LEFT)
    palette.bind("<Double-Button-1>", lambda e: _add_component(owner), add="+")
    palette.bind("<Return>", lambda e: _add_component(owner), add="+")

    center = tk.Frame(body, bg=owner.theme_panel_bg)
    body.add(center, stretch="always", minsize=520)
    center_top = tk.Frame(center, bg=owner.theme_panel_bg, padx=10, pady=6)
    center_top.pack(fill=tk.X)
    tk.Label(
        center_top,
        text="自由画布（拖拽组件自由排版，支持绝对布局代码导出）",
        font=("Microsoft YaHei", 8),
        bg=owner.theme_panel_bg,
        fg="#8FA1B8",
        anchor="w",
    ).pack(side=tk.LEFT, fill=tk.X, expand=True)

    canvas_wrap = tk.Frame(center, bg=owner.theme_panel_bg, padx=8, pady=0)
    canvas_wrap.pack(fill=tk.BOTH, expand=True, pady=(0, 8))
    canvas = tk.Canvas(
        canvas_wrap,
        bg="#101723",
        highlightthickness=0,
        borderwidth=0,
        relief="flat",
        scrollregion=(0, 0, CANVAS_REGION_W, CANVAS_REGION_H),
    )
    canvas_x = ttk.Scrollbar(canvas_wrap, orient="horizontal", command=canvas.xview)
    canvas_y = ttk.Scrollbar(canvas_wrap, orient="vertical", command=canvas.yview)
    canvas.configure(xscrollcommand=canvas_x.set, yscrollcommand=canvas_y.set)
    canvas.grid(row=0, column=0, sticky="nsew")
    canvas_y.grid(row=0, column=1, sticky="ns")
    canvas_x.grid(row=1, column=0, sticky="ew")
    canvas_wrap.grid_rowconfigure(0, weight=1)
    canvas_wrap.grid_columnconfigure(0, weight=1)
    owner._ui_designer_canvas = canvas
    canvas.bind("<ButtonPress-1>", lambda e: _on_canvas_release(owner, e), add="+")

    right = tk.Frame(body, bg=owner.theme_panel_bg, width=300)
    body.add(right, stretch="never", minsize=260)
    tk.Label(
        right,
        text="属性",
        font=("Microsoft YaHei", 9, "bold"),
        bg=owner.theme_panel_bg,
        fg="#9FB0C5",
        anchor="w",
        padx=10,
        pady=8,
    ).pack(fill=tk.X)

    owner._ui_designer_info_var = tk.StringVar(value="未选中组件")
    tk.Label(
        right,
        textvariable=owner._ui_designer_info_var,
        font=("Microsoft YaHei", 8),
        bg=owner.theme_panel_bg,
        fg="#D1DDEA",
        anchor="w",
        padx=10,
        pady=2,
    ).pack(fill=tk.X)

    prop_body = tk.Frame(right, bg=owner.theme_panel_bg, padx=10, pady=8)
    prop_body.pack(fill=tk.BOTH, expand=True)

    owner._ui_designer_prop_vars = {
        "name": tk.StringVar(value=""),
        "kind": tk.StringVar(value=""),
        "text": tk.StringVar(value=""),
        "event": tk.StringVar(value=""),
        "columns": tk.StringVar(value=""),
        "rows": tk.StringVar(value=""),
        "x": tk.StringVar(value=""),
        "y": tk.StringVar(value=""),
        "w": tk.StringVar(value=""),
        "h": tk.StringVar(value=""),
    }

    def _row(label, key, readonly=False):
        row = tk.Frame(prop_body, bg=owner.theme_panel_bg)
        row.pack(fill=tk.X, pady=(0, 6))
        tk.Label(
            row,
            text=label,
            width=8,
            font=("Microsoft YaHei", 8),
            bg=owner.theme_panel_bg,
            fg="#8FA1B8",
            anchor="w",
        ).pack(side=tk.LEFT)
        entry = tk.Entry(
            row,
            textvariable=owner._ui_designer_prop_vars[key],
            font=("Microsoft YaHei", 8),
            bg=owner.theme_panel_inner_bg,
            fg=owner.theme_fg,
            insertbackground=owner.theme_fg,
            relief="flat",
            bd=0,
            highlightthickness=1,
            highlightbackground=owner.theme_toolbar_border,
            highlightcolor=owner.theme_accent,
        )
        if readonly:
            entry.configure(state="readonly")
        entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        if not readonly:
            entry.bind("<Return>", lambda e: _apply_properties(owner), add="+")
        return entry

    _row("标识", "name", readonly=True)
    _row("类型", "kind", readonly=True)
    _row("文本", "text")
    _row("函数", "event")
    _row("列定义", "columns")
    _row("行数", "rows")
    _row("X", "x")
    _row("Y", "y")
    _row("宽", "w")
    _row("高", "h")

    tk.Button(
        prop_body,
        text="应用属性",
        command=lambda: _apply_properties(owner),
        font=("Microsoft YaHei", 8),
        bg=owner.theme_toolbar_group_bg,
        fg=owner.theme_toolbar_fg,
        activebackground=owner.theme_toolbar_hover,
        activeforeground="#FFFFFF",
        relief="flat",
        bd=0,
        padx=8,
        pady=3,
        cursor="hand2",
    ).pack(anchor="w", pady=(4, 0))

    tk.Label(
        right,
        text="提示:\n1. 左侧添加组件\n2. 中间拖拽排版\n3. 右侧改属性\n4. 导出到编辑区",
        font=("Microsoft YaHei", 8),
        bg=owner.theme_panel_bg,
        fg="#8FA1B8",
        justify="left",
        anchor="w",
        padx=10,
        pady=8,
    ).pack(fill=tk.X, side=tk.BOTTOM)
    return panel


def ensure_embedded_ui_designer(owner, parent):
    _ensure_state(owner)
    panel = getattr(owner, "_ui_designer_embedded_panel", None)
    if panel is not None:
        try:
            if panel.winfo_exists() and panel.master is parent:
                return panel
        except tk.TclError:
            pass
        try:
            panel.destroy()
        except tk.TclError:
            pass

    panel = _build_designer_panel(owner, parent, title_text="可视化界面设计 UI DESIGNER")
    owner._ui_designer_embedded_panel = panel
    _render_canvas(owner)
    _refresh_property_panel(owner)
    return panel


def open_ui_designer(owner, event=None):
    del event
    switcher = getattr(owner, "_switch_workspace_mode", None)
    if callable(switcher):
        try:
            switcher("designer")
            if hasattr(owner, "status_main_var"):
                owner.status_main_var.set("已切换到可视化界面设计模式")
            return "break"
        except Exception:
            pass

    _ensure_state(owner)
    win = _ensure_window(owner)
    try:
        win.deiconify()
        win.lift()
        win.focus_force()
    except tk.TclError:
        pass
    if hasattr(owner, "status_main_var"):
        owner.status_main_var.set("界面设计器已打开（组件化 + 自由拖拽 + 代码导出）")
    return "break"
