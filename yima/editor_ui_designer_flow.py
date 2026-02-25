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
CANVAS_RESIZE_HANDLE = 8


COMPONENT_CATALOG = [
    ("窗口", {"x": 48, "y": 40, "w": 960, "h": 640, "text": "我的窗口", "singleton": True}),
    ("文字", {"w": 180, "h": 34, "text": "文字内容"}),
    ("输入框", {"w": 240, "h": 36, "text": "输入内容"}),
    ("多行文本框", {"w": 320, "h": 120, "text": "请输入多行内容"}),
    ("按钮", {"w": 150, "h": 40, "text": "按钮", "event": "处理点击"}),
    ("复选框", {"w": 160, "h": 34, "text": "勾选项", "event": "处理勾选"}),
    ("单选按钮", {"w": 160, "h": 34, "text": "单选项", "event": "处理选择"}),
    ("组合框", {"w": 240, "h": 36, "text": "选项1,选项2"}),
    ("数值框", {"w": 180, "h": 36, "text": "0"}),
    ("数值滑块", {"w": 260, "h": 36, "text": "0~100"}),
    ("进度条", {"w": 260, "h": 28, "text": "进度 50%"}),
    ("日期选择器", {"w": 220, "h": 36, "text": "2026-01-01"}),
    ("图片框", {"w": 240, "h": 160, "text": "图片占位"}),
    ("列表框", {"w": 260, "h": 200, "text": "列表数据", "columns": "项目", "rows": 8}),
    ("树形视图", {"w": 320, "h": 220, "text": "树形数据", "columns": "节点,值", "rows": 8}),
    ("表格", {"w": 420, "h": 220, "text": "数据表", "columns": "列1,列2,列3", "rows": 8}),
    ("卡片", {"w": 420, "h": 260, "text": "卡片标题"}),
    ("分组框", {"w": 360, "h": 240, "text": "分组容器"}),
    ("选项卡", {"w": 420, "h": 280, "text": "选项卡容器"}),
    ("分割容器", {"w": 420, "h": 260, "text": "分割布局"}),
    ("表格布局面板", {"w": 420, "h": 260, "text": "网格布局"}),
    ("流式布局面板", {"w": 420, "h": 260, "text": "流式布局"}),
    ("菜单栏", {"w": 460, "h": 34, "text": "文件 编辑 视图"}),
    ("工具栏", {"w": 460, "h": 38, "text": "新建 保存 导出"}),
    ("状态栏", {"w": 460, "h": 30, "text": "就绪"}),
    ("登录模板", {"w": 420, "h": 240, "text": "账号登录", "action_text": "登录", "event": "处理登录"}),
    ("列表模板", {"w": 560, "h": 320, "text": "数据列表", "action_text": "查询", "event": "执行查询", "columns": "名称,说明", "rows": 10}),
]
COMPONENT_KIND_SET = {item[0] for item in COMPONENT_CATALOG}
WINDOW_COMPONENT_KIND = "窗口"
COMPONENT_SINGLETON_KINDS = {
    kind for kind, config in COMPONENT_CATALOG if bool(config.get("singleton"))
}
TEXT_COMPONENT_KINDS = {"文字", "菜单栏", "工具栏", "状态栏"}
INPUT_COMPONENT_KINDS = {"输入框", "多行文本框", "组合框", "数值框", "数值滑块", "日期选择器"}
BUTTON_COMPONENT_KINDS = {"按钮", "复选框", "单选按钮"}
TABLE_COMPONENT_KINDS = {"表格", "列表框", "树形视图"}
CARD_COMPONENT_KINDS = {"卡片", "图片框", "分组框", "选项卡", "分割容器", "表格布局面板", "流式布局面板", "进度条"}
COMPONENT_PALETTE_GROUPS = [
    ("容器", [WINDOW_COMPONENT_KIND, "卡片", "分组框", "选项卡", "分割容器", "表格布局面板", "流式布局面板"]),
    ("常用控件", ["文字", "输入框", "多行文本框", "按钮", "复选框", "单选按钮", "组合框", "数值框", "数值滑块", "日期选择器"]),
    ("数据控件", ["表格", "列表框", "树形视图", "进度条", "图片框"]),
    ("菜单与状态", ["菜单栏", "工具栏", "状态栏"]),
    ("模板", ["登录模板", "列表模板"]),
]
DATA_BACKEND_CHOICES = [
    ("sqlite", "SQLite"),
    ("json", "JSON文件"),
]
DATA_BACKEND_KEY_TO_LABEL = {key: label for key, label in DATA_BACKEND_CHOICES}
DATA_BACKEND_LABEL_TO_KEY = {label: key for key, label in DATA_BACKEND_CHOICES}

PROPERTY_EDITABLE_KEYS_BY_KIND = {
    "default": {"text", "event", "action_text", "columns", "rows", "x", "y", "w", "h"},
    WINDOW_COMPONENT_KIND: {"text", "x", "y", "w", "h"},
    "文字": {"text", "x", "y", "w", "h"},
    "菜单栏": {"text", "x", "y", "w", "h"},
    "工具栏": {"text", "x", "y", "w", "h"},
    "状态栏": {"text", "x", "y", "w", "h"},
    "输入框": {"text", "x", "y", "w", "h"},
    "多行文本框": {"text", "x", "y", "w", "h"},
    "组合框": {"text", "x", "y", "w", "h"},
    "数值框": {"text", "x", "y", "w", "h"},
    "数值滑块": {"text", "x", "y", "w", "h"},
    "日期选择器": {"text", "x", "y", "w", "h"},
    "按钮": {"text", "event", "x", "y", "w", "h"},
    "复选框": {"text", "event", "x", "y", "w", "h"},
    "单选按钮": {"text", "event", "x", "y", "w", "h"},
    "表格": {"text", "columns", "rows", "x", "y", "w", "h"},
    "列表框": {"text", "columns", "rows", "x", "y", "w", "h"},
    "树形视图": {"text", "columns", "rows", "x", "y", "w", "h"},
    "卡片": {"text", "x", "y", "w", "h"},
    "图片框": {"text", "x", "y", "w", "h"},
    "分组框": {"text", "x", "y", "w", "h"},
    "选项卡": {"text", "x", "y", "w", "h"},
    "分割容器": {"text", "x", "y", "w", "h"},
    "表格布局面板": {"text", "x", "y", "w", "h"},
    "流式布局面板": {"text", "x", "y", "w", "h"},
    "进度条": {"text", "x", "y", "w", "h"},
    "登录模板": {"text", "action_text", "event", "x", "y", "w", "h"},
    "列表模板": {"text", "action_text", "event", "columns", "rows", "x", "y", "w", "h"},
}
PROPERTY_HINT_BY_KIND = {
    "default": "按顺序调整：文本、位置(X/Y)、尺寸(宽/高)。函数名只给有点击行为的组件填写。",
    WINDOW_COMPONENT_KIND: "窗口组件只需要：文本(窗口标题)、宽/高、位置。",
    "文字": "文字组件只需要文本和位置尺寸，通常用于标题或说明。",
    "菜单栏": "菜单栏可先写菜单项文字，后续再补菜单事件逻辑。",
    "工具栏": "工具栏适合放常用动作说明，先完成布局和文字。",
    "状态栏": "状态栏通常位于底部，建议宽度拉满。",
    "输入框": "输入框建议先改文本(占位提示)，再调整位置尺寸。",
    "多行文本框": "多行文本框建议设置较高高度，便于输入备注。",
    "组合框": "组合框文本可先写候选项提示，后续在逻辑中填真实选项。",
    "数值框": "数值框建议默认值写数字文本，业务层再做校验。",
    "数值滑块": "滑块可先放占位，导出后可替换为具体控件逻辑。",
    "日期选择器": "日期选择器先以输入框形式导出，业务层可补日期校验。",
    "按钮": "按钮至少填文本和函数名，导出后会自动生成对应业务函数。",
    "复选框": "复选框会按可点击控件导出，建议填写函数名处理状态变化。",
    "单选按钮": "单选按钮会按可点击控件导出，建议填写函数名处理选择。",
    "表格": "表格建议先配列定义(逗号分隔)和行数，再调整尺寸。",
    "列表框": "列表框当前按表格导出，可用单列展示列表数据。",
    "树形视图": "树形视图当前按表格导出，后续可升级真实树控件。",
    "卡片": "卡片适合放说明或状态信息，重点是文本和尺寸。",
    "图片框": "图片框当前按卡片导出，可先占位后续再接图片加载。",
    "分组框": "分组框适合作为一组控件的视觉容器。",
    "选项卡": "选项卡当前按容器占位导出，先确定区域尺寸。",
    "分割容器": "分割容器当前按容器占位导出，先确定布局比例。",
    "表格布局面板": "表格布局面板用于网格布局占位，后续可升级自动布局逻辑。",
    "流式布局面板": "流式布局面板用于流式排版占位，后续可升级自动换行逻辑。",
    "进度条": "进度条当前按容器占位导出，可在业务层更新文本进度。",
    "登录模板": "登录模板建议填写按钮文案和函数名，导出后自动串联业务层与数据层。",
    "列表模板": "列表模板建议同时配置列定义、按钮文案和函数名。",
}
QUICK_START_SCENES = [
    {"key": "blank", "title": "空白窗口", "desc": "只保留窗口，适合从零手动搭建"},
    {"key": "form", "title": "录入表单", "desc": "标题 + 两个输入框 + 提交按钮"},
    {"key": "query", "title": "查询表格", "desc": "关键词输入 + 查询按钮 + 数据表格"},
]


def _catalog_map():
    return {kind: dict(config) for kind, config in COMPONENT_CATALOG}


def _normalize_data_backend(value):
    text = str(value or "").strip().lower()
    if text in {"json", "json文件", "json file", "json-file"}:
        return "json"
    return "sqlite"


def _backend_label_of(key):
    backend_key = _normalize_data_backend(key)
    return DATA_BACKEND_KEY_TO_LABEL.get(backend_key, DATA_BACKEND_KEY_TO_LABEL["sqlite"])


def _backend_key_from_label(text):
    raw = str(text or "").strip()
    if raw in DATA_BACKEND_LABEL_TO_KEY:
        return _normalize_data_backend(DATA_BACKEND_LABEL_TO_KEY[raw])
    return _normalize_data_backend(raw)


def _normalize_layer_export_prefix(text, fallback="界面设计"):
    value = str(text or "").strip()
    value = re.sub(r"[\\/:*?\"<>|]+", "_", value)
    value = re.sub(r"\s+", "_", value)
    value = value.strip("._")
    if not value:
        return str(fallback or "界面设计")
    return value[:60]


def _set_data_backend(owner, backend, sync_vars=True):
    _ensure_state(owner)
    key = _normalize_data_backend(backend)
    owner._ui_designer_data_backend = key
    if not sync_vars:
        return key
    label = _backend_label_of(key)
    keep_vars = []
    for var in list(getattr(owner, "_ui_designer_backend_vars", []) or []):
        if var is None:
            continue
        try:
            if str(var.get()) != label:
                var.set(label)
            keep_vars.append(var)
        except Exception:
            continue
    owner._ui_designer_backend_vars = keep_vars
    return key


def _create_data_backend_selector(owner, parent):
    _ensure_state(owner)
    wrap = tk.Frame(parent, bg=owner.theme_toolbar_bg)
    wrap.pack(side=tk.LEFT, padx=(14, 0))
    tk.Label(
        wrap,
        text="数据层：",
        font=("Microsoft YaHei", 8),
        bg=owner.theme_toolbar_bg,
        fg=owner.theme_toolbar_muted,
    ).pack(side=tk.LEFT)
    backend_var = tk.StringVar(value=_backend_label_of(getattr(owner, "_ui_designer_data_backend", "sqlite")))
    combo = ttk.Combobox(
        wrap,
        textvariable=backend_var,
        values=[label for _key, label in DATA_BACKEND_CHOICES],
        state="readonly",
        width=9,
    )
    combo.pack(side=tk.LEFT, padx=(4, 0))

    def _on_backend_change(_event=None):
        selected_key = _backend_key_from_label(backend_var.get())
        _set_data_backend(owner, selected_key)
        saver = getattr(owner, "_save_project_state", None)
        if callable(saver):
            try:
                saver()
            except Exception:
                pass
        if hasattr(owner, "status_main_var"):
            owner.status_main_var.set(f"界面设计器：数据层后端已切换为 {_backend_label_of(selected_key)}")

    combo.bind("<<ComboboxSelected>>", _on_backend_change, add="+")
    owner._ui_designer_backend_vars.append(backend_var)
    return wrap


def _prompt_layer_export_backend(owner):
    _ensure_state(owner)
    default_backend = _normalize_data_backend(getattr(owner, "_ui_designer_data_backend", "sqlite"))
    default_prefix = _normalize_layer_export_prefix(getattr(owner, "_ui_designer_layer_export_prefix", "界面设计"))
    result = {
        "ok": False,
        "backend": default_backend,
        "remember": True,
        "prefix": default_prefix,
        "remember_prefix": True,
    }

    dialog = tk.Toplevel(owner.root)
    dialog.title("导出三层代码")
    dialog.transient(owner.root)
    dialog.configure(bg=owner.theme_bg)
    try:
        dialog.resizable(False, False)
    except tk.TclError:
        pass
    try:
        dialog.grab_set()
    except tk.TclError:
        pass

    try:
        owner.root.update_idletasks()
        # 先给一个安全初始尺寸，避免构建内容时被压缩裁剪。
        w = 460
        h = 320
        x = int(owner.root.winfo_x() + max(0, (owner.root.winfo_width() - w) / 2))
        y = int(owner.root.winfo_y() + max(0, (owner.root.winfo_height() - h) / 2))
        dialog.geometry(f"{w}x{h}+{x}+{y}")
    except Exception:
        pass

    body = tk.Frame(dialog, bg=owner.theme_bg, padx=14, pady=12)
    body.pack(fill=tk.BOTH, expand=True)

    tk.Label(
        body,
        text="选择本次三层导出的数据层后端",
        font=("Microsoft YaHei", 9, "bold"),
        bg=owner.theme_bg,
        fg="#DFE6EE",
        anchor="w",
    ).pack(fill=tk.X, pady=(0, 8))

    row = tk.Frame(body, bg=owner.theme_bg)
    row.pack(fill=tk.X)
    tk.Label(
        row,
        text="后端：",
        font=("Microsoft YaHei", 8),
        bg=owner.theme_bg,
        fg=owner.theme_toolbar_muted,
    ).pack(side=tk.LEFT)
    backend_var = tk.StringVar(value=_backend_label_of(default_backend))
    combo = ttk.Combobox(
        row,
        textvariable=backend_var,
        values=[label for _key, label in DATA_BACKEND_CHOICES],
        state="readonly",
        width=10,
    )
    combo.pack(side=tk.LEFT, padx=(4, 0))
    try:
        combo.focus_set()
    except tk.TclError:
        pass

    prefix_row = tk.Frame(body, bg=owner.theme_bg)
    prefix_row.pack(fill=tk.X, pady=(10, 0))
    tk.Label(
        prefix_row,
        text="前缀：",
        font=("Microsoft YaHei", 8),
        bg=owner.theme_bg,
        fg=owner.theme_toolbar_muted,
    ).pack(side=tk.LEFT)
    prefix_var = tk.StringVar(value=default_prefix)
    prefix_entry = tk.Entry(
        prefix_row,
        textvariable=prefix_var,
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
    prefix_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(4, 0), ipady=2)

    remember_var = tk.BooleanVar(value=True)
    tk.Checkbutton(
        body,
        text="记住为当前项目默认后端",
        variable=remember_var,
        onvalue=True,
        offvalue=False,
        bg=owner.theme_bg,
        fg=owner.theme_fg,
        activebackground=owner.theme_bg,
        activeforeground="#FFFFFF",
        selectcolor=owner.theme_panel_inner_bg,
        font=("Microsoft YaHei", 8),
        anchor="w",
    ).pack(fill=tk.X, pady=(10, 0))
    remember_prefix_var = tk.BooleanVar(value=True)
    tk.Checkbutton(
        body,
        text="记住为默认导出前缀",
        variable=remember_prefix_var,
        onvalue=True,
        offvalue=False,
        bg=owner.theme_bg,
        fg=owner.theme_fg,
        activebackground=owner.theme_bg,
        activeforeground="#FFFFFF",
        selectcolor=owner.theme_panel_inner_bg,
        font=("Microsoft YaHei", 8),
        anchor="w",
    ).pack(fill=tk.X, pady=(4, 0))

    action = tk.Frame(body, bg=owner.theme_bg)
    action.pack(fill=tk.X, pady=(14, 0))

    def _close(ok):
        result["ok"] = bool(ok)
        result["backend"] = _backend_key_from_label(backend_var.get())
        result["remember"] = bool(remember_var.get())
        result["prefix"] = _normalize_layer_export_prefix(prefix_var.get(), fallback=default_prefix)
        result["remember_prefix"] = bool(remember_prefix_var.get())
        try:
            dialog.destroy()
        except tk.TclError:
            pass

    tk.Button(
        action,
        text="取消",
        command=lambda: _close(False),
        font=("Microsoft YaHei", 8),
        bg=owner.theme_toolbar_group_bg,
        fg=owner.theme_toolbar_fg,
        activebackground=owner.theme_toolbar_hover,
        activeforeground="#FFFFFF",
        relief="flat",
        bd=0,
        padx=10,
        pady=3,
        cursor="hand2",
    ).pack(side=tk.RIGHT)
    tk.Button(
        action,
        text="开始导出",
        command=lambda: _close(True),
        font=("Microsoft YaHei", 8),
        bg="#0E639C",
        fg="#FFFFFF",
        activebackground="#1577B8",
        activeforeground="#FFFFFF",
        relief="flat",
        bd=0,
        padx=12,
        pady=3,
        cursor="hand2",
    ).pack(side=tk.RIGHT, padx=(0, 6))

    # 按内容自动计算弹窗尺寸，解决高 DPI/大字体时按钮看不见的问题。
    try:
        owner.root.update_idletasks()
        dialog.update_idletasks()
        req_w = max(500, int(dialog.winfo_reqwidth()) + 24)
        req_h = max(350, int(dialog.winfo_reqheight()) + 24)
        max_w = max(480, int(dialog.winfo_screenwidth()) - 80)
        max_h = max(320, int(dialog.winfo_screenheight()) - 120)
        final_w = min(req_w, max_w)
        final_h = min(req_h, max_h)
        x = int(owner.root.winfo_x() + max(0, (owner.root.winfo_width() - final_w) / 2))
        y = int(owner.root.winfo_y() + max(0, (owner.root.winfo_height() - final_h) / 2))
        dialog.geometry(f"{final_w}x{final_h}+{x}+{y}")
    except Exception:
        pass

    dialog.bind("<Return>", lambda _e: _close(True), add="+")
    dialog.bind("<Escape>", lambda _e: _close(False), add="+")
    dialog.protocol("WM_DELETE_WINDOW", lambda: _close(False))
    owner.root.wait_window(dialog)
    if not result["ok"]:
        return None
    return {
        "backend": _normalize_data_backend(result["backend"]),
        "remember": bool(result["remember"]),
        "prefix": _normalize_layer_export_prefix(result.get("prefix"), fallback=default_prefix),
        "remember_prefix": bool(result.get("remember_prefix")),
    }


def _editable_property_keys(kind):
    key = str(kind or "")
    default_keys = PROPERTY_EDITABLE_KEYS_BY_KIND.get("default", set())
    custom_keys = PROPERTY_EDITABLE_KEYS_BY_KIND.get(key)
    if custom_keys is None:
        return set(default_keys)
    return set(custom_keys)


def _set_property_hint_text(owner, text):
    hint_var = getattr(owner, "_ui_designer_prop_hint_var", None)
    if hint_var is None:
        return
    try:
        hint_var.set(str(text or ""))
    except Exception:
        pass


def _apply_property_field_state(owner, kind):
    widgets = getattr(owner, "_ui_designer_prop_widgets", None)
    if not isinstance(widgets, dict):
        return
    editable = set() if kind is None else _editable_property_keys(kind)
    for key, meta in widgets.items():
        if not isinstance(meta, dict):
            continue
        entry = meta.get("entry")
        if entry is None:
            continue
        readonly = bool(meta.get("readonly"))
        if readonly:
            next_state = "readonly"
        elif key in editable:
            next_state = "normal"
        else:
            next_state = "disabled"
        try:
            entry.configure(state=next_state)
        except tk.TclError:
            continue


def _resolve_quick_start_scene(scene_key):
    key = str(scene_key or "").strip().lower()
    if key == "query":
        return {
            "key": "query",
            "title": "查询表格",
            "window": {"text": "数据查询", "w": 980, "h": 660},
            "components": [
                {"kind": "文字", "name": "关键词标签", "text": "关键词", "x": 120, "y": 120, "w": 100, "h": 34},
                {"kind": "输入框", "name": "关键词输入", "text": "请输入关键词", "x": 220, "y": 118, "w": 300, "h": 36},
                {"kind": "按钮", "name": "查询按钮", "text": "查询", "event": "执行查询", "x": 540, "y": 116, "w": 120, "h": 40},
                {
                    "kind": "表格",
                    "name": "结果表格",
                    "text": "查询结果",
                    "columns": "编号,名称,说明",
                    "rows": 10,
                    "x": 120,
                    "y": 180,
                    "w": 780,
                    "h": 360,
                },
            ],
        }
    if key == "form":
        return {
            "key": "form",
            "title": "录入表单",
            "window": {"text": "信息录入", "w": 900, "h": 620},
            "components": [
                {"kind": "文字", "name": "姓名标签", "text": "姓名", "x": 140, "y": 140, "w": 100, "h": 34},
                {"kind": "输入框", "name": "姓名输入", "text": "请输入姓名", "x": 240, "y": 138, "w": 300, "h": 36},
                {"kind": "文字", "name": "手机标签", "text": "手机号", "x": 140, "y": 196, "w": 100, "h": 34},
                {"kind": "输入框", "name": "手机输入", "text": "请输入手机号", "x": 240, "y": 194, "w": 300, "h": 36},
                {"kind": "按钮", "name": "提交按钮", "text": "提交", "event": "提交表单", "x": 240, "y": 260, "w": 140, "h": 42},
            ],
        }
    return {
        "key": "blank",
        "title": "空白窗口",
        "window": {"text": "我的窗口", "w": 960, "h": 640},
        "components": [],
    }


def _new_component_from_scene_spec(owner, spec):
    kind = str(spec.get("kind", "文字"))
    if kind not in COMPONENT_KIND_SET:
        kind = "文字"
    comp = _new_component(
        owner,
        kind,
        x=_to_int(spec.get("x", 120), 120),
        y=_to_int(spec.get("y", 90), 90),
    )
    for key in ("text", "event", "action_text", "columns"):
        if key in spec:
            comp[key] = str(spec.get(key, comp.get(key, "")))
    if "name" in spec:
        wanted_name = _sanitize_identifier(spec.get("name", ""), comp.get("name", ""))
        if wanted_name:
            existing = {
                str(item.get("name", ""))
                for item in list(getattr(owner, "_ui_designer_components", []) or [])
            }
            name = wanted_name
            seq = 2
            while name in existing:
                name = f"{wanted_name}_{seq}"
                seq += 1
            comp["name"] = name
    if "rows" in spec:
        comp["rows"] = max(3, _to_int(spec.get("rows", comp.get("rows", 8)), comp.get("rows", 8)))
    min_w = 360 if kind == WINDOW_COMPONENT_KIND else 60
    min_h = 240 if kind == WINDOW_COMPONENT_KIND else 24
    comp["w"] = _clamp(_to_int(spec.get("w", comp.get("w", 180)), comp.get("w", 180)), min_w, CANVAS_REGION_W)
    comp["h"] = _clamp(_to_int(spec.get("h", comp.get("h", 36)), comp.get("h", 36)), min_h, CANVAS_REGION_H)
    max_x = max(0, CANVAS_REGION_W - _to_int(comp.get("w", 180), 180))
    max_y = max(0, CANVAS_REGION_H - _to_int(comp.get("h", 36), 36))
    comp["x"] = _clamp(_to_int(spec.get("x", comp.get("x", 0)), comp.get("x", 0)), 0, max_x)
    comp["y"] = _clamp(_to_int(spec.get("y", comp.get("y", 0)), comp.get("y", 0)), 0, max_y)
    return comp


def _apply_quick_start_scene(owner, scene_key, clear_existing=True):
    _ensure_component_baseline(owner)
    scene = _resolve_quick_start_scene(scene_key)
    window_comp = _ensure_window_component(owner)
    if clear_existing:
        owner._ui_designer_components = [window_comp]
    window_cfg = scene.get("window", {}) or {}
    window_comp["text"] = str(window_cfg.get("text", window_comp.get("text", "我的窗口"))).strip() or "我的窗口"
    window_comp["w"] = _clamp(_to_int(window_cfg.get("w", window_comp.get("w", 960)), 960), 360, CANVAS_REGION_W)
    window_comp["h"] = _clamp(_to_int(window_cfg.get("h", window_comp.get("h", 640)), 640), 240, CANVAS_REGION_H)

    created = []
    for spec in list(scene.get("components", []) or []):
        comp = _new_component_from_scene_spec(owner, spec)
        owner._ui_designer_components.append(comp)
        created.append(comp)

    owner._ui_designer_selected_uid = int((created[0] if created else window_comp).get("uid", 0))
    _render_canvas(owner)
    _refresh_property_panel(owner)
    if hasattr(owner, "status_main_var"):
        suffix = "并清空旧组件" if clear_existing else "并保留已有组件"
        owner.status_main_var.set(f"界面设计器：已应用一键起步 - {scene.get('title', '空白窗口')}（{suffix}）")
    return "break"


def _prompt_quick_start_scene(owner):
    _ensure_state(owner)
    result = {"ok": False, "scene": "form", "clear": True}

    dialog = tk.Toplevel(owner.root)
    dialog.title("一键起步")
    dialog.transient(owner.root)
    dialog.configure(bg=owner.theme_bg)
    try:
        dialog.resizable(False, False)
    except tk.TclError:
        pass
    try:
        dialog.grab_set()
    except tk.TclError:
        pass

    body = tk.Frame(dialog, bg=owner.theme_bg, padx=14, pady=12)
    body.pack(fill=tk.BOTH, expand=True)
    tk.Label(
        body,
        text="选择一个基础场景，先生成可运行页面骨架，再改细节。",
        font=("Microsoft YaHei", 9, "bold"),
        bg=owner.theme_bg,
        fg="#DFE6EE",
        anchor="w",
    ).pack(fill=tk.X, pady=(0, 8))

    scene_var = tk.StringVar(value="form")
    for scene in QUICK_START_SCENES:
        row = tk.Frame(body, bg=owner.theme_bg)
        row.pack(fill=tk.X, pady=(0, 6))
        tk.Radiobutton(
            row,
            text=f"{scene['title']}：{scene['desc']}",
            variable=scene_var,
            value=scene["key"],
            bg=owner.theme_bg,
            fg=owner.theme_fg,
            activebackground=owner.theme_bg,
            activeforeground="#FFFFFF",
            selectcolor=owner.theme_panel_inner_bg,
            font=("Microsoft YaHei", 8),
            anchor="w",
            justify="left",
        ).pack(fill=tk.X)

    clear_var = tk.BooleanVar(value=True)
    tk.Checkbutton(
        body,
        text="应用前清空当前组件（窗口保留）",
        variable=clear_var,
        onvalue=True,
        offvalue=False,
        bg=owner.theme_bg,
        fg=owner.theme_fg,
        activebackground=owner.theme_bg,
        activeforeground="#FFFFFF",
        selectcolor=owner.theme_panel_inner_bg,
        font=("Microsoft YaHei", 8),
        anchor="w",
    ).pack(fill=tk.X, pady=(8, 0))

    action = tk.Frame(body, bg=owner.theme_bg)
    action.pack(fill=tk.X, pady=(14, 0))

    def _close(ok):
        result["ok"] = bool(ok)
        result["scene"] = str(scene_var.get() or "form")
        result["clear"] = bool(clear_var.get())
        try:
            dialog.destroy()
        except tk.TclError:
            pass

    tk.Button(
        action,
        text="取消",
        command=lambda: _close(False),
        font=("Microsoft YaHei", 8),
        bg=owner.theme_toolbar_group_bg,
        fg=owner.theme_toolbar_fg,
        activebackground=owner.theme_toolbar_hover,
        activeforeground="#FFFFFF",
        relief="flat",
        bd=0,
        padx=10,
        pady=3,
        cursor="hand2",
    ).pack(side=tk.RIGHT)
    tk.Button(
        action,
        text="开始生成",
        command=lambda: _close(True),
        font=("Microsoft YaHei", 8),
        bg="#0E639C",
        fg="#FFFFFF",
        activebackground="#1577B8",
        activeforeground="#FFFFFF",
        relief="flat",
        bd=0,
        padx=12,
        pady=3,
        cursor="hand2",
    ).pack(side=tk.RIGHT, padx=(0, 6))

    # 依据内容自动计算弹窗大小，避免高 DPI 或大字体时按钮被截断。
    try:
        owner.root.update_idletasks()
        dialog.update_idletasks()
        req_w = max(460, int(dialog.winfo_reqwidth()) + 24)
        req_h = max(320, int(dialog.winfo_reqheight()) + 24)
        x = int(owner.root.winfo_x() + max(0, (owner.root.winfo_width() - req_w) / 2))
        y = int(owner.root.winfo_y() + max(0, (owner.root.winfo_height() - req_h) / 2))
        dialog.geometry(f"{req_w}x{req_h}+{x}+{y}")
    except Exception:
        pass

    dialog.bind("<Return>", lambda _e: _close(True), add="+")
    dialog.bind("<Escape>", lambda _e: _close(False), add="+")
    dialog.protocol("WM_DELETE_WINDOW", lambda: _close(False))
    owner.root.wait_window(dialog)
    if not result["ok"]:
        return None
    return {"scene": result["scene"], "clear": bool(result["clear"])}


def run_ui_designer_quick_start(owner, event=None):
    del event
    choice = _prompt_quick_start_scene(owner)
    if not choice:
        if hasattr(owner, "status_main_var"):
            owner.status_main_var.set("界面设计器：已取消一键起步")
        return "break"
    return _apply_quick_start_scene(owner, choice.get("scene"), clear_existing=bool(choice.get("clear", True)))


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
    if not hasattr(owner, "_ui_designer_resize"):
        owner._ui_designer_resize = {
            "uid": None,
            "anchor": "",
            "start_x": 0,
            "start_y": 0,
            "x": 0,
            "y": 0,
            "w": 0,
            "h": 0,
        }
    if not hasattr(owner, "_ui_designer_data_backend"):
        owner._ui_designer_data_backend = "sqlite"
    owner._ui_designer_data_backend = _normalize_data_backend(getattr(owner, "_ui_designer_data_backend", "sqlite"))
    if not hasattr(owner, "_ui_designer_backend_vars"):
        owner._ui_designer_backend_vars = []
    if not hasattr(owner, "_ui_designer_layer_export_prefix"):
        owner._ui_designer_layer_export_prefix = "界面设计"
    if not hasattr(owner, "_ui_designer_prop_widgets"):
        owner._ui_designer_prop_widgets = {}
    if not hasattr(owner, "_ui_designer_prop_hint_var"):
        owner._ui_designer_prop_hint_var = None
    if not hasattr(owner, "_ui_designer_palette_kind_map"):
        owner._ui_designer_palette_kind_map = {}
    owner._ui_designer_layer_export_prefix = _normalize_layer_export_prefix(
        getattr(owner, "_ui_designer_layer_export_prefix", "界面设计")
    )


def _find_first_component_by_kind(owner, kind):
    _ensure_state(owner)
    target = str(kind or "")
    for item in owner._ui_designer_components:
        if str(item.get("kind", "")) == target:
            return item
    return None


def _ensure_window_component(owner):
    exists = _find_first_component_by_kind(owner, WINDOW_COMPONENT_KIND)
    if exists is not None:
        return exists
    comp = _new_component(owner, WINDOW_COMPONENT_KIND)
    owner._ui_designer_components.insert(0, comp)
    return comp


def _ensure_component_baseline(owner):
    _ensure_state(owner)
    window_comp = _ensure_window_component(owner)
    if getattr(owner, "_ui_designer_selected_uid", None) is None:
        owner._ui_designer_selected_uid = int(window_comp.get("uid", 0))


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
    catalog_map = _catalog_map()
    base = catalog_map.get(kind, {"w": 180, "h": 34, "text": kind})
    uid = _next_uid(owner)
    name = f"{kind}{uid}"
    default_x = _to_int(base.get("x", x), x)
    default_y = _to_int(base.get("y", y), y)
    return {
        "uid": uid,
        "kind": kind,
        "name": name,
        "text": str(base.get("text", kind)),
        "x": default_x,
        "y": default_y,
        "w": max(80, _to_int(base.get("w", 180), 180)),
        "h": max(28, _to_int(base.get("h", 34), 34)),
        "event": str(base.get("event", "")),
        "action_text": str(base.get("action_text", "")),
        "columns": str(base.get("columns", "列1,列2")),
        "rows": max(3, _to_int(base.get("rows", 8), 8)),
    }


def _find_component(owner, uid):
    _ensure_state(owner)
    target_uid = _to_int(uid, -1)
    if target_uid < 0:
        return None
    for item in owner._ui_designer_components:
        if _to_int(item.get("uid", -1), -1) == target_uid:
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
    if kind == WINDOW_COMPONENT_KIND:
        return {"fill": "#0F1726", "text": "#DCE8F7"}
    if kind in BUTTON_COMPONENT_KINDS:
        return {"fill": "#154E7A", "text": "#FFFFFF"}
    if kind in INPUT_COMPONENT_KINDS:
        return {"fill": "#1A2433", "text": "#D8E0EA"}
    if kind in TABLE_COMPONENT_KINDS:
        return {"fill": "#1D2A3C", "text": "#DCE7F5"}
    if kind in CARD_COMPONENT_KINDS:
        return {"fill": "#1A2230", "text": "#DCE7F5"}
    if kind in {"登录模板", "列表模板"}:
        return {"fill": "#1D2738", "text": "#DCE7F5"}
    if kind in TEXT_COMPONENT_KINDS:
        return {"fill": "#223144", "text": "#DCE7F5"}
    return {"fill": "#223144", "text": "#DCE7F5"}


def _preview_text(raw, fallback="", limit=18):
    text = str(raw or "").strip().replace("\n", " ")
    if not text:
        text = str(fallback or "")
    if len(text) > max(4, int(limit)):
        return text[: max(3, int(limit) - 1)] + "…"
    return text


def _draw_component_preview(canvas, kind, x, y, x2, y2, text, colors, tag):
    tags = ("component", tag)
    items = []
    w = max(1, x2 - x)
    h = max(1, y2 - y)
    label = _preview_text(text, fallback=kind, limit=22)

    if w < 36 or h < 24:
        items.append(
            canvas.create_text(
                x + 6,
                y + 6,
                text=label,
                fill=colors["text"],
                anchor="nw",
                font=("Microsoft YaHei", 8),
                tags=tags,
            )
        )
        return items

    left = x + 8
    top = y + 26
    right = x2 - 8
    bottom = y2 - 8
    if right <= left or bottom <= top:
        items.append(
            canvas.create_text(
                x + 8,
                y + max(20, int(h / 2)),
                text=label,
                fill=colors["text"],
                anchor="w",
                font=("Microsoft YaHei", 9),
                tags=tags,
            )
        )
        return items

    if kind == WINDOW_COMPONENT_KIND:
        title_h = min(32, max(24, int(h * 0.12)))
        items.append(
            canvas.create_rectangle(
                left,
                top,
                right,
                top + title_h,
                fill="#1E2C43",
                outline="#304766",
                width=1,
                tags=tags,
            )
        )
        items.append(
            canvas.create_rectangle(
                left,
                top + title_h,
                right,
                bottom,
                fill="#0A1930",
                outline="#304766",
                width=1,
                tags=tags,
            )
        )
        items.append(
            canvas.create_text(
                left + 8,
                top + int(title_h / 2),
                text=label,
                fill="#E8F2FF",
                anchor="w",
                font=("Microsoft YaHei", 9, "bold"),
                tags=tags,
            )
        )
        return items

    if kind == "登录模板":
        items.append(canvas.create_rectangle(left, top, right, bottom, fill="#1A2538", outline="#354D70", width=1, tags=tags))
        line_h = max(16, int((bottom - top) * 0.18))
        items.append(canvas.create_rectangle(left + 10, top + 28, right - 10, top + 28 + line_h, fill="#0E1726", outline="#48658C", width=1, tags=tags))
        items.append(canvas.create_rectangle(left + 10, top + 28 + line_h + 8, right - 10, top + 28 + line_h * 2 + 8, fill="#0E1726", outline="#48658C", width=1, tags=tags))
        items.append(canvas.create_rectangle(left + 10, bottom - line_h - 10, right - 10, bottom - 10, fill="#1E71B8", outline="#5FB2FF", width=1, tags=tags))
        items.append(canvas.create_text(left + 12, top + 10, text=label, fill="#DCE8F7", anchor="nw", font=("Microsoft YaHei", 9, "bold"), tags=tags))
        return items

    if kind == "列表模板":
        items.append(canvas.create_rectangle(left, top, right, bottom, fill="#1A2538", outline="#354D70", width=1, tags=tags))
        head_h = max(20, int((bottom - top) * 0.18))
        items.append(canvas.create_rectangle(left + 10, top + 8, right - 86, top + 8 + head_h, fill="#0E1726", outline="#48658C", width=1, tags=tags))
        items.append(canvas.create_rectangle(right - 74, top + 8, right - 10, top + 8 + head_h, fill="#1E71B8", outline="#5FB2FF", width=1, tags=tags))
        table_top = top + head_h + 18
        items.append(canvas.create_rectangle(left + 10, table_top, right - 10, bottom - 10, fill="#111B2A", outline="#48658C", width=1, tags=tags))
        for row in range(1, 4):
            ly = table_top + int((bottom - 10 - table_top) * row / 4)
            items.append(canvas.create_line(left + 10, ly, right - 10, ly, fill="#344A67", width=1, tags=tags))
        items.append(canvas.create_text(left + 12, top + 10, text=label, fill="#DCE8F7", anchor="nw", font=("Microsoft YaHei", 9, "bold"), tags=tags))
        return items

    if kind in BUTTON_COMPONENT_KINDS:
        center_y = top + int((bottom - top) / 2)
        if kind == "复选框":
            box = max(12, min(18, bottom - top - 6))
            bx = left + 6
            by = center_y - int(box / 2)
            items.append(canvas.create_rectangle(bx, by, bx + box, by + box, fill="#0F1726", outline="#7FB1E8", width=1, tags=tags))
            items.append(canvas.create_line(bx + 3, by + int(box * 0.55), bx + int(box * 0.45), by + box - 3, fill="#8FD4FF", width=2, tags=tags))
            items.append(canvas.create_line(bx + int(box * 0.45), by + box - 3, bx + box - 2, by + 3, fill="#8FD4FF", width=2, tags=tags))
            items.append(canvas.create_text(bx + box + 8, center_y, text=label, fill="#E4F0FF", anchor="w", font=("Microsoft YaHei", 9), tags=tags))
            return items
        if kind == "单选按钮":
            r = max(6, min(9, int((bottom - top) / 3)))
            cx = left + 10 + r
            cy = center_y
            items.append(canvas.create_oval(cx - r, cy - r, cx + r, cy + r, fill="#0F1726", outline="#7FB1E8", width=1, tags=tags))
            items.append(canvas.create_oval(cx - 3, cy - 3, cx + 3, cy + 3, fill="#8FD4FF", outline="#8FD4FF", width=1, tags=tags))
            items.append(canvas.create_text(cx + r + 8, center_y, text=label, fill="#E4F0FF", anchor="w", font=("Microsoft YaHei", 9), tags=tags))
            return items
        items.append(canvas.create_rectangle(left + 6, top + 6, right - 6, bottom - 6, fill="#1E71B8", outline="#67B9FF", width=1, tags=tags))
        items.append(canvas.create_text((left + right) / 2, (top + bottom) / 2, text=label, fill="#FFFFFF", anchor="c", font=("Microsoft YaHei", 9, "bold"), tags=tags))
        return items

    if kind in INPUT_COMPONENT_KINDS:
        if kind == "数值滑块":
            ly = top + int((bottom - top) / 2)
            items.append(canvas.create_line(left + 10, ly, right - 10, ly, fill="#84A7CF", width=3, tags=tags))
            knob_x = left + int((right - left) * 0.62)
            items.append(canvas.create_oval(knob_x - 6, ly - 6, knob_x + 6, ly + 6, fill="#5FB2FF", outline="#BCE4FF", width=1, tags=tags))
            items.append(canvas.create_text(left + 4, top + 2, text=label, fill="#CFDFF3", anchor="nw", font=("Microsoft YaHei", 8), tags=tags))
            return items

        if kind == "多行文本框":
            items.append(canvas.create_rectangle(left + 4, top + 4, right - 4, bottom - 4, fill="#0E1726", outline="#4E6C93", width=1, tags=tags))
            for row in range(1, 4):
                ly = top + 8 + row * max(12, int((bottom - top - 16) / 4))
                items.append(canvas.create_line(left + 10, ly, right - 10, ly, fill="#2C3F5A", width=1, tags=tags))
            items.append(canvas.create_text(left + 10, top + 10, text=label, fill="#AFC4DD", anchor="nw", font=("Microsoft YaHei", 8), tags=tags))
            return items

        entry_h = max(18, min(28, bottom - top - 8))
        entry_y = top + int((bottom - top - entry_h) / 2)
        items.append(canvas.create_rectangle(left + 4, entry_y, right - 4, entry_y + entry_h, fill="#0E1726", outline="#4E6C93", width=1, tags=tags))
        items.append(canvas.create_text(left + 10, entry_y + int(entry_h / 2), text=label, fill="#AFC4DD", anchor="w", font=("Microsoft YaHei", 8), tags=tags))

        if kind == "组合框":
            arrow_w = max(18, min(24, int((right - left) * 0.18)))
            items.append(canvas.create_rectangle(right - 4 - arrow_w, entry_y, right - 4, entry_y + entry_h, fill="#1E2F47", outline="#4E6C93", width=1, tags=tags))
            cx = right - 4 - int(arrow_w / 2)
            cy = entry_y + int(entry_h / 2)
            items.append(canvas.create_polygon(cx - 4, cy - 2, cx + 4, cy - 2, cx, cy + 3, fill="#9DC8F5", outline="", tags=tags))
        elif kind == "日期选择器":
            icon_w = max(18, min(24, int((right - left) * 0.2)))
            items.append(canvas.create_rectangle(right - 4 - icon_w, entry_y, right - 4, entry_y + entry_h, fill="#1E2F47", outline="#4E6C93", width=1, tags=tags))
            ix = right - 4 - icon_w + 4
            iy = entry_y + 4
            items.append(canvas.create_rectangle(ix, iy, right - 8, entry_y + entry_h - 4, fill="#2A3C58", outline="#87B8EF", width=1, tags=tags))
            items.append(canvas.create_line(ix, iy + 5, right - 8, iy + 5, fill="#87B8EF", width=1, tags=tags))
        elif kind == "数值框":
            ctl_w = max(16, min(22, int((right - left) * 0.16)))
            items.append(canvas.create_rectangle(right - 4 - ctl_w, entry_y, right - 4, entry_y + int(entry_h / 2), fill="#1E2F47", outline="#4E6C93", width=1, tags=tags))
            items.append(canvas.create_rectangle(right - 4 - ctl_w, entry_y + int(entry_h / 2), right - 4, entry_y + entry_h, fill="#1E2F47", outline="#4E6C93", width=1, tags=tags))
            cx = right - 4 - int(ctl_w / 2)
            items.append(canvas.create_polygon(cx - 3, entry_y + int(entry_h / 4) + 2, cx + 3, entry_y + int(entry_h / 4) + 2, cx, entry_y + int(entry_h / 4) - 2, fill="#9DC8F5", outline="", tags=tags))
            items.append(canvas.create_polygon(cx - 3, entry_y + int(entry_h * 3 / 4) - 2, cx + 3, entry_y + int(entry_h * 3 / 4) - 2, cx, entry_y + int(entry_h * 3 / 4) + 2, fill="#9DC8F5", outline="", tags=tags))
        return items

    if kind in TABLE_COMPONENT_KINDS:
        table_left = left + 4
        table_top = top + 4
        table_right = right - 4
        table_bottom = bottom - 4
        header_h = max(18, min(24, int((table_bottom - table_top) * 0.2)))
        items.append(canvas.create_rectangle(table_left, table_top, table_right, table_bottom, fill="#111B2A", outline="#48658C", width=1, tags=tags))
        items.append(canvas.create_rectangle(table_left, table_top, table_right, table_top + header_h, fill="#24384F", outline="#48658C", width=1, tags=tags))
        col_count = 1 if kind == "列表框" else 3
        for c in range(1, col_count):
            lx = table_left + int((table_right - table_left) * c / col_count)
            items.append(canvas.create_line(lx, table_top, lx, table_bottom, fill="#35506F", width=1, tags=tags))
        row_count = 4
        for r in range(1, row_count):
            ly = table_top + header_h + int((table_bottom - table_top - header_h) * r / row_count)
            items.append(canvas.create_line(table_left, ly, table_right, ly, fill="#2E445F", width=1, tags=tags))
        if kind == "树形视图":
            base_y = table_top + header_h + 8
            items.append(canvas.create_line(table_left + 12, base_y, table_left + 12, min(table_bottom - 8, base_y + 36), fill="#7AA9D6", width=1, tags=tags))
            items.append(canvas.create_line(table_left + 12, base_y + 12, table_left + 24, base_y + 12, fill="#7AA9D6", width=1, tags=tags))
            items.append(canvas.create_line(table_left + 12, base_y + 24, table_left + 24, base_y + 24, fill="#7AA9D6", width=1, tags=tags))
        return items

    if kind in CARD_COMPONENT_KINDS:
        if kind == "进度条":
            track_h = max(12, min(16, int((bottom - top) * 0.28)))
            ly = top + int((bottom - top - track_h) / 2)
            items.append(canvas.create_rectangle(left + 4, ly, right - 4, ly + track_h, fill="#0F1726", outline="#55779F", width=1, tags=tags))
            fill_w = max(20, int((right - left - 10) * 0.55))
            items.append(canvas.create_rectangle(left + 5, ly + 1, left + 5 + fill_w, ly + track_h - 1, fill="#2F7FE3", outline="#2F7FE3", width=1, tags=tags))
            items.append(canvas.create_text((left + right) / 2, ly + int(track_h / 2), text=label, fill="#E4F0FF", anchor="c", font=("Microsoft YaHei", 8), tags=tags))
            return items

        if kind == "图片框":
            items.append(canvas.create_rectangle(left + 4, top + 4, right - 4, bottom - 4, fill="#0E1726", outline="#4E6C93", width=1, tags=tags))
            items.append(canvas.create_line(left + 8, bottom - 8, right - 8, top + 8, fill="#8AB8E8", width=1, tags=tags))
            items.append(canvas.create_line(left + 8, top + 8, right - 8, bottom - 8, fill="#8AB8E8", width=1, tags=tags))
            items.append(canvas.create_text((left + right) / 2, bottom - 14, text=label, fill="#AFC4DD", anchor="c", font=("Microsoft YaHei", 8), tags=tags))
            return items

        if kind == "分组框":
            group_top = top + 10
            items.append(canvas.create_rectangle(left + 4, group_top, right - 4, bottom - 4, fill="#142236", outline="#4E6C93", width=1, tags=tags))
            items.append(canvas.create_text(left + 12, top + 6, text=label, fill="#9FC7F3", anchor="w", font=("Microsoft YaHei", 8, "bold"), tags=tags))
            return items

        if kind == "选项卡":
            tab_h = max(16, min(22, int((bottom - top) * 0.22)))
            items.append(canvas.create_rectangle(left + 4, top + tab_h + 2, right - 4, bottom - 4, fill="#111B2A", outline="#4E6C93", width=1, tags=tags))
            items.append(canvas.create_rectangle(left + 8, top + 4, left + 70, top + tab_h, fill="#2B4362", outline="#6DAEE8", width=1, tags=tags))
            items.append(canvas.create_rectangle(left + 72, top + 6, left + 132, top + tab_h, fill="#1A2A40", outline="#4E6C93", width=1, tags=tags))
            items.append(canvas.create_text(left + 14, top + int(tab_h / 2) + 1, text="选项1", fill="#E4F0FF", anchor="w", font=("Microsoft YaHei", 8), tags=tags))
            items.append(canvas.create_text(left + 78, top + int(tab_h / 2) + 1, text="选项2", fill="#9FB4CF", anchor="w", font=("Microsoft YaHei", 8), tags=tags))
            return items

        if kind == "分割容器":
            items.append(canvas.create_rectangle(left + 4, top + 4, right - 4, bottom - 4, fill="#111B2A", outline="#4E6C93", width=1, tags=tags))
            mid = left + int((right - left) / 2)
            items.append(canvas.create_line(mid, top + 8, mid, bottom - 8, fill="#6DAEE8", width=2, tags=tags))
            items.append(canvas.create_text(left + 12, top + 10, text=label, fill="#AFC4DD", anchor="nw", font=("Microsoft YaHei", 8), tags=tags))
            return items

        if kind == "表格布局面板":
            items.append(canvas.create_rectangle(left + 4, top + 4, right - 4, bottom - 4, fill="#111B2A", outline="#4E6C93", width=1, tags=tags))
            for c in range(1, 4):
                lx = left + 4 + int((right - left - 8) * c / 4)
                items.append(canvas.create_line(lx, top + 4, lx, bottom - 4, fill="#38516F", width=1, tags=tags))
            for r in range(1, 3):
                ly = top + 4 + int((bottom - top - 8) * r / 3)
                items.append(canvas.create_line(left + 4, ly, right - 4, ly, fill="#38516F", width=1, tags=tags))
            items.append(canvas.create_text(left + 10, top + 10, text=label, fill="#AFC4DD", anchor="nw", font=("Microsoft YaHei", 8), tags=tags))
            return items

        if kind == "流式布局面板":
            items.append(canvas.create_rectangle(left + 4, top + 4, right - 4, bottom - 4, fill="#111B2A", outline="#4E6C93", width=1, tags=tags))
            chip_top = top + 10
            chip_x = left + 10
            for idx in range(4):
                chip_w = 40 + (idx % 2) * 16
                if chip_x + chip_w > right - 10:
                    chip_x = left + 10
                    chip_top += 20
                items.append(canvas.create_rectangle(chip_x, chip_top, chip_x + chip_w, chip_top + 14, fill="#2A4361", outline="#6FAEE6", width=1, tags=tags))
                chip_x += chip_w + 8
            items.append(canvas.create_text(left + 10, top + 10, text=label, fill="#AFC4DD", anchor="nw", font=("Microsoft YaHei", 8), tags=tags))
            return items

        items.append(canvas.create_rectangle(left + 4, top + 4, right - 4, bottom - 4, fill="#162338", outline="#4E6C93", width=1, tags=tags))
        items.append(canvas.create_rectangle(left + 4, top + 4, right - 4, top + 24, fill="#23374F", outline="#4E6C93", width=1, tags=tags))
        items.append(canvas.create_text(left + 10, top + 14, text=label, fill="#DCE8F7", anchor="w", font=("Microsoft YaHei", 8, "bold"), tags=tags))
        return items

    if kind in TEXT_COMPONENT_KINDS:
        if kind == "菜单栏":
            items.append(canvas.create_rectangle(left + 4, top + 4, right - 4, top + 24, fill="#203247", outline="#48658C", width=1, tags=tags))
            items.append(canvas.create_text(left + 10, top + 14, text=label, fill="#E4F0FF", anchor="w", font=("Microsoft YaHei", 8), tags=tags))
            return items
        if kind == "工具栏":
            items.append(canvas.create_rectangle(left + 4, top + 4, right - 4, top + 26, fill="#1D2D44", outline="#48658C", width=1, tags=tags))
            ix = left + 10
            for _ in range(5):
                items.append(canvas.create_rectangle(ix, top + 9, ix + 10, top + 19, fill="#7FAEDA", outline="#9DCAEF", width=1, tags=tags))
                ix += 16
            return items
        if kind == "状态栏":
            bar_h = max(16, min(22, int((bottom - top) * 0.4)))
            items.append(canvas.create_rectangle(left + 4, bottom - bar_h - 4, right - 4, bottom - 4, fill="#1D2D44", outline="#48658C", width=1, tags=tags))
            items.append(canvas.create_text(left + 10, bottom - int(bar_h / 2) - 4, text=label, fill="#BBD4EF", anchor="w", font=("Microsoft YaHei", 8), tags=tags))
            return items
        items.append(canvas.create_text(left + 4, top + int((bottom - top) / 2), text=label, fill=colors["text"], anchor="w", font=("Microsoft YaHei", 10), tags=tags))
        return items

    items.append(canvas.create_text(left + 4, top + int((bottom - top) / 2), text=label, fill=colors["text"], anchor="w", font=("Microsoft YaHei", 9), tags=tags))
    return items


def _render_canvas(owner):
    _ensure_component_baseline(owner)
    canvas = getattr(owner, "_ui_designer_canvas", None)
    if canvas is None:
        return
    _draw_grid(owner)
    canvas.delete("component")
    selected_uid = getattr(owner, "_ui_designer_selected_uid", None)

    components = list(getattr(owner, "_ui_designer_components", []) or [])
    components.sort(
        key=lambda item: (
            0 if str(item.get("kind", "")) == WINDOW_COMPONENT_KIND else 1,
            _to_int(item.get("y", 0), 0),
            _to_int(item.get("x", 0), 0),
            _to_int(item.get("uid", 0), 0),
        )
    )

    for comp in components:
        uid = int(comp.get("uid", 0))
        tag = f"comp_{uid}"
        x = _clamp(_to_int(comp.get("x", 0), 0), 0, CANVAS_REGION_W - 20)
        y = _clamp(_to_int(comp.get("y", 0), 0), 0, CANVAS_REGION_H - 20)
        kind = str(comp.get("kind", "文字"))
        min_w = 360 if kind == WINDOW_COMPONENT_KIND else 60
        min_h = 240 if kind == WINDOW_COMPONENT_KIND else 24
        w = _clamp(_to_int(comp.get("w", 180), 180), min_w, CANVAS_REGION_W)
        h = _clamp(_to_int(comp.get("h", 36), 36), min_h, CANVAS_REGION_H)
        x2 = min(CANVAS_REGION_W, x + w)
        y2 = min(CANVAS_REGION_H, y + h)
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
        preview_item_ids = _draw_component_preview(canvas, kind, x, y, x2, y2, text, colors, tag)
        name_id = canvas.create_text(
            x2 - 8,
            y2 - 8,
            text=str(comp.get("name", f"控件{uid}")),
            fill="#8FA1B8",
            anchor="se",
            font=("Microsoft YaHei", 8),
            tags=("component", tag),
        )
        bind_item_ids = [rect_id, kind_badge, name_id]
        bind_item_ids.extend(list(preview_item_ids or []))
        for item_id in bind_item_ids:
            canvas.tag_bind(item_id, "<ButtonPress-1>", lambda e, target_uid=uid: _on_canvas_press(owner, e, target_uid))
            canvas.tag_bind(item_id, "<B1-Motion>", lambda e, target_uid=uid: _on_canvas_drag(owner, e, target_uid))
            canvas.tag_bind(item_id, "<ButtonRelease-1>", lambda e: _on_canvas_release(owner, e))

        # 选中组件显示缩放手柄：拖拽手柄可直接改宽高。
        if selected:
            hs = CANVAS_RESIZE_HANDLE
            handles = [
                ("nw", x, y),
                ("ne", x2, y),
                ("sw", x, y2),
                ("se", x2, y2),
            ]
            for anchor, hx, hy in handles:
                handle_id = canvas.create_rectangle(
                    hx - hs,
                    hy - hs,
                    hx + hs,
                    hy + hs,
                    fill="#4CA8FF",
                    outline="#BFE3FF",
                    width=1,
                    tags=("component", tag, "resize_handle"),
                )
                canvas.tag_bind(
                    handle_id,
                    "<ButtonPress-1>",
                    lambda e, target_uid=uid, target_anchor=anchor: _on_resize_press(owner, e, target_uid, target_anchor),
                )
                canvas.tag_bind(handle_id, "<B1-Motion>", lambda e, target_uid=uid: _on_resize_drag(owner, e, target_uid))
                canvas.tag_bind(handle_id, "<ButtonRelease-1>", lambda e: _on_canvas_release(owner, e))


def _refresh_property_panel(owner):
    _ensure_component_baseline(owner)
    comp = _selected_component(owner)
    info_var = getattr(owner, "_ui_designer_info_var", None)
    vars_map = getattr(owner, "_ui_designer_prop_vars", None)
    if info_var is None or not isinstance(vars_map, dict):
        return
    if comp is None:
        info_var.set("未选中组件")
        for key in ("name", "kind", "text", "event", "action_text", "columns", "rows", "x", "y", "w", "h"):
            if key in vars_map:
                vars_map[key].set("")
        _set_property_hint_text(owner, "先选中组件，再填写高亮字段。灰色字段表示当前组件不需要。")
        _apply_property_field_state(owner, None)
        return

    kind = str(comp.get("kind", ""))
    info_var.set(f"已选中：{comp.get('name', '')} ({kind})")
    vars_map["name"].set(str(comp.get("name", "")))
    vars_map["kind"].set(kind)
    vars_map["text"].set(str(comp.get("text", "")))
    vars_map["event"].set(str(comp.get("event", "")))
    if "action_text" in vars_map:
        vars_map["action_text"].set(str(comp.get("action_text", "")))
    vars_map["columns"].set(str(comp.get("columns", "")))
    vars_map["rows"].set(str(comp.get("rows", 8)))
    vars_map["x"].set(str(comp.get("x", 0)))
    vars_map["y"].set(str(comp.get("y", 0)))
    vars_map["w"].set(str(comp.get("w", 180)))
    vars_map["h"].set(str(comp.get("h", 36)))
    _set_property_hint_text(owner, PROPERTY_HINT_BY_KIND.get(kind, PROPERTY_HINT_BY_KIND["default"]))
    _apply_property_field_state(owner, kind)


def _select_component(owner, uid):
    selected_uid = _to_int(uid, -1)
    if selected_uid < 0:
        return
    owner._ui_designer_selected_uid = selected_uid
    _render_canvas(owner)
    _refresh_property_panel(owner)


def _on_canvas_press(owner, event, uid):
    canvas = getattr(owner, "_ui_designer_canvas", None)
    if canvas is None:
        return "break"
    target_uid = _to_int(uid, -1)
    if target_uid < 0:
        return "break"
    cx = _to_int(canvas.canvasx(event.x), 0)
    cy = _to_int(canvas.canvasy(event.y), 0)
    owner._ui_designer_resize = {
        "uid": None,
        "anchor": "",
        "start_x": 0,
        "start_y": 0,
        "x": 0,
        "y": 0,
        "w": 0,
        "h": 0,
    }
    owner._ui_designer_drag = {"uid": target_uid, "start_x": cx, "start_y": cy}
    owner._ui_designer_selected_uid = target_uid
    _refresh_property_panel(owner)
    return "break"


def _component_min_size(kind):
    if str(kind or "") == WINDOW_COMPONENT_KIND:
        return 360, 240
    return 60, 24


def _on_resize_press(owner, event, uid, anchor):
    canvas = getattr(owner, "_ui_designer_canvas", None)
    comp = _find_component(owner, uid)
    if canvas is None or comp is None:
        return "break"
    target_uid = _to_int(uid, -1)
    if target_uid < 0:
        return "break"
    cx = _to_int(canvas.canvasx(event.x), 0)
    cy = _to_int(canvas.canvasy(event.y), 0)
    owner._ui_designer_drag = {"uid": None, "start_x": 0, "start_y": 0}
    owner._ui_designer_resize = {
        "uid": target_uid,
        "anchor": str(anchor or "se"),
        "start_x": cx,
        "start_y": cy,
        "x": _to_int(comp.get("x", 0), 0),
        "y": _to_int(comp.get("y", 0), 0),
        "w": _to_int(comp.get("w", 180), 180),
        "h": _to_int(comp.get("h", 36), 36),
    }
    owner._ui_designer_selected_uid = target_uid
    _refresh_property_panel(owner)
    return "break"


def _on_resize_drag(owner, event, uid):
    canvas = getattr(owner, "_ui_designer_canvas", None)
    comp = _find_component(owner, uid)
    resize = getattr(owner, "_ui_designer_resize", {}) or {}
    target_uid = _to_int(uid, -1)
    resize_uid = _to_int(resize.get("uid", -1), -1)
    if canvas is None or comp is None or target_uid < 0 or resize_uid != target_uid:
        return "break"

    cx = _to_int(canvas.canvasx(event.x), resize.get("start_x", 0))
    cy = _to_int(canvas.canvasy(event.y), resize.get("start_y", 0))
    dx = cx - _to_int(resize.get("start_x", cx), cx)
    dy = cy - _to_int(resize.get("start_y", cy), cy)

    left0 = _to_int(resize.get("x", 0), 0)
    top0 = _to_int(resize.get("y", 0), 0)
    right0 = left0 + max(20, _to_int(resize.get("w", 180), 180))
    bottom0 = top0 + max(20, _to_int(resize.get("h", 36), 36))
    min_w, min_h = _component_min_size(comp.get("kind", ""))
    anchor = str(resize.get("anchor", "se") or "se")

    left = left0
    right = right0
    top = top0
    bottom = bottom0
    if "w" in anchor:
        left = _clamp(left0 + dx, 0, right0 - min_w)
    if "e" in anchor:
        right = _clamp(right0 + dx, left + min_w, CANVAS_REGION_W)
    if "n" in anchor:
        top = _clamp(top0 + dy, 0, bottom0 - min_h)
    if "s" in anchor:
        bottom = _clamp(bottom0 + dy, top + min_h, CANVAS_REGION_H)

    comp["x"] = _clamp(left, 0, CANVAS_REGION_W - min_w)
    comp["y"] = _clamp(top, 0, CANVAS_REGION_H - min_h)
    comp["w"] = _clamp(right - left, min_w, CANVAS_REGION_W)
    comp["h"] = _clamp(bottom - top, min_h, CANVAS_REGION_H)

    max_x = max(0, CANVAS_REGION_W - _to_int(comp.get("w", min_w), min_w))
    max_y = max(0, CANVAS_REGION_H - _to_int(comp.get("h", min_h), min_h))
    comp["x"] = _clamp(_to_int(comp.get("x", 0), 0), 0, max_x)
    comp["y"] = _clamp(_to_int(comp.get("y", 0), 0), 0, max_y)

    _render_canvas(owner)
    _refresh_property_panel(owner)
    return "break"


def _on_canvas_drag(owner, event, uid):
    canvas = getattr(owner, "_ui_designer_canvas", None)
    comp = _find_component(owner, uid)
    drag = getattr(owner, "_ui_designer_drag", {}) or {}
    resize = getattr(owner, "_ui_designer_resize", {}) or {}
    target_uid = _to_int(uid, -1)
    drag_uid = _to_int(drag.get("uid", -1), -1)
    resize_uid = _to_int(resize.get("uid", -1), -1)
    if canvas is None or comp is None or target_uid < 0 or drag_uid != target_uid or resize_uid == target_uid:
        return "break"
    cx = _to_int(canvas.canvasx(event.x), comp.get("x", 0))
    cy = _to_int(canvas.canvasy(event.y), comp.get("y", 0))
    dx = cx - _to_int(drag.get("start_x", cx), cx)
    dy = cy - _to_int(drag.get("start_y", cy), cy)
    comp_w = max(20, _to_int(comp.get("w", 180), 180))
    comp_h = max(20, _to_int(comp.get("h", 36), 36))
    max_x = max(0, CANVAS_REGION_W - comp_w)
    max_y = max(0, CANVAS_REGION_H - comp_h)
    comp["x"] = _clamp(_to_int(comp.get("x", 0)) + dx, 0, max_x)
    comp["y"] = _clamp(_to_int(comp.get("y", 0)) + dy, 0, max_y)
    owner._ui_designer_drag = {"uid": target_uid, "start_x": cx, "start_y": cy}
    _render_canvas(owner)
    _refresh_property_panel(owner)
    return "break"


def _on_canvas_background_press(owner, event=None):
    canvas = getattr(owner, "_ui_designer_canvas", None)
    if canvas is None:
        return None
    drag = getattr(owner, "_ui_designer_drag", {}) or {}
    resize = getattr(owner, "_ui_designer_resize", {}) or {}
    if _to_int(drag.get("uid", -1), -1) >= 0 or _to_int(resize.get("uid", -1), -1) >= 0:
        return None
    if event is not None:
        current = canvas.find_withtag("current")
        if current:
            try:
                tags = set(canvas.gettags(current[0]))
            except tk.TclError:
                tags = set()
            if "component" in tags or "resize_handle" in tags:
                # 让组件自身的按下/拖拽绑定继续处理，不在这里拦截。
                return None
    _on_canvas_release(owner, event)
    return None


def _on_canvas_motion(owner, event=None):
    drag = getattr(owner, "_ui_designer_drag", {}) or {}
    resize = getattr(owner, "_ui_designer_resize", {}) or {}
    resize_uid = _to_int(resize.get("uid", -1), -1)
    if resize_uid >= 0:
        return _on_resize_drag(owner, event, resize_uid)
    drag_uid = _to_int(drag.get("uid", -1), -1)
    if drag_uid >= 0:
        return _on_canvas_drag(owner, event, drag_uid)
    return None


def _on_canvas_release(owner, event=None):
    del event
    owner._ui_designer_drag = {"uid": None, "start_x": 0, "start_y": 0}
    owner._ui_designer_resize = {
        "uid": None,
        "anchor": "",
        "start_x": 0,
        "start_y": 0,
        "x": 0,
        "y": 0,
        "w": 0,
        "h": 0,
    }
    return "break"


def _selected_palette_kind(owner, fallback="文字"):
    palette = getattr(owner, "_ui_designer_palette", None)
    if palette is None:
        return str(fallback or "文字")

    if isinstance(palette, tk.Listbox):
        try:
            selection = palette.curselection()
            if selection:
                idx = int(selection[0])
                if 0 <= idx < len(COMPONENT_CATALOG):
                    return str(COMPONENT_CATALOG[idx][0])
        except Exception:
            pass
        return str(fallback or "文字")

    kind_map = getattr(owner, "_ui_designer_palette_kind_map", {}) or {}
    if isinstance(palette, ttk.Treeview):
        for item_id in list(palette.selection()):
            kind = str(kind_map.get(item_id, ""))
            if kind in COMPONENT_KIND_SET:
                return kind
            for child_id in palette.get_children(item_id):
                child_kind = str(kind_map.get(child_id, ""))
                if child_kind in COMPONENT_KIND_SET:
                    return child_kind
        for group_id in palette.get_children(""):
            for child_id in palette.get_children(group_id):
                child_kind = str(kind_map.get(child_id, ""))
                if child_kind in COMPONENT_KIND_SET:
                    return child_kind
    return str(fallback or "文字")


def _build_palette_tree(owner, parent):
    theme_bg = getattr(owner, "theme_panel_inner_bg", "#18212F")
    theme_fg = getattr(owner, "theme_fg", "#DCE7F5")
    theme_muted = getattr(owner, "theme_toolbar_muted", "#8FA1B8")
    theme_accent = getattr(owner, "theme_accent", "#2F7FE3")
    theme_border = getattr(owner, "theme_toolbar_border", "#2A3A4F")
    style_name = f"YimaUiPalette{id(parent)}.Treeview"
    style = ttk.Style(parent)
    try:
        style.theme_use("clam")
    except Exception:
        pass
    style.configure(
        style_name,
        background=theme_bg,
        fieldbackground=theme_bg,
        foreground=theme_fg,
        borderwidth=0,
        rowheight=24,
        relief="flat",
        font=("Microsoft YaHei", 9),
    )
    style.map(
        style_name,
        background=[("selected", theme_accent)],
        foreground=[("selected", "#FFFFFF")],
    )

    palette = ttk.Treeview(
        parent,
        show="tree",
        selectmode="browse",
        style=style_name,
        height=10,
    )
    palette_vsb = ttk.Scrollbar(parent, orient="vertical", command=palette.yview)
    palette.configure(yscrollcommand=palette_vsb.set)
    palette.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    palette_vsb.pack(side=tk.RIGHT, fill=tk.Y)

    kind_map = {}
    for group_name, kind_list in COMPONENT_PALETTE_GROUPS:
        valid_kinds = [kind for kind in kind_list if kind in COMPONENT_KIND_SET]
        if not valid_kinds:
            continue
        group_id = palette.insert("", tk.END, text=str(group_name), open=True)
        for kind in valid_kinds:
            child_id = palette.insert(group_id, tk.END, text=f"  {kind}")
            kind_map[child_id] = kind

    owner._ui_designer_palette_kind_map = dict(kind_map)

    for group_id in palette.get_children(""):
        children = list(palette.get_children(group_id))
        if children:
            palette.selection_set(children[0])
            palette.focus(children[0])
            break

    def _on_tree_double_click(event=None):
        del event
        focus_id = palette.focus()
        if focus_id and focus_id not in kind_map:
            try:
                is_open = bool(palette.item(focus_id, "open"))
                palette.item(focus_id, open=not is_open)
                return "break"
            except tk.TclError:
                return "break"
        selected_kind = _selected_palette_kind(owner)
        if selected_kind in COMPONENT_KIND_SET:
            return _add_component(owner, selected_kind)
        return "break"

    def _on_tree_return(event=None):
        del event
        selected_kind = _selected_palette_kind(owner)
        if selected_kind in COMPONENT_KIND_SET:
            return _add_component(owner, selected_kind)
        return "break"

    palette.bind("<Double-Button-1>", _on_tree_double_click, add="+")
    palette.bind("<Return>", _on_tree_return, add="+")
    palette.bind("<KP_Enter>", _on_tree_return, add="+")

    try:
        # 避免某些主题下分组项文字过淡，附加轻量颜色标签。
        for group_id in palette.get_children(""):
            palette.item(group_id, tags=("group",))
        palette.tag_configure("group", foreground=theme_muted)
    except Exception:
        pass

    return palette


def _add_component(owner, kind=None):
    _ensure_component_baseline(owner)
    if kind not in COMPONENT_KIND_SET:
        kind = _selected_palette_kind(owner, fallback="文字")

    if kind in COMPONENT_SINGLETON_KINDS:
        exists = _find_first_component_by_kind(owner, kind)
        if exists is not None:
            _select_component(owner, exists.get("uid", 0))
            if hasattr(owner, "status_main_var"):
                owner.status_main_var.set(f"界面设计器：{kind} 组件只允许一个，已定位到现有组件")
            return "break"

    offset = len(owner._ui_designer_components) * 16
    if kind == WINDOW_COMPONENT_KIND:
        comp = _new_component(owner, kind, x=48, y=40)
    else:
        comp = _new_component(owner, kind, x=120 + offset, y=90 + offset)
    owner._ui_designer_components.append(comp)
    _select_component(owner, comp["uid"])
    if hasattr(owner, "status_main_var"):
        owner.status_main_var.set(f"界面设计器：已添加组件 {kind}")
    return "break"


def _delete_selected_component(owner):
    _ensure_component_baseline(owner)
    comp = _selected_component(owner)
    if comp is None:
        return "break"
    if str(comp.get("kind", "")) == WINDOW_COMPONENT_KIND:
        if hasattr(owner, "status_main_var"):
            owner.status_main_var.set("界面设计器：窗口是必选组件，不能删除")
        return "break"
    owner._ui_designer_components = [item for item in owner._ui_designer_components if int(item.get("uid", -1)) != int(comp["uid"])]
    owner._ui_designer_selected_uid = None
    _ensure_window_component(owner)
    _render_canvas(owner)
    _refresh_property_panel(owner)
    if hasattr(owner, "status_main_var"):
        owner.status_main_var.set("界面设计器：已删除选中组件")
    return "break"


def _clear_components(owner):
    _ensure_component_baseline(owner)
    win_uid = None
    for item in list(owner._ui_designer_components):
        if str(item.get("kind", "")) == WINDOW_COMPONENT_KIND:
            win_uid = int(item.get("uid", 0))
            break
    owner._ui_designer_components = [item for item in owner._ui_designer_components if str(item.get("kind", "")) == WINDOW_COMPONENT_KIND]
    if not owner._ui_designer_components:
        win = _ensure_window_component(owner)
        win_uid = int(win.get("uid", 0))
    owner._ui_designer_selected_uid = win_uid
    _render_canvas(owner)
    _refresh_property_panel(owner)
    if hasattr(owner, "status_main_var"):
        owner.status_main_var.set("界面设计器：已清空页面组件，保留窗口")
    return "break"


def _apply_properties(owner):
    _ensure_component_baseline(owner)
    comp = _selected_component(owner)
    vars_map = getattr(owner, "_ui_designer_prop_vars", None)
    if comp is None or not isinstance(vars_map, dict):
        return "break"

    kind = str(comp.get("kind", ""))
    editable = _editable_property_keys(kind)

    if "text" in editable:
        comp["text"] = str(vars_map["text"].get() or "").strip()
    if "event" in editable:
        comp["event"] = str(vars_map["event"].get() or "").strip()
    if "action_text" in editable and vars_map.get("action_text") is not None:
        comp["action_text"] = str(vars_map["action_text"].get() or "").strip()
    if "columns" in editable:
        comp["columns"] = str(vars_map["columns"].get() or "").strip()
    if "rows" in editable:
        comp["rows"] = max(3, _to_int(vars_map["rows"].get(), comp.get("rows", 8)))

    if kind == WINDOW_COMPONENT_KIND:
        if "w" in editable:
            comp["w"] = _clamp(_to_int(vars_map["w"].get(), comp.get("w", 960)), 360, CANVAS_REGION_W)
        if "h" in editable:
            comp["h"] = _clamp(_to_int(vars_map["h"].get(), comp.get("h", 640)), 240, CANVAS_REGION_H)
    else:
        if "w" in editable:
            comp["w"] = _clamp(_to_int(vars_map["w"].get(), comp.get("w", 180)), 60, CANVAS_REGION_W)
        if "h" in editable:
            comp["h"] = _clamp(_to_int(vars_map["h"].get(), comp.get("h", 36)), 24, CANVAS_REGION_H)

    max_x = max(0, CANVAS_REGION_W - _to_int(comp.get("w", 180), 180))
    max_y = max(0, CANVAS_REGION_H - _to_int(comp.get("h", 36), 36))
    if "x" in editable:
        comp["x"] = _clamp(_to_int(vars_map["x"].get(), comp.get("x", 0)), 0, max_x)
    if "y" in editable:
        comp["y"] = _clamp(_to_int(vars_map["y"].get(), comp.get("y", 0)), 0, max_y)

    # 防止组件因尺寸变化后跑出画布边界。
    comp["x"] = _clamp(_to_int(comp.get("x", 0), 0), 0, max_x)
    comp["y"] = _clamp(_to_int(comp.get("y", 0), 0), 0, max_y)

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


def _guess_param_name_from_input(component_name, index, used_names):
    base = _sanitize_identifier(component_name, f"参数{index}")
    base = re.sub(r"(输入框|输入)\d*$", "", base)
    base = re.sub(r"_?\d+$", "", base).strip("_")
    if not base:
        base = f"参数{index}"
    if base[0].isdigit():
        base = f"参数_{base}"
    name = base
    seq = 2
    while name in used_names:
        name = f"{base}_{seq}"
        seq += 1
    used_names.add(name)
    return name


def _infer_button_bindings(export_items):
    items = list(export_items or [])
    input_items = [item for item in items if str(item.get("kind", "")) in INPUT_COMPONENT_KINDS]
    table_items = [item for item in items if str(item.get("kind", "")) in TABLE_COMPONENT_KINDS]
    query_keywords = ("查", "查询", "搜索", "检索", "筛选")
    bindings = {}

    for button in items:
        if str(button.get("kind", "")) not in BUTTON_COMPONENT_KINDS:
            continue
        fn_name = str(button.get("event_fn", "") or "")
        if not fn_name or fn_name in bindings:
            continue

        bx = _to_int(button.get("x", 0), 0)
        by = _to_int(button.get("y", 0), 0)
        bw = _to_int(button.get("w", 120), 120)
        text = str(button.get("text", "") or "")
        fn_text = str(fn_name)

        nearby_inputs = []
        for inp in input_items:
            ix = _to_int(inp.get("x", 0), 0)
            iy = _to_int(inp.get("y", 0), 0)
            iw = _to_int(inp.get("w", 200), 200)
            vertical_delta = abs(iy - by)
            if vertical_delta > 180:
                continue
            if ix > bx + bw + 420:
                continue
            score = vertical_delta * 3 + abs((ix + int(iw / 2)) - (bx + int(bw / 2)))
            nearby_inputs.append((score, inp))
        nearby_inputs.sort(key=lambda pair: pair[0])
        selected_inputs = [pair[1] for pair in nearby_inputs[:2]]
        selected_inputs.sort(key=lambda inp: (_to_int(inp.get("y", 0), 0), _to_int(inp.get("x", 0), 0)))

        used_params = set()
        param_names = []
        input_names = []
        for idx, inp in enumerate(selected_inputs, start=1):
            input_names.append(str(inp.get("name", "")))
            param_names.append(_guess_param_name_from_input(inp.get("name", ""), idx, used_params))

        table_name = ""
        table_score = None
        for table in table_items:
            tx = _to_int(table.get("x", 0), 0)
            ty = _to_int(table.get("y", 0), 0)
            delta_y = ty - by
            if delta_y < -220:
                continue
            score = abs(delta_y) * 2 + abs(tx - bx)
            if table_score is None or score < table_score:
                table_score = score
                table_name = str(table.get("name", ""))

        query_mode = bool(table_name) and any(keyword in (text + fn_text) for keyword in query_keywords)
        bindings[fn_name] = {
            "input_components": input_names,
            "param_names": param_names,
            "table_component": table_name,
            "query_mode": query_mode,
        }
    return bindings


def _collect_design_export_context(owner):
    _ensure_component_baseline(owner)
    all_components = list(getattr(owner, "_ui_designer_components", []) or [])

    window_component = None
    for item in all_components:
        if str(item.get("kind", "")) == WINDOW_COMPONENT_KIND:
            window_component = item
            break

    win_title = "可视化界面"
    win_w = 960
    win_h = 640
    if window_component is not None:
        title = str(window_component.get("text", "")).strip()
        win_title = title or win_title
        win_w = max(360, _to_int(window_component.get("w", win_w), win_w))
        win_h = max(240, _to_int(window_component.get("h", win_h), win_h))

    comps = [item for item in all_components if str(item.get("kind", "")) != WINDOW_COMPONENT_KIND]
    comps.sort(key=lambda item: (_to_int(item.get("y", 0)), _to_int(item.get("x", 0)), _to_int(item.get("uid", 0))))

    used_names = set()
    export_items = []
    for index, comp in enumerate(comps, start=1):
        kind = str(comp.get("kind", "文字"))
        base_name = _sanitize_identifier(comp.get("name", ""), f"控件{index}")
        name = base_name
        n = 2
        while name in used_names:
            name = f"{base_name}_{n}"
            n += 1
        used_names.add(name)

        item = {
            "index": index,
            "kind": kind,
            "name": name,
            "x": _to_int(comp.get("x", 0), 0),
            "y": _to_int(comp.get("y", 0), 0),
            "w": max(60, _to_int(comp.get("w", 160), 160)),
            "h": max(24, _to_int(comp.get("h", 34), 34)),
            "text": str(comp.get("text", "")).strip() or kind,
            "action_text": str(comp.get("action_text", "")).strip(),
            "event_fn": "",
            "columns": _normalize_columns(comp.get("columns", "列1,列2")),
            "rows": max(3, _to_int(comp.get("rows", 8), 8)),
        }
        if kind in BUTTON_COMPONENT_KINDS:
            if kind == "复选框":
                default_event = f"处理勾选_{index}"
            elif kind == "单选按钮":
                default_event = f"处理选择_{index}"
            else:
                default_event = f"处理点击_{index}"
            item["event_fn"] = _sanitize_function_name(comp.get("event", ""), default_event)
        elif kind == "登录模板":
            item["action_text"] = item["action_text"] or "登录"
            item["event_fn"] = _sanitize_function_name(comp.get("event", ""), f"处理登录_{index}")
        elif kind == "列表模板":
            item["action_text"] = item["action_text"] or "查询"
            item["event_fn"] = _sanitize_function_name(comp.get("event", ""), f"执行查询_{index}")
            item["rows"] = max(3, _to_int(comp.get("rows", 10), 10))
        export_items.append(item)

    return {
        "window_title": win_title,
        "window_w": win_w,
        "window_h": win_h,
        "items": export_items,
    }


def _generate_ym_code(owner):
    context = _collect_design_export_context(owner)

    lines = [
        "# --- 可视化界面设计器导出 ---",
        f"窗口 = 建窗口({json.dumps(context['window_title'], ensure_ascii=False)}, {context['window_w']}, {context['window_h']})",
        "",
    ]
    generated_events = []

    for item in context["items"]:
        index = int(item["index"])
        kind = str(item["kind"])
        name = str(item["name"])
        x = int(item["x"])
        y = int(item["y"])
        w = int(item["w"])
        h = int(item["h"])
        text = str(item["text"])

        if kind == "多行文本框":
            lines.append(f"{name} = 加多行文本框(窗口, {json.dumps(text, ensure_ascii=False)})")
            lines.append(f"设位置({name}, {x}, {y}, {w}, {h})")
        elif kind == "组合框":
            combo_options = _normalize_columns(text)
            default_value = str(combo_options[0] if combo_options else "")
            lines.append(
                f"{name} = 加组合框(窗口, {json.dumps(combo_options, ensure_ascii=False)}, "
                f"{json.dumps(default_value, ensure_ascii=False)})"
            )
            lines.append(f"设位置({name}, {x}, {y}, {w}, {h})")
        elif kind == "复选框":
            fn_name = str(item["event_fn"])
            lines.append(f"{name} = 加复选框(窗口, {json.dumps(text, ensure_ascii=False)}, {json.dumps(fn_name, ensure_ascii=False)})")
            lines.append(f"设位置({name}, {x}, {y}, {w}, {h})")
            generated_events.append(fn_name)
        elif kind == "单选按钮":
            fn_name = str(item["event_fn"])
            group_name = "默认单选组"
            option_value = str(text or name)
            lines.append(
                f"{name} = 加单选按钮(窗口, {json.dumps(text, ensure_ascii=False)}, {json.dumps(fn_name, ensure_ascii=False)}, "
                f"{json.dumps(group_name, ensure_ascii=False)}, {json.dumps(option_value, ensure_ascii=False)})"
            )
            lines.append(f"设位置({name}, {x}, {y}, {w}, {h})")
            generated_events.append(fn_name)
        elif kind in TEXT_COMPONENT_KINDS:
            lines.append(f"{name} = 加文字(窗口, {json.dumps(text, ensure_ascii=False)})")
            lines.append(f"设位置({name}, {x}, {y}, {w}, {h})")
        elif kind in INPUT_COMPONENT_KINDS:
            lines.append(f"{name} = 加输入框(窗口)")
            lines.append(f"设位置({name}, {x}, {y}, {w}, {h})")
        elif kind in BUTTON_COMPONENT_KINDS:
            fn_name = str(item["event_fn"])
            lines.append(f"{name} = 加按钮(窗口, {json.dumps(text, ensure_ascii=False)}, {json.dumps(fn_name, ensure_ascii=False)})")
            lines.append(f"设位置({name}, {x}, {y}, {w}, {h})")
            generated_events.append(fn_name)
        elif kind in TABLE_COMPONENT_KINDS:
            columns = list(item["columns"])
            rows = int(item["rows"])
            lines.append(f"{name} = 加表格(窗口, {json.dumps(columns, ensure_ascii=False)}, {rows})")
            lines.append(f"设位置({name}, {x}, {y}, {w}, {h})")
        elif kind in CARD_COMPONENT_KINDS:
            lines.append(f"{name} = 加卡片(窗口, {json.dumps(text, ensure_ascii=False)})")
            lines.append(f"设位置({name}, {x}, {y}, {w}, {h})")
        elif kind == "登录模板":
            action_text = str(item["action_text"])
            fn_name = str(item["event_fn"])
            lines.append(
                f"{name} = 加登录模板(窗口, {json.dumps(text, ensure_ascii=False)}, "
                f"{json.dumps(action_text, ensure_ascii=False)}, {json.dumps(fn_name, ensure_ascii=False)})"
            )
            lines.append(f"设位置({name}[\"卡片\"], {x}, {y}, {w}, {h})")
            generated_events.append(fn_name)
        elif kind == "列表模板":
            action_text = str(item["action_text"])
            fn_name = str(item["event_fn"])
            columns = list(item["columns"])
            rows = int(item["rows"])
            lines.append(
                f"{name} = 加列表模板(窗口, {json.dumps(text, ensure_ascii=False)}, "
                f"{json.dumps(columns, ensure_ascii=False)}, {rows}, "
                f"{json.dumps(action_text, ensure_ascii=False)}, {json.dumps(fn_name, ensure_ascii=False)})"
            )
            lines.append(f"设位置({name}[\"卡片\"], {x}, {y}, {w}, {h})")
            generated_events.append(fn_name)
        else:
            lines.append(f"# 未识别组件：{json.dumps(kind, ensure_ascii=False)}")
        lines.append("")

    generated_events = sorted(set(generated_events))
    for fn_name in generated_events:
        lines.append(f"功能 {fn_name}")
        lines.append("    # TODO: 在这里填写业务逻辑")
        lines.append(f"    弹窗(\"提示\", \"触发：{fn_name}\")")
        lines.append("")

    lines.append("打开界面(窗口)")
    return "\n".join(lines).rstrip() + "\n"


def _generate_layered_ym_codes(owner, data_backend=None):
    context = _collect_design_export_context(owner)
    button_bindings = _infer_button_bindings(context["items"])
    ui_lines = [
        "# --- 可视化界面设计器导出：界面层 ---",
        "引入 \"界面设计_业务层\" 叫做 业务",
        "",
        f"窗口 = 建窗口({json.dumps(context['window_title'], ensure_ascii=False)}, {context['window_w']}, {context['window_h']})",
        "",
    ]
    event_map = {}
    list_template_specs = []
    login_template_specs = []

    for item in context["items"]:
        index = int(item["index"])
        kind = str(item["kind"])
        name = str(item["name"])
        x = int(item["x"])
        y = int(item["y"])
        w = int(item["w"])
        h = int(item["h"])
        text = str(item["text"])
        fn_name = str(item.get("event_fn", "") or "")

        if kind == "多行文本框":
            ui_lines.append(f"{name} = 加多行文本框(窗口, {json.dumps(text, ensure_ascii=False)})")
            ui_lines.append(f"设位置({name}, {x}, {y}, {w}, {h})")
        elif kind == "组合框":
            combo_options = _normalize_columns(text)
            default_value = str(combo_options[0] if combo_options else "")
            ui_lines.append(
                f"{name} = 加组合框(窗口, {json.dumps(combo_options, ensure_ascii=False)}, "
                f"{json.dumps(default_value, ensure_ascii=False)})"
            )
            ui_lines.append(f"设位置({name}, {x}, {y}, {w}, {h})")
        elif kind == "复选框":
            ui_lines.append(f"{name} = 加复选框(窗口, {json.dumps(text, ensure_ascii=False)}, {json.dumps(fn_name, ensure_ascii=False)})")
            ui_lines.append(f"设位置({name}, {x}, {y}, {w}, {h})")
            if fn_name and fn_name not in event_map:
                event_map[fn_name] = {
                    "kind": kind,
                    "component_name": name,
                    **dict(button_bindings.get(fn_name, {})),
                }
        elif kind == "单选按钮":
            group_name = "默认单选组"
            option_value = str(text or name)
            ui_lines.append(
                f"{name} = 加单选按钮(窗口, {json.dumps(text, ensure_ascii=False)}, {json.dumps(fn_name, ensure_ascii=False)}, "
                f"{json.dumps(group_name, ensure_ascii=False)}, {json.dumps(option_value, ensure_ascii=False)})"
            )
            ui_lines.append(f"设位置({name}, {x}, {y}, {w}, {h})")
            if fn_name and fn_name not in event_map:
                event_map[fn_name] = {
                    "kind": kind,
                    "component_name": name,
                    **dict(button_bindings.get(fn_name, {})),
                }
        elif kind in TEXT_COMPONENT_KINDS:
            ui_lines.append(f"{name} = 加文字(窗口, {json.dumps(text, ensure_ascii=False)})")
            ui_lines.append(f"设位置({name}, {x}, {y}, {w}, {h})")
        elif kind in INPUT_COMPONENT_KINDS:
            ui_lines.append(f"{name} = 加输入框(窗口)")
            ui_lines.append(f"设位置({name}, {x}, {y}, {w}, {h})")
        elif kind in BUTTON_COMPONENT_KINDS:
            ui_lines.append(f"{name} = 加按钮(窗口, {json.dumps(text, ensure_ascii=False)}, {json.dumps(fn_name, ensure_ascii=False)})")
            ui_lines.append(f"设位置({name}, {x}, {y}, {w}, {h})")
            if fn_name and fn_name not in event_map:
                event_map[fn_name] = {
                    "kind": kind,
                    "component_name": name,
                    **dict(button_bindings.get(fn_name, {})),
                }
        elif kind in TABLE_COMPONENT_KINDS:
            ui_lines.append(f"{name} = 加表格(窗口, {json.dumps(item['columns'], ensure_ascii=False)}, {int(item['rows'])})")
            ui_lines.append(f"设位置({name}, {x}, {y}, {w}, {h})")
        elif kind in CARD_COMPONENT_KINDS:
            ui_lines.append(f"{name} = 加卡片(窗口, {json.dumps(text, ensure_ascii=False)})")
            ui_lines.append(f"设位置({name}, {x}, {y}, {w}, {h})")
        elif kind == "登录模板":
            ui_lines.append(
                f"{name} = 加登录模板(窗口, {json.dumps(text, ensure_ascii=False)}, "
                f"{json.dumps(item['action_text'], ensure_ascii=False)}, {json.dumps(fn_name, ensure_ascii=False)})"
            )
            ui_lines.append(f"设位置({name}[\"卡片\"], {x}, {y}, {w}, {h})")
            if fn_name and fn_name not in event_map:
                prefix = _sanitize_identifier(name, f"登录模板{index}")
                data_auth_fn = f"{prefix}_登录校验"
                event_map[fn_name] = {"kind": kind, "component_name": name, "data_auth_fn": data_auth_fn}
                login_template_specs.append({"prefix": prefix, "event_fn": fn_name, "data_auth_fn": data_auth_fn})
        elif kind == "列表模板":
            ui_lines.append(
                f"{name} = 加列表模板(窗口, {json.dumps(text, ensure_ascii=False)}, "
                f"{json.dumps(item['columns'], ensure_ascii=False)}, {int(item['rows'])}, "
                f"{json.dumps(item['action_text'], ensure_ascii=False)}, {json.dumps(fn_name, ensure_ascii=False)})"
            )
            ui_lines.append(f"设位置({name}[\"卡片\"], {x}, {y}, {w}, {h})")
            if fn_name and fn_name not in event_map:
                prefix = _sanitize_identifier(name, f"列表模板{index}")
                query_fn = f"{prefix}_查询"
                create_fn = f"{prefix}_新增"
                update_fn = f"{prefix}_更新"
                delete_fn = f"{prefix}_删除"
                event_map[fn_name] = {
                    "kind": kind,
                    "component_name": name,
                    "query_fn": query_fn,
                    "create_fn": create_fn,
                    "update_fn": update_fn,
                    "delete_fn": delete_fn,
                }
                list_template_specs.append(
                    {
                        "index": index,
                        "prefix": prefix,
                        "event_fn": fn_name,
                        "query_fn": query_fn,
                        "create_fn": create_fn,
                        "update_fn": update_fn,
                        "delete_fn": delete_fn,
                    }
                )
        else:
            ui_lines.append(f"# 未识别组件：{json.dumps(kind, ensure_ascii=False)}")
        ui_lines.append("")

    for fn_name, meta in event_map.items():
        source_kind = str(meta.get("kind", ""))
        comp_name = str(meta.get("component_name", ""))
        ui_lines.append(f"功能 {fn_name}")
        if source_kind == "登录模板":
            ui_lines.append(f"    账号 = 读输入({comp_name}[\"账号输入框\"])")
            ui_lines.append(f"    密码 = 读输入({comp_name}[\"密码输入框\"])")
            ui_lines.append(f"    结果 = 业务.{fn_name}(账号, 密码)")
            ui_lines.append("    弹窗(\"提示\", 转文字(结果))")
        elif source_kind == "列表模板":
            ui_lines.append(f"    关键字 = 读输入({comp_name}[\"关键字输入框\"])")
            ui_lines.append(f"    行列表 = 业务.{fn_name}(关键字)")
            ui_lines.append(f"    表格清空({comp_name}[\"表格\"])")
            ui_lines.append("    重复 长度(行列表) 次 叫做 序号")
            ui_lines.append("        行 = 行列表[序号]")
            ui_lines.append(f"        表格加行({comp_name}[\"表格\"], 行)")
        elif source_kind in BUTTON_COMPONENT_KINDS:
            param_names = list(meta.get("param_names", []) or [])
            input_components = list(meta.get("input_components", []) or [])
            table_component = str(meta.get("table_component", "") or "")
            query_mode = bool(meta.get("query_mode")) and bool(table_component)
            for idx, input_name in enumerate(input_components):
                if idx >= len(param_names):
                    break
                ui_lines.append(f"    {param_names[idx]} = 读输入({input_name})")
            call_args = ", ".join(param_names)
            if query_mode:
                if call_args:
                    ui_lines.append(f"    行列表 = 业务.{fn_name}({call_args})")
                else:
                    ui_lines.append(f"    行列表 = 业务.{fn_name}()")
                ui_lines.append(f"    表格清空({table_component})")
                ui_lines.append("    重复 长度(行列表) 次 叫做 序号")
                ui_lines.append("        行 = 行列表[序号]")
                ui_lines.append(f"        表格加行({table_component}, 行)")
            else:
                if call_args:
                    ui_lines.append(f"    结果 = 业务.{fn_name}({call_args})")
                else:
                    ui_lines.append(f"    结果 = 业务.{fn_name}()")
                ui_lines.append("    弹窗(\"提示\", 转文字(结果))")
        else:
            ui_lines.append(f"    结果 = 业务.{fn_name}()")
            ui_lines.append("    弹窗(\"提示\", 转文字(结果))")
        ui_lines.append("")

    if list_template_specs:
        ui_lines.append("# --- 列表模板默认操作示例（可选调用）---")
        for spec in list_template_specs:
            prefix = str(spec["prefix"])
            create_fn = str(spec["create_fn"])
            update_fn = str(spec["update_fn"])
            delete_fn = str(spec["delete_fn"])
            ui_lines.append(f"功能 {prefix}_新增示例")
            ui_lines.append(f"    结果 = 业务.{create_fn}(\"示例标题\", \"示例说明\")")
            ui_lines.append("    弹窗(\"新增\", 转文字(结果))")
            ui_lines.append("")
            ui_lines.append(f"功能 {prefix}_更新示例")
            ui_lines.append(f"    结果 = 业务.{update_fn}(\"1\", \"示例标题-更新\", \"示例说明-更新\")")
            ui_lines.append("    弹窗(\"更新\", 转文字(结果))")
            ui_lines.append("")
            ui_lines.append(f"功能 {prefix}_删除示例")
            ui_lines.append(f"    结果 = 业务.{delete_fn}(\"1\")")
            ui_lines.append("    弹窗(\"删除\", 转文字(结果))")
            ui_lines.append("")

    ui_lines.append("打开界面(窗口)")
    ui_code = "\n".join(ui_lines).rstrip() + "\n"

    logic_lines = [
        "# --- 可视化界面设计器导出：业务层 ---",
        "引入 \"界面设计_数据层\" 叫做 数据",
        "# 这里写业务逻辑，界面层会调用同名函数。",
        "",
        "功能 初始化()",
        "    数据.初始化()",
        "    返回 {\"成功\": 对, \"消息\": \"业务层初始化完成\"}",
        "",
    ]
    for fn_name, meta in event_map.items():
        source_kind = str(meta.get("kind", ""))
        if source_kind == "登录模板":
            logic_lines.append(f"功能 {fn_name}(账号, 密码)")
            logic_lines.append("    如果 去空格(账号) == \"\" 或者 去空格(密码) == \"\" 就")
            logic_lines.append("        返回 {\"成功\": 错, \"消息\": \"账号或密码不能为空\"}")
            data_auth_fn = str(meta.get("data_auth_fn", ""))
            if data_auth_fn:
                logic_lines.append(f"    返回 数据.{data_auth_fn}(账号, 密码)")
            else:
                logic_lines.append("    返回 {\"成功\": 对, \"消息\": \"登录校验通过：\" + 账号}")
        elif source_kind == "列表模板":
            query_fn = str(meta.get("query_fn", fn_name))
            if fn_name != query_fn:
                logic_lines.append(f"功能 {fn_name}(关键字)")
                logic_lines.append(f"    返回 {query_fn}(关键字)")
                logic_lines.append("")
        elif source_kind in BUTTON_COMPONENT_KINDS:
            param_names = list(meta.get("param_names", []) or [])
            table_component = str(meta.get("table_component", "") or "")
            query_mode = bool(meta.get("query_mode")) and bool(table_component)
            signature = ", ".join(param_names)
            if signature:
                logic_lines.append(f"功能 {fn_name}({signature})")
            else:
                logic_lines.append(f"功能 {fn_name}()")
            if query_mode:
                logic_lines.append("    # TODO: 返回二维列表，每一行对应表格一行")
                if param_names:
                    logic_lines.append(f"    关键字 = 去空格({param_names[0]})")
                    logic_lines.append("    如果 关键字 == \"\" 就")
                    logic_lines.append("        返回 新列表()")
                logic_lines.append("    返回 [[\"示例\", \"请替换为真实数据\"]]")
            else:
                logic_lines.append(f"    返回 \"请实现业务函数：{fn_name}\"")
        else:
            logic_lines.append(f"功能 {fn_name}()")
            logic_lines.append(f"    返回 \"请实现业务函数：{fn_name}\"")
        logic_lines.append("")

    if list_template_specs:
        logic_lines.append("# --- 列表模板：标准 CRUD 占位函数 ---")
        for spec in list_template_specs:
            query_fn = str(spec["query_fn"])
            create_fn = str(spec["create_fn"])
            update_fn = str(spec["update_fn"])
            delete_fn = str(spec["delete_fn"])
            logic_lines.append(f"功能 {query_fn}(关键字)")
            logic_lines.append(f"    返回 数据.{query_fn}(关键字)")
            logic_lines.append("")
            logic_lines.append(f"功能 {create_fn}(标题, 说明)")
            logic_lines.append("    如果 去空格(标题) == \"\" 就")
            logic_lines.append("        返回 {\"成功\": 错, \"消息\": \"标题不能为空\"}")
            logic_lines.append(f"    返回 数据.{create_fn}(标题, 说明)")
            logic_lines.append("")
            logic_lines.append(f"功能 {update_fn}(编号文本, 标题, 说明)")
            logic_lines.append("    如果 去空格(编号文本) == \"\" 就")
            logic_lines.append("        返回 {\"成功\": 错, \"消息\": \"编号不能为空\"}")
            logic_lines.append("    编号 = 转数字(编号文本)")
            logic_lines.append(f"    返回 数据.{update_fn}(编号, 标题, 说明)")
            logic_lines.append("")
            logic_lines.append(f"功能 {delete_fn}(编号文本)")
            logic_lines.append("    如果 去空格(编号文本) == \"\" 就")
            logic_lines.append("        返回 {\"成功\": 错, \"消息\": \"编号不能为空\"}")
            logic_lines.append("    编号 = 转数字(编号文本)")
            logic_lines.append(f"    返回 数据.{delete_fn}(编号)")
            logic_lines.append("")

    logic_code = "\n".join(logic_lines).rstrip() + "\n"

    data_backend = _normalize_data_backend(
        data_backend if data_backend is not None else getattr(owner, "_ui_designer_data_backend", "sqlite")
    )
    if data_backend == "json":
        data_lines = [
            "# --- 可视化界面设计器导出：数据层（JSON文件） ---",
            "引入 \"数据工具\" 叫做 数据",
            "引入 \"系统工具\" 叫做 系统",
            "",
            "数据文件 = \"界面设计_数据.json\"",
            "数据仓库 = {\"用户\": 新列表()}",
            "",
            "功能 确保仓库结构()",
            "    如果 取反 存在(数据仓库, \"用户\") 就",
            "        数据仓库[\"用户\"] = 新列表()",
            "",
            "功能 保存仓库()",
            "    确保仓库结构()",
            "    数据.写JSON(数据文件, 数据仓库, 对)",
            "    返回 对",
            "",
            "功能 初始化()",
            "    如果 系统.文件存在(数据文件) 就",
            "        读回 = 数据.读JSON(数据文件)",
            "        如果 读回 != 空 就",
            "            数据仓库 = 读回",
            "    确保仓库结构()",
            "    如果 长度(数据仓库[\"用户\"]) == 0 就",
            "        加入(数据仓库[\"用户\"], {\"账号\": \"admin\", \"密码\": \"123456\"})",
            "    保存仓库()",
            "    返回 对",
            "",
        ]
        if login_template_specs:
            data_lines.append("# --- 登录模板数据函数（JSON）---")
            for spec in login_template_specs:
                auth_fn = str(spec["data_auth_fn"])
                data_lines.append(f"功能 {auth_fn}(账号, 密码)")
                data_lines.append("    确保仓库结构()")
                data_lines.append("    账号值 = 去空格(账号)")
                data_lines.append("    密码值 = 去空格(密码)")
                data_lines.append("    重复 长度(数据仓库[\"用户\"]) 次 叫做 序号")
                data_lines.append("        用户 = 数据仓库[\"用户\"][序号]")
                data_lines.append("        如果 转文字(用户[\"账号\"]) == 账号值 并且 转文字(用户[\"密码\"]) == 密码值 就")
                data_lines.append("            返回 {\"成功\": 对, \"消息\": \"登录成功\"}")
                data_lines.append("    返回 {\"成功\": 错, \"消息\": \"账号或密码错误\"}")
                data_lines.append("")
        if list_template_specs:
            data_lines.append("# --- 列表模板数据函数（JSON + CRUD）---")
            for spec in list_template_specs:
                index = int(spec.get("index", 1))
                list_key = f"列表_{index}"
                query_fn = str(spec["query_fn"])
                create_fn = str(spec["create_fn"])
                update_fn = str(spec["update_fn"])
                delete_fn = str(spec["delete_fn"])
                data_lines.append(f"功能 {query_fn}(关键字)")
                data_lines.append("    确保仓库结构()")
                data_lines.append(f"    如果 取反 存在(数据仓库, \"{list_key}\") 就")
                data_lines.append(f"        数据仓库[\"{list_key}\"] = 新列表()")
                data_lines.append("    词 = 去空格(关键字)")
                data_lines.append("    结果 = 新列表()")
                data_lines.append(f"    重复 长度(数据仓库[\"{list_key}\"]) 次 叫做 序号")
                data_lines.append(f"        项 = 数据仓库[\"{list_key}\"][序号]")
                data_lines.append("        编号 = 转文字(项[\"编号\"])")
                data_lines.append("        标题 = 转文字(项[\"标题\"])")
                data_lines.append("        说明 = 转文字(项[\"说明\"])")
                data_lines.append("        如果 词 == \"\" 或者 包含(标题, 词) 或者 包含(说明, 词) 就")
                data_lines.append("            加入(结果, [编号, 标题, 说明])")
                data_lines.append("    返回 结果")
                data_lines.append("")
                data_lines.append(f"功能 {create_fn}(标题, 说明)")
                data_lines.append("    确保仓库结构()")
                data_lines.append(f"    如果 取反 存在(数据仓库, \"{list_key}\") 就")
                data_lines.append(f"        数据仓库[\"{list_key}\"] = 新列表()")
                data_lines.append(f"    新编号 = 长度(数据仓库[\"{list_key}\"]) + 1")
                data_lines.append(f"    加入(数据仓库[\"{list_key}\"], {{\"编号\": 新编号, \"标题\": 标题, \"说明\": 说明}})")
                data_lines.append("    保存仓库()")
                data_lines.append("    返回 {\"成功\": 对, \"消息\": \"新增成功\"}")
                data_lines.append("")
                data_lines.append(f"功能 {update_fn}(编号, 标题, 说明)")
                data_lines.append("    确保仓库结构()")
                data_lines.append(f"    如果 取反 存在(数据仓库, \"{list_key}\") 就")
                data_lines.append("        返回 {\"成功\": 错, \"消息\": \"记录不存在\"}")
                data_lines.append("    目标编号 = 转文字(编号)")
                data_lines.append("    命中 = 错")
                data_lines.append(f"    重复 长度(数据仓库[\"{list_key}\"]) 次 叫做 序号")
                data_lines.append(f"        项 = 数据仓库[\"{list_key}\"][序号]")
                data_lines.append("        如果 转文字(项[\"编号\"]) == 目标编号 就")
                data_lines.append("            项[\"标题\"] = 标题")
                data_lines.append("            项[\"说明\"] = 说明")
                data_lines.append("            命中 = 对")
                data_lines.append("            停下")
                data_lines.append("    如果 取反 命中 就")
                data_lines.append("        返回 {\"成功\": 错, \"消息\": \"未找到要更新的记录\"}")
                data_lines.append("    保存仓库()")
                data_lines.append("    返回 {\"成功\": 对, \"消息\": \"更新成功\"}")
                data_lines.append("")
                data_lines.append(f"功能 {delete_fn}(编号)")
                data_lines.append("    确保仓库结构()")
                data_lines.append(f"    如果 取反 存在(数据仓库, \"{list_key}\") 就")
                data_lines.append("        返回 {\"成功\": 错, \"消息\": \"记录不存在\"}")
                data_lines.append("    目标编号 = 转文字(编号)")
                data_lines.append("    命中 = 错")
                data_lines.append(f"    重复 长度(数据仓库[\"{list_key}\"]) 次 叫做 序号")
                data_lines.append(f"        项 = 数据仓库[\"{list_key}\"][序号]")
                data_lines.append("        如果 转文字(项[\"编号\"]) == 目标编号 就")
                data_lines.append(f"            删除(数据仓库[\"{list_key}\"], 序号)")
                data_lines.append("            命中 = 对")
                data_lines.append("            停下")
                data_lines.append("    如果 取反 命中 就")
                data_lines.append("        返回 {\"成功\": 错, \"消息\": \"未找到要删除的记录\"}")
                data_lines.append("    保存仓库()")
                data_lines.append("    返回 {\"成功\": 对, \"消息\": \"删除成功\"}")
                data_lines.append("")
    else:
        data_lines = [
            "# --- 可视化界面设计器导出：数据层（SQLite） ---",
            "引入 \"本地数据库\" 叫做 库",
            "",
            "数据库文件 = \"界面设计_数据.db\"",
            "连接 = 空",
            "",
            "功能 取连接()",
            "    如果 连接 == 空 就",
            "        连接 = 库.打开数据库(数据库文件)",
            "    返回 连接",
            "",
            "功能 初始化()",
            "    本地连接 = 取连接()",
        ]
        if login_template_specs:
            data_lines.append("    库.执行SQL(本地连接, \"CREATE TABLE IF NOT EXISTS 用户(账号 TEXT PRIMARY KEY, 密码 TEXT)\")")
            data_lines.append("    库.执行SQL(本地连接, \"INSERT OR IGNORE INTO 用户(账号, 密码) VALUES(?, ?)\", [\"admin\", \"123456\"])")
        for spec in list_template_specs:
            index = int(spec.get("index", 1))
            table_name = f"列表数据_{index}"
            data_lines.append(
                f"    库.执行SQL(本地连接, \"CREATE TABLE IF NOT EXISTS {table_name}(编号 INTEGER PRIMARY KEY AUTOINCREMENT, 标题 TEXT, 说明 TEXT)\")"
            )
        data_lines.append("    返回 对")
        data_lines.append("")
        if login_template_specs:
            data_lines.append("# --- 登录模板数据函数（SQLite）---")
            for spec in login_template_specs:
                auth_fn = str(spec["data_auth_fn"])
                data_lines.append(f"功能 {auth_fn}(账号, 密码)")
                data_lines.append("    本地连接 = 取连接()")
                data_lines.append("    结果 = 库.查询SQL(本地连接, \"SELECT 账号 FROM 用户 WHERE 账号 = ? AND 密码 = ? LIMIT 1\", [账号, 密码])")
                data_lines.append("    如果 长度(结果) > 0 就")
                data_lines.append("        返回 {\"成功\": 对, \"消息\": \"登录成功\"}")
                data_lines.append("    返回 {\"成功\": 错, \"消息\": \"账号或密码错误\"}")
                data_lines.append("")
        if list_template_specs:
            data_lines.append("# --- 列表模板数据函数（SQLite + CRUD）---")
            for spec in list_template_specs:
                index = int(spec.get("index", 1))
                table_name = f"列表数据_{index}"
                query_fn = str(spec["query_fn"])
                create_fn = str(spec["create_fn"])
                update_fn = str(spec["update_fn"])
                delete_fn = str(spec["delete_fn"])
                data_lines.append(f"功能 {query_fn}(关键字)")
                data_lines.append("    本地连接 = 取连接()")
                data_lines.append("    词 = 去空格(关键字)")
                data_lines.append("    如果 词 == \"\" 就")
                data_lines.append(
                    f"        原始结果 = 库.查询SQL(本地连接, \"SELECT 编号, 标题, 说明 FROM {table_name} ORDER BY 编号 DESC\")"
                )
                data_lines.append("    不然")
                data_lines.append("        模式 = \"%\" + 词 + \"%\"")
                data_lines.append(
                    f"        原始结果 = 库.查询SQL(本地连接, \"SELECT 编号, 标题, 说明 FROM {table_name} WHERE 标题 LIKE ? OR 说明 LIKE ? ORDER BY 编号 DESC\", [模式, 模式])"
                )
                data_lines.append("    结果 = 新列表()")
                data_lines.append("    重复 长度(原始结果) 次 叫做 序号")
                data_lines.append("        项 = 原始结果[序号]")
                data_lines.append("        加入(结果, [转文字(项[\"编号\"]), 转文字(项[\"标题\"]), 转文字(项[\"说明\"])])")
                data_lines.append("    返回 结果")
                data_lines.append("")
                data_lines.append(f"功能 {create_fn}(标题, 说明)")
                data_lines.append("    本地连接 = 取连接()")
                data_lines.append(
                    f"    库.执行SQL(本地连接, \"INSERT INTO {table_name}(标题, 说明) VALUES(?, ?)\", [标题, 说明])"
                )
                data_lines.append("    返回 {\"成功\": 对, \"消息\": \"新增成功\"}")
                data_lines.append("")
                data_lines.append(f"功能 {update_fn}(编号, 标题, 说明)")
                data_lines.append("    本地连接 = 取连接()")
                data_lines.append(
                    f"    库.执行SQL(本地连接, \"UPDATE {table_name} SET 标题 = ?, 说明 = ? WHERE 编号 = ?\", [标题, 说明, 编号])"
                )
                data_lines.append("    返回 {\"成功\": 对, \"消息\": \"更新成功\"}")
                data_lines.append("")
                data_lines.append(f"功能 {delete_fn}(编号)")
                data_lines.append("    本地连接 = 取连接()")
                data_lines.append(f"    库.执行SQL(本地连接, \"DELETE FROM {table_name} WHERE 编号 = ?\", [编号])")
                data_lines.append("    返回 {\"成功\": 对, \"消息\": \"删除成功\"}")
                data_lines.append("")

    data_code = "\n".join(data_lines).rstrip() + "\n"
    return ui_code, logic_code, data_code


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


def _upsert_code_to_named_tab(owner, filename, code):
    target_tab_id = None
    for tab_id, data in list(getattr(owner, "tabs_data", {}).items()):
        if str(data.get("filepath", "")) == str(filename):
            target_tab_id = tab_id
            break

    editor = None
    try:
        if target_tab_id is None:
            owner._create_editor_tab(str(filename), str(code))
            target_tab_id = owner._get_current_tab_id()
            if target_tab_id and target_tab_id in owner.tabs_data:
                editor = owner.tabs_data[target_tab_id].get("editor")
        else:
            owner.notebook.select(target_tab_id)
            editor = owner.tabs_data[target_tab_id].get("editor")
            if editor is None:
                return False
            editor.delete("1.0", tk.END)
            editor.insert("1.0", str(code))
    except tk.TclError:
        return False
    except Exception:
        return False

    if target_tab_id and target_tab_id in owner.tabs_data:
        owner.tabs_data[target_tab_id]["dirty"] = True
        try:
            owner._update_tab_title(target_tab_id)
        except Exception:
            pass

    if editor is not None:
        try:
            editor.focus_set()
        except tk.TclError:
            pass
    try:
        owner._schedule_highlight()
        owner._update_line_numbers()
        owner._update_cursor_status()
        owner._schedule_diagnose()
        owner._refresh_outline()
    except Exception:
        pass
    return bool(target_tab_id)


def export_ui_design_to_editor(owner):
    code = _generate_ym_code(owner)
    ok = _insert_code_to_editor(owner, code)
    if ok and hasattr(owner, "status_main_var"):
        owner.status_main_var.set("界面设计器：已导出到编辑区")
    return "break"


def export_ui_design_to_layered_editors(owner, event=None, choose_backend=False):
    del event
    backend = _normalize_data_backend(getattr(owner, "_ui_designer_data_backend", "sqlite"))
    prefix = _normalize_layer_export_prefix(getattr(owner, "_ui_designer_layer_export_prefix", "界面设计"))
    remembered = True
    remember_prefix = True
    if choose_backend:
        choice = _prompt_layer_export_backend(owner)
        if not choice:
            if hasattr(owner, "status_main_var"):
                owner.status_main_var.set("界面设计器：已取消导出三层代码")
            return "break"
        backend = _normalize_data_backend(choice.get("backend"))
        remembered = bool(choice.get("remember"))
        prefix = _normalize_layer_export_prefix(choice.get("prefix"), fallback=prefix)
        remember_prefix = bool(choice.get("remember_prefix"))
        if remembered:
            _set_data_backend(owner, backend)
        if remember_prefix:
            owner._ui_designer_layer_export_prefix = prefix
            if hasattr(owner, "_ui_designer_layer_export_prefix"):
                owner._ui_designer_layer_export_prefix = _normalize_layer_export_prefix(owner._ui_designer_layer_export_prefix)
        else:
            # 仅本次导出时，保持当前默认前缀不变。
            pass
        if remembered or remember_prefix:
            saver = getattr(owner, "_save_project_state", None)
            if callable(saver):
                try:
                    saver()
                except Exception:
                    pass

    ui_code, logic_code, data_code = _generate_layered_ym_codes(owner, data_backend=backend)
    data_filename = f"{prefix}_数据层.ym"
    logic_filename = f"{prefix}_业务层.ym"
    ui_filename = f"{prefix}_界面层.ym"
    ok_data = _upsert_code_to_named_tab(owner, data_filename, data_code)
    ok_logic = _upsert_code_to_named_tab(owner, logic_filename, logic_code)
    ok_ui = _upsert_code_to_named_tab(owner, ui_filename, ui_code)
    backend_label = _backend_label_of(backend)
    if ok_data and ok_logic and ok_ui and hasattr(owner, "status_main_var"):
        backend_suffix = "，并记住当前项目后端" if remembered else "，后端仅用于本次导出"
        prefix_suffix = "，并记住导出前缀" if remember_prefix else "，前缀仅用于本次导出"
        owner.status_main_var.set(
            f"界面设计器：已导出三层代码（前缀：{prefix}，后端：{backend_label}{backend_suffix}{prefix_suffix}）"
        )
    elif hasattr(owner, "status_main_var"):
        owner.status_main_var.set("界面设计器：导出三层代码失败")
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
    _ensure_component_baseline(owner)
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
    panel = _build_designer_panel(owner, win, title_text="界面设计器 UI DESIGNER")
    panel.pack(fill=tk.BOTH, expand=True)
    owner._ui_designer_window = win
    _render_canvas(owner)
    _refresh_property_panel(owner)
    return win


def _build_designer_panel(owner, parent, title_text="可视化界面设计 UI DESIGNER"):
    _ensure_component_baseline(owner)
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
    _create_data_backend_selector(owner, top)

    _tool_button(owner, top, "一键起步", lambda: run_ui_designer_quick_start(owner))
    _tool_button(owner, top, "复制代码", lambda: copy_ui_design_code(owner))
    _tool_button(owner, top, "导出三层代码...", lambda: export_ui_design_to_layered_editors(owner, choose_backend=True))
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
    palette = _build_palette_tree(owner, palette_wrap)
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
    tk.Button(
        action_left,
        text="一键起步",
        command=lambda: run_ui_designer_quick_start(owner),
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
    ).pack(side=tk.RIGHT)

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
    canvas.bind("<ButtonPress-1>", lambda e: _on_canvas_background_press(owner, e), add="+")
    canvas.bind("<B1-Motion>", lambda e: _on_canvas_motion(owner, e), add="+")
    canvas.bind("<ButtonRelease-1>", lambda e: _on_canvas_release(owner, e), add="+")

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
    owner._ui_designer_prop_hint_var = tk.StringVar(value="先选组件再编辑。灰色字段可忽略。")
    tk.Label(
        right,
        textvariable=owner._ui_designer_prop_hint_var,
        font=("Microsoft YaHei", 8),
        bg=owner.theme_panel_bg,
        fg="#8FA1B8",
        justify="left",
        anchor="w",
        padx=10,
        pady=0,
    ).pack(fill=tk.X, pady=(0, 4))

    prop_body = tk.Frame(right, bg=owner.theme_panel_bg, padx=10, pady=8)
    prop_body.pack(fill=tk.BOTH, expand=True)

    owner._ui_designer_prop_vars = {
        "name": tk.StringVar(value=""),
        "kind": tk.StringVar(value=""),
        "text": tk.StringVar(value=""),
        "event": tk.StringVar(value=""),
        "action_text": tk.StringVar(value=""),
        "columns": tk.StringVar(value=""),
        "rows": tk.StringVar(value=""),
        "x": tk.StringVar(value=""),
        "y": tk.StringVar(value=""),
        "w": tk.StringVar(value=""),
        "h": tk.StringVar(value=""),
    }
    prop_widgets = {}

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
        prop_widgets[key] = {"entry": entry, "readonly": bool(readonly)}
        return entry

    _row("标识", "name", readonly=True)
    _row("类型", "kind", readonly=True)
    _row("文本", "text")
    _row("按钮文案", "action_text")
    _row("函数", "event")
    _row("列定义", "columns")
    _row("行数", "rows")
    _row("X", "x")
    _row("Y", "y")
    _row("宽", "w")
    _row("高", "h")
    owner._ui_designer_prop_widgets = prop_widgets

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
        text="提示:\n1. 先点“一键起步”生成基础页面\n2. 左侧继续添加组件微调布局\n3. 右侧优先填写高亮属性\n4. 再导出到编辑区或导出三层代码",
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
