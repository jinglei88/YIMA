"""IDE shell initialization and shared owner-level helpers."""

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
import tkinter as tk
from tkinter import ttk


def initialize_editor(owner, root):
    self = owner
    self.root = root
    self.root.title("易码 - 极简中文编程语言")
    
    # 维护多标签状态数据
    # 格式: { tab_id: { "filepath": str, "editor": ScrolledText, "line_numbers": Text } }
    self.tabs_data = {}
    # 记录默认寻找目录
    self.workspace_dir = os.path.dirname(os.path.abspath(__file__))
    self.tool_root_dir = os.path.dirname(os.path.abspath(__file__))
    self.recent_projects = []
    self.last_project_dir = None
    self.last_open_file = None
    self.last_session_files = []
    self._state_dir = os.path.join(os.path.expanduser("~"), ".yima_ide")
    self._state_file = os.path.join(self._state_dir, "editor_state.json")
    self._highlight_after_id = None
    self._diagnose_after_id = None
    self._outline_after_id = None
    self._semantic_module_cache = {}
    self._py_module_member_cache = {}
    self._py_module_member_detail_cache = {}
    self._py_module_member_signature_cache = {}
    self._runtime_builtin_signature_cache = {}
    self._runtime_builtin_signature_loaded = False
    self.find_dialog = None
    self.find_var = tk.StringVar(value="")
    self.replace_var = tk.StringVar(value="")
    self._autocomplete_items = []
    self._autocomplete_row_ids = []
    self._autocomplete_replace_start = None
    self._autocomplete_replace_end = None
    self._autocomplete_popup_line = None
    self._autocomplete_mouse_down = False
    self._calltip_flash_after_id = None
    self.autocomplete_max_items = 16
    # 补全匹配策略：
    # - 默认 False：仅前缀匹配（更真实，避免误导）
    # - 设为 True：允许“包含匹配”作为兜底
    self.autocomplete_fuzzy_enabled = False
    self._last_edit_tab_id = None
    self._last_edit_index = None
    self._last_edit_word = ""
    self._last_edit_ts = 0.0
    self._load_project_state()
    self._pair_map = {
        "(": ")",
        "（": "）",
        "[": "]",
        "【": "】",
        "{": "}",
        "\"": "\"",
        "'": "'",
    }
    
    # 计算系统 DPI 缩放比例 (相对于标准的 96 DPI)
    self.dpi_scale = self.root.winfo_fpixels('1i') / 96.0
    if self.dpi_scale < 1.0:
        self.dpi_scale = 1.0
    
    # 加载并设置窗口图标与小图标
    self.icon_file = None
    try:
        logo_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logo.png")
        if os.path.exists(logo_path):
            img = tk.PhotoImage(file=logo_path)
            self.root.iconphoto(True, img)
            # 缩小为侧边栏使用的小图标
            # 高分屏下缩小倍数相应减小，使图标稍微变大
            subsample_factor = max(1, int(18 / self.dpi_scale))
            self.icon_file = img.subsample(subsample_factor, subsample_factor)
    except Exception as e:
        print(f"⚠️ 小提示：找不到图标文件 logo.png：{e}")
        
    # 根据系统缩放重设初始窗口大小（默认更大，并避免超出屏幕）
    screen_w = self.root.winfo_screenwidth()
    screen_h = self.root.winfo_screenheight()
    win_w = min(int(1200 * self.dpi_scale), max(900, int(screen_w * 0.94)))
    win_h = min(int(820 * self.dpi_scale), max(650, int(screen_h * 0.90)))
    self.root.geometry(f"{win_w}x{win_h}")
    self.root.configure(bg="#1A1E24")
    
    # 字体设定（使用大白话、符合国人习惯的微软雅黑）
    self.font_code = ("Microsoft YaHei", 10)
    self.font_ui = ("Microsoft YaHei", 9)
    self.font_ui_bold = ("Microsoft YaHei", 10, "bold")
    
    # 现代暗黑专业主题色调 (VS Code 风)
    self.theme_bg = "#1E1E1E"          # 编辑器 & 控制台主背景
    self.theme_sidebar_bg = "#1A202A"  # 侧边栏文件树背景
    self.theme_toolbar_bg = "#1C222B"  # 顶部工具栏 & 状态条背景
    self.theme_fg = "#CCCCCC"          # 默认普通文字颜色
    self.theme_line_bg = "#2D2D30"     # 当前行高亮颜色
    self.theme_gutter_bg = "#1E1E1E"   # 行号区背景色与主区融合
    self.theme_gutter_fg = "#858585"   # 行号文字颜色
    self.theme_sash = "#2B3544"        # 分割线颜色 (稍微提亮使其起分隔作用但不变宽)
    self.theme_toolbar_group_bg = "#242C37"
    self.theme_toolbar_border = "#323D4C"
    self.theme_toolbar_hover = "#2E3845"
    self.theme_toolbar_fg = "#DFE6EE"
    self.theme_toolbar_muted = "#9DABBE"
    self.theme_panel_bg = "#202833"
    self.theme_panel_inner_bg = "#171D26"
    self.theme_accent = "#1E7BC8"
    
    # 定义代码片段 (Snippets) 字典
    self.snippets = {
        "如果": "如果 真 就\n    显示 \"在这里写代码\"",
        "不然": "不然\n    显示 \"在这里写代码\"",
        "否则如果": "否则如果 真 就\n    显示 \"在这里写代码\"",
        "功能": "功能 新功能()\n    显示 \"功能已执行\"",
        "当": "当 真 的时候\n    显示 \"循环中\"",
        "重复": "重复 3 次\n    显示 \"循环中\"",
        "遍历": "数据 = 新列表(1, 2, 3)\n遍历 数据 里的每一个 叫做 项\n    显示 项",
        "尝试": "尝试\n    显示 \"执行中\"\n如果出错\n    显示 \"发生错误\"",
        "显示": "显示 \"这里是输出\"",
        "定义图纸": "定义图纸 用户(名字)\n    它的 名字 = 名字\n\n    功能 打招呼()\n        显示 \"你好，\" + 它的 名字",
    }

    self.builtin_words = self._builtin_word_catalog()
    
    # 智能联想词库 (合并了所有常用字面量、系统函数和代码片段)
    self.autocomplete_words = sorted(list(set(
        ["功能", "返回", "叫做", "尝试", "如果出错",
        "如果", "否则如果", "不然", "当", "的时候", "重复", "次", "遍历", "里的每一个", "停下", "略过",
        "引入", "输入", "定义图纸", "造一个", "它的",
        "对", "错", "空"] +
        self.builtin_words +
        list(self.snippets.keys())
    )))

    # 配置 ttk 全局样式以适配字体缩放与暗黑主题
    style = ttk.Style()
    # 统一使用 clam 主题作为基础以获得更好的跨平台扁平化外观
    try:
        style.theme_use("clam")
    except tk.TclError:
        pass
    
    # 行高也按比例缩放适配大字体
    scaled_rowheight = int(28 * self.dpi_scale)
    
    # 定制 Treeview
    style.configure("Treeview", font=self.font_ui, rowheight=scaled_rowheight,
                    background=self.theme_panel_inner_bg, foreground=self.theme_fg, fieldbackground=self.theme_panel_inner_bg, borderwidth=0)
    style.map("Treeview", background=[("selected", self.theme_accent)], foreground=[("selected", "#FFFFFF")])
    style.configure("Treeview.Heading", font=("Microsoft YaHei", 9, "bold"), background=self.theme_panel_bg, foreground="#CED8E5", borderwidth=0)

    # 定制暗黑简约滚动条
    style.configure("Vertical.TScrollbar", background="#3A4555", troughcolor=self.theme_panel_inner_bg, bordercolor=self.theme_panel_inner_bg, arrowcolor="#B6C5D8", relief="flat", borderwidth=0)
    style.configure("Horizontal.TScrollbar", background="#3A4555", troughcolor=self.theme_panel_inner_bg, bordercolor=self.theme_panel_inner_bg, arrowcolor="#B6C5D8", relief="flat", borderwidth=0)
    style.map("Vertical.TScrollbar", background=[("active", "#4C5D73")])
    style.map("Horizontal.TScrollbar", background=[("active", "#4C5D73")])
    style.configure(
        "YimaAutocomplete.Treeview",
        font=self.font_code,
        rowheight=int(max(22, 24 * self.dpi_scale)),
        background=self.theme_sidebar_bg,
        foreground=self.theme_fg,
        fieldbackground=self.theme_sidebar_bg,
        borderwidth=0,
    )
    style.map(
        "YimaAutocomplete.Treeview",
        background=[("selected", "#143A59")],
        foreground=[("selected", "#FFFFFF")],
    )
    style.configure(
        "YimaAutocomplete.Treeview.Heading",
        font=("Microsoft YaHei", 9, "bold"),
        background="#1B2A40",
        foreground="#C7D7EB",
        borderwidth=0,
        relief="flat",
    )
    
    # 定制 Notebook 标签页无缝沉浸式外观
    style.configure("TNotebook", background=self.theme_bg, borderwidth=0, padding=0)
    # 未选中的标签
    style.configure("TNotebook.Tab", font=self.font_ui, padding=[15, 6], background="#2D2D30", foreground="#888888", borderwidth=0, focuscolor=self.theme_bg)
    # 选中的标签完美融入背景 (无底边框)
    style.map("TNotebook.Tab", background=[("selected", self.theme_bg)], foreground=[("selected", "#FFFFFF")], expand=[("selected", [0, 1, 0, 0])])
    
    # 彻底干掉 Notebook 原生的客户端框线
    style.layout("TNotebook.client", [("Notebook.client", {"sticky": "nswe"})])

    self.setup_ui()
    self.bind_global_shortcuts()
    self.root.protocol("WM_DELETE_WINDOW", self.on_app_close)



def get_current_tab_id(owner):
    try:
        return owner.notebook.select()
    except tk.TclError:
        return None


def schedule_highlight(owner, event=None):
    del event
    if owner._highlight_after_id:
        try:
            owner.root.after_cancel(owner._highlight_after_id)
        except tk.TclError:
            pass
    owner._highlight_after_id = owner.root.after(80, owner.highlight)


def get_current_editor(owner):
    tab_id = owner._get_current_tab_id()
    if tab_id and tab_id in owner.tabs_data:
        return owner.tabs_data[tab_id]["editor"]
    return None


def get_current_line_numbers(owner):
    tab_id = owner._get_current_tab_id()
    if tab_id and tab_id in owner.tabs_data:
        return owner.tabs_data[tab_id]["line_numbers"]
    return None


def get_tab_id_by_editor(owner, editor):
    for tab_id, data in owner.tabs_data.items():
        if data.get("editor") is editor:
            return tab_id
    return None


def update_tab_title(owner, tab_id):
    if tab_id not in owner.tabs_data:
        return
    filepath = owner.tabs_data[tab_id].get("filepath", "未命名代码.ym")
    display_name = os.path.basename(filepath) if filepath != "未命名代码.ym" else "未命名代码.ym"
    dirty_prefix = "● " if owner.tabs_data[tab_id].get("dirty") else ""
    try:
        owner.notebook.tab(tab_id, text=f" {dirty_prefix}{display_name}   ✖ ")
    except tk.TclError:
        pass
