# d:\易码\易码编辑器.py
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
from tkinter import scrolledtext, filedialog, messagebox, simpledialog, ttk
from tkinter import font as tkfont
import sys
import io
import shutil
import re
import builtins
import os
import json
import inspect
import importlib
import importlib.util
import time

# 将当前目录添加到系统路径，确保能找到 yima 包
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from 易码 import 执行源码
from yima.错误 import 易码错误
from yima.词法分析 import 词法分析器, Token类型
from yima.语法分析 import 语法分析器

class 易码IDE:
    def __init__(self, root):
        self.root = root
        self.root.title("易码 - 极简中文编程语言")
        
        # 维护多标签状态数据
        # 格式: { tab_id: { "filepath": str, "editor": ScrolledText, "line_numbers": Text } }
        self.tabs_data = {}
        # 记录默认寻找目录
        self.workspace_dir = os.path.dirname(os.path.abspath(__file__))
        self.recent_projects = []
        self.last_project_dir = None
        self.last_open_file = None
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
            "如果": "如果 ‹条件› 就\n    ‹代码›",
            "不然": "不然\n    ‹代码›",
            "否则如果": "否则如果 ‹条件› 就\n    ‹代码›",
            "功能": "功能 ‹名字›(‹参数›)\n    ‹代码›",
            "当": "当 ‹条件› 的时候\n    ‹代码›",
            "重复": "重复 ‹次数› 次\n    ‹代码›",
            "遍历": "遍历 ‹列表› 里的每一个 叫做 ‹元素›\n    ‹代码›",
            "尝试": "尝试\n    ‹可能出错的代码›\n如果出错\n    ‹处理错误›",
            "显示": "显示 ‹内容›",
            "定义图纸": "定义图纸 ‹名字›(‹属性›)\n    它的 ‹属性› = ‹属性›\n\n    功能 ‹方法›()\n        ‹代码›",
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

    def _builtin_word_catalog(self):
        return [
            "新列表", "加入", "插入", "长度", "删除",
            "转数字", "转文字", "取随机数",
            "所有键", "所有值", "存在",
            "截取", "查找", "替换", "分割", "去空格", "包含",
            "读文件", "写文件", "追加文件",
            "文件存在", "目录存在", "创建目录", "列出目录", "删除文件", "删除目录",
            "复制文件", "移动文件", "重命名", "遍历文件",
            "复制目录", "压缩目录", "解压缩", "哈希文本", "哈希文件", "下载文件",
            "匹配文件", "文件信息", "目录大小", "格式时间", "解析时间", "写日志", "读日志", "睡眠",
            "拼路径", "绝对路径", "当前目录", "读环境变量", "写环境变量", "执行命令",
            "解析JSON", "生成JSON", "读JSON", "写JSON", "读CSV", "写CSV", "读INI", "写INI",
            "发起请求", "发GET", "发POST", "读响应JSON", "发GET_JSON", "发POST_JSON",
            "打开数据库", "执行SQL", "查询SQL", "开始事务", "提交事务", "回滚事务", "关闭数据库",
            "排序", "倒序", "去重", "合并", "最大值", "最小值",
            "绝对值", "四舍五入", "现在时间", "时间戳",
            "类型",
            "显示", "输入",
            "建窗口", "加文字", "加输入框", "加按钮", "读输入", "改文字", "弹窗", "弹窗输入", "打开界面",
            "加表格", "表格加行", "表格清空", "表格所有行", "表格选中行", "表格选中序号", "表格删行", "表格改行",
            "画布", "标题", "图标", "向前走", "向后走", "左转", "右转", "抬笔", "落笔", "画笔颜色", "背景颜色", "去", "笔粗",
            "画圆", "停一下", "定格", "速度", "隐藏画笔", "关闭动画", "刷新画面", "清除", "写字", "开始监听", "绑定按键",
            "计算距离", "当前X", "当前Y",
        ]

    def _builtin_module_exports(self):
        return {
            "文件管理": ["读文件", "写文件", "追加文件"],
            "系统工具": [
                "文件存在", "目录存在", "创建目录", "列出目录", "删除文件", "删除目录",
                "复制文件", "移动文件", "重命名", "遍历文件",
                "复制目录", "压缩目录", "解压缩", "哈希文本", "哈希文件", "下载文件",
                "匹配文件", "文件信息", "目录大小", "格式时间", "解析时间", "写日志", "读日志", "睡眠",
                "拼路径", "绝对路径", "当前目录", "读环境变量", "写环境变量", "执行命令",
            ],
            "数据工具": ["解析JSON", "生成JSON", "读JSON", "写JSON", "读CSV", "写CSV", "读INI", "写INI"],
            "网络请求": ["发起请求", "发GET", "发POST", "读响应JSON", "发GET_JSON", "发POST_JSON"],
            "本地数据库": ["打开数据库", "执行SQL", "查询SQL", "关闭数据库", "开始事务", "提交事务", "回滚事务"],
            "图形界面": [
                "建窗口", "加文字", "加输入框", "读输入", "改文字", "加按钮", "弹窗", "弹窗输入", "打开界面",
                "加表格", "表格加行", "表格清空", "表格所有行", "表格选中行", "表格选中序号", "表格删行", "表格改行",
            ],
            "画板": [
                "画布", "标题", "图标", "向前走", "向后走", "左转", "右转", "抬笔", "落笔", "画笔颜色",
                "背景颜色", "去", "笔粗", "画圆", "停一下", "定格", "速度", "隐藏画笔", "关闭动画",
                "刷新画面", "清除", "写字", "开始监听", "绑定按键", "计算距离", "当前X", "当前Y",
            ],
            "魔法生态库": sorted(self.builtin_words),
        }

    def _style_scrolledtext_vbar(self, text_widget, parent=None):
        """
        统一 ScrolledText 滚动条为暗色。
        - 若传 parent：隐藏内置 tk.Scrollbar，改用 ttk.Scrollbar（推荐，跨平台稳定）
        - 若不传 parent：兜底样式化内置 tk.Scrollbar
        """
        try:
            frame = getattr(text_widget, "frame", None)
            if frame:
                frame.configure(bg=self.theme_bg, bd=0, highlightthickness=0)
        except tk.TclError:
            pass

        if parent is not None:
            内置条 = getattr(text_widget, "vbar", None)
            if 内置条:
                try:
                    内置条.pack_forget()
                except tk.TclError:
                    pass
            外挂条 = ttk.Scrollbar(parent, orient="vertical", command=text_widget.yview)
            外挂条.pack(side=tk.RIGHT, fill=tk.Y)
            text_widget.configure(yscrollcommand=外挂条.set)
            text_widget.vbar = 外挂条
            return

        vbar = getattr(text_widget, "vbar", None)
        if not vbar:
            return

        scrollbar_width = max(10, int(11 * self.dpi_scale))
        style_options = {
            "width": scrollbar_width,
            "bg": "#3A4555",
            "activebackground": "#4C5D73",
            "troughcolor": self.theme_panel_inner_bg,
            "relief": "flat",
            "borderwidth": 0,
            "highlightthickness": 0,
            "elementborderwidth": 0,
            "highlightbackground": self.theme_panel_inner_bg,
            "highlightcolor": self.theme_panel_inner_bg,
        }
        for key, value in style_options.items():
            try:
                vbar.configure(**{key: value})
            except tk.TclError:
                pass

    def setup_ui(self):
        # 顶部现代化菜单栏（分组 + 主按钮）
        toolbar_shell = tk.Frame(
            self.root,
            bg=self.theme_toolbar_bg,
            highlightthickness=1,
            highlightbackground=self.theme_toolbar_border,
            highlightcolor=self.theme_toolbar_border,
            bd=0,
        )
        toolbar_shell.pack(fill=tk.X)

        toolbar = tk.Frame(toolbar_shell, bg=self.theme_toolbar_bg, padx=12, pady=8)
        toolbar.pack(fill=tk.X)

        def create_tool_btn(parent, text, cmd, variant="ghost", font=None, compact=False):
            style_map = {
                "ghost": {
                    "bg": self.theme_toolbar_group_bg,
                    "fg": self.theme_toolbar_fg,
                    "hover_bg": self.theme_toolbar_hover,
                    "hover_fg": "#FFFFFF",
                    "border": self.theme_toolbar_border,
                    "hover_border": "#4F627B",
                },
                "run": {
                    "bg": "#2E7D32",
                    "fg": "#FFFFFF",
                    "hover_bg": "#3D9742",
                    "hover_fg": "#FFFFFF",
                    "border": "#459E4A",
                    "hover_border": "#67B96C",
                },
                "accent": {
                    "bg": "#0E639C",
                    "fg": "#FFFFFF",
                    "hover_bg": "#1577B8",
                    "hover_fg": "#FFFFFF",
                    "border": "#2D82BC",
                    "hover_border": "#4A9DCE",
                },
                "subtle": {
                    "bg": self.theme_panel_bg,
                    "fg": "#C9D4E1",
                    "hover_bg": self.theme_toolbar_hover,
                    "hover_fg": "#FFFFFF",
                    "border": self.theme_toolbar_border,
                    "hover_border": "#4F627B",
                },
            }
            conf = style_map.get(variant, style_map["ghost"])
            pad_x = 8 if compact else 10
            pad_y = 2 if compact else 4
            btn = tk.Button(
                parent,
                text=text,
                command=cmd,
                font=font or self.font_ui,
                bg=conf["bg"],
                fg=conf["fg"],
                activebackground=conf["hover_bg"],
                activeforeground=conf["hover_fg"],
                relief="flat",
                borderwidth=0,
                highlightthickness=1,
                highlightbackground=conf["border"],
                highlightcolor=conf["border"],
                cursor="hand2",
                padx=pad_x,
                pady=pad_y,
                takefocus=0,
            )
            def _enter(_e):
                btn.configure(
                    bg=conf["hover_bg"],
                    fg=conf["hover_fg"],
                    highlightbackground=conf["hover_border"],
                    highlightcolor=conf["hover_border"],
                )
            def _leave(_e):
                btn.configure(
                    bg=conf["bg"],
                    fg=conf["fg"],
                    highlightbackground=conf["border"],
                    highlightcolor=conf["border"],
                )
            btn.bind("<Enter>", _enter)
            btn.bind("<Leave>", _leave)
            return btn

        def create_tool_group(group_name, items):
            group_frame = tk.Frame(
                toolbar,
                bg=self.theme_toolbar_group_bg,
                highlightthickness=1,
                highlightbackground=self.theme_toolbar_border,
                highlightcolor=self.theme_toolbar_border,
                bd=0,
            )
            group_frame.pack(side=tk.LEFT, padx=(0, 8))
            tk.Label(
                group_frame,
                text=group_name,
                bg=self.theme_toolbar_group_bg,
                fg=self.theme_toolbar_muted,
                font=("Microsoft YaHei", 8, "bold"),
                padx=8,
            ).pack(side=tk.LEFT, pady=4)
            for btn_text, btn_cmd in items:
                create_tool_btn(group_frame, btn_text, btn_cmd, variant="ghost").pack(side=tk.LEFT, padx=(0, 4), pady=4)
            return group_frame

        right_actions = tk.Frame(toolbar, bg=self.theme_toolbar_bg)
        right_actions.pack(side=tk.RIGHT)
        create_tool_btn(
            right_actions,
            "导出软件(exe)",
            self.export_exe,
            variant="accent",
            font=("Microsoft YaHei", 10, "bold"),
        ).pack(side=tk.RIGHT, ipadx=6)

        create_tool_btn(
            right_actions,
            "运行代码",
            self.run_code,
            variant="run",
            font=("Microsoft YaHei", 10, "bold"),
        ).pack(side=tk.RIGHT, padx=(0, 10), ipadx=6)

        create_tool_group("项目", [
            ("新建", self.new_project),
            ("打开", self.open_project),
            ("历史", self.open_recent_project_menu),
        ])
        create_tool_group("文件", [
            ("打开单文件", self.open_file),
            ("保存代码", self.save_file),
        ])
        create_tool_group("编辑", [
            ("查找替换", self.open_find_dialog),
            ("同词多光标", self.multi_cursor_add_next),
            ("重命名", self.rename_symbol),
        ])

        tk.Frame(self.root, height=1, bg=self.theme_toolbar_border, bd=0).pack(fill=tk.X)

        # 主分割区 (外层水平分割：左拉侧边栏，右拉主界面)
        # 将分割线收拢到极致 1px
        self.main_paned = tk.PanedWindow(self.root, orient=tk.HORIZONTAL, sashwidth=1, bg=self.theme_sash, borderwidth=0)
        self.main_paned.pack(fill=tk.BOTH, expand=True)
        
        # --- 左侧：资源管理器 (Sidebar) ---
        sidebar_frame = tk.Frame(self.main_paned, bg=self.theme_sidebar_bg)

        sidebar_header = tk.Frame(sidebar_frame, bg=self.theme_sidebar_bg, padx=10, pady=10)
        sidebar_header.pack(fill=tk.X)
        title_wrap = tk.Frame(sidebar_header, bg=self.theme_sidebar_bg)
        title_wrap.pack(side=tk.LEFT, fill=tk.X, expand=True)
        tk.Label(
            title_wrap,
            text="资源管理器",
            font=("Microsoft YaHei", 10, "bold"),
            bg=self.theme_sidebar_bg,
            fg="#E7EDF7",
            anchor="w",
        ).pack(anchor="w")
        tk.Label(
            title_wrap,
            text="EXPLORER",
            font=("Microsoft YaHei", 8),
            bg=self.theme_sidebar_bg,
            fg="#8FA1B8",
            anchor="w",
        ).pack(anchor="w")
        create_tool_btn(
            sidebar_header,
            "刷新",
            self.refresh_file_tree,
            variant="subtle",
            compact=True,
            font=("Microsoft YaHei", 8),
        ).pack(side=tk.RIGHT, padx=(6, 0))

        # 文件列表树容器（卡片化）
        tree_card = tk.Frame(
            sidebar_frame,
            bg=self.theme_panel_bg,
            highlightthickness=1,
            highlightbackground=self.theme_toolbar_border,
            highlightcolor=self.theme_toolbar_border,
            bd=0,
        )
        tree_card.pack(fill=tk.BOTH, expand=True, padx=8, pady=(0, 8))
        tree_container = tk.Frame(tree_card, bg=self.theme_panel_inner_bg)
        tree_container.pack(fill=tk.BOTH, expand=True, padx=1, pady=1)

        self.tree = ttk.Treeview(tree_container, selectmode="browse")

        # 滚动条 (垂直 + 水平)
        vsb = ttk.Scrollbar(tree_container, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(tree_container, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self.tree.grid(column=0, row=0, sticky="nsew")
        vsb.grid(column=1, row=0, sticky="ns")
        hsb.grid(column=0, row=1, sticky="ew")

        tree_container.grid_columnconfigure(0, weight=1)
        tree_container.grid_rowconfigure(0, weight=1)

        # 代码结构大纲区（功能 / 图纸导航 + 折叠）
        outline_section = tk.Frame(
            sidebar_frame,
            bg=self.theme_panel_bg,
            highlightthickness=1,
            highlightbackground=self.theme_toolbar_border,
            highlightcolor=self.theme_toolbar_border,
            bd=0,
        )
        outline_section.pack(fill=tk.X, padx=8, pady=(0, 8))
        outline_top = tk.Frame(outline_section, bg=self.theme_panel_bg, padx=8, pady=6)
        outline_top.pack(fill=tk.X)

        tk.Label(
            outline_top,
            text="代码大纲 OUTLINE",
            font=("Microsoft YaHei", 8, "bold"),
            bg=self.theme_panel_bg,
            fg="#8FA1B8",
            anchor="w",
        ).pack(side=tk.LEFT, fill=tk.X, expand=True)

        create_tool_btn(
            outline_top,
            "折叠/展开",
            self.toggle_fold_from_outline,
            variant="subtle",
            compact=True,
            font=("Microsoft YaHei", 8),
        ).pack(side=tk.RIGHT, padx=(4, 0))
        create_tool_btn(
            outline_top,
            "全部展开",
            self.unfold_all_blocks,
            variant="subtle",
            compact=True,
            font=("Microsoft YaHei", 8),
        ).pack(side=tk.RIGHT)

        outline_container = tk.Frame(outline_section, bg=self.theme_panel_bg, padx=8)
        outline_container.pack(fill=tk.X, pady=(0, 8))

        self.outline_listbox = tk.Listbox(
            outline_container,
            height=9,
            font=self.font_ui,
            bg=self.theme_panel_inner_bg,
            fg=self.theme_fg,
            selectbackground=self.theme_accent,
            selectforeground="#FFFFFF",
            borderwidth=0,
            highlightthickness=0,
            relief="flat",
        )
        outline_vsb = ttk.Scrollbar(outline_container, orient="vertical", command=self.outline_listbox.yview)
        self.outline_listbox.configure(yscrollcommand=outline_vsb.set)

        self.outline_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        outline_vsb.pack(side=tk.RIGHT, fill=tk.Y)

        self.outline_listbox.bind("<Double-Button-1>", self.on_outline_activate)
        self.outline_listbox.bind("<Return>", self.on_outline_activate)
        self.outline_listbox.bind("<ButtonRelease-1>", self._outline_update_status)

        # 语法/语义问题区（可点击跳转）
        issue_section = tk.Frame(
            sidebar_frame,
            bg=self.theme_panel_bg,
            highlightthickness=1,
            highlightbackground=self.theme_toolbar_border,
            highlightcolor=self.theme_toolbar_border,
            bd=0,
        )
        issue_section.pack(fill=tk.X, padx=8, pady=(0, 10))
        issue_top = tk.Frame(issue_section, bg=self.theme_panel_bg, padx=8, pady=6)
        issue_top.pack(fill=tk.X)

        tk.Label(
            issue_top,
            text="问题列表 ISSUES",
            font=("Microsoft YaHei", 8, "bold"),
            bg=self.theme_panel_bg,
            fg="#8FA1B8",
            anchor="w",
        ).pack(side=tk.LEFT, fill=tk.X, expand=True)

        self.issue_count_var = tk.StringVar(value="0")
        tk.Label(
            issue_top,
            textvariable=self.issue_count_var,
            font=("Microsoft YaHei", 8, "bold"),
            bg=self.theme_panel_inner_bg,
            fg="#9FCBFF",
            padx=8,
            pady=1,
            anchor="e",
        ).pack(side=tk.RIGHT)

        issue_container = tk.Frame(issue_section, bg=self.theme_panel_bg, padx=8)
        issue_container.pack(fill=tk.X, pady=(0, 8))

        self.issue_listbox = tk.Listbox(
            issue_container,
            height=7,
            font=self.font_ui,
            bg=self.theme_panel_inner_bg,
            fg=self.theme_fg,
            selectbackground=self.theme_accent,
            selectforeground="#FFFFFF",
            borderwidth=0,
            highlightthickness=0,
            relief="flat",
        )
        issue_vsb = ttk.Scrollbar(issue_container, orient="vertical", command=self.issue_listbox.yview)
        issue_hsb = ttk.Scrollbar(issue_container, orient="horizontal", command=self.issue_listbox.xview)
        self.issue_listbox.configure(yscrollcommand=issue_vsb.set, xscrollcommand=issue_hsb.set)

        self.issue_listbox.grid(column=0, row=0, sticky="nsew")
        issue_vsb.grid(column=1, row=0, sticky="ns")
        issue_hsb.grid(column=0, row=1, sticky="ew")
        issue_container.grid_columnconfigure(0, weight=1)
        issue_container.grid_rowconfigure(0, weight=1)

        self.issue_listbox.bind("<Double-Button-1>", self.on_issue_activate)
        self.issue_listbox.bind("<Return>", self.on_issue_activate)
        self.issue_listbox.bind("<ButtonRelease-1>", self._issue_update_status)
        
        # 初始给左侧多分配一点空间，防止文字被遮挡
        sidebar_default_width = int(250 * self.dpi_scale)
        self.main_paned.add(sidebar_frame, stretch="never", minsize=sidebar_default_width)
        
        # --- 右侧：内层垂直分割（上代码，下输出） ---
        self.right_paned = tk.PanedWindow(
            self.main_paned,
            orient=tk.VERTICAL,
            sashwidth=max(6, int(6 * self.dpi_scale)),
            showhandle=True,
            handlesize=max(9, int(9 * self.dpi_scale)),
            handlepad=max(2, int(2 * self.dpi_scale)),
            sashrelief="raised",
            bg=self.theme_sash,
            borderwidth=0,
        )
        try:
            self.right_paned.configure(sashcursor="sb_v_double_arrow")
        except tk.TclError:
            try:
                self.right_paned.configure(sashcursor="size_ns")
            except tk.TclError:
                pass
        self.main_paned.add(self.right_paned, stretch="always", minsize=600)
        
        # 代码多标签区 (Notebook)
        editor_frame = tk.Frame(self.right_paned, bg=self.theme_bg, borderwidth=0)
        
        self.notebook = ttk.Notebook(editor_frame, padding=0)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        self.notebook.bind("<Button-1>", self.on_tab_click)
        
        self.right_paned.add(editor_frame, stretch="always", minsize=400)
        
        # 输出区
        output_frame = tk.Frame(
            self.right_paned,
            bg=self.theme_bg,
            highlightthickness=1,
            highlightbackground=self.theme_toolbar_border,
            highlightcolor=self.theme_toolbar_border,
            bd=0,
        )
        
        # 输出区顶栏
        out_top = tk.Frame(output_frame, bg=self.theme_panel_bg, padx=2, pady=1)
        out_top.pack(fill=tk.X)
        tk.Label(
            out_top,
            text="调试控制台（开发日志）",
            font=("Microsoft YaHei", 9, "bold"),
            bg=self.theme_panel_bg,
            fg="#E7EDF7",
            anchor="w",
            padx=15,
            pady=4,
        ).pack(side=tk.LEFT)
        tk.Label(
            out_top,
            text="用于：运行日志 / 报错定位",
            font=("Microsoft YaHei", 8),
            bg=self.theme_panel_bg,
            fg="#9FB0C5",
            anchor="w",
            padx=8,
        ).pack(side=tk.LEFT)
        清空按钮 = create_tool_btn(
            out_top,
            text="清空",
            cmd=self._clear_output_console,
            variant="subtle",
            compact=True,
            font=("Microsoft YaHei", 8, "bold"),
        )
        清空按钮.pack(side=tk.RIGHT, padx=(0, 8))
        
        terminal_font = ("Consolas" if sys.platform == "win32" else "Courier New", 11)
        self.output = scrolledtext.ScrolledText(output_frame, font=terminal_font, height=9, bg=self.theme_bg, fg="#A8C7FA", state=tk.DISABLED, padx=15, pady=5, spacing1=3, borderwidth=0, relief="flat", highlightthickness=0, insertbackground="#CCCCCC")
        self.output.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self._style_scrolledtext_vbar(self.output, parent=output_frame)
        self.right_paned.add(output_frame, stretch="never", minsize=120)
        self._clear_output_console(keep_intro=True)

        # 底部状态栏（当前文件 / 语法诊断 / 光标位置）
        status_bar = tk.Frame(
            self.root,
            bg="#171C23",
            height=int(28 * self.dpi_scale),
            highlightthickness=1,
            highlightbackground=self.theme_toolbar_border,
            highlightcolor=self.theme_toolbar_border,
            bd=0,
        )
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        status_bar.pack_propagate(False)

        self.status_main_var = tk.StringVar(value="就绪")
        self.status_diag_var = tk.StringVar(value="语法检查：等待输入")
        self.status_pos_var = tk.StringVar(value="行 1，列 1")

        tk.Label(
            status_bar,
            textvariable=self.status_main_var,
            font=self.font_ui,
            bg="#171C23",
            fg="#D7E0EC",
            anchor="w",
            padx=10
        ).pack(side=tk.LEFT, fill=tk.X, expand=True)

        tk.Frame(status_bar, width=1, bg=self.theme_toolbar_border).pack(side=tk.RIGHT, fill=tk.Y, pady=5)

        self.status_diag_label = tk.Label(
            status_bar,
            textvariable=self.status_diag_var,
            font=self.font_ui,
            bg="#171C23",
            fg="#A9D6B3",
            anchor="e",
            padx=8
        )
        self.status_diag_label.pack(side=tk.RIGHT)
        self.status_diag_label.bind("<Button-1>", self.jump_to_diagnostic)
        self.status_diag_label.configure(cursor="hand2")

        tk.Frame(status_bar, width=1, bg=self.theme_toolbar_border).pack(side=tk.RIGHT, fill=tk.Y, pady=5)

        tk.Label(
            status_bar,
            textvariable=self.status_pos_var,
            font=self.font_ui,
            bg="#171C23",
            fg="#D7E0EC",
            anchor="e",
            padx=10
        ).pack(side=tk.RIGHT)
        
        # 树状图右键菜单
        self.tree_menu = tk.Menu(self.root, tearoff=0, font=self.font_ui)
        self.tree_menu.add_command(label="📄 新建代码文件", command=self.create_new_file_in_tree)
        self.tree_menu.add_command(label="📁 新建文件夹", command=self.create_new_folder_in_tree)
        self.tree_menu.add_separator()
        self.tree_menu.add_command(label="🗑️ 删除", command=self.delete_item_in_tree)
        
        # 智能弹出提示框（双列：类型 + 候选）
        self.autocomplete_popup = tk.Frame(
            self.root,
            bg=self.theme_toolbar_border,
            bd=1,
            highlightthickness=1,
            highlightbackground="#102033",
            highlightcolor="#1E3B5B",
        )
        self.autocomplete_tree = ttk.Treeview(
            self.autocomplete_popup,
            columns=("kind", "item"),
            show="headings",
            selectmode="browse",
            style="YimaAutocomplete.Treeview",
        )
        self.autocomplete_tree.heading("kind", text="类型")
        self.autocomplete_tree.heading("item", text="候选")
        self.autocomplete_tree.column("kind", anchor="w", width=120, minwidth=90, stretch=False)
        self.autocomplete_tree.column("item", anchor="w", width=280, minwidth=180, stretch=True)
        self.autocomplete_vsb = ttk.Scrollbar(self.autocomplete_popup, orient="vertical", command=self.autocomplete_tree.yview)
        self.autocomplete_hsb = ttk.Scrollbar(self.autocomplete_popup, orient="horizontal", command=self.autocomplete_tree.xview)
        self.autocomplete_tree.configure(yscrollcommand=self.autocomplete_vsb.set, xscrollcommand=self.autocomplete_hsb.set)
        self.autocomplete_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.autocomplete_vsb.pack(side=tk.RIGHT, fill=tk.Y)
        self.autocomplete_hsb.pack(side=tk.BOTTOM, fill=tk.X)
        self.autocomplete_popup.place_forget()

        self.autocomplete_tree.bind("<ButtonPress-1>", self._on_autocomplete_mouse_press)
        self.autocomplete_tree.bind("<Up>", self._handle_autocomplete_nav)
        self.autocomplete_tree.bind("<Down>", self._handle_autocomplete_nav)
        self.autocomplete_tree.bind("<Prior>", self._handle_autocomplete_nav)
        self.autocomplete_tree.bind("<Next>", self._handle_autocomplete_nav)
        self.autocomplete_tree.bind("<Return>", self._accept_autocomplete)
        self.autocomplete_tree.bind("<KP_Enter>", self._accept_autocomplete)
        self.autocomplete_tree.bind("<Escape>", lambda e: (self._hide_autocomplete(), "break")[1])
        self.autocomplete_tree.bind("<ButtonRelease-1>", self._accept_autocomplete)
        self.autocomplete_tree.bind("<Double-Button-1>", self._accept_autocomplete)

        # 参数提示（Call Tip）
        self.calltip_popup = tk.Frame(
            self.root,
            bg="#0F1B2B",
            bd=1,
            highlightthickness=1,
            highlightbackground="#2B4664",
            highlightcolor="#2B4664",
        )
        self.calltip_label = tk.Label(
            self.calltip_popup,
            text="",
            font=self.font_code,
            bg="#0F1B2B",
            fg="#DCEBFF",
            anchor="w",
            justify="left",
            padx=8,
            pady=4,
        )
        self.calltip_label.pack(fill=tk.BOTH, expand=True)
        self.calltip_popup.place_forget()
        
        # 初始化界面后：优先恢复上次项目；恢复失败则创建默认代码页
        if not self._try_restore_last_project():
            self.refresh_file_tree()
            self._create_editor_tab("未命名代码.ym")

    def setup_tags(self, editor=None):
        target_editor = editor if editor else self._get_current_editor()
        if not target_editor:
            return
            
        # 设定语法高亮颜色 (采用舒适的现代护眼主题)
        target_editor.tag_configure("Keyword", foreground="#C586C0", font=(self.font_code[0], self.font_code[1], "bold"))  # 紫红：控制流
        target_editor.tag_configure("Define", foreground="#569CD6", font=(self.font_code[0], self.font_code[1], "bold"))   # 蓝色：定义类
        target_editor.tag_configure("Operator", foreground="#D4D4D4") # 灰色：操作符 (不再加粗)
        target_editor.tag_configure("String", foreground="#CE9178")                                         # 棕橙：字符串
        target_editor.tag_configure("Number", foreground="#B5CEA8")                                         # 浅绿：数字
        target_editor.tag_configure("Comment", foreground="#6A9955", font=(self.font_code[0], self.font_code[1], "italic"))# 幽绿：注释
        target_editor.tag_configure("Boolean", foreground="#4FC1FF", font=(self.font_code[0], self.font_code[1], "bold"))  # 亮蓝：布尔值
        target_editor.tag_configure("Builtin", foreground="#DCDCAA", font=(self.font_code[0], self.font_code[1], "bold"))  # 浅黄：内置函数
        target_editor.tag_configure("ModuleAlias", foreground="#4FC1FF", font=(self.font_code[0], self.font_code[1], "bold"))  # 模块别名对象（如 系统）
        target_editor.tag_configure("ObjectRef", foreground="#9CDCFE")  # 普通对象变量（如 工具）
        target_editor.tag_configure("MemberName", foreground="#FFD27F", font=(self.font_code[0], self.font_code[1], "bold"))  # 点调用成员（如 断言相等）
        target_editor.tag_configure("ErrorLine", background="#51222A")
        target_editor.tag_configure("WarnLine", background="#4D4521")
        target_editor.tag_configure("SearchMatch", background="#3B3A1A", foreground="#F3E99A")
        target_editor.tag_configure("SearchCurrent", background="#6A5C1A", foreground="#FFF4AA")
        target_editor.tag_configure("MultiCursorSel", background="#1D4B63", foreground="#FFFFFF")
        
        # 控制台专用标签
        self.output.tag_configure("ConsoleError", foreground="#FF6B6B", font=(self.output.cget("font"),))
        
        # 当前行高亮
        target_editor.tag_configure("CurrentLine", background=self.theme_line_bg)
        target_editor.tag_lower("CurrentLine")
        target_editor.tag_raise("ErrorLine")
        target_editor.tag_raise("WarnLine")
        target_editor.tag_raise("SearchMatch")
        target_editor.tag_raise("SearchCurrent")
        target_editor.tag_raise("MultiCursorSel")
        target_editor.tag_raise("ModuleAlias")
        target_editor.tag_raise("ObjectRef")
        target_editor.tag_raise("MemberName")
        
    def bind_events(self, editor=None):
        target_editor = editor if editor else self._get_current_editor()
        if not target_editor:
            return
            
        target_editor.bind("<KeyRelease>", self._remember_edit_cursor, add="+")
        target_editor.bind("<KeyRelease>", self._schedule_highlight)
        target_editor.bind("<KeyRelease>", self._update_line_numbers, add="+")
        target_editor.bind("<KeyRelease>", self._highlight_current_line, add="+")
        target_editor.bind("<KeyRelease>", self._schedule_diagnose, add="+")
        target_editor.bind("<KeyRelease>", self._schedule_outline_update, add="+")
        target_editor.bind("<KeyRelease>", self._update_cursor_status, add="+")
        target_editor.bind("<ButtonRelease>", self._highlight_current_line, add="+")
        target_editor.bind("<ButtonRelease>", self._update_cursor_status, add="+")
        target_editor.bind("<ButtonRelease>", self._schedule_calltip_update, add="+")
        target_editor.bind("<ButtonRelease>", self._remember_edit_cursor, add="+")
        target_editor.bind("<ButtonRelease-1>", self._sync_insert_after_click, add="+")
        target_editor.bind("<MouseWheel>", self._update_line_numbers, add="+")
        target_editor.bind("<Configure>", self._update_line_numbers, add="+")
        target_editor.bind("<FocusIn>", self._update_cursor_status, add="+")
        target_editor.bind("<<Modified>>", self._on_editor_modified, add="+")
        target_editor.bind("<Alt-Button-1>", self.multi_cursor_alt_click, add="+")
        target_editor.bind("<KeyPress>", self._handle_multi_cursor_key, add="+")
        target_editor.bind("<KeyPress>", self._handle_auto_pairs, add="+")
        
        # 智能回车换行与自动缩进
        target_editor.bind("<Return>", self._handle_return)
        target_editor.bind("<KP_Enter>", self._handle_return)
        
        # Tab 键代码片段补全 / 多行缩进 / 占位符跳转
        target_editor.bind("<Tab>", self._handle_tab)
        target_editor.bind("<Shift-Tab>", self._handle_shift_tab)
        
        # 绑定资源管理器双击事件和右键菜单事件
        self.tree.bind("<Double-1>", self.on_tree_double_click)
        self.tree.bind("<Button-3>", self.popup_tree_menu) 
        
        # 绑定 Tab 切换事件以恢复高亮
        self.notebook.bind("<<NotebookTabChanged>>", self.on_tab_changed)
        
        # 智能联想按键绑定
        target_editor.bind("<KeyRelease>", self._check_autocomplete, add="+")
        target_editor.bind("<FocusOut>", self._on_editor_focus_out)
        target_editor.bind("<Button-1>", self._handle_editor_left_click)
        target_editor.bind("<Up>", self._handle_autocomplete_nav)
        target_editor.bind("<Down>", self._handle_autocomplete_nav)
        target_editor.bind("<Prior>", self._handle_autocomplete_nav)
        target_editor.bind("<Next>", self._handle_autocomplete_nav)
        target_editor.bind("<Escape>", lambda e: self._hide_autocomplete())
        target_editor.bind("<Control-space>", self._trigger_autocomplete)
    # ==========================
    # 编辑器核心组件获取
    # ==========================
    def _get_current_tab_id(self):
        try:
            return self.notebook.select()
        except tk.TclError:
            return None

    def _schedule_highlight(self, event=None):
        """防抖高亮，避免每次按键都做全量扫描。"""
        if self._highlight_after_id:
            try:
                self.root.after_cancel(self._highlight_after_id)
            except tk.TclError:
                pass
        self._highlight_after_id = self.root.after(80, self.highlight)
            
    def _get_current_editor(self):
        tab_id = self._get_current_tab_id()
        if tab_id and tab_id in self.tabs_data:
            return self.tabs_data[tab_id]["editor"]
        return None
        
    def _get_current_line_numbers(self):
        tab_id = self._get_current_tab_id()
        if tab_id and tab_id in self.tabs_data:
            return self.tabs_data[tab_id]["line_numbers"]
        return None

    def _get_tab_id_by_editor(self, editor):
        for tab_id, data in self.tabs_data.items():
            if data.get("editor") is editor:
                return tab_id
        return None

    def _update_tab_title(self, tab_id):
        if tab_id not in self.tabs_data:
            return
        filepath = self.tabs_data[tab_id].get("filepath", "未命名代码.ym")
        display_name = os.path.basename(filepath) if filepath != "未命名代码.ym" else "未命名代码.ym"
        dirty_prefix = "● " if self.tabs_data[tab_id].get("dirty") else ""
        try:
            self.notebook.tab(tab_id, text=f" {dirty_prefix}{display_name}   ✖ ")
        except tk.TclError:
            pass

    def _set_diagnostic_status(self, text, level="ok"):
        self.status_diag_var.set(text)
        color_map = {
            "ok": "#C8E6C9",
            "info": "#9CDCFE",
            "warn": "#FFD27F",
            "error": "#FFAB91",
        }
        try:
            self.status_diag_label.configure(fg=color_map.get(level, "#D4D4D4"))
        except tk.TclError:
            pass

    def jump_to_diagnostic(self, event=None):
        tab_id = self._get_current_tab_id()
        editor = self._get_current_editor()
        if not tab_id or tab_id not in self.tabs_data or not editor:
            return "break"

        问题列表 = self._构建问题列表(tab_id)
        if not 问题列表:
            self.status_main_var.set("当前没有可跳转的语法/语义问题")
            return "break"

        导航索引 = int(self.tabs_data[tab_id].get("diagnostic_nav_index", 0) or 0)
        目标项 = 问题列表[导航索引 % len(问题列表)]
        self.tabs_data[tab_id]["diagnostic_nav_index"] = (导航索引 + 1) % len(问题列表)

        line = max(1, int(目标项.get("line") or 1))
        col = 目标项.get("col")
        col_index = max(0, int(col) - 1) if col else 0
        target = f"{line}.{col_index}"

        if hasattr(self, "issue_listbox"):
            try:
                self.issue_listbox.selection_clear(0, tk.END)
                self.issue_listbox.selection_set(导航索引 % len(问题列表))
                self.issue_listbox.activate(导航索引 % len(问题列表))
            except tk.TclError:
                pass

        try:
            editor.mark_set("insert", target)
            editor.see(target)
            editor.focus_set()
            self._highlight_current_line()
            self._update_cursor_status()
            self.status_main_var.set(
                f"已定位问题（{(导航索引 % len(问题列表)) + 1}/{len(问题列表)}）：第 {line} 行"
                + (f"，第 {col} 列" if col else "")
                + f" - {目标项.get('message', '')}"
            )
        except tk.TclError:
            self.status_main_var.set("错误位置定位失败（行列已变化）")
        return "break"

    def _构建问题列表(self, tab_id):
        if not tab_id or tab_id not in self.tabs_data:
            return []

        data = self.tabs_data[tab_id]
        结果 = []
        去重键 = set()

        diagnostic = data.get("diagnostic")
        if diagnostic:
            is_warn = str(diagnostic.get("type", "")) == "语义提示"
            if not is_warn:
                行号 = int(diagnostic.get("line") or 1)
                键 = ("error", 行号, diagnostic.get("col"), diagnostic.get("message", ""), "语法")
                if 键 not in 去重键:
                    去重键.add(键)
                    结果.append({
                        "level": "error",
                        "line": 行号,
                        "col": diagnostic.get("col"),
                        "message": diagnostic.get("message", ""),
                        "type": diagnostic.get("type", "语法错误"),
                        "category": "语法",
                    })

        for warn in data.get("semantic_warnings", []) or []:
            行号 = int(warn.get("line") or 1)
            分类 = str(warn.get("category", "语义") or "语义")
            键 = ("warn", 行号, warn.get("col"), warn.get("message", ""), 分类)
            if 键 in 去重键:
                continue
            去重键.add(键)
            结果.append({
                "level": "warn",
                "line": 行号,
                "col": warn.get("col"),
                "message": warn.get("message", ""),
                "type": warn.get("type", "语义提示"),
                "category": 分类,
            })

        return 结果

    def _refresh_issue_list(self):
        if not hasattr(self, "issue_listbox"):
            return
        tab_id = self._get_current_tab_id()
        if not tab_id or tab_id not in self.tabs_data:
            try:
                self.issue_listbox.delete(0, tk.END)
                self.issue_listbox.insert(tk.END, "(当前文件无语法/语义问题)")
                self.issue_listbox.itemconfig(0, foreground="#777777")
                self.issue_count_var.set("0")
            except tk.TclError:
                pass
            return

        问题列表 = self._构建问题列表(tab_id)
        self.tabs_data[tab_id]["issue_items"] = 问题列表
        self.tabs_data[tab_id]["diagnostic_nav_index"] = 0

        try:
            self.issue_listbox.delete(0, tk.END)
        except tk.TclError:
            return

        if not 问题列表:
            self.issue_listbox.insert(tk.END, "(当前文件无语法/语义问题)")
            try:
                self.issue_listbox.itemconfig(0, foreground="#777777")
            except tk.TclError:
                pass
            self.issue_count_var.set("0")
            return

        self.issue_count_var.set(str(len(问题列表)))
        for i, item in enumerate(问题列表):
            if item["level"] == "error":
                前缀 = "[错]"
            else:
                前缀 = "[提]"
            消息 = str(item.get("message", "")).strip()
            显示文本 = f"{前缀} L{item['line']} {消息}"
            self.issue_listbox.insert(tk.END, 显示文本)
            try:
                颜色 = "#FFAB91" if item["level"] == "error" else "#FFD27F"
                self.issue_listbox.itemconfig(i, foreground=颜色)
            except tk.TclError:
                pass

        self.issue_listbox.selection_clear(0, tk.END)
        self.issue_listbox.selection_set(0)
        self.issue_listbox.activate(0)

    def _get_selected_issue_item(self):
        tab_id = self._get_current_tab_id()
        if not tab_id or tab_id not in self.tabs_data:
            return None
        selection = self.issue_listbox.curselection() if hasattr(self, "issue_listbox") else ()
        if not selection:
            return None
        idx = selection[0]
        items = self.tabs_data[tab_id].get("issue_items", [])
        if idx < 0 or idx >= len(items):
            return None
        return items[idx]

    def _issue_update_status(self, event=None):
        item = self._get_selected_issue_item()
        if not item:
            return
        级别文本 = "错误" if item.get("level") == "error" else "提示"
        分类文本 = "语法" if item.get("level") == "error" else str(item.get("category", "语义") or "语义")
        self.status_main_var.set(f"问题列表：{级别文本}/{分类文本}（第 {item['line']} 行）- {item.get('message', '')}")

    def on_issue_activate(self, event=None):
        item = self._get_selected_issue_item()
        editor = self._get_current_editor()
        if not item or not editor:
            return "break"

        line = max(1, int(item.get("line") or 1))
        col = item.get("col")
        col_index = max(0, int(col) - 1) if col else 0
        target = f"{line}.{col_index}"

        try:
            editor.mark_set("insert", target)
            editor.see(target)
            editor.focus_set()
            self._highlight_current_line()
            self._update_cursor_status()
            self.status_main_var.set(
                f"已定位问题：第 {line} 行"
                + (f"，第 {col} 列" if col else "")
                + f" - {item.get('message', '')}"
            )
        except tk.TclError:
            self.status_main_var.set("问题位置定位失败（行列已变化）")
        return "break"

    def _update_status_main(self):
        tab_id = self._get_current_tab_id()
        if not tab_id or tab_id not in self.tabs_data:
            self.status_main_var.set("就绪")
            return
        filepath = self.tabs_data[tab_id].get("filepath", "未命名代码.ym")
        display_name = os.path.basename(filepath) if filepath != "未命名代码.ym" else "未命名代码.ym"
        dirty_hint = "（未保存）" if self.tabs_data[tab_id].get("dirty") else "（已保存）"
        self.status_main_var.set(f"文件：{display_name} {dirty_hint}")

    def _update_cursor_status(self, event=None):
        editor = self._get_current_editor()
        if not editor:
            return
        try:
            line, col = editor.index("insert").split(".")
            self.status_pos_var.set(f"行 {int(line)}，列 {int(col) + 1}")
        except (ValueError, tk.TclError):
            pass
        self._update_status_main()

    def _on_editor_modified(self, event):
        editor = event.widget
        try:
            if not editor.edit_modified():
                return
        except tk.TclError:
            return

        tab_id = self._get_tab_id_by_editor(editor)
        if tab_id and tab_id in self.tabs_data:
            if not self.tabs_data[tab_id].get("dirty"):
                self.tabs_data[tab_id]["dirty"] = True
                self._update_tab_title(tab_id)
                if tab_id == self._get_current_tab_id():
                    self._update_status_main()
            # 代码发生变更后，旧折叠范围可能失效，自动展开并重算
            if self.tabs_data[tab_id].get("folds"):
                self._clear_all_folds(tab_id)
            if tab_id == self._get_current_tab_id():
                self._schedule_highlight()
                self._schedule_diagnose()
                self._schedule_outline_update()
                self._update_line_numbers()
                self._update_cursor_status()
        editor.edit_modified(False)

    def _schedule_diagnose(self, event=None):
        if self._diagnose_after_id:
            try:
                self.root.after_cancel(self._diagnose_after_id)
            except tk.TclError:
                pass
        self._diagnose_after_id = self.root.after(120, self._run_live_diagnose)

    def _默认模块别名(self, 模块名):
        名称 = str(模块名 or "").replace("\\", "/").rstrip("/")
        if not 名称:
            return "模块"
        名称 = 名称.split("/")[-1]
        if 名称.endswith(".ym"):
            名称 = 名称[:-3]
        return 名称 or "模块"

    def _收集块声明(self, 语句列表):
        名称集 = set()
        函数签名 = {}
        for 语句 in 语句列表 or []:
            类型名 = type(语句).__name__
            if 类型名 == "变量设定节点":
                名称集.add(getattr(语句, "名称", ""))
            elif 类型名 == "定义函数节点":
                函数名 = getattr(语句, "函数名", "")
                if 函数名:
                    名称集.add(函数名)
                    函数签名[函数名] = len(getattr(语句, "参数列表", []) or [])
            elif 类型名 == "图纸定义节点":
                图纸名 = getattr(语句, "图纸名", "")
                if 图纸名:
                    名称集.add(图纸名)
            elif 类型名 == "引入语句节点":
                别名 = getattr(语句, "别名", None) or self._默认模块别名(getattr(语句, "模块名", ""))
                if 别名:
                    名称集.add(别名)
            elif 类型名 == "重复循环节点":
                变量名 = getattr(语句, "循环变量名", None)
                if 变量名:
                    名称集.add(变量名)
            elif 类型名 == "遍历循环节点":
                元素名 = getattr(语句, "元素名", "")
                if 元素名:
                    名称集.add(元素名)
            elif 类型名 == "尝试语句节点":
                错误名 = getattr(语句, "错误捕获名", None)
                if 错误名:
                    名称集.add(错误名)
        名称集.discard("")
        return 名称集, 函数签名

    def _语义模块搜索路径(self, tab_id=None):
        路径列表 = []

        if tab_id and tab_id in self.tabs_data:
            文件路径 = self.tabs_data[tab_id].get("filepath")
            if 文件路径 and os.path.isfile(文件路径):
                基础目录 = os.path.dirname(os.path.abspath(文件路径))
                路径列表.extend([基础目录, os.path.join(基础目录, "示例")])

        路径列表.extend([
            self.workspace_dir,
            os.path.join(self.workspace_dir, "示例"),
            os.getcwd(),
            os.path.join(os.getcwd(), "示例"),
        ])

        去重列表 = []
        for 路径 in 路径列表:
            if not 路径:
                continue
            绝对路径 = os.path.abspath(路径)
            if 绝对路径 not in 去重列表:
                去重列表.append(绝对路径)
        return 去重列表

    def _语义定位易码模块(self, 模块名, tab_id=None):
        名称 = str(模块名 or "").strip().replace("\\", "/")
        if not 名称:
            return None

        if os.path.isabs(名称):
            if os.path.isfile(名称):
                return os.path.abspath(名称)
            if os.path.isfile(名称 + ".ym"):
                return os.path.abspath(名称 + ".ym")
            return None

        带后缀 = 名称 if 名称.endswith(".ym") else f"{名称}.ym"
        for 基础路径 in self._语义模块搜索路径(tab_id):
            候选列表 = [
                os.path.join(基础路径, 带后缀),
                os.path.join(基础路径, 名称),
            ]
            for 候选 in 候选列表:
                if os.path.isfile(候选):
                    return os.path.abspath(候选)
        return None

    def _语义正则兜底导出(self, 代码):
        标识符模式 = r'[\u4e00-\u9fa5A-Za-z_][\u4e00-\u9fa5A-Za-z0-9_]*'
        导出符号 = set()
        导出类型 = {}
        导出签名 = {}
        类型优先级 = {"function": 5, "blueprint": 4, "class": 3, "alias": 2, "variable": 1, "member": 0}

        def 记导出(名称, 类型, 签名=""):
            名称文本 = str(名称 or "").strip()
            if not 名称文本:
                return
            导出符号.add(名称文本)
            旧类型 = 导出类型.get(名称文本, "member")
            if 类型优先级.get(类型, 0) >= 类型优先级.get(旧类型, 0):
                导出类型[名称文本] = 类型
            签名文本 = str(签名 or "").strip()
            if 签名文本 and not 导出签名.get(名称文本):
                导出签名[名称文本] = 签名文本

        代码文本 = str(代码 or "")
        功能行模式 = re.compile(rf'^\s*功能\s+({标识符模式})(.*)$')
        图纸行模式 = re.compile(rf'^\s*定义图纸\s+({标识符模式})(.*)$')
        变量行模式 = re.compile(rf'^\s*({标识符模式})\s*=')
        引入行模式 = re.compile(
            rf'^\s*引入\s*["“](.+?)["”]\s*(?:叫做\s*({标识符模式}))?\s*$'
        )

        for 行文本 in 代码文本.splitlines():
            去空 = 行文本.strip()
            if not 去空 or 去空.startswith("#"):
                continue

            功能匹配 = 功能行模式.match(行文本)
            if 功能匹配:
                名称 = 功能匹配.group(1)
                尾部 = str(功能匹配.group(2) or "").strip()
                参数列表 = []
                if 尾部.startswith("(") and ")" in 尾部:
                    参数串 = 尾部[1:尾部.find(")")]
                    参数列表 = [p.strip() for p in str(参数串).split(",") if p.strip()]
                else:
                    需要匹配 = re.search(rf'\b需要\b\s*(.*)$', 尾部)
                    if 需要匹配:
                        参数串 = str(需要匹配.group(1) or "").strip()
                        参数列表 = [p.strip() for p in re.split(r'[,\s]+', 参数串) if p.strip()]
                记导出(名称, "function", self._格式化参数签名(参数列表))
                continue

            图纸匹配 = 图纸行模式.match(行文本)
            if 图纸匹配:
                名称 = 图纸匹配.group(1)
                尾部 = str(图纸匹配.group(2) or "").strip()
                参数列表 = []
                if 尾部.startswith("(") and ")" in 尾部:
                    参数串 = 尾部[1:尾部.find(")")]
                    参数列表 = [p.strip() for p in str(参数串).split(",") if p.strip()]
                else:
                    需要匹配 = re.search(rf'\b需要\b\s*(.*)$', 尾部)
                    if 需要匹配:
                        参数串 = str(需要匹配.group(1) or "").strip()
                        参数列表 = [p.strip() for p in re.split(r'[,\s]+', 参数串) if p.strip()]
                记导出(名称, "blueprint", self._格式化参数签名(参数列表))
                continue

            变量匹配 = 变量行模式.match(行文本)
            if 变量匹配:
                记导出(变量匹配.group(1), "variable")
                continue

            引入匹配 = 引入行模式.match(行文本)
            if 引入匹配:
                模块名 = str(引入匹配.group(1) or "").strip()
                别名 = str(引入匹配.group(2) or "").strip()
                名称 = 别名 if 别名 else self._默认模块别名(模块名)
                记导出(名称, "alias")

        return 导出符号, 导出类型, 导出签名

    def _语义读取模块导出(self, 模块路径):
        绝对路径 = os.path.abspath(str(模块路径))
        try:
            修改时间 = os.stat(绝对路径).st_mtime_ns
        except OSError as e:
            return None, f"读取模块信息失败：{e}"

        缓存项 = self._semantic_module_cache.get(绝对路径)
        if 缓存项 and 缓存项.get("mtime") == 修改时间:
            return set(缓存项.get("symbols", set())), 缓存项.get("error")

        代码 = ""
        try:
            with open(绝对路径, "r", encoding="utf-8") as f:
                代码 = f.read()
            语法树 = 语法分析器(词法分析器(代码).分析()).解析()
        except Exception as e:
            错误文本 = f"模块解析失败：{e}"
            兜底符号, 兜底类型, 兜底签名 = self._语义正则兜底导出(代码)
            if 兜底符号:
                self._semantic_module_cache[绝对路径] = {
                    "mtime": 修改时间,
                    "symbols": set(兜底符号),
                    "symbol_kinds": dict(兜底类型),
                    "symbol_signatures": dict(兜底签名),
                    "error": 错误文本,
                }
                return set(兜底符号), None
            self._semantic_module_cache[绝对路径] = {
                "mtime": 修改时间,
                "symbols": set(),
                "symbol_kinds": {},
                "symbol_signatures": {},
                "error": 错误文本,
            }
            return None, 错误文本

        导出符号 = set()
        导出类型 = {}
        导出签名 = {}
        类型优先级 = {"function": 5, "blueprint": 4, "class": 3, "alias": 2, "variable": 1, "member": 0}

        def 记导出(名称, 类型, 签名=""):
            if not 名称:
                return
            导出符号.add(名称)
            旧类型 = 导出类型.get(名称, "member")
            if 类型优先级.get(类型, 0) >= 类型优先级.get(旧类型, 0):
                导出类型[名称] = 类型
            if 签名 and (not 导出签名.get(名称)):
                导出签名[名称] = 签名

        for 语句 in getattr(语法树, "语句列表", []) or []:
            类型名 = type(语句).__name__
            if 类型名 == "变量设定节点":
                名称 = getattr(语句, "名称", "")
                记导出(名称, "variable")
            elif 类型名 == "定义函数节点":
                名称 = getattr(语句, "函数名", "")
                参数列表 = list(getattr(语句, "参数列表", []) or [])
                记导出(名称, "function", self._格式化参数签名(参数列表))
            elif 类型名 == "图纸定义节点":
                名称 = getattr(语句, "图纸名", "")
                参数列表 = list(getattr(语句, "参数列表", []) or [])
                记导出(名称, "blueprint", self._格式化参数签名(参数列表))
            elif 类型名 == "引入语句节点":
                名称 = getattr(语句, "别名", None) or self._默认模块别名(getattr(语句, "模块名", ""))
                记导出(名称, "alias")

        self._semantic_module_cache[绝对路径] = {
            "mtime": 修改时间,
            "symbols": set(导出符号),
            "symbol_kinds": dict(导出类型),
            "symbol_signatures": dict(导出签名),
            "error": None,
        }
        return 导出符号, None

    def _语义读取模块导出详情(self, 模块路径):
        绝对路径 = os.path.abspath(str(模块路径))
        符号, 错误 = self._语义读取模块导出(绝对路径)
        if 错误:
            return {}, 错误
        缓存项 = self._semantic_module_cache.get(绝对路径) or {}
        类型表 = dict(缓存项.get("symbol_kinds", {}))
        if not 类型表 and 符号:
            类型表 = {名称: "member" for 名称 in 符号}
        return 类型表, None

    def _语义读取模块导出签名(self, 模块路径):
        绝对路径 = os.path.abspath(str(模块路径))
        _, 错误 = self._语义读取模块导出(绝对路径)
        if 错误:
            return {}, 错误
        缓存项 = self._semantic_module_cache.get(绝对路径) or {}
        签名表 = dict(缓存项.get("symbol_signatures", {}))
        return 签名表, None

    def _语义分析(self, 语法树, tab_id=None):
        警告列表 = []
        已记录 = set()
        内置名称 = set(self.builtin_words)
        内置名称.update({"对", "错", "空"})
        内置模块导出 = self._builtin_module_exports()

        def 记警告(行号, 消息, 列号=None, 分类="语义"):
            try:
                行号值 = max(1, int(行号 or 1))
            except (ValueError, TypeError):
                行号值 = 1
            try:
                列号值 = int(列号) if 列号 else None
            except (ValueError, TypeError):
                列号值 = None
            分类值 = str(分类 or "语义")
            键 = (行号值, 列号值, 消息, 分类值)
            if 键 in 已记录:
                return
            已记录.add(键)
            警告列表.append({
                "line": 行号值,
                "col": 列号值,
                "message": 消息,
                "type": "语义提示",
                "category": 分类值,
            })

        def 名称已定义(名字, 作用域栈):
            if not 名字:
                return True
            if 名字 in 内置名称:
                return True
            for 作用域 in reversed(作用域栈):
                if 名字 in 作用域:
                    return True
            return False

        def 查函数参数个数(名字, 函数栈):
            for 函数字典 in reversed(函数栈):
                if 名字 in 函数字典:
                    return 函数字典[名字]
            return None

        def 语句定义名称信息(语句):
            类型名 = type(语句).__name__
            if 类型名 == "定义函数节点":
                名称 = getattr(语句, "函数名", "")
                return (名称, "功能", getattr(语句, "行号", 1)) if 名称 else None
            if 类型名 == "图纸定义节点":
                名称 = getattr(语句, "图纸名", "")
                return (名称, "图纸", getattr(语句, "行号", 1)) if 名称 else None
            if 类型名 == "引入语句节点":
                名称 = getattr(语句, "别名", None) or self._默认模块别名(getattr(语句, "模块名", ""))
                return (名称, "模块别名", getattr(语句, "行号", 1)) if 名称 else None
            return None

        def 检查参数重复(参数列表, 函数名, 行号, 类型名描述):
            已有 = set()
            for 参数 in 参数列表 or []:
                if 参数 in 已有:
                    记警告(行号, f"{类型名描述}【{函数名}】的参数【{参数}】重复定义。")
                else:
                    已有.add(参数)

        def 收集块内直接赋值名(语句列表):
            名称集 = set()
            for 语句 in 语句列表 or []:
                if type(语句).__name__ == "变量设定节点":
                    名称 = getattr(语句, "名称", "")
                    if 名称:
                        名称集.add(名称)
            return 名称集

        def 分析表达式(节点, 作用域栈, 函数栈, 在图纸体=False):
            if 节点 is None:
                return
            类型名 = type(节点).__name__

            if 类型名 == "变量访问节点":
                名字 = getattr(节点, "名称", "")
                if not 名称已定义(名字, 作用域栈):
                    记警告(getattr(节点, "行号", 1), f"名称【{名字}】在当前上下文可能未定义。")
                return

            if 类型名 == "函数调用节点":
                名字 = getattr(节点, "函数名", "")
                参数列表 = getattr(节点, "参数列表", []) or []
                if not 名称已定义(名字, 作用域栈):
                    记警告(getattr(节点, "行号", 1), f"调用目标【{名字}】可能未定义。")
                else:
                    期望个数 = 查函数参数个数(名字, 函数栈)
                    if 期望个数 is not None and 期望个数 != len(参数列表):
                        记警告(getattr(节点, "行号", 1), f"功能【{名字}】参数个数可能不匹配：期望 {期望个数}，实际 {len(参数列表)}。")
                for 参数 in 参数列表:
                    分析表达式(参数, 作用域栈, 函数栈, 在图纸体=在图纸体)
                return

            if 类型名 == "动态调用节点":
                分析表达式(getattr(节点, "目标节点", None), 作用域栈, 函数栈, 在图纸体=在图纸体)
                for 参数 in getattr(节点, "参数列表", []) or []:
                    分析表达式(参数, 作用域栈, 函数栈, 在图纸体=在图纸体)
                return

            if 类型名 == "二元运算节点":
                分析表达式(getattr(节点, "左边", None), 作用域栈, 函数栈, 在图纸体=在图纸体)
                分析表达式(getattr(节点, "右边", None), 作用域栈, 函数栈, 在图纸体=在图纸体)
                return

            if 类型名 == "一元运算节点":
                分析表达式(getattr(节点, "操作数", None), 作用域栈, 函数栈, 在图纸体=在图纸体)
                return

            if 类型名 == "属性访问节点":
                分析表达式(getattr(节点, "对象节点", None), 作用域栈, 函数栈, 在图纸体=在图纸体)
                return

            if 类型名 == "属性设置节点":
                分析表达式(getattr(节点, "对象节点", None), 作用域栈, 函数栈, 在图纸体=在图纸体)
                分析表达式(getattr(节点, "值节点", None), 作用域栈, 函数栈, 在图纸体=在图纸体)
                return

            if 类型名 == "索引访问节点":
                分析表达式(getattr(节点, "对象节点", None), 作用域栈, 函数栈, 在图纸体=在图纸体)
                分析表达式(getattr(节点, "索引节点", None), 作用域栈, 函数栈, 在图纸体=在图纸体)
                return

            if 类型名 == "索引设置节点":
                分析表达式(getattr(节点, "对象节点", None), 作用域栈, 函数栈, 在图纸体=在图纸体)
                分析表达式(getattr(节点, "索引节点", None), 作用域栈, 函数栈, 在图纸体=在图纸体)
                分析表达式(getattr(节点, "值节点", None), 作用域栈, 函数栈, 在图纸体=在图纸体)
                return

            if 类型名 == "列表字面量节点":
                for 项 in getattr(节点, "元素列表", []) or []:
                    分析表达式(项, 作用域栈, 函数栈, 在图纸体=在图纸体)
                return

            if 类型名 == "字典字面量节点":
                for 键节点, 值节点 in getattr(节点, "键值对列表", []) or []:
                    分析表达式(键节点, 作用域栈, 函数栈, 在图纸体=在图纸体)
                    分析表达式(值节点, 作用域栈, 函数栈, 在图纸体=在图纸体)
                return

            if 类型名 == "输入表达式节点":
                分析表达式(getattr(节点, "提示语句表达式", None), 作用域栈, 函数栈, 在图纸体=在图纸体)
                return

            if 类型名 == "实例化节点":
                图纸名 = getattr(节点, "图纸名", "")
                if 图纸名 and not 名称已定义(图纸名, 作用域栈):
                    记警告(getattr(节点, "行号", 1), f"图纸【{图纸名}】可能未定义。")
                for 参数 in getattr(节点, "参数列表", []) or []:
                    分析表达式(参数, 作用域栈, 函数栈, 在图纸体=在图纸体)
                return

            if 类型名 == "自身属性访问节点":
                if not 在图纸体:
                    记警告(getattr(节点, "行号", 1), "【它的】建议只在图纸定义内部使用。")
                return

            if 类型名 == "自身属性设置节点":
                if not 在图纸体:
                    记警告(getattr(节点, "行号", 1), "【它的】建议只在图纸定义内部使用。")
                分析表达式(getattr(节点, "值节点", None), 作用域栈, 函数栈, 在图纸体=在图纸体)
                return

        def 分析代码块(
            语句列表,
            上层作用域栈,
            上层函数栈,
            额外名称=None,
            额外函数签名=None,
            在函数体=False,
            循环层级=0,
            在图纸体=False,
        ):
            块声明名, 块函数签名 = self._收集块声明(语句列表)
            本地作用域 = set(块声明名)
            if 额外名称:
                本地作用域.update(额外名称)
            本地函数签名 = dict(块函数签名)
            if 额外函数签名:
                本地函数签名.update(额外函数签名)
            当前作用域栈 = list(上层作用域栈) + [本地作用域]
            当前函数栈 = list(上层函数栈) + [本地函数签名]

            同块已定义 = {}
            for 语句 in 语句列表 or []:
                定义信息 = 语句定义名称信息(语句)
                if not 定义信息:
                    continue
                名称, 定义类型, 行号 = 定义信息
                if 名称 in 同块已定义:
                    前类型, 前行号 = 同块已定义[名称]
                    记警告(行号, f"名称【{名称}】在同一代码块重复定义（前一次：第 {前行号} 行，类型：{前类型}）。")
                else:
                    同块已定义[名称] = (定义类型, 行号)

            for 语句 in 语句列表 or []:
                类型名 = type(语句).__name__
                if 类型名 == "显示语句节点":
                    分析表达式(getattr(语句, "表达式", None), 当前作用域栈, 当前函数栈, 在图纸体=在图纸体)
                elif 类型名 == "变量设定节点":
                    分析表达式(getattr(语句, "表达式", None), 当前作用域栈, 当前函数栈, 在图纸体=在图纸体)
                elif 类型名 == "如果语句节点":
                    分支赋值集合列表 = []
                    for 条件, 分支 in getattr(语句, "条件分支列表", []) or []:
                        分析表达式(条件, 当前作用域栈, 当前函数栈, 在图纸体=在图纸体)
                        分析代码块(分支, 当前作用域栈, 当前函数栈, 在函数体=在函数体, 循环层级=循环层级, 在图纸体=在图纸体)
                        分支赋值集合列表.append(收集块内直接赋值名(分支))
                    否则分支 = getattr(语句, "否则分支列表", None)
                    是否有否则 = 否则分支 is not None
                    if 是否有否则:
                        分析代码块(否则分支, 当前作用域栈, 当前函数栈, 在函数体=在函数体, 循环层级=循环层级, 在图纸体=在图纸体)
                        分支赋值集合列表.append(收集块内直接赋值名(否则分支))
                    # 只有在存在“否则”时，才认为变量一定会被赋值；将所有分支共同赋值的变量提升到当前块作用域。
                    if 是否有否则 and 分支赋值集合列表:
                        必定赋值名 = set.intersection(*分支赋值集合列表)
                        if 必定赋值名:
                            当前作用域栈[-1].update(必定赋值名)
                elif 类型名 == "当循环节点":
                    分析表达式(getattr(语句, "条件", None), 当前作用域栈, 当前函数栈, 在图纸体=在图纸体)
                    分析代码块(
                        getattr(语句, "循环体", []),
                        当前作用域栈,
                        当前函数栈,
                        在函数体=在函数体,
                        循环层级=循环层级 + 1,
                        在图纸体=在图纸体,
                    )
                elif 类型名 == "重复循环节点":
                    分析表达式(getattr(语句, "次数表达式", None), 当前作用域栈, 当前函数栈, 在图纸体=在图纸体)
                    额外名 = set()
                    变量名 = getattr(语句, "循环变量名", None)
                    if 变量名:
                        额外名.add(变量名)
                    分析代码块(
                        getattr(语句, "循环体", []),
                        当前作用域栈,
                        当前函数栈,
                        额外名称=额外名,
                        在函数体=在函数体,
                        循环层级=循环层级 + 1,
                        在图纸体=在图纸体,
                    )
                elif 类型名 == "遍历循环节点":
                    分析表达式(getattr(语句, "列表表达式", None), 当前作用域栈, 当前函数栈, 在图纸体=在图纸体)
                    额外名 = set()
                    元素名 = getattr(语句, "元素名", "")
                    if 元素名:
                        额外名.add(元素名)
                    分析代码块(
                        getattr(语句, "循环体", []),
                        当前作用域栈,
                        当前函数栈,
                        额外名称=额外名,
                        在函数体=在函数体,
                        循环层级=循环层级 + 1,
                        在图纸体=在图纸体,
                    )
                elif 类型名 == "尝试语句节点":
                    分析代码块(
                        getattr(语句, "尝试代码块", []),
                        当前作用域栈,
                        当前函数栈,
                        在函数体=在函数体,
                        循环层级=循环层级,
                        在图纸体=在图纸体,
                    )
                    额外名 = set()
                    错误名 = getattr(语句, "错误捕获名", None)
                    if 错误名:
                        额外名.add(错误名)
                    分析代码块(
                        getattr(语句, "出错代码块", []),
                        当前作用域栈,
                        当前函数栈,
                        额外名称=额外名,
                        在函数体=在函数体,
                        循环层级=循环层级,
                        在图纸体=在图纸体,
                    )
                elif 类型名 == "定义函数节点":
                    函数名 = getattr(语句, "函数名", "")
                    参数列表 = list(getattr(语句, "参数列表", []) or [])
                    检查参数重复(参数列表, 函数名 or "匿名功能", getattr(语句, "行号", 1), "功能")
                    参数名 = set(参数列表)
                    分析代码块(
                        getattr(语句, "代码块", []),
                        当前作用域栈,
                        当前函数栈,
                        额外名称=参数名,
                        在函数体=True,
                        循环层级=0,
                        在图纸体=在图纸体,
                    )
                elif 类型名 == "图纸定义节点":
                    图纸名 = getattr(语句, "图纸名", "")
                    参数列表 = list(getattr(语句, "参数列表", []) or [])
                    检查参数重复(参数列表, 图纸名 or "匿名图纸", getattr(语句, "行号", 1), "图纸")
                    参数名 = set(参数列表)
                    分析代码块(
                        getattr(语句, "代码块", []),
                        当前作用域栈,
                        当前函数栈,
                        额外名称=参数名,
                        在函数体=False,
                        循环层级=0,
                        在图纸体=True,
                    )
                elif 类型名 == "返回语句节点":
                    if not 在函数体:
                        记警告(getattr(语句, "行号", 1), "【返回】建议只在功能内部使用。")
                    分析表达式(getattr(语句, "表达式", None), 当前作用域栈, 当前函数栈, 在图纸体=在图纸体)
                elif 类型名 == "跳出语句节点":
                    if 循环层级 <= 0:
                        记警告(getattr(语句, "行号", 1), "【停下】建议只在循环内部使用。")
                elif 类型名 == "继续语句节点":
                    if 循环层级 <= 0:
                        记警告(getattr(语句, "行号", 1), "【略过】建议只在循环内部使用。")
                elif 类型名 == "引入语句节点":
                    continue
                else:
                    分析表达式(语句, 当前作用域栈, 当前函数栈, 在图纸体=在图纸体)

        顶层语句 = getattr(语法树, "语句列表", []) or []
        分析代码块(顶层语句, [set(内置名称)], [dict()], 在函数体=False, 循环层级=0, 在图纸体=False)
        警告列表.sort(key=lambda x: (x.get("line") or 1, x.get("col") or 0))
        return 警告列表

    def _run_live_diagnose(self):
        self._diagnose_after_id = None
        editor = self._get_current_editor()
        tab_id = self._get_current_tab_id()
        if not editor or not tab_id or tab_id not in self.tabs_data:
            return

        editor.tag_remove("ErrorLine", "1.0", "end")
        editor.tag_remove("WarnLine", "1.0", "end")
        code = editor.get("1.0", "end-1c")
        if not code.strip():
            self.tabs_data[tab_id]["diagnostic"] = None
            self.tabs_data[tab_id]["semantic_warnings"] = []
            self.tabs_data[tab_id]["issue_items"] = []
            self.tabs_data[tab_id]["diagnostic_nav_index"] = 0
            self._set_diagnostic_status("语法检查：等待输入", level="info")
            self._refresh_issue_list()
            return

        try:
            tokens = 词法分析器(code).分析()
            语法树 = 语法分析器(tokens).解析()
            语义警告 = self._语义分析(语法树, tab_id=tab_id)
            self.tabs_data[tab_id]["semantic_warnings"] = 语义警告

            if 语义警告:
                首条 = 语义警告[0]
                line = int(首条.get("line") or 1)
                col = 首条.get("col")
                try:
                    editor.tag_add("WarnLine", f"{line}.0", f"{line}.end+1c")
                except tk.TclError:
                    pass
                self.tabs_data[tab_id]["diagnostic"] = 首条
                self._set_diagnostic_status(
                    f"语义提示：第 {line} 行"
                    + (f"，列 {col}" if col else "")
                    + f" - {首条.get('message', '')}（共 {len(语义警告)} 处）",
                    level="warn"
                )
            else:
                self.tabs_data[tab_id]["diagnostic"] = None
                self._set_diagnostic_status("语法检查：通过", level="ok")
            self._refresh_issue_list()
        except 易码错误 as e:
            line = int(e.行号) if e.行号 else 1
            line = max(1, line)
            col = int(e.列号) if e.列号 else None
            try:
                editor.tag_add("ErrorLine", f"{line}.0", f"{line}.end+1c")
            except tk.TclError:
                pass

            error_text = str(e.消息).replace("\n", " ")
            col_text = f"，列 {col}" if col else ""
            self.tabs_data[tab_id]["diagnostic"] = {
                "line": line,
                "col": col,
                "message": error_text,
                "type": e.错误类型,
            }
            self.tabs_data[tab_id]["semantic_warnings"] = []
            self._set_diagnostic_status(
                f"{e.错误类型}：第 {line} 行{col_text} - {error_text}",
                level="error"
            )
            self._refresh_issue_list()
        except Exception as e:
            self.tabs_data[tab_id]["diagnostic"] = None
            self.tabs_data[tab_id]["semantic_warnings"] = []
            self._set_diagnostic_status(f"语法检查失败：{e}", level="error")
            self._refresh_issue_list()

    def _handle_return(self, event=None):
        if self._autocomplete_is_visible():
            self._accept_autocomplete()
            return "break"
        return self._auto_indent(event)

    def _tab_current_word(self, editor):
        insert_idx = editor.index("insert")
        line_start = editor.index("insert linestart")
        line_text_before = editor.get(line_start, insert_idx)
        match = re.search(r'[\u4e00-\u9fa5a-zA-Z0-9_]+$', line_text_before)
        return insert_idx, line_start, (match.group(0) if match else "")

    def _tab_find_nearby_standalone_snippet_line(self, editor, center_line):
        """在光标附近寻找“只输入了模板关键词”的独立行，避免 Tab 误在旧行展开。"""
        try:
            total_lines = int(editor.index("end-1c").split(".")[0])
            center = int(center_line)
        except Exception:
            return None

        low = max(1, center - 4)
        high = min(total_lines, center + 8)
        candidates = []
        for line_no in range(low, high + 1):
            try:
                line_text = editor.get(f"{line_no}.0", f"{line_no}.end")
            except tk.TclError:
                continue
            stripped = line_text.strip()
            if not stripped:
                continue
            # 只匹配“整行就是关键词”的情况，避免误把已展开的模板行再次识别。
            if stripped in self.snippets and "‹" not in stripped and "›" not in stripped:
                candidates.append(line_no)

        if not candidates:
            return None
        # 同距离时优先选择更靠下的一行（更接近“刚输入”的场景）。
        return sorted(candidates, key=lambda ln: (abs(ln - center), -ln))[0]

    def _tab_selection_info(self, editor, insert_idx=None):
        try:
            sel_start = editor.index(tk.SEL_FIRST)
            sel_end = editor.index(tk.SEL_LAST)
            sel_text = editor.get(sel_start, sel_end)
        except tk.TclError:
            return {
                "start": None,
                "end": None,
                "text": "",
                "contains_cursor": False,
            }
        if insert_idx is None:
            contains_cursor = True
        else:
            try:
                contains_cursor = (
                    editor.compare(sel_start, "<=", insert_idx)
                    and editor.compare(insert_idx, "<", sel_end)
                )
            except tk.TclError:
                contains_cursor = False
        return {
            "start": sel_start,
            "end": sel_end,
            "text": sel_text,
            "contains_cursor": contains_cursor,
        }

    def _remember_edit_cursor(self, event=None):
        editor = None
        if event is not None and hasattr(event, "widget"):
            candidate = getattr(event, "widget", None)
            if isinstance(candidate, tk.Text) and self._get_tab_id_by_editor(candidate):
                editor = candidate
        if editor is None:
            editor = self._get_current_editor()
        if not editor:
            return

        tab_id = self._get_tab_id_by_editor(editor)
        if not tab_id:
            return
        try:
            idx, _, word = self._tab_current_word(editor)
        except Exception:
            return
        self._last_edit_tab_id = tab_id
        self._last_edit_index = idx
        self._last_edit_word = str(word or "")
        self._last_edit_ts = time.monotonic()

    def _tab_placeholder_range_on_line(self, editor, index_value):
        try:
            index_text = editor.index(index_value)
            line_text, col_text = index_text.split(".")
            line_no = int(line_text)
            col_no = int(col_text)
        except Exception:
            return (None, None)
        try:
            line_code = editor.get(f"{line_no}.0", f"{line_no}.end")
        except tk.TclError:
            return (None, None)
            
        # 寻找包含光标位置的最内层 ‹ 和 ›
        left = line_code.rfind("‹", 0, max(0, col_no) + 1)
        if left != -1:
            # 找到左括号后，向右寻找右括号，起点是左括号位置，而非光标位置
            right = line_code.find("›", left)
            if right != -1:
                # 只要光标在这个括号范围内（或者刚超出一点点，代表可能刚刚在括号内打完字）
                if left <= col_no <= right + 1:
                    return (f"{line_no}.{left}", f"{line_no}.{right + 1}")
        
        # 容错：如果光标刚好跑到了右括号外面一个字符（如：删除了再输入导致偏移）
        left = line_code.rfind("‹", 0, max(0, col_no))
        if left != -1:
            right = line_code.find("›", left)
            if right != -1:
                if left <= col_no <= right + 2:
                    return (f"{line_no}.{left}", f"{line_no}.{right + 1}")
                    
        return (None, None)

    def _tab_jump_to_next_placeholder(self, editor, from_index):
        try:
            search_index = editor.index(from_index or "insert")
        except tk.TclError:
            search_index = editor.index("insert")
        while True:
            start_idx = editor.search('\u2039', search_index, "end")
            if not start_idx:
                return False
            line_end = editor.index(f"{start_idx} lineend")
            line_rest = editor.get(start_idx, line_end)
            match = re.match(r"\u2039.+?\u203a", line_rest)
            if not match:
                search_index = editor.index(f"{start_idx}+1c")
                continue
            end_idx = f"{start_idx} + {len(match.group(0))}c"
            editor.tag_remove("sel", "1.0", "end")
            editor.tag_add("sel", start_idx, end_idx)
            editor.mark_set("insert", start_idx)
            editor.see("insert")
            return True

    def _expand_snippet_at_cursor(self, editor, snippet_word, typed_word=''):
        snippet_name = str(snippet_word or '').strip()
        snippet_text = self.snippets.get(snippet_name)
        if not snippet_text:
            return False

        # 简单逻辑：找到光标前的关键词，删掉它，在原位插入代码模板
        insert_idx = editor.index('insert')
        line_start = editor.index('insert linestart')
        line_before = editor.get(line_start, insert_idx)
        remove_word = str(typed_word or snippet_name).strip()

        # 计算要删除的起点（光标前面的关键词）
        if remove_word and line_before.endswith(remove_word):
            del_start = f'insert - {len(remove_word)}c'
        else:
            del_start = 'insert'

        # 删除关键词，插入代码模板
        # 必须先把 del_start 转成绝对位置！否则 delete 后 insert 标记移动，
        # 再次计算 "insert - Nc" 会跳到错误的行
        del_start = editor.index(del_start)

        # 智能缩进：根据插入位置的缩进级别，调整模板的每一行
        base_col = int(del_start.split('.')[1])
        base_indent = " " * base_col
        if base_col > 0:
            lines = snippet_text.split('\n')
            # 第一行不加缩进（因为它替换了关键词的位置），后续行加基础缩进
            snippet_text = lines[0] + ''.join('\n' + base_indent + line for line in lines[1:])

        editor.delete(del_start, 'insert')
        editor.insert(del_start, snippet_text)

        # 光标跳到框架下方新行，方便用户继续写 否则如果 / 不然 等
        try:
            # 计算插入起始行的缩进（与框架头对齐）
            start_line = int(del_start.split('.')[0])
            start_col = int(del_start.split('.')[1])
            缩进文本 = " " * start_col
            # 找到插入的最后一行
            行数 = snippet_text.count('\n')
            末行 = start_line + 行数
            editor.mark_set('insert', f'{末行}.end')
            editor.insert('insert', '\n' + 缩进文本)
            editor.tag_remove('sel', '1.0', 'end')
        except Exception:
            try:
                editor.mark_set('insert', f'{del_start} + {len(snippet_text)}c')
                editor.tag_remove('sel', '1.0', 'end')
            except tk.TclError:
                pass
        self.highlight()
        return True


    def _handle_tab(self, event=None):
        editor = None
        if event is not None and hasattr(event, "widget"):
            candidate = getattr(event, "widget", None)
            if isinstance(candidate, tk.Text) and self._get_tab_id_by_editor(candidate):
                editor = candidate
        if editor is None:
            editor = self._get_current_editor()
        if not editor: return "break"
        try:
            editor.focus_set()
        except tk.TclError:
            pass

        强制展开词 = ""
        光标前词 = ""
        insert_idx, _, 光标前词 = self._tab_current_word(editor)
        try:
            当前行号 = int(insert_idx.split(".")[0])
        except Exception:
            当前行号 = 1

        # 当前光标前已形成模板词时，直接在当前行展开，忽略旧弹窗状态
        if 光标前词 and 光标前词 in self.snippets:
            self._hide_autocomplete()
            self._expand_snippet_at_cursor(editor, 光标前词, typed_word=光标前词)
            return "break"

        if self._autocomplete_is_visible():
            是模板候选 = False
            同行弹窗 = False
            try:
                当前行 = editor.index("insert").split(".")[0]
                同行弹窗 = bool(self._autocomplete_popup_line and str(self._autocomplete_popup_line) == str(当前行))
                idx = self._autocomplete_current_index()
                if 0 <= idx < len(self._autocomplete_items):
                    当前候选 = self._autocomplete_items[idx] or {}
                    是模板候选 = str(当前候选.get("source", "")).strip() == "snippet"
                    if 是模板候选:
                        强制展开词 = str(当前候选.get("insert", "")).strip()
            except Exception:
                是模板候选 = False
                同行弹窗 = False
                强制展开词 = ""

            if 是模板候选:
                # 模板展开只走“当前光标前词”路径；弹窗模板在 Tab 时不直接展开。
                # 这样可避免中文输入法未提交/旧弹窗状态导致跨行插入。
                self._hide_autocomplete()
                if 同行弹窗 and 光标前词 and (光标前词 in self.snippets):
                    self._expand_snippet_at_cursor(editor, 光标前词, typed_word=光标前词)
                return "break"
            else:
                self._accept_autocomplete()
                return "break"

        选区 = self._tab_selection_info(editor, insert_idx)
        sel_start = 选区["start"]
        sel_end = 选区["end"]
        sel_text = 选区["text"]
        sel_contains_cursor = bool(选区["contains_cursor"])
        if sel_start and sel_end and (not sel_contains_cursor):
            sel_start = None
            sel_end = None
            sel_text = ""
            try:
                editor.tag_remove("sel", "1.0", "end")
            except tk.TclError:
                pass

        当前选中占位符 = bool(
            sel_start and sel_end and sel_contains_cursor
            and sel_text.startswith("‹") and sel_text.endswith("›")
        )
        if 当前选中占位符:
            if self._tab_jump_to_next_placeholder(editor, sel_end):
                return "break"
        elif self._tab_jump_to_next_placeholder(editor, insert_idx):
            return "break"

        # 没有更多占位符了：如果光标在缩进块内，跳出到块下方新行
        try:
            当前行文本 = editor.get("insert linestart", "insert lineend")
            当前缩进 = len(当前行文本) - len(当前行文本.lstrip())
            if 当前缩进 > 0 or (当前选中占位符 and sel_text):
                # 找到当前块的结束位置：向下扫描直到缩进变小或文件结束
                当前行号 = int(editor.index("insert").split(".")[0])
                总行数 = int(editor.index("end-1c").split(".")[0])
                目标行 = 当前行号
                for i in range(当前行号, 总行数 + 1):
                    行 = editor.get(f"{i}.0", f"{i}.end")
                    if 行.strip():
                        行缩进 = len(行) - len(行.lstrip())
                        if 行缩进 >= 当前缩进 or i == 当前行号:
                            目标行 = i
                        else:
                            break
                    else:
                        目标行 = i
                        break

                # 计算父级缩进（比当前缩进少一级）
                父级缩进 = max(0, 当前缩进 - 4)
                缩进文本 = " " * 父级缩进

                # 在块下方插入新行
                editor.mark_set("insert", f"{目标行}.end")
                editor.insert("insert", "\n" + 缩进文本)
                self.highlight()
                return "break"
        except Exception:
            pass

        if sel_start and sel_end and sel_contains_cursor and not 当前选中占位符:
            try:
                start_line = int(sel_start.split('.')[0])
                end_line = int(sel_end.split('.')[0])
                if sel_end.split('.')[1] == '0' and start_line != end_line:
                    end_line -= 1
                for i in range(start_line, end_line + 1):
                    editor.insert(f"{i}.0", "    ")
                return "break"
            except Exception:
                pass

        if sel_start and sel_end and sel_contains_cursor and not 当前选中占位符:
            try:
                editor.delete(sel_start, sel_end)
            except tk.TclError:
                pass
        editor.insert("insert", "    ")
        return "break"

    def _handle_auto_pairs(self, event):
        editor = self._get_current_editor()
        if not editor or event.widget is not editor:
            return

        # Ctrl 组合键放行
        if event.state & 0x4:
            return

        ch = event.char
        
        # 输入普通字符时，如果存在选区，不仅要替换文本，在中文输入法下也更符合直觉
        if ch and ord(ch) >= 32 and event.keysym not in ("Return", "Tab", "Escape"):
            try:
                if editor.index(tk.SEL_FIRST) != editor.index(tk.SEL_LAST):
                    editor.delete(tk.SEL_FIRST, tk.SEL_LAST)
            except tk.TclError:
                pass

        # 中文输入法下的句号自动转英文点：系统。 -> 系统.
        # 仅在代码区生效；字符串/注释中保留原样，避免影响中文文本输入。
        if ch in ("。", "．", "｡"):
            try:
                prev_tags = editor.tag_names("insert-1c")
            except tk.TclError:
                prev_tags = ()
            try:
                cur_tags = editor.tag_names("insert")
            except tk.TclError:
                cur_tags = ()

            在字符串或注释内 = (
                ("String" in prev_tags) or ("Comment" in prev_tags)
                or ("String" in cur_tags) or ("Comment" in cur_tags)
            )
            if not 在字符串或注释内:
                try:
                    editor.delete(tk.SEL_FIRST, tk.SEL_LAST)
                except tk.TclError:
                    pass
                editor.insert("insert", ".")
                # 立即触发成员补全，避免中文输入法下必须再按一次键
                try:
                    self.root.after_idle(self._check_autocomplete)
                except Exception:
                    pass
                return "break"

        if ch in self._pair_map:
            right = self._pair_map[ch]
            try:
                sel_start = editor.index(tk.SEL_FIRST)
                sel_end = editor.index(tk.SEL_LAST)
                selected = editor.get(sel_start, sel_end)
                editor.delete(sel_start, sel_end)
                editor.insert(sel_start, f"{ch}{selected}{right}")
                editor.mark_set("insert", f"{sel_start} + {len(ch) + len(selected) + len(right)}c")
                return "break"
            except tk.TclError:
                editor.insert("insert", f"{ch}{right}")
                editor.mark_set("insert", "insert-1c")
                return "break"

        if ch and ch in self._pair_map.values():
            next_char = editor.get("insert", "insert+1c")
            if next_char == ch:
                editor.mark_set("insert", "insert+1c")
                return "break"

        if event.keysym == "BackSpace":
            prev_char = editor.get("insert-1c", "insert")
            next_char = editor.get("insert", "insert+1c")
            if prev_char in self._pair_map and self._pair_map[prev_char] == next_char:
                editor.delete("insert-1c", "insert+1c")
                return "break"

    def _get_multi_state(self, tab_id=None):
        target_tab_id = tab_id if tab_id else self._get_current_tab_id()
        if not target_tab_id or target_tab_id not in self.tabs_data:
            return None, None
        data = self.tabs_data[target_tab_id]
        state = data.setdefault(
            "multi_cursor",
            {"query": "", "stage": "ranges", "ranges": [], "points": [], "last_abs": -1}
        )
        return target_tab_id, state

    def _index_to_abs(self, editor, idx):
        try:
            return len(editor.get("1.0", idx))
        except tk.TclError:
            return 0

    def _sort_unique_indices(self, editor, indices):
        uniq = {}
        for idx in indices:
            uniq[self._index_to_abs(editor, idx)] = idx
        return [uniq[k] for k in sorted(uniq.keys())]

    def _find_all_symbol_ranges(self, editor, symbol_name):
        code = editor.get("1.0", "end-1c")
        pattern = self._symbol_pattern(symbol_name)
        ranges = []
        for m in pattern.finditer(code):
            start = f"1.0 + {m.start()}c"
            end = f"1.0 + {m.end()}c"
            ranges.append((start, end))
        return ranges

    def _convert_ranges_to_points(self, editor, state, use_end=True):
        points = []
        for start, end in state.get("ranges", []):
            idx = end if use_end else start
            try:
                points.append(editor.index(idx))
            except tk.TclError:
                continue
        state["stage"] = "points"
        state["ranges"] = []
        state["points"] = self._sort_unique_indices(editor, points)
        return state["points"]

    def _handle_editor_left_click(self, event):
        editor = self._get_current_editor()
        tab_id, state = self._get_multi_state()
        if not editor or event.widget is not editor or state is None:
            return

        # Alt + 左键由专门的多光标入口处理
        if event.state & 0x0008:
            return

        self._hide_autocomplete()
        self._hide_calltip()
        try:
            click_idx = editor.index(f"@{event.x},{event.y}")
            editor.mark_set("insert", click_idx)
            editor.tag_remove("sel", "1.0", "end")
            editor.focus_set()
        except tk.TclError:
            pass

        if state.get("ranges") or state.get("points"):
            self._clear_multi_cursor_mode(tab_id)
            self.status_main_var.set("多光标模式已退出")

    def _sync_insert_after_click(self, event=None):
        editor = self._get_current_editor()
        if not editor:
            return
        if event is not None and event.widget is not editor:
            return
        try:
            if event is not None:
                idx = editor.index(f"@{event.x},{event.y}")
                editor.mark_set("insert", idx)
        except tk.TclError:
            pass

    def multi_cursor_alt_click(self, event=None):
        editor = self._get_current_editor()
        tab_id, state = self._get_multi_state()
        if not editor or not tab_id or state is None:
            return "break"
        if event is None or event.widget is not editor:
            return "break"

        self._hide_autocomplete()

        try:
            click_idx = editor.index(f"@{event.x},{event.y}")
        except tk.TclError:
            return "break"

        if state["stage"] == "ranges" and state.get("ranges"):
            self._convert_ranges_to_points(editor, state, use_end=True)

        points = list(state.get("points", []))
        if not points:
            points = [editor.index("insert")]

        click_abs = self._index_to_abs(editor, click_idx)
        point_abs = [self._index_to_abs(editor, p) for p in points]
        if click_abs in point_abs:
            if len(points) > 1:
                points = [p for p in points if self._index_to_abs(editor, p) != click_abs]
            else:
                points = [click_idx]
        else:
            points.append(click_idx)

        state["query"] = ""
        state["stage"] = "points"
        state["ranges"] = []
        state["points"] = self._sort_unique_indices(editor, points)
        state["last_abs"] = self._index_to_abs(editor, state["points"][-1]) if state["points"] else -1

        editor.mark_set("insert", click_idx)
        editor.focus_set()
        self._render_multi_cursor_state(tab_id)
        self.status_main_var.set(f"多光标：已放置 {len(state['points'])} 个光标点（Alt+点击继续，Esc退出）")
        return "break"

    def _render_multi_cursor_state(self, tab_id=None):
        target_tab_id, state = self._get_multi_state(tab_id)
        if not target_tab_id or state is None:
            return
        editor = self.tabs_data[target_tab_id].get("editor")
        if not editor:
            return

        editor.tag_remove("MultiCursorSel", "1.0", "end")
        if state["stage"] == "ranges":
            for start, end in state["ranges"]:
                try:
                    editor.tag_add("MultiCursorSel", start, end)
                except tk.TclError:
                    continue
        else:
            # Tk 文本组件不支持多个插入光标，这里用单字符高亮模拟“多光标点”
            for point in state["points"]:
                try:
                    next_idx = editor.index(f"{point}+1c")
                    if next_idx != point:
                        editor.tag_add("MultiCursorSel", point, next_idx)
                    else:
                        prev_idx = editor.index(f"{point}-1c")
                        if prev_idx != point:
                            editor.tag_add("MultiCursorSel", prev_idx, point)
                except tk.TclError:
                    continue

    def _clear_multi_cursor_mode(self, tab_id=None, keep_query=False):
        target_tab_id, state = self._get_multi_state(tab_id)
        if not target_tab_id or state is None:
            return
        editor = self.tabs_data[target_tab_id].get("editor")
        if editor:
            editor.tag_remove("MultiCursorSel", "1.0", "end")
        query = state.get("query", "") if keep_query else ""
        state["query"] = query
        state["stage"] = "ranges"
        state["ranges"] = []
        state["points"] = []
        state["last_abs"] = -1

    def _update_after_multi_edit(self, tab_id, status_text=""):
        if not tab_id or tab_id not in self.tabs_data:
            return
        self.tabs_data[tab_id]["dirty"] = True
        self._update_tab_title(tab_id)
        self._update_status_main()
        if status_text:
            self.status_main_var.set(status_text)
        self._schedule_highlight()
        self._schedule_diagnose()
        self._schedule_outline_update()
        self._update_line_numbers()
        self._update_cursor_status()
        self._render_multi_cursor_state(tab_id)

    def multi_cursor_add_next(self, event=None):
        editor = self._get_current_editor()
        tab_id, state = self._get_multi_state()
        if not editor or not tab_id or state is None:
            return "break"

        if state["stage"] != "ranges":
            self._clear_multi_cursor_mode(tab_id)
            _, state = self._get_multi_state(tab_id)

        word = state["query"] or self._get_symbol_near_cursor(editor)
        if not word:
            self.status_main_var.set("多光标：请先把光标放在符号上，或先选中一个符号")
            return "break"

        all_ranges = self._find_all_symbol_ranges(editor, word)
        if not all_ranges:
            self.status_main_var.set(f"多光标：未找到符号【{word}】")
            return "break"

        state["query"] = word
        selected_start_abs = {self._index_to_abs(editor, s) for s, _ in state["ranges"]}

        if not state["ranges"]:
            cursor_abs = self._index_to_abs(editor, "insert")
            chosen = None
            for s, e in all_ranges:
                s_abs = self._index_to_abs(editor, s)
                e_abs = self._index_to_abs(editor, e)
                if s_abs <= cursor_abs <= e_abs:
                    chosen = (s, e)
                    break
            if not chosen:
                for s, e in all_ranges:
                    s_abs = self._index_to_abs(editor, s)
                    if s_abs >= cursor_abs:
                        chosen = (s, e)
                        break
            if not chosen:
                chosen = all_ranges[0]
            state["ranges"] = [chosen]
            state["last_abs"] = self._index_to_abs(editor, chosen[0])
        else:
            candidates = sorted(all_ranges, key=lambda r: self._index_to_abs(editor, r[0]))
            next_choice = None
            for s, e in candidates:
                s_abs = self._index_to_abs(editor, s)
                if s_abs > state["last_abs"] and s_abs not in selected_start_abs:
                    next_choice = (s, e)
                    break
            if not next_choice:
                for s, e in candidates:
                    s_abs = self._index_to_abs(editor, s)
                    if s_abs not in selected_start_abs:
                        next_choice = (s, e)
                        break
            if not next_choice:
                self.status_main_var.set(f"多光标：{word} 已全部选中")
                self._render_multi_cursor_state(tab_id)
                return "break"
            state["ranges"].append(next_choice)
            state["last_abs"] = self._index_to_abs(editor, next_choice[0])

        state["ranges"] = sorted(state["ranges"], key=lambda r: self._index_to_abs(editor, r[0]))
        self._render_multi_cursor_state(tab_id)
        self.status_main_var.set(f"多光标：已选中 {len(state['ranges'])} 处【{word}】（Ctrl+D继续，Esc退出）")
        return "break"

    def multi_cursor_select_all(self, event=None):
        editor = self._get_current_editor()
        tab_id, state = self._get_multi_state()
        if not editor or not tab_id or state is None:
            return "break"

        word = self._get_symbol_near_cursor(editor) or state.get("query", "")
        if not word:
            self.status_main_var.set("多光标：请先把光标放在符号上，或先选中一个符号")
            return "break"

        all_ranges = self._find_all_symbol_ranges(editor, word)
        if not all_ranges:
            self.status_main_var.set(f"多光标：未找到符号【{word}】")
            return "break"

        state["query"] = word
        state["stage"] = "ranges"
        state["ranges"] = sorted(all_ranges, key=lambda r: self._index_to_abs(editor, r[0]))
        state["points"] = []
        state["last_abs"] = self._index_to_abs(editor, state["ranges"][-1][0]) if state["ranges"] else -1
        self._render_multi_cursor_state(tab_id)
        self.status_main_var.set(f"多光标：已全选 {len(state['ranges'])} 处【{word}】（直接输入可同步编辑）")
        return "break"

    def _multi_apply_insert_char(self, ch):
        editor = self._get_current_editor()
        tab_id, state = self._get_multi_state()
        if not editor or not tab_id or state is None:
            return

        if state["stage"] == "ranges" and state["ranges"]:
            operations = sorted(state["ranges"], key=lambda r: self._index_to_abs(editor, r[0]), reverse=True)
            new_points = []
            for start, end in operations:
                try:
                    editor.delete(start, end)
                    editor.insert(start, ch)
                    new_points.append(editor.index(f"{start}+{len(ch)}c"))
                except tk.TclError:
                    continue
            state["stage"] = "points"
            state["ranges"] = []
            state["points"] = self._sort_unique_indices(editor, new_points)
        else:
            points = self._sort_unique_indices(editor, state["points"])
            new_points = []
            for point in sorted(points, key=lambda p: self._index_to_abs(editor, p), reverse=True):
                try:
                    editor.insert(point, ch)
                    new_points.append(editor.index(f"{point}+{len(ch)}c"))
                except tk.TclError:
                    continue
            state["stage"] = "points"
            state["points"] = self._sort_unique_indices(editor, new_points)

        self._update_after_multi_edit(tab_id, f"多光标编辑：同步输入 {len(state['points']) or len(state['ranges'])} 处")

    def _multi_apply_backspace(self):
        editor = self._get_current_editor()
        tab_id, state = self._get_multi_state()
        if not editor or not tab_id or state is None:
            return

        new_points = []
        if state["stage"] == "ranges" and state["ranges"]:
            operations = sorted(state["ranges"], key=lambda r: self._index_to_abs(editor, r[0]), reverse=True)
            for start, end in operations:
                try:
                    editor.delete(start, end)
                    new_points.append(start)
                except tk.TclError:
                    continue
            state["ranges"] = []
            state["stage"] = "points"
        else:
            points = self._sort_unique_indices(editor, state["points"])
            for point in sorted(points, key=lambda p: self._index_to_abs(editor, p), reverse=True):
                try:
                    if self._index_to_abs(editor, point) <= 0:
                        continue
                    start = editor.index(f"{point}-1c")
                    editor.delete(start, point)
                    new_points.append(start)
                except tk.TclError:
                    continue
            state["stage"] = "points"

        state["points"] = self._sort_unique_indices(editor, new_points)
        self._update_after_multi_edit(tab_id, "多光标编辑：已同步退格")

    def _multi_apply_delete(self):
        editor = self._get_current_editor()
        tab_id, state = self._get_multi_state()
        if not editor or not tab_id or state is None:
            return

        new_points = []
        if state["stage"] == "ranges" and state["ranges"]:
            operations = sorted(state["ranges"], key=lambda r: self._index_to_abs(editor, r[0]), reverse=True)
            for start, end in operations:
                try:
                    editor.delete(start, end)
                    new_points.append(start)
                except tk.TclError:
                    continue
            state["ranges"] = []
            state["stage"] = "points"
        else:
            points = self._sort_unique_indices(editor, state["points"])
            for point in sorted(points, key=lambda p: self._index_to_abs(editor, p), reverse=True):
                try:
                    editor.delete(point, f"{point}+1c")
                    new_points.append(point)
                except tk.TclError:
                    continue
            state["stage"] = "points"

        state["points"] = self._sort_unique_indices(editor, new_points)
        self._update_after_multi_edit(tab_id, "多光标编辑：已同步删除")

    def _handle_multi_cursor_key(self, event):
        editor = self._get_current_editor()
        tab_id, state = self._get_multi_state()
        if not editor or not tab_id or state is None:
            return
        if event.widget is not editor:
            return

        active = bool(state.get("ranges") or state.get("points"))
        if not active:
            return

        if event.keysym == "Escape":
            self._clear_multi_cursor_mode(tab_id)
            self.status_main_var.set("多光标模式已退出")
            return "break"

        # 导航键按下时退出多光标模式，并交给系统默认移动
        if event.keysym in ("Left", "Right", "Up", "Down", "Home", "End", "Prior", "Next"):
            self._clear_multi_cursor_mode(tab_id)
            return

        # Ctrl 组合键交给其他快捷键处理
        if event.state & 0x4:
            return

        if event.keysym == "BackSpace":
            self._multi_apply_backspace()
            return "break"
        if event.keysym == "Delete":
            self._multi_apply_delete()
            return "break"
        if event.keysym == "Return":
            self._multi_apply_insert_char("\n")
            return "break"
        if event.keysym == "Tab":
            self._multi_apply_insert_char("    ")
            return "break"

        if event.char and ord(event.char) >= 32:
            self._multi_apply_insert_char(event.char)
            return "break"

    def _count_indent_width(self, line_text):
        width = 0
        for ch in line_text:
            if ch == " ":
                width += 1
            elif ch == "\t":
                width += 4
            else:
                break
        return width

    def _get_block_end_line(self, editor, start_line):
        line_count = int(editor.index("end-1c").split(".")[0])
        if start_line >= line_count:
            return None

        start_text = editor.get(f"{start_line}.0", f"{start_line}.end")
        if not start_text.strip():
            return None

        base_indent = self._count_indent_width(start_text)
        end_line = start_line
        has_child = False

        for ln in range(start_line + 1, line_count + 1):
            text = editor.get(f"{ln}.0", f"{ln}.end")
            stripped = text.strip()
            if not stripped:
                if has_child:
                    end_line = ln
                continue

            indent = self._count_indent_width(text)
            if indent > base_indent:
                has_child = True
                end_line = ln
                continue
            break

        while end_line > start_line and not editor.get(f"{end_line}.0", f"{end_line}.end").strip():
            end_line -= 1

        if not has_child or end_line <= start_line:
            return None
        return end_line

    def _schedule_outline_update(self, event=None):
        if self._outline_after_id:
            try:
                self.root.after_cancel(self._outline_after_id)
            except tk.TclError:
                pass
        self._outline_after_id = self.root.after(260, self._refresh_outline)

    def _refresh_outline(self):
        self._outline_after_id = None
        if not hasattr(self, "outline_listbox"):
            return

        editor = self._get_current_editor()
        tab_id = self._get_current_tab_id()
        if not editor or not tab_id or tab_id not in self.tabs_data:
            self.outline_listbox.delete(0, tk.END)
            return

        previous_selected_line = None
        try:
            prev_idx = self.outline_listbox.curselection()
            if prev_idx:
                prev_item = self.tabs_data[tab_id].get("outline_items", [])[prev_idx[0]]
                previous_selected_line = prev_item.get("line")
        except Exception:
            previous_selected_line = None

        self.outline_listbox.delete(0, tk.END)
        code_lines = editor.get("1.0", "end-1c").splitlines()
        folds = self.tabs_data[tab_id].setdefault("folds", {})
        items = []

        for line_no, line_text in enumerate(code_lines, start=1):
            stripped = line_text.strip()
            if not stripped or stripped.startswith("#"):
                continue

            kind = None
            name = None
            m_func = re.match(r'^\s*功能\s+([^\s(（]+)', line_text)
            if m_func:
                kind = "功能"
                name = m_func.group(1)
            else:
                m_class = re.match(r'^\s*定义图纸\s+([^\s(（]+)', line_text)
                if m_class:
                    kind = "图纸"
                    name = m_class.group(1)

            if not kind or not name:
                continue

            indent_level = self._count_indent_width(line_text) // 4
            collapsed = bool(folds.get(line_no, {}).get("collapsed"))
            marker = "[+]" if collapsed else "[-]"
            kind_mark = "功能" if kind == "功能" else "图纸"
            indent_prefix = "  " * min(indent_level, 6)
            display_text = f"{indent_prefix}{marker} {kind_mark} {name}  (L{line_no})"

            items.append({
                "line": line_no,
                "kind": kind,
                "name": name,
                "indent_level": indent_level,
                "display_text": display_text,
            })
            self.outline_listbox.insert(tk.END, display_text)

        self.tabs_data[tab_id]["outline_items"] = items

        if not items:
            self.outline_listbox.insert(tk.END, "(当前文件暂无功能/图纸结构)")
            try:
                self.outline_listbox.itemconfig(0, foreground="#777777")
            except tk.TclError:
                pass
            return

        selected_idx = 0
        if previous_selected_line:
            for i, item in enumerate(items):
                if item["line"] == previous_selected_line:
                    selected_idx = i
                    break
        self.outline_listbox.selection_clear(0, tk.END)
        self.outline_listbox.selection_set(selected_idx)
        self.outline_listbox.activate(selected_idx)

    def _get_selected_outline_item(self):
        tab_id = self._get_current_tab_id()
        if not tab_id or tab_id not in self.tabs_data:
            return None
        selection = self.outline_listbox.curselection()
        if not selection:
            return None
        idx = selection[0]
        items = self.tabs_data[tab_id].get("outline_items", [])
        if idx < 0 or idx >= len(items):
            return None
        return items[idx]

    def _outline_update_status(self, event=None):
        item = self._get_selected_outline_item()
        if not item:
            return
        self.status_main_var.set(f"大纲：{item['kind']} {item['name']}（第 {item['line']} 行）")

    def on_outline_activate(self, event=None):
        item = self._get_selected_outline_item()
        if not item:
            return "break"
        editor = self._get_current_editor()
        if not editor:
            return "break"

        target = f"{item['line']}.0"
        editor.mark_set("insert", target)
        editor.see(target)
        editor.focus_set()
        self._highlight_current_line()
        self._update_cursor_status()
        self.status_main_var.set(f"已定位到：{item['kind']} {item['name']}（第 {item['line']} 行）")
        return "break"

    def _toggle_fold_by_line(self, line_no):
        editor = self._get_current_editor()
        tab_id = self._get_current_tab_id()
        if not editor or not tab_id or tab_id not in self.tabs_data:
            return False

        folds = self.tabs_data[tab_id].setdefault("folds", {})
        fold_meta = folds.get(line_no)

        if fold_meta and fold_meta.get("collapsed"):
            tag = fold_meta.get("tag")
            if tag:
                editor.tag_remove(tag, "1.0", "end")
                try:
                    editor.tag_configure(tag, elide=False)
                except tk.TclError:
                    pass
            fold_meta["collapsed"] = False
            self._update_line_numbers()
            return True

        end_line = self._get_block_end_line(editor, line_no)
        if not end_line:
            return False

        tag_name = fold_meta.get("tag") if fold_meta else f"FoldBlock_{line_no}"
        editor.tag_configure(tag_name, elide=True)
        editor.tag_remove(tag_name, "1.0", "end")
        editor.tag_add(tag_name, f"{line_no + 1}.0", f"{end_line}.end+1c")
        folds[line_no] = {"tag": tag_name, "end_line": end_line, "collapsed": True}
        self._update_line_numbers()
        return True

    def _clear_all_folds(self, tab_id=None):
        target_tab_id = tab_id if tab_id else self._get_current_tab_id()
        if not target_tab_id or target_tab_id not in self.tabs_data:
            return

        editor = self.tabs_data[target_tab_id].get("editor")
        if not editor:
            return

        folds = self.tabs_data[target_tab_id].get("folds", {})
        for fold_meta in folds.values():
            tag = fold_meta.get("tag")
            if not tag:
                continue
            editor.tag_remove(tag, "1.0", "end")
            try:
                editor.tag_configure(tag, elide=False)
            except tk.TclError:
                pass
        self.tabs_data[target_tab_id]["folds"] = {}

    def toggle_fold_from_outline(self, event=None):
        item = self._get_selected_outline_item()
        if not item:
            return self.toggle_fold_current_line(event)

        ok = self._toggle_fold_by_line(item["line"])
        if ok:
            self._refresh_outline()
            self.status_main_var.set(f"已切换折叠：{item['kind']} {item['name']}")
        else:
            self.status_main_var.set("当前位置没有可折叠代码块")
        return "break"

    def toggle_fold_current_line(self, event=None):
        editor = self._get_current_editor()
        if not editor:
            return "break"
        line_no = int(editor.index("insert").split(".")[0])
        ok = self._toggle_fold_by_line(line_no)
        if ok:
            self._refresh_outline()
            self.status_main_var.set(f"已切换第 {line_no} 行代码块折叠")
        else:
            self.status_main_var.set("当前位置没有可折叠代码块")
        return "break"

    def unfold_all_blocks(self, event=None):
        self._clear_all_folds()
        self._refresh_outline()
        self.status_main_var.set("已展开当前文件全部折叠块")
        return "break"

    def _update_line_numbers(self, event=None):
        editor = self._get_current_editor()
        line_numbers = self._get_current_line_numbers()
        if not editor or not line_numbers:
            return
            
        line_numbers.config(state=tk.NORMAL)
        line_numbers.delete("1.0", tk.END)
        line_count = editor.index("end-1c").split(".")[0]
        line_numbers_string = "\n".join(str(i) for i in range(1, int(line_count) + 1))
        line_numbers.insert("1.0", line_numbers_string)
        
        # 靠右对齐
        line_numbers.tag_configure("right", justify="right")
        line_numbers.tag_add("right", "1.0", "end")
        
        line_numbers.config(state=tk.DISABLED)
        # 同步滚动位置
        line_numbers.yview_moveto(editor.yview()[0])
        # 同步更新缩进引导线
        self._update_indent_guides()
        
    def _update_indent_guides(self, event=None):
        tab_id = self._get_current_tab_id()
        if not tab_id or tab_id not in self.tabs_data: return
        
        editor = self.tabs_data[tab_id]["editor"]
        canvas = self.tabs_data[tab_id].get("guide_canvas")
        if not canvas: return
        
        canvas.delete("all")
        
        # 缩进引导线颜色
        guide_colors = ["#333333", "#3B3B5A", "#333333", "#3B3B5A"]
        
        try:
            first_line = int(editor.index("@0,0").split(".")[0])
            last_line = int(editor.index(f"@0,{editor.winfo_height()}").split(".")[0])
        except: return
        
        # 第一次扫描：收集每行的缩进级别和位置
        line_data = []
        for line_num in range(first_line, last_line + 1):
            line_text = editor.get(f"{line_num}.0", f"{line_num}.end")
            bbox = editor.bbox(f"{line_num}.0")
            if not bbox: continue
            
            stripped = line_text.lstrip()
            if stripped:
                indent = len(line_text) - len(stripped)
                levels = indent // 4
            else:
                levels = 0  # 空行继承上下文
            
            line_data.append((line_num, levels, bbox))
        
        # 空行继承上一行的缩进级别（让引导线贯穿空行）
        for i in range(len(line_data)):
            if line_data[i][1] == 0 and i > 0:
                prev_levels = line_data[i-1][1]
                # 检查下一个有内容的行的缩进
                next_levels = 0
                for j in range(i+1, len(line_data)):
                    if line_data[j][1] > 0:
                        next_levels = line_data[j][1]
                        break
                # 取前后缩进的较小值
                inherited = min(prev_levels, next_levels) if next_levels > 0 else 0
                if inherited > 0:
                    line_data[i] = (line_data[i][0], inherited, line_data[i][2])
        
        # 绘制引导线
        canvas_width = int(canvas.cget("width"))
        for line_num, levels, bbox in line_data:
            if levels == 0: continue
            _, y, _, h = bbox
            for lvl in range(levels):
                x = 5 + lvl * 6
                if x >= canvas_width - 2: break
                color = guide_colors[lvl % len(guide_colors)]
                canvas.create_line(x, y, x, y + h, fill=color, width=1)
        
    def _highlight_current_line(self, event=None):
        editor = self._get_current_editor()
        if not editor: return
        editor.tag_remove("CurrentLine", "1.0", "end")
        editor.tag_add("CurrentLine", "insert linestart", "insert lineend+1c")
        
    def _auto_indent(self, event=None):
        editor = self._get_current_editor()
        if not editor: return "break"
        
        line_text = editor.get("insert linestart", "insert lineend")
        
        # 由于拦截了 Return，我们需要手动插入换行符
        editor.insert("insert", "\n")
        
        # 获取原来那行的开头空白保持当前缩进
        indent = ""
        for char in line_text:
            if char in [' ', '\t']:
                indent += char
            else:
                break
                
        # 看看上文需不需要额外再加一层缩进
        stripped_prev = line_text.strip()
        # 这些词结尾或者开头的句子通常表示下一行要缩进
        indent_triggers = ["如果", "否则如果", "不然", "尝试", "如果出错", "重复", "功能", "定义图纸", "当", "遍历"]
        
        for trigger in indent_triggers:
            if stripped_prev.startswith(trigger) or stripped_prev.endswith("的时候") or stripped_prev.endswith("就"):
                indent += "    " # 加四个空格
                break
                
        if indent:
            editor.insert("insert", indent)
            
        editor.see("insert")
        self._highlight_current_line()
        return "break"
        
    def _handle_shift_tab(self, event=None):
        editor = self._get_current_editor()
        if not editor: return "break"
        
        # 决定要处理哪些行
        try:
            sel_start = editor.index(tk.SEL_FIRST)
            sel_end = editor.index(tk.SEL_LAST)
            start_line = int(sel_start.split('.')[0])
            end_line = int(sel_end.split('.')[0])
            if sel_end.split('.')[1] == '0' and start_line != end_line:
                end_line -= 1
        except tk.TclError:
            # 没有选区时，只回退当前行
            insert_pos = editor.index("insert")
            start_line = int(insert_pos.split('.')[0])
            end_line = start_line
            
        # 执行回退缩进
        for i in range(start_line, end_line + 1):
            line_text = editor.get(f"{i}.0", f"{i}.end")
            # 找到开头的空白字符数
            space_count = 0
            for char in line_text:
                if char == ' ': space_count += 1
                elif char == '\t': space_count += 4 # 临时将 tab 算成 4 空格的权重
                else: break
            
            # 最多拿掉 4 个空格
            remove_count = min(4, space_count)
            if remove_count > 0:
                editor.delete(f"{i}.0", f"{i}.{remove_count}")
                
        return "break"

    def _trigger_autocomplete(self, event=None):
        self._check_autocomplete(event=None)
        return "break"

    def _schedule_calltip_update(self, event=None):
        try:
            self.root.after_idle(self._update_calltip)
        except Exception:
            pass

    def _autocomplete_is_visible(self):
        try:
            return bool(self.autocomplete_popup.winfo_ismapped())
        except Exception:
            return False

    def _is_autocomplete_widget(self, 控件):
        当前 = 控件
        for _ in range(8):
            if 当前 is None:
                return False
            if 当前 is self.autocomplete_popup or 当前 is self.autocomplete_tree:
                return True
            当前 = getattr(当前, "master", None)
        return False

    def _autocomplete_select_index(self, 索引):
        总数 = len(self._autocomplete_row_ids)
        if 总数 <= 0:
            return
        idx = max(0, min(总数 - 1, int(索引)))
        行id = self._autocomplete_row_ids[idx]
        try:
            self.autocomplete_tree.selection_set(行id)
            self.autocomplete_tree.focus(行id)
            self.autocomplete_tree.see(行id)
        except tk.TclError:
            pass

    def _autocomplete_current_index(self):
        if not self._autocomplete_row_ids:
            return 0
        try:
            选择项 = self.autocomplete_tree.selection()
            if 选择项:
                return max(0, self._autocomplete_row_ids.index(选择项[0]))
            焦点项 = self.autocomplete_tree.focus()
            if 焦点项:
                return max(0, self._autocomplete_row_ids.index(焦点项))
        except Exception:
            pass
        return 0

    def _autocomplete_index_from_event(self, event=None):
        if event is None or not hasattr(event, "y"):
            return None
        try:
            行id = self.autocomplete_tree.identify_row(event.y)
            if not 行id:
                return None
            return self._autocomplete_row_ids.index(行id)
        except Exception:
            return None

    def _on_autocomplete_mouse_press(self, event=None):
        self._autocomplete_mouse_down = True
        try:
            self.autocomplete_tree.focus_set()
        except tk.TclError:
            pass
        return None

    def _on_editor_focus_out(self, event=None):
        # 点击补全列表时，编辑器会先失焦；延后判断可避免误隐藏
        self.root.after(20, self._hide_autocomplete_if_focus_lost)

    def _hide_autocomplete_if_focus_lost(self):
        if not self._autocomplete_is_visible():
            return
        if self._autocomplete_mouse_down:
            try:
                鼠标控件 = self.root.winfo_containing(self.root.winfo_pointerx(), self.root.winfo_pointery())
            except tk.TclError:
                鼠标控件 = None
            if self._is_autocomplete_widget(鼠标控件):
                return
            self._autocomplete_mouse_down = False
        焦点控件 = self.root.focus_get()
        if self._is_autocomplete_widget(焦点控件):
            return
        try:
            鼠标控件 = self.root.winfo_containing(self.root.winfo_pointerx(), self.root.winfo_pointery())
            if self._is_autocomplete_widget(鼠标控件):
                return
        except tk.TclError:
            pass
        self._hide_autocomplete()
        self._hide_calltip()

    def _hide_autocomplete(self):
        try:
            self.autocomplete_popup.place_forget()
        except tk.TclError:
            pass
        try:
            for 行id in self.autocomplete_tree.get_children():
                self.autocomplete_tree.delete(行id)
        except tk.TclError:
            pass
        self._autocomplete_items = []
        self._autocomplete_row_ids = []
        self._autocomplete_replace_start = None
        self._autocomplete_replace_end = None
        self._autocomplete_popup_line = None
        self._autocomplete_mouse_down = False

    def _hide_calltip(self):
        try:
            self.calltip_popup.place_forget()
        except tk.TclError:
            pass

    def _show_calltip(self, editor, 文本):
        if not editor:
            self._hide_calltip()
            return
        内容文本 = str(文本 or "").strip()
        if not 内容文本:
            self._hide_calltip()
            return

        bbox = editor.bbox("insert")
        if not bbox:
            self._hide_calltip()
            return

        try:
            self.calltip_label.configure(text=内容文本)
            self.root.update_idletasks()
            字体对象 = tkfont.Font(font=self.calltip_label.cget("font"))
            文字宽度 = max(220, 字体对象.measure(内容文本) + 18)
            根宽度 = max(420, int(self.root.winfo_width()))
            最大宽度 = max(260, 根宽度 - 16)
            提示宽度 = min(文字宽度, 最大宽度)
            提示高度 = max(30, 字体对象.metrics("linespace") + 14)

            x, y, _, 行高 = bbox
            root_x = editor.winfo_rootx() - self.root.winfo_rootx() + x + 4
            root_y = editor.winfo_rooty() - self.root.winfo_rooty() + y - 提示高度 - 6
            if root_y < 8:
                root_y = editor.winfo_rooty() - self.root.winfo_rooty() + y + 行高 + 4
            if root_x + 提示宽度 > 根宽度 - 8:
                root_x = max(8, 根宽度 - 提示宽度 - 8)

            self.calltip_popup.place(x=root_x, y=root_y, width=提示宽度, height=提示高度)
            self.calltip_popup.lift()
        except Exception:
            self._hide_calltip()

    def _ensure_runtime_builtin_signatures(self):
        if self._runtime_builtin_signature_loaded:
            return
        self._runtime_builtin_signature_loaded = True
        try:
            临时解释器 = 解释器()
            记录本 = dict(getattr(临时解释器.全局环境, "记录本", {}) or {})
            for 名称, 对象 in 记录本.items():
                if not callable(对象):
                    continue
                self._runtime_builtin_signature_cache[str(名称)] = self._安全签名文本(对象)
        except Exception:
            self._runtime_builtin_signature_cache = {}

    def _builtin_signature_of(self, 名称):
        self._ensure_runtime_builtin_signatures()
        return str(self._runtime_builtin_signature_cache.get(str(名称), "()") or "()")

    def _拆分签名参数(self, 签名):
        签名文本 = str(签名 or "").strip()
        if not 签名文本.startswith("(") or not 签名文本.endswith(")"):
            return []
        内文 = 签名文本[1:-1]
        if not 内文.strip():
            return []
        结果 = []
        当前 = []
        括号层 = 0
        方括号层 = 0
        花括号层 = 0
        字符串引号 = ""
        转义 = False
        for ch in 内文:
            if 字符串引号:
                当前.append(ch)
                if 转义:
                    转义 = False
                elif ch == "\\":
                    转义 = True
                elif ch == 字符串引号:
                    字符串引号 = ""
                continue
            if ch in ("'", '"'):
                字符串引号 = ch
                当前.append(ch)
                continue
            if ch == "(":
                括号层 += 1
            elif ch == ")" and 括号层 > 0:
                括号层 -= 1
            elif ch == "[":
                方括号层 += 1
            elif ch == "]" and 方括号层 > 0:
                方括号层 -= 1
            elif ch == "{":
                花括号层 += 1
            elif ch == "}" and 花括号层 > 0:
                花括号层 -= 1
            if ch == "," and 括号层 == 0 and 方括号层 == 0 and 花括号层 == 0:
                结果.append("".join(当前).strip())
                当前 = []
                continue
            当前.append(ch)
        if 当前:
            结果.append("".join(当前).strip())
        return [p for p in 结果 if p != ""]

    def _高亮当前参数签名(self, 签名, 参数序号):
        签名文本 = str(签名 or "").strip()
        if not 签名文本:
            return "()"
        参数列表 = self._拆分签名参数(签名文本)
        if not 参数列表:
            return 签名文本
        try:
            idx = max(0, int(参数序号) - 1)
        except Exception:
            idx = 0
        if idx < len(参数列表):
            参数列表[idx] = f"【{参数列表[idx]}】"
        return "(" + ", ".join(参数列表) + ")"

    def _解析当前调用上下文(self, 行前文本):
        文本 = str(行前文本 or "")
        if not 文本:
            return None

        括号层 = 0
        方括号层 = 0
        花括号层 = 0
        开括号位置 = -1
        for i in range(len(文本) - 1, -1, -1):
            ch = 文本[i]
            if ch == ")":
                括号层 += 1
                continue
            if ch == "]":
                方括号层 += 1
                continue
            if ch == "}":
                花括号层 += 1
                continue
            if ch == "(":
                if 括号层 == 0 and 方括号层 == 0 and 花括号层 == 0:
                    开括号位置 = i
                    break
                if 括号层 > 0:
                    括号层 -= 1
                continue
            if ch == "[" and 方括号层 > 0:
                方括号层 -= 1
                continue
            if ch == "{" and 花括号层 > 0:
                花括号层 -= 1
                continue
        if 开括号位置 < 0:
            return None

        标识符模式 = r'[\u4e00-\u9fa5A-Za-z_][\u4e00-\u9fa5A-Za-z0-9_]*'
        左侧文本 = 文本[:开括号位置]
        名称匹配 = re.search(rf'({标识符模式}(?:\.{标识符模式})*)\s*$', 左侧文本)
        if not 名称匹配:
            return None
        调用名 = 名称匹配.group(1)

        参数区域 = 文本[开括号位置 + 1:]
        逗号数 = 0
        括号层 = 0
        方括号层 = 0
        花括号层 = 0
        字符串引号 = ""
        转义 = False
        for ch in 参数区域:
            if 字符串引号:
                if 转义:
                    转义 = False
                elif ch == "\\":
                    转义 = True
                elif ch == 字符串引号:
                    字符串引号 = ""
                continue
            if ch in ("'", '"'):
                字符串引号 = ch
                continue
            if ch == "(":
                括号层 += 1
                continue
            if ch == ")" and 括号层 > 0:
                括号层 -= 1
                continue
            if ch == "[":
                方括号层 += 1
                continue
            if ch == "]" and 方括号层 > 0:
                方括号层 -= 1
                continue
            if ch == "{":
                花括号层 += 1
                continue
            if ch == "}" and 花括号层 > 0:
                花括号层 -= 1
                continue
            if ch == "," and 括号层 == 0 and 方括号层 == 0 and 花括号层 == 0:
                逗号数 += 1

        参数序号 = 1 if not 参数区域.strip() else (逗号数 + 1)
        return {"调用名": 调用名, "参数序号": 参数序号}

    def _解析调用表达式签名(self, 调用表达式, 上下文, tab_id=None):
        名称 = str(调用表达式 or "").strip()
        if not 名称:
            return ""

        功能签名 = dict((上下文 or {}).get("功能签名", {}) or {})
        图纸签名 = dict((上下文 or {}).get("图纸签名", {}) or {})
        导入签名 = dict((上下文 or {}).get("导入导出签名", {}) or {})
        别名签名映射 = dict((上下文 or {}).get("别名成员签名映射", {}) or {})
        引入别名 = dict((上下文 or {}).get("引入别名", {}) or {})

        if 名称 in 功能签名:
            return 功能签名[名称]
        if 名称 in 图纸签名:
            return 图纸签名[名称]
        if 名称 in 导入签名:
            return 导入签名[名称]
        if 名称 in self.builtin_words:
            return self._builtin_signature_of(名称)

        if "." in 名称:
            片段 = 名称.split(".")
            对象名 = 片段[0].strip()
            成员名 = 片段[-1].strip()
            模块成员签名 = dict(别名签名映射.get(对象名, {}) or {})
            if 成员名 in 模块成员签名:
                return str(模块成员签名.get(成员名) or "()")
            模块名 = 引入别名.get(对象名) or self._跨标签查别名模块(对象名, 当前tab_id=tab_id)
            if 模块名:
                签名表 = self._获取模块补全成员签名(模块名, tab_id=tab_id)
                if 成员名 in 签名表:
                    return str(签名表.get(成员名) or "()")
            if 成员名 in self.builtin_words:
                return self._builtin_signature_of(成员名)

        return ""

    def _update_calltip(self, editor=None, tab_id=None, 全文=None, 行前文本=None, 上下文=None):
        编辑器 = editor if editor else self._get_current_editor()
        if not 编辑器:
            self._hide_calltip()
            return
        当前tab = tab_id if tab_id else self._get_current_tab_id()
        try:
            if 全文 is None:
                全文 = 编辑器.get("1.0", "end-1c")
            if 行前文本 is None:
                行前文本 = 编辑器.get("insert linestart", "insert")
        except tk.TclError:
            self._hide_calltip()
            return

        调用上下文 = self._解析当前调用上下文(行前文本)
        if not 调用上下文:
            self._hide_calltip()
            return

        try:
            光标行 = int(编辑器.index("insert").split(".")[0])
        except Exception:
            光标行 = 1
        调用上下文数据 = 上下文 if 上下文 is not None else self._收集补全上下文(全文 or "", tab_id=当前tab, 光标行=光标行)
        签名 = self._解析调用表达式签名(调用上下文["调用名"], 调用上下文数据, tab_id=当前tab)
        if not 签名:
            self._hide_calltip()
            return

        高亮签名 = self._高亮当前参数签名(签名, 调用上下文["参数序号"])
        提示文本 = f"{调用上下文['调用名']}{高亮签名}    参数 {调用上下文['参数序号']}"
        self._show_calltip(编辑器, 提示文本)

    def _autocomplete_match(self, 候选词, 前缀):
        if not 候选词:
            return False
        if not 前缀:
            return True
        if 候选词 == 前缀:
            return True
        if 候选词.startswith(前缀):
            return True
        return len(前缀) >= 2 and (前缀 in 候选词)

    def _格式化参数签名(self, 参数列表):
        参数 = [str(p).strip() for p in (参数列表 or []) if str(p).strip()]
        return f"({', '.join(参数)})" if 参数 else "()"

    def _安全签名文本(self, 可调用对象):
        try:
            签名 = str(inspect.signature(可调用对象))
        except Exception:
            return "()"
        if not 签名:
            return "()"
        if len(签名) > 44:
            return f"{签名[:41]}...)"
        return 签名

    def _提取定义签名(self, 全文):
        标识符模式 = r'[\u4e00-\u9fa5A-Za-z_][\u4e00-\u9fa5A-Za-z0-9_]*'
        内容 = 全文 or ""
        功能签名 = {}
        图纸签名 = {}
        功能模式 = re.compile(
            rf'^\s*功能\s+({标识符模式})\s*(?:\((.*?)\))?',
            re.MULTILINE,
        )
        图纸模式 = re.compile(
            rf'^\s*定义图纸\s+({标识符模式})\s*(?:\((.*?)\))?',
            re.MULTILINE,
        )

        for 名称, 参数串 in 功能模式.findall(内容):
            参数列表 = [p.strip() for p in str(参数串 or "").split(",") if p.strip()]
            功能签名[名称] = self._格式化参数签名(参数列表)
        for 名称, 参数串 in 图纸模式.findall(内容):
            参数列表 = [p.strip() for p in str(参数串 or "").split(",") if p.strip()]
            图纸签名[名称] = self._格式化参数签名(参数列表)
        return 功能签名, 图纸签名

    def _提取图纸成员映射(self, 全文):
        标识符模式 = r'[\u4e00-\u9fa5A-Za-z_][\u4e00-\u9fa5A-Za-z0-9_]*'
        行列表 = (全文 or "").splitlines()
        图纸成员映射 = {}
        图纸成员类型映射 = {}
        图纸成员签名映射 = {}

        图纸头模式 = re.compile(rf'^\s*定义图纸\s+({标识符模式})\s*(?:\((.*?)\))?')
        功能头模式 = re.compile(rf'^\s*功能\s+({标识符模式})\s*(?:\((.*?)\))?')
        自身属性模式 = re.compile(rf'^\s*它的\s+({标识符模式})\b')

        i = 0
        while i < len(行列表):
            行文本 = 行列表[i]
            匹配 = 图纸头模式.match(行文本)
            if not 匹配:
                i += 1
                continue

            图纸名 = str(匹配.group(1) or "").strip()
            if not 图纸名:
                i += 1
                continue
            图纸缩进 = self._行首缩进宽度(行文本)

            成员集 = set(图纸成员映射.get(图纸名, set()))
            类型表 = dict(图纸成员类型映射.get(图纸名, {}))
            签名表 = dict(图纸成员签名映射.get(图纸名, {}))

            i += 1
            while i < len(行列表):
                子行 = 行列表[i]
                去空 = 子行.strip()
                if not 去空 or 去空.startswith("#"):
                    i += 1
                    continue

                子缩进 = self._行首缩进宽度(子行)
                if 子缩进 <= 图纸缩进:
                    break

                功能匹配 = 功能头模式.match(子行)
                if 功能匹配:
                    名称 = str(功能匹配.group(1) or "").strip()
                    参数串 = str(功能匹配.group(2) or "")
                    参数列表 = [p.strip() for p in 参数串.split(",") if p.strip()]
                    if 名称:
                        成员集.add(名称)
                        类型表[名称] = "function"
                        签名表[名称] = self._格式化参数签名(参数列表)
                    i += 1
                    continue

                属性匹配 = 自身属性模式.match(子行)
                if 属性匹配:
                    名称 = str(属性匹配.group(1) or "").strip()
                    if 名称:
                        成员集.add(名称)
                        类型表[名称] = "variable"
                    i += 1
                    continue

                i += 1

            图纸成员映射[图纸名] = 成员集
            图纸成员类型映射[图纸名] = 类型表
            图纸成员签名映射[图纸名] = 签名表

        return 图纸成员映射, 图纸成员类型映射, 图纸成员签名映射

    def _提取对象实例映射(self, 全文):
        标识符模式 = r'[\u4e00-\u9fa5A-Za-z_][\u4e00-\u9fa5A-Za-z0-9_]*'
        映射 = {}
        模式 = re.compile(
            rf'^\s*({标识符模式})\s*=\s*造一个\s+({标识符模式})\b',
            re.MULTILINE,
        )
        for 对象名, 图纸名 in 模式.findall(全文 or ""):
            对象名 = str(对象名 or "").strip()
            图纸名 = str(图纸名 or "").strip()
            if 对象名 and 图纸名:
                映射[对象名] = 图纸名
        return 映射

    def _行首缩进宽度(self, 行文本):
        行 = str(行文本 or "").replace("\t", "    ")
        return len(行) - len(行.lstrip(" "))

    def _提取当前作用域局部变量(self, 全文, 光标行):
        标识符模式 = r'[\u4e00-\u9fa5A-Za-z_][\u4e00-\u9fa5A-Za-z0-9_]*'
        内容 = 全文 or ""
        行列表 = 内容.splitlines()
        if not 行列表:
            return set()

        try:
            目标行 = int(光标行 or 1)
        except (TypeError, ValueError):
            目标行 = 1
        目标行 = max(1, min(目标行, len(行列表)))

        作用域栈 = []
        功能头模式 = re.compile(rf'^\s*功能\s+({标识符模式})\s*(?:\((.*?)\))?')
        图纸头模式 = re.compile(rf'^\s*定义图纸\s+({标识符模式})\s*(?:\((.*?)\))?')

        for 行号 in range(1, 目标行 + 1):
            行文本 = 行列表[行号 - 1]
            去空 = 行文本.strip()
            if not 去空 or 去空.startswith("#"):
                continue

            缩进 = self._行首缩进宽度(行文本)
            while 作用域栈 and 行号 > 作用域栈[-1]["line"] and 缩进 <= 作用域栈[-1]["indent"]:
                作用域栈.pop()

            匹配 = 功能头模式.match(行文本) or 图纸头模式.match(行文本)
            if 匹配:
                参数串 = str(匹配.group(2) or "")
                参数列表 = [p.strip() for p in 参数串.split(",") if p.strip()]
                作用域栈.append({
                    "line": 行号,
                    "indent": 缩进,
                    "params": 参数列表,
                })

        if not 作用域栈:
            return set()

        当前作用域 = 作用域栈[-1]
        局部变量 = set(当前作用域.get("params", []))
        赋值模式 = re.compile(rf'^\s*({标识符模式})\s*=')
        遍历模式 = re.compile(rf'^\s*遍历\b.*?\b叫做\s+({标识符模式})\b')
        重复模式 = re.compile(rf'^\s*重复\b.*?\b次\s+叫做\s+({标识符模式})\b')
        捕获模式 = re.compile(rf'^\s*如果出错\s+叫做\s+({标识符模式})\b')

        for 行号 in range(当前作用域["line"] + 1, 目标行 + 1):
            行文本 = 行列表[行号 - 1]
            去空 = 行文本.strip()
            if not 去空 or 去空.startswith("#"):
                continue

            缩进 = self._行首缩进宽度(行文本)
            if 缩进 <= 当前作用域["indent"]:
                break

            赋值 = 赋值模式.match(行文本)
            if 赋值:
                局部变量.add(赋值.group(1))
            遍历 = 遍历模式.match(行文本)
            if 遍历:
                局部变量.add(遍历.group(1))
            重复 = 重复模式.match(行文本)
            if 重复:
                局部变量.add(重复.group(1))
            捕获 = 捕获模式.match(行文本)
            if 捕获:
                局部变量.add(捕获.group(1))

        return 局部变量

    def _提取引入别名映射(self, 全文):
        映射 = {}
        模式 = re.compile(
            r'^\s*引入\s*["“](.+?)["”]\s*叫做\s*([\u4e00-\u9fa5A-Za-z_][\u4e00-\u9fa5A-Za-z0-9_]*)',
            re.MULTILINE,
        )
        for 模块名, 别名 in 模式.findall(全文 or ""):
            模块名 = str(模块名).strip()
            别名 = str(别名).strip()
            if 模块名 and 别名:
                映射[别名] = 模块名
        return 映射

    def _跨标签查别名模块(self, 别名, 当前tab_id=None):
        目标别名 = str(别名 or "").strip()
        if not 目标别名:
            return None
        for tab_id, 数据 in self.tabs_data.items():
            if 当前tab_id and tab_id == 当前tab_id:
                continue
            编辑器 = 数据.get("editor")
            if not 编辑器:
                continue
            try:
                文本 = 编辑器.get("1.0", "end-1c")
            except tk.TclError:
                continue
            映射 = self._提取引入别名映射(文本)
            if 目标别名 in 映射:
                return 映射[目标别名]
        return None

    def _获取模块补全成员(self, 模块名, tab_id=None):
        名称 = str(模块名 or "").strip()
        if not 名称:
            return set()

        内置导出 = self._builtin_module_exports()
        if 名称 in 内置导出:
            return set(内置导出.get(名称, []))

        if 名称 == "魔法生态库":
            return set(self.builtin_words)

        本地路径 = self._语义定位易码模块(名称, tab_id=tab_id)
        if 本地路径:
            导出符号, _ = self._语义读取模块导出(本地路径)
            return set(导出符号 or set())

        if 名称 in self._py_module_member_cache:
            return set(self._py_module_member_cache.get(名称, []))

        try:
            模块对象 = importlib.import_module(名称)
            成员 = {名字 for 名字 in dir(模块对象) if 名字 and not str(名字).startswith("_")}
        except Exception:
            成员 = set()
        self._py_module_member_cache[名称] = sorted(成员)
        return 成员

    def _获取模块补全成员详情(self, 模块名, tab_id=None):
        名称 = str(模块名 or "").strip()
        if not 名称:
            return {}

        内置导出 = self._builtin_module_exports()
        if 名称 in 内置导出:
            return {成员名: "function" for 成员名 in 内置导出.get(名称, [])}

        if 名称 == "魔法生态库":
            return {词: "builtin" for 词 in self.builtin_words}

        本地路径 = self._语义定位易码模块(名称, tab_id=tab_id)
        if 本地路径:
            类型表, _ = self._语义读取模块导出详情(本地路径)
            return dict(类型表 or {})

        if 名称 in self._py_module_member_detail_cache:
            return dict(self._py_module_member_detail_cache.get(名称, {}))

        详情 = {}
        签名详情 = {}
        try:
            模块对象 = importlib.import_module(名称)
            for 成员名 in dir(模块对象):
                成员名 = str(成员名)
                if not 成员名 or 成员名.startswith("_"):
                    continue
                类型 = "member"
                try:
                    值 = getattr(模块对象, 成员名)
                    if inspect.isclass(值):
                        类型 = "class"
                        签名详情[成员名] = self._安全签名文本(值)
                    elif callable(值):
                        类型 = "function"
                        签名详情[成员名] = self._安全签名文本(值)
                except Exception:
                    pass
                详情[成员名] = 类型
        except Exception:
            详情 = {}
            签名详情 = {}

        self._py_module_member_detail_cache[名称] = dict(详情)
        self._py_module_member_signature_cache[名称] = dict(签名详情)
        return 详情

    def _获取模块补全成员签名(self, 模块名, tab_id=None):
        名称 = str(模块名 or "").strip()
        if not 名称:
            return {}

        内置导出 = self._builtin_module_exports()
        if 名称 in 内置导出:
            return {成员名: self._builtin_signature_of(成员名) for 成员名 in 内置导出.get(名称, [])}

        if 名称 == "魔法生态库":
            return {词: self._builtin_signature_of(词) for 词 in self.builtin_words}

        本地路径 = self._语义定位易码模块(名称, tab_id=tab_id)
        if 本地路径:
            签名表, _ = self._语义读取模块导出签名(本地路径)
            return dict(签名表 or {})

        if 名称 in self._py_module_member_signature_cache:
            return dict(self._py_module_member_signature_cache.get(名称, {}))

        签名详情 = {}
        try:
            模块对象 = importlib.import_module(名称)
            for 成员名 in dir(模块对象):
                成员名 = str(成员名)
                if not 成员名 or 成员名.startswith("_"):
                    continue
                try:
                    值 = getattr(模块对象, 成员名)
                except Exception:
                    continue
                if callable(值):
                    签名详情[成员名] = self._安全签名文本(值)
        except Exception:
            签名详情 = {}

        self._py_module_member_signature_cache[名称] = dict(签名详情)
        return 签名详情

    def _收集补全上下文(self, 全文, tab_id=None, 光标行=None):
        标识符模式 = r'[\u4e00-\u9fa5A-Za-z_][\u4e00-\u9fa5A-Za-z0-9_]*'
        内容 = 全文 or ""
        局部词 = set(re.findall(r'[\u4e00-\u9fa5A-Za-z0-9_]{2,}', 内容))
        功能名 = set(re.findall(rf'^\s*功能\s+({标识符模式})', 内容, re.MULTILINE))
        图纸名 = set(re.findall(rf'^\s*定义图纸\s+({标识符模式})', 内容, re.MULTILINE))
        变量名 = set(re.findall(rf'^\s*({标识符模式})\s*=', 内容, re.MULTILINE))
        功能签名, 图纸签名 = self._提取定义签名(内容)
        当前局部变量 = self._提取当前作用域局部变量(内容, 光标行)
        引入别名 = self._提取引入别名映射(内容)
        图纸成员映射, 图纸成员类型映射, 图纸成员签名映射 = self._提取图纸成员映射(内容)
        对象实例映射 = self._提取对象实例映射(内容)
        引入模块名 = {str(模块名).strip() for 模块名 in 引入别名.values() if str(模块名).strip()}
        对象成员历史 = {}
        for 对象名, 成员名 in re.findall(rf'({标识符模式})\.({标识符模式})', 内容):
            if not 对象名 or not 成员名:
                continue
            对象成员历史.setdefault(对象名, set()).add(成员名)

        别名成员映射 = {}
        别名成员类型映射 = {}
        别名成员签名映射 = {}
        导入导出平铺 = set()
        导入导出类型 = {}
        导入导出签名 = {}
        类型优先级 = {"function": 5, "blueprint": 4, "class": 3, "alias": 2, "variable": 1, "member": 0, "builtin": 0}

        def 合并导入类型(名称, 类型):
            if not 名称:
                return
            当前 = 导入导出类型.get(名称, "member")
            if 类型优先级.get(类型, 0) >= 类型优先级.get(当前, 0):
                导入导出类型[名称] = 类型

        def 合并导入签名(名称, 签名):
            if 名称 and 签名 and not 导入导出签名.get(名称):
                导入导出签名[名称] = 签名

        for 别名, 模块名 in 引入别名.items():
            成员详情 = self._获取模块补全成员详情(模块名, tab_id=tab_id)
            成员签名 = self._获取模块补全成员签名(模块名, tab_id=tab_id)
            if 成员详情:
                别名成员类型映射[别名] = dict(成员详情)
                成员集 = set(成员详情.keys())
                别名成员映射[别名] = 成员集
                别名成员签名映射[别名] = dict(成员签名 or {})
                导入导出平铺.update(成员集)
                for 成员名, 成员类型 in 成员详情.items():
                    合并导入类型(成员名, 成员类型)
                    合并导入签名(成员名, (成员签名 or {}).get(成员名, ""))
            else:
                成员集 = self._获取模块补全成员(模块名, tab_id=tab_id)
                if 成员集:
                    别名成员映射[别名] = set(成员集)
                    别名成员签名映射[别名] = dict(成员签名 or {})
                    导入导出平铺.update(成员集)
                    for 成员名 in 成员集:
                        合并导入类型(成员名, "member")
                        合并导入签名(成员名, (成员签名 or {}).get(成员名, ""))

        for 对象名, 图纸类型名 in 对象实例映射.items():
            成员集 = set(图纸成员映射.get(图纸类型名, set()))
            类型表 = dict(图纸成员类型映射.get(图纸类型名, {}))
            签名表 = dict(图纸成员签名映射.get(图纸类型名, {}))
            if not 成员集:
                continue
            别名成员映射.setdefault(对象名, set()).update(成员集)
            if 类型表:
                别名成员类型映射.setdefault(对象名, {}).update(类型表)
            if 签名表:
                别名成员签名映射.setdefault(对象名, {}).update(签名表)

        return {
            "局部词": 局部词,
            "功能名": 功能名,
            "图纸名": 图纸名,
            "变量名": 变量名,
            "当前局部变量": 当前局部变量,
            "功能签名": 功能签名,
            "图纸签名": 图纸签名,
            "引入别名": 引入别名,
            "引入模块名": 引入模块名,
            "别名成员映射": 别名成员映射,
            "别名成员类型映射": 别名成员类型映射,
            "别名成员签名映射": 别名成员签名映射,
            "对象成员历史": 对象成员历史,
            "导入导出平铺": 导入导出平铺,
            "导入导出类型": 导入导出类型,
            "导入导出签名": 导入导出签名,
        }

    def _展示自动补全候选(self, editor, 排序候选):
        self._autocomplete_items = []
        self._autocomplete_row_ids = []
        try:
            for 行id in self.autocomplete_tree.get_children():
                self.autocomplete_tree.delete(行id)
        except tk.TclError:
            pass
        显示内容列表 = []
        显示标签列表 = []

        标签映射 = {
            "snippet": "模板",
            "builtin": "内置能力",
            "builtin_func": "内置功能",
            "keyword": "关键字",
            "function": "功能",
            "blueprint": "图纸",
            "alias": "模块别名",
            "module": "模块名",
            "member": "模块成员",
            "member_func": "模块功能",
            "member_blueprint": "模块图纸",
            "member_class": "模块类",
            "member_var": "模块变量",
            "member_alias": "模块别名",
            "imported": "已引入",
            "imported_func": "已引入功能",
            "imported_blueprint": "已引入图纸",
            "imported_class": "已引入类",
            "imported_var": "已引入变量",
            "imported_alias": "已引入别名",
            "variable": "变量",
            "local_word": "上下文词",
        }
        颜色映射 = {
            "snippet": "#9CDCFE",
            "builtin": "#DCDCAA",
            "builtin_func": "#DCDCAA",
            "keyword": "#C586C0",
            "function": "#4FC1FF",
            "blueprint": "#C586C0",
            "alias": "#B5CEA8",
            "module": "#CE9178",
            "member": "#E8E8E8",
            "member_func": "#4FC1FF",
            "member_blueprint": "#C586C0",
            "member_class": "#FFB86C",
            "member_var": "#7BD88F",
            "member_alias": "#B5CEA8",
            "imported": "#FFD27F",
            "imported_func": "#4FC1FF",
            "imported_blueprint": "#C586C0",
            "imported_class": "#FFB86C",
            "imported_var": "#7BD88F",
            "imported_alias": "#B5CEA8",
            "variable": "#7BD88F",
            "local_word": "#9AA6B2",
        }

        for 行号, 候选 in enumerate(排序候选[:28]):
            if isinstance(候选, dict):
                来源 = str(候选.get("source", "")).strip()
                词 = str(候选.get("insert", "")).strip()
                签名 = str(候选.get("sig", "")).strip()
                可调用 = bool(候选.get("callable", False))
            else:
                来源 = str(候选[1] if len(候选) > 1 else "").strip()
                词 = str(候选[2] if len(候选) > 2 else "").strip()
                签名 = str(候选[3] if len(候选) > 3 else "").strip()
                可调用 = bool(候选[4]) if len(候选) > 4 else False
            if not 词:
                continue
            标签 = 标签映射.get(来源, "上下文")
            显示内容 = f"{词}{签名}" if 签名 else 词
            self._autocomplete_items.append({
                "insert": 词,
                "source": 来源,
                "sig": 签名,
                "callable": 可调用,
            })
            显示标签列表.append(标签)
            显示内容列表.append(显示内容)
            try:
                行id = f"ac_{len(self._autocomplete_row_ids)}"
                标签名 = f"src_{来源}" if 来源 else "src_default"
                self.autocomplete_tree.insert("", "end", iid=行id, values=(标签, 显示内容), tags=(标签名,))
                self._autocomplete_row_ids.append(行id)
                self.autocomplete_tree.tag_configure(标签名, foreground=颜色映射.get(来源, self.theme_fg))
            except tk.TclError:
                pass

        if not self._autocomplete_items:
            self._hide_autocomplete()
            return

        self._autocomplete_select_index(0)
        try:
            self._autocomplete_popup_line = editor.index("insert").split(".")[0]
        except Exception:
            self._autocomplete_popup_line = None

        bbox = editor.bbox("insert")
        if not bbox:
            self._hide_autocomplete()
            return
        x, y, _, height = bbox
        root_x = editor.winfo_rootx() - self.root.winfo_rootx() + x + 5
        root_y = editor.winfo_rooty() - self.root.winfo_rooty() + y + height + 5

        try:
            self.root.update_idletasks()
            字体对象 = tkfont.Font(font=self.font_code)
            最大标签宽 = max((字体对象.measure(t) for t in 显示标签列表), default=80)
            最大内容宽 = max((字体对象.measure(t) for t in 显示内容列表), default=260)
            类型列宽 = max(92, min(180, 最大标签宽 + 28))
            内容列宽 = max(260, 最大内容宽 + 28)
            根宽度 = max(420, int(self.root.winfo_width()))
            目标宽度 = max(420, 类型列宽 + 内容列宽 + 26)
            可用最大宽度 = max(320, 根宽度 - 16)
            列表宽度 = min(目标宽度, 可用最大宽度)
            if root_x + 列表宽度 > 根宽度 - 8:
                root_x = max(8, 根宽度 - 列表宽度 - 8)

            行高 = max(20, 字体对象.metrics("linespace") + 6)
            可见行数 = min(max(4, len(self._autocomplete_items)), 10)
            标题高度 = 26
            水平滚动条高度 = max(12, int(16 * self.dpi_scale))
            列表高度 = max(140, 标题高度 + 行高 * 可见行数 + 水平滚动条高度 + 8)

            最终内容列宽 = max(180, 列表宽度 - 类型列宽 - 20)
            self.autocomplete_tree.column("kind", width=类型列宽, minwidth=88, stretch=False)
            self.autocomplete_tree.column("item", width=最终内容列宽, minwidth=180, stretch=True)
            self.autocomplete_popup.place(x=root_x, y=root_y, width=列表宽度, height=列表高度)
        except Exception:
            self.autocomplete_popup.place(x=root_x, y=root_y)
        self.autocomplete_popup.lift()

    def _get_context_snippets(self, editor):
        """检测光标前的代码块类型，返回上下文相关的 snippet 建议列表。
        返回格式: set of snippet names that should be boosted."""
        try:
            cursor_line = int(editor.index("insert").split(".")[0])
        except Exception:
            return set()

        # 上下文关联规则：前面的代码块 → 建议的后续 snippet
        上下文规则 = {
            "如果": {"否则如果", "不然"},
            "否则如果": {"否则如果", "不然"},
            "尝试": {"如果出错"},
        }

        # 获取当前行的缩进级别
        try:
            当前行文本 = editor.get(f"{cursor_line}.0", f"{cursor_line}.end")
            当前缩进 = len(当前行文本) - len(当前行文本.lstrip())
        except Exception:
            当前缩进 = 0

        # 向上扫描，寻找同级或更低缩进级别的代码块头
        for i in range(cursor_line - 1, max(0, cursor_line - 30), -1):
            try:
                行文本 = editor.get(f"{i}.0", f"{i}.end")
            except Exception:
                continue
            stripped = 行文本.strip()
            if not stripped:
                continue
            行缩进 = len(行文本) - len(行文本.lstrip())

            # 如果遇到同级或更低缩进的代码行
            if 行缩进 <= 当前缩进:
                for 关键词, 建议集 in 上下文规则.items():
                    if stripped.startswith(关键词):
                        return 建议集
                # 遇到了同级但不匹配的行，停止搜索
                break

        return set()

    def _check_autocomplete(self, event=None):
        # 排除 Ctrl 组合键（手动触发除外）
        if event and (event.state & 0x4):
            self._hide_autocomplete()
            self._hide_calltip()
            return
        if event and event.keysym in ("Up", "Down", "Left", "Right", "Prior", "Next", "Return", "KP_Enter", "Tab", "Escape"):
            if event.keysym == "Escape":
                self._hide_autocomplete()
                self._hide_calltip()
            elif event.keysym in ("Left", "Right", "Up", "Down", "Prior", "Next"):
                self._schedule_calltip_update()
            elif event.keysym in ("Return", "KP_Enter", "Tab"):
                self._schedule_calltip_update()
            return

        editor = self._get_current_editor()
        tab_id = self._get_current_tab_id()
        if not editor:
            return

        全文 = editor.get("1.0", "end-1c")
        行前文本 = editor.get("insert linestart", "insert")
        try:
            光标行 = int(editor.index("insert").split(".")[0])
        except Exception:
            光标行 = 1
        标识符模式 = r'[\u4e00-\u9fa5A-Za-z_][\u4e00-\u9fa5A-Za-z0-9_]*'
        上下文 = self._收集补全上下文(全文, tab_id=tab_id, 光标行=光标行)
        self._update_calltip(editor=editor, tab_id=tab_id, 全文=全文, 行前文本=行前文本, 上下文=上下文)

        点号匹配 = re.search(rf'({标识符模式})\.([\u4e00-\u9fa5A-Za-z0-9_]*)$', 行前文本)
        if 点号匹配:
            对象名 = 点号匹配.group(1)
            成员前缀 = 点号匹配.group(2) or ""
            成员候选集合 = set(上下文["别名成员映射"].get(对象名, set()))
            成员候选集合.update(上下文.get("对象成员历史", {}).get(对象名, set()))
            成员类型映射 = dict(上下文.get("别名成员类型映射", {}).get(对象名, {}))
            成员签名映射 = dict(上下文.get("别名成员签名映射", {}).get(对象名, {}))

            if not 成员候选集合:
                跨标签模块 = self._跨标签查别名模块(对象名, 当前tab_id=tab_id)
                if 跨标签模块:
                    跨标签详情 = self._获取模块补全成员详情(跨标签模块, tab_id=tab_id)
                    跨标签签名 = self._获取模块补全成员签名(跨标签模块, tab_id=tab_id)
                    if 跨标签详情:
                        成员候选集合.update(跨标签详情.keys())
                        成员类型映射.update(跨标签详情)
                        成员签名映射.update(跨标签签名 or {})
                    else:
                        成员候选集合.update(self._获取模块补全成员(跨标签模块, tab_id=tab_id))
                        成员签名映射.update(跨标签签名 or {})

            成员候选 = sorted(成员候选集合)
            if not 成员候选:
                self._hide_autocomplete()
                return

            类型到来源 = {
                "function": "member_func",
                "blueprint": "member_blueprint",
                "class": "member_class",
                "variable": "member_var",
                "alias": "member_alias",
            }
            排名列表 = []
            for 成员名 in 成员候选:
                if not self._autocomplete_match(成员名, 成员前缀):
                    continue
                基础分 = 0 if (成员前缀 and 成员名.startswith(成员前缀)) else (0.2 if not 成员前缀 else 1.8)
                成员类型 = 成员类型映射.get(成员名, "member")
                成员来源 = 类型到来源.get(成员类型, "member")
                排名列表.append({
                    "score": 基础分 + len(成员名) / 260.0,
                    "source": 成员来源,
                    "insert": 成员名,
                    "sig": str(成员签名映射.get(成员名, "") or ""),
                    "callable": 成员类型 in {"function", "class"},
                })

            if not 排名列表:
                self._hide_autocomplete()
                return

            self._autocomplete_replace_start = "insert" if not 成员前缀 else f"insert - {len(成员前缀)}c"
            self._autocomplete_replace_end = "insert"
            self._展示自动补全候选(editor, sorted(排名列表, key=lambda x: (x["score"], x["insert"])))
            return

        普通匹配 = re.search(rf'({标识符模式})$', 行前文本)
        if not 普通匹配:
            self._hide_autocomplete()
            return

        当前词 = 普通匹配.group(1)
        if len(当前词) < 1:
            self._hide_autocomplete()
            return

        功能签名 = 上下文.get("功能签名", {})
        图纸签名 = 上下文.get("图纸签名", {})
        导入签名 = 上下文.get("导入导出签名", {})
        当前局部变量 = 上下文.get("当前局部变量", set()) or set()
        候选映射 = {}

        def 加候选(词, 来源, 基础分, 签名="", 可调用=False):
            if not self._autocomplete_match(词, 当前词):
                return
            分数 = 基础分
            if 词 == 当前词:
                分数 -= 1.1
            elif 词.startswith(当前词):
                分数 -= 0.4
            分数 += len(词) / 260.0
            旧 = 候选映射.get(词)
            新项 = {
                "score": 分数,
                "source": 来源,
                "insert": 词,
                "sig": str(签名 or ""),
                "callable": bool(可调用),
            }
            if 旧 is None or 分数 < 旧["score"]:
                候选映射[词] = 新项
            elif 旧 is not None:
                if (not 旧.get("sig")) and 新项.get("sig"):
                    旧["sig"] = 新项["sig"]
                if 新项.get("callable") and not 旧.get("callable"):
                    旧["callable"] = True

        上下文建议 = self._get_context_snippets(editor)

        for 词 in self.autocomplete_words:
            if 词 in self.snippets:
                # 上下文相关的 snippet 排在最前面
                分数 = -1.5 if 词 in 上下文建议 else -0.2
                加候选(词, "snippet", 分数, 可调用=False)
            elif 词 in self.builtin_words:
                加候选(词, "builtin_func", 0.08, 签名=self._builtin_signature_of(词), 可调用=True)
            else:
                # 上下文相关的关键词也排在前面（如 尝试 后面的 如果出错）
                分数 = -1.5 if 词 in 上下文建议 else 0.26
                加候选(词, "keyword", 分数, 可调用=False)

        for 词 in 上下文["功能名"]:
            加候选(词, "function", 0.05, 签名=功能签名.get(词, "()"), 可调用=True)
        for 词 in 上下文["图纸名"]:
            加候选(词, "blueprint", 0.09, 签名=图纸签名.get(词, "()"), 可调用=False)
        for 词 in 上下文["变量名"]:
            权重 = 0.02 if 词 in 当前局部变量 else 0.35
            加候选(词, "variable", 权重, 可调用=False)
        for 词 in 上下文["引入别名"].keys():
            加候选(词, "alias", 0.12, 可调用=False)
        for 词 in 上下文.get("引入模块名", set()):
            加候选(词, "module", 0.22, 可调用=False)
        导入类型 = 上下文.get("导入导出类型", {})
        导入类型到来源 = {
            "function": "imported_func",
            "blueprint": "imported_blueprint",
            "class": "imported_class",
            "variable": "imported_var",
            "alias": "imported_alias",
        }
        for 词 in 上下文["导入导出平铺"]:
            词类型 = 导入类型.get(词, "member")
            来源 = 导入类型到来源.get(词类型, "imported")
            可调用 = 词类型 in {"function", "class"}
            加候选(词, 来源, 0.46, 签名=导入签名.get(词, ""), 可调用=可调用)
        for 词 in 上下文["局部词"]:
            if 词 not in self.autocomplete_words:
                加候选(词, "local_word", 0.7, 可调用=False)

        if not 候选映射:
            self._hide_autocomplete()
            return

        self._autocomplete_replace_start = f"insert - {len(当前词)}c"
        self._autocomplete_replace_end = "insert"
        排序后 = sorted(候选映射.values(), key=lambda x: (x["score"], x["insert"]))
        self._展示自动补全候选(editor, 排序后)

    def _handle_autocomplete_nav(self, event):
        if not self._autocomplete_is_visible():
            return # 交给系统默认处理

        总数 = len(self._autocomplete_row_ids)
        if 总数 <= 0:
            return "break"

        idx = self._autocomplete_current_index()
         
        if event.keysym == 'Up':
            idx = max(0, idx - 1)
        elif event.keysym == 'Down':
            idx = min(总数 - 1, idx + 1)
        elif event.keysym == 'Prior':
            idx = max(0, idx - 8)
        elif event.keysym == 'Next':
            idx = min(总数 - 1, idx + 8)
             
        self._autocomplete_select_index(idx)
        return "break" # 阻止光标移动

    def _accept_autocomplete(self, event=None):
        if not self._autocomplete_is_visible():
            return "break"
        self._autocomplete_mouse_down = False

        idx = self._autocomplete_index_from_event(event)
        if idx is None:
            idx = self._autocomplete_current_index()

        if idx < 0 or idx >= len(self._autocomplete_items):
            self._hide_autocomplete()
            return "break"

        当前候选 = self._autocomplete_items[idx]
        selected_word = str(当前候选.get("insert", "")).strip()
        selected_source = str(当前候选.get("source", "")).strip()
        selected_callable = bool(当前候选.get("callable", False))
        if not selected_word:
            self._hide_autocomplete()
            return "break"

        editor = self._get_current_editor()
        if not editor:
            self._hide_autocomplete()
            return "break"

        start_index = self._autocomplete_replace_start
        end_index = self._autocomplete_replace_end or "insert"
        if not start_index:
            line_text = editor.get("insert linestart", "insert")
            match = re.search(r'([\u4e00-\u9fa5A-Za-z0-9_]+)$', line_text)
            if match:
                start_index = f"insert - {len(match.group(1))}c"
            else:
                start_index = "insert"

        try:
            insert_pos = editor.index("insert")
            start_pos = editor.index(start_index)
            end_pos = editor.index(end_index)

            当前行 = insert_pos.split(".")[0]
            起始行 = start_pos.split(".")[0]
            结束行 = end_pos.split(".")[0]
            跨行或错序 = (
                起始行 != 当前行
                or 结束行 != 当前行
                or editor.compare(start_pos, ">", end_pos)
            )
            if 跨行或错序:
                line_text = editor.get("insert linestart", "insert")
                match = re.search(r'([\u4e00-\u9fa5A-Za-z0-9_]+)$', line_text)
                if match:
                    start_pos = editor.index(f"insert - {len(match.group(1))}c")
                else:
                    start_pos = insert_pos
                end_pos = insert_pos

            editor.delete(start_pos, end_pos)
            editor.insert(start_pos, selected_word)
            末尾位置 = editor.index(f"{start_pos} + {len(selected_word)}c")

            自动补括号来源 = {"function", "member", "member_func", "imported", "imported_func", "builtin_func", "member_class", "imported_class"}
            if selected_callable or (selected_source in 自动补括号来源):
                下一个字符 = editor.get(末尾位置, f"{末尾位置}+1c")
                if 下一个字符 != "(":
                    editor.insert(末尾位置, "()")
                    editor.mark_set("insert", f"{末尾位置}+1c")
                else:
                    editor.mark_set("insert", f"{末尾位置}+1c")
            else:
                editor.mark_set("insert", 末尾位置)

            editor.focus_set()
            self.highlight()
        except tk.TclError:
            pass

        self._hide_autocomplete()
        self._schedule_calltip_update()
        return "break"

    def bind_global_shortcuts(self):
        self.root.bind("<Control-s>", self._shortcut_save)
        self.root.bind("<Control-o>", self._shortcut_open)
        self.root.bind("<Control-n>", self._shortcut_new)
        self.root.bind("<F5>", self._shortcut_run)
        self.root.bind("<Control-d>", self._shortcut_multi_add_next)
        self.root.bind("<Control-D>", self._shortcut_multi_add_next)
        self.root.bind("<Control-Shift-L>", self._shortcut_multi_select_all)
        self.root.bind("<Control-Shift-l>", self._shortcut_multi_select_all)
        self.root.bind("<Control-f>", self._shortcut_find)
        self.root.bind("<Control-h>", self._shortcut_replace)
        self.root.bind("<Control-Shift-R>", self._shortcut_rename_symbol)
        self.root.bind("<Control-Shift-r>", self._shortcut_rename_symbol)
        self.root.bind("<Alt-f>", self._shortcut_toggle_fold)
        self.root.bind("<Alt-u>", self._shortcut_unfold_all)

    def _shortcut_save(self, event=None):
        self.save_file(show_message=False)
        return "break"

    def _shortcut_open(self, event=None):
        self.open_file()
        return "break"

    def _shortcut_new(self, event=None):
        self.clear_code()
        return "break"

    def _shortcut_run(self, event=None):
        self.run_code()
        return "break"

    def _shortcut_multi_add_next(self, event=None):
        return self.multi_cursor_add_next(event)

    def _shortcut_multi_select_all(self, event=None):
        return self.multi_cursor_select_all(event)

    def _shortcut_find(self, event=None):
        self.open_find_dialog(focus_replace=False)
        return "break"

    def _shortcut_replace(self, event=None):
        self.open_find_dialog(focus_replace=True)
        return "break"

    def _shortcut_rename_symbol(self, event=None):
        return self.rename_symbol(event)

    def _shortcut_toggle_fold(self, event=None):
        return self.toggle_fold_current_line(event)

    def _shortcut_unfold_all(self, event=None):
        return self.unfold_all_blocks(event)

    def _symbol_pattern(self, name):
        escaped = re.escape(name)
        return re.compile(rf'(?<![\u4e00-\u9fa5A-Za-z0-9_]){escaped}(?![\u4e00-\u9fa5A-Za-z0-9_])')

    def _is_valid_symbol_name(self, name):
        return bool(re.fullmatch(r'[\u4e00-\u9fa5A-Za-z_][\u4e00-\u9fa5A-Za-z0-9_]*', name))

    def _get_symbol_near_cursor(self, editor):
        try:
            selected = editor.get(tk.SEL_FIRST, tk.SEL_LAST).strip()
            if self._is_valid_symbol_name(selected):
                return selected
        except tk.TclError:
            pass

        insert_idx = editor.index("insert")
        line_no_str, col_str = insert_idx.split(".")
        line_no = int(line_no_str)
        col = int(col_str)
        line_text = editor.get(f"{line_no}.0", f"{line_no}.end")

        for match in re.finditer(r'[\u4e00-\u9fa5A-Za-z_][\u4e00-\u9fa5A-Za-z0-9_]*', line_text):
            if match.start() <= col <= match.end():
                return match.group(0)
        return ""

    def rename_symbol(self, event=None):
        editor = self._get_current_editor()
        tab_id = self._get_current_tab_id()
        if not editor or not tab_id or tab_id not in self.tabs_data:
            return "break"
        self._clear_multi_cursor_mode(tab_id)

        old_name = self._get_symbol_near_cursor(editor)
        if not old_name:
            messagebox.showinfo("重命名符号", "请先把光标放到一个变量/功能/图纸名称上，或先选中一个名称。")
            return "break"

        new_name = simpledialog.askstring(
            "批量重命名",
            f"将符号【{old_name}】重命名为：",
            initialvalue=old_name,
            parent=self.root
        )
        if new_name is None:
            return "break"

        new_name = new_name.strip()
        if not new_name:
            messagebox.showwarning("重命名失败", "新名称不能为空。")
            return "break"
        if new_name == old_name:
            self.status_main_var.set("重命名取消：新旧名称相同")
            return "break"
        if not self._is_valid_symbol_name(new_name):
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
                    f"将在当前文件把【{old_name}】替换为【{new_name}】\n预计影响 {replaced_count} 处，是否继续？"
                ):
                    self.status_main_var.set("重命名已取消")
                    return "break"
                for start, end in reversed(ranges):
                    replaced_code = replaced_code[:start] + new_name + replaced_code[end:]
        except Exception:
            # 文件暂时不合法时，回退到整词替换模式
            pass

        if replaced_count <= 0:
            pattern = self._symbol_pattern(old_name)
            matches = list(pattern.finditer(code))
            count = len(matches)
            if count == 0:
                self.status_main_var.set(f"未找到可重命名项：{old_name}")
                return "break"
            if not messagebox.askyesno(
                "确认重命名",
                f"当前文件存在语法问题，将使用整词模式重命名。\n【{old_name}】 -> 【{new_name}】\n预计影响 {count} 处，是否继续？"
            ):
                self.status_main_var.set("重命名已取消")
                return "break"
            replaced_code, replaced_count = pattern.subn(new_name, code)
            if replaced_count <= 0:
                self.status_main_var.set("重命名未产生修改")
                return "break"

        editor.edit_separator()
        editor.delete("1.0", "end")
        editor.insert("1.0", replaced_code)
        editor.edit_separator()

        self.tabs_data[tab_id]["dirty"] = True
        self._update_tab_title(tab_id)
        self._update_status_main()
        self.highlight()
        self._schedule_diagnose()
        self._schedule_outline_update()
        self._update_line_numbers()
        self.status_main_var.set(f"重命名完成：{old_name} -> {new_name}（共 {replaced_count} 处）")
        return "break"

    def _clear_find_marks(self, editor=None):
        target = editor if editor else self._get_current_editor()
        if not target:
            return
        target.tag_remove("SearchMatch", "1.0", "end")
        target.tag_remove("SearchCurrent", "1.0", "end")

    def _highlight_find_matches(self, event=None):
        editor = self._get_current_editor()
        if not editor:
            return 0

        query = self.find_var.get()
        self._clear_find_marks(editor)
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

    def _focus_find_result(self, start_idx, end_idx, query):
        editor = self._get_current_editor()
        if not editor:
            return
        editor.tag_remove("SearchCurrent", "1.0", "end")
        editor.tag_add("SearchCurrent", start_idx, end_idx)
        editor.tag_remove("sel", "1.0", "end")
        editor.tag_add("sel", start_idx, end_idx)
        editor.mark_set("insert", end_idx)
        editor.see(start_idx)
        self.status_main_var.set(f"查找：已定位“{query}”")

    def _find_next(self, event=None):
        editor = self._get_current_editor()
        if not editor:
            return "break"
        query = self.find_var.get()
        if not query:
            return "break"

        self._highlight_find_matches()
        start = editor.index("insert+1c")
        idx = editor.search(query, start, stopindex="end")
        if not idx:
            idx = editor.search(query, "1.0", stopindex=start)

        if idx:
            end = f"{idx}+{len(query)}c"
            self._focus_find_result(idx, end, query)
        else:
            self.status_main_var.set(f"查找：未找到“{query}”")
        return "break"

    def _find_prev(self, event=None):
        editor = self._get_current_editor()
        if not editor:
            return "break"
        query = self.find_var.get()
        if not query:
            return "break"

        self._highlight_find_matches()
        start = editor.index("insert-1c")
        idx = editor.search(query, start, stopindex="1.0", backwards=True)
        if not idx:
            idx = editor.search(query, "end-1c", stopindex=start, backwards=True)

        if idx:
            end = f"{idx}+{len(query)}c"
            self._focus_find_result(idx, end, query)
        else:
            self.status_main_var.set(f"查找：未找到“{query}”")
        return "break"

    def _replace_one(self, event=None):
        editor = self._get_current_editor()
        if not editor:
            return "break"
        query = self.find_var.get()
        replacement = self.replace_var.get()
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
            self._find_next()
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
            self.status_main_var.set(f"替换：已将“{query}”替换为“{replacement}”")
            self._highlight_find_matches()
            self._find_next()
        else:
            self.status_main_var.set(f"替换：未找到“{query}”")
        return "break"

    def _replace_all(self, event=None):
        editor = self._get_current_editor()
        if not editor:
            return "break"
        query = self.find_var.get()
        replacement = self.replace_var.get()
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

        self._highlight_find_matches()
        self.status_main_var.set(f"替换：共替换 {count} 处")
        return "break"

    def open_find_dialog(self, event=None, focus_replace=False):
        if self.find_dialog and self.find_dialog.winfo_exists():
            self.find_dialog.deiconify()
            self.find_dialog.lift()
        else:
            self.find_dialog = tk.Toplevel(self.root)
            self.find_dialog.title("查找与替换")
            self.find_dialog.configure(bg=self.theme_sidebar_bg)
            self.find_dialog.resizable(False, False)
            self.find_dialog.transient(self.root)

            width = int(430 * self.dpi_scale)
            height = int(150 * self.dpi_scale)
            x = self.root.winfo_x() + max(30, int(40 * self.dpi_scale))
            y = self.root.winfo_y() + max(70, int(80 * self.dpi_scale))
            self.find_dialog.geometry(f"{width}x{height}+{x}+{y}")

            container = tk.Frame(self.find_dialog, bg=self.theme_sidebar_bg, padx=12, pady=10)
            container.pack(fill=tk.BOTH, expand=True)

            row1 = tk.Frame(container, bg=self.theme_sidebar_bg)
            row1.pack(fill=tk.X, pady=(0, 8))
            tk.Label(row1, text="查找：", font=self.font_ui, bg=self.theme_sidebar_bg, fg=self.theme_fg, width=6, anchor="e").pack(side=tk.LEFT)
            self.find_entry = tk.Entry(
                row1,
                textvariable=self.find_var,
                font=self.font_code,
                bg=self.theme_bg,
                fg=self.theme_fg,
                insertbackground="#FFFFFF",
                relief="flat",
                highlightthickness=1,
                highlightbackground=self.theme_sash,
                highlightcolor="#0E639C"
            )
            self.find_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=3)
            self.find_entry.bind("<Return>", self._find_next)
            self.find_entry.bind("<KeyRelease>", self._highlight_find_matches)

            row2 = tk.Frame(container, bg=self.theme_sidebar_bg)
            row2.pack(fill=tk.X, pady=(0, 8))
            tk.Label(row2, text="替换：", font=self.font_ui, bg=self.theme_sidebar_bg, fg=self.theme_fg, width=6, anchor="e").pack(side=tk.LEFT)
            self.replace_entry = tk.Entry(
                row2,
                textvariable=self.replace_var,
                font=self.font_code,
                bg=self.theme_bg,
                fg=self.theme_fg,
                insertbackground="#FFFFFF",
                relief="flat",
                highlightthickness=1,
                highlightbackground=self.theme_sash,
                highlightcolor="#0E639C"
            )
            self.replace_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=3)
            self.replace_entry.bind("<Return>", self._replace_one)

            btn_row = tk.Frame(container, bg=self.theme_sidebar_bg)
            btn_row.pack(fill=tk.X)

            def _btn(text, cmd):
                return tk.Button(
                    btn_row, text=text, command=cmd, font=self.font_ui,
                    bg=self.theme_toolbar_bg, fg=self.theme_fg,
                    activebackground="#505050", activeforeground="#FFFFFF",
                    relief="flat", borderwidth=0, padx=8, pady=4, cursor="hand2"
                )

            _btn("上一个", self._find_prev).pack(side=tk.LEFT, padx=(0, 6))
            _btn("下一个", self._find_next).pack(side=tk.LEFT, padx=(0, 6))
            _btn("替换", self._replace_one).pack(side=tk.LEFT, padx=(0, 6))
            _btn("全部替换", self._replace_all).pack(side=tk.LEFT, padx=(0, 6))
            _btn("关闭", lambda: self.find_dialog.withdraw()).pack(side=tk.RIGHT)

            self.find_dialog.bind("<Escape>", lambda e: self.find_dialog.withdraw())
            self.find_dialog.protocol("WM_DELETE_WINDOW", lambda: self.find_dialog.withdraw())

        editor = self._get_current_editor()
        if editor:
            try:
                selected = editor.get(tk.SEL_FIRST, tk.SEL_LAST)
                if selected and "\n" not in selected:
                    self.find_var.set(selected)
            except tk.TclError:
                pass
            self._highlight_find_matches()

        if focus_replace and hasattr(self, "replace_entry"):
            self.replace_entry.focus_set()
            self.replace_entry.select_range(0, tk.END)
        elif hasattr(self, "find_entry"):
            self.find_entry.focus_set()
            self.find_entry.select_range(0, tk.END)
        return "break"

    def highlight(self, event=None):
        editor = self._get_current_editor()
        if not editor: return
        self._highlight_after_id = None
        
        code = editor.get("1.0", "end-1c")
        
        # 先清除所有高亮
        for tag in ["Define", "Keyword", "Operator", "String", "Number", "Comment", "Boolean", "Builtin", "ModuleAlias", "ObjectRef", "MemberName"]:
            editor.tag_remove(tag, "1.0", "end")
            
        # 1. 高亮数字 (包含小数)
        for match in re.finditer(r'\b\d+(\.\d+)?\b', code):
            start_idx = f"1.0 + {match.start()}c"
            end_idx = f"1.0 + {match.end()}c"
            editor.tag_add("Number", start_idx, end_idx)
            
        # 2. 高亮字符串 (双引号包含的内容)
        for match in re.finditer(r'"[^"]*"', code):
            start_idx = f"1.0 + {match.start()}c"
            end_idx = f"1.0 + {match.end()}c"
            editor.tag_add("String", start_idx, end_idx)

        # 3. 高亮注释 (# 开始到行尾)
        for match in re.finditer(r'#.*', code):
            start_idx = f"1.0 + {match.start()}c"
            end_idx = f"1.0 + {match.end()}c"
            editor.tag_add("Comment", start_idx, end_idx)
            
        # 4. 高亮关键字与操作符
        # Define 控制结构定义
        defines = ["功能", "返回", "叫做", "尝试", "如果出错", "定义图纸", "造一个", "它的"]
        
        # Keyword 流程控制
        keywords = ["如果", "就", "否则如果", "不然",
                   "当", "的时候", "重复", "次", "遍历", "里的每一个",
                   "停下", "略过", "引入"]
                   
        operators = ["而且", "并且", "或者", "取反", "!",
                     "+", "-", "*", "/", "%", "**", "//", "==", "!=", ">", "<", ">=", "<="]
        
        booleans = ["对", "错", "空"]
        
        builtins_list = self.builtin_words
        
        def apply_tags(word_list, tag_name):
            # 将单词按长度降序排列，保证长词(如有包含关系)优先被匹配
            for kw in sorted(word_list, key=len, reverse=True):
                start = "1.0"
                while True:
                    # 使用精确字面量匹配
                    start = editor.search(kw, start, stopindex="end")
                    if not start:
                        break
                    
                    end = f"{start} + {len(kw)}c"
                    
                    # ★ 全词边界检测：防止 "长度" 匹配到 "长度值"，"错" 匹配到 "错误信息"
                    is_word = True
                    # 检查前一个字符
                    try:
                        prev_char = editor.get(f"{start} - 1c", start)
                        if prev_char and re.match(r'[\u4e00-\u9fa5a-zA-Z0-9_]', prev_char):
                            is_word = False
                    except tk.TclError:
                        pass
                    # 检查后一个字符
                    if is_word:
                        try:
                            next_char = editor.get(end, f"{end} + 1c")
                            if next_char and re.match(r'[\u4e00-\u9fa5a-zA-Z0-9_]', next_char):
                                # 特殊豁免：操作符后面紧跟中文是允许的（如 "==" 后跟条件）
                                if tag_name != "Operator":
                                    is_word = False
                        except tk.TclError:
                            pass
                    
                    # 防止破坏已经高亮的字符串、注释，或者已经被标记的更高优先级结构
                    existing_tags = editor.tag_names(start)
                    conflict_tags = ["String", "Comment", "Define", "Keyword", "Operator", "Boolean", "Builtin"]
                    
                    if is_word and not any(t in existing_tags for t in conflict_tags):
                        editor.tag_add(tag_name, start, end)
                        
                    start = end

        apply_tags(defines, "Define")
        apply_tags(keywords, "Keyword")
        apply_tags(operators, "Operator")
        apply_tags(booleans, "Boolean")
        apply_tags(builtins_list, "Builtin")

        # 5. 高亮对象成员调用：对象.成员
        #    - 模块别名对象（来自 引入 ... 叫做 ...）用 ModuleAlias
        #    - 其他对象名用 ObjectRef
        #    - 点后的成员名统一用 MemberName
        别名集合 = set(self._提取引入别名映射(code).keys())
        标识符模式 = r'[\u4e00-\u9fa5A-Za-z_][\u4e00-\u9fa5A-Za-z0-9_]*'

        def 在字符串或注释内(索引):
            标签 = editor.tag_names(索引)
            return ("String" in 标签) or ("Comment" in 标签)

        for match in re.finditer(rf'({标识符模式})\.({标识符模式})', code):
            obj_start = f"1.0 + {match.start(1)}c"
            obj_end = f"1.0 + {match.end(1)}c"
            member_start = f"1.0 + {match.start(2)}c"
            member_end = f"1.0 + {match.end(2)}c"
            if 在字符串或注释内(obj_start):
                continue
            obj_name = match.group(1)
            obj_tag = "ModuleAlias" if obj_name in 别名集合 else "ObjectRef"
            editor.tag_add(obj_tag, obj_start, obj_end)
            editor.tag_add("MemberName", member_start, member_end)

        # 6. 高亮正在输入的对象点号（如 系统.）
        for match in re.finditer(rf'({标识符模式})\.(?=\s|$|[)\],])', code):
            obj_start = f"1.0 + {match.start(1)}c"
            obj_end = f"1.0 + {match.end(1)}c"
            if 在字符串或注释内(obj_start):
                continue
            obj_name = match.group(1)
            obj_tag = "ModuleAlias" if obj_name in 别名集合 else "ObjectRef"
            editor.tag_add(obj_tag, obj_start, obj_end)

    def print_output(self, text, is_error=False):
        try:
            self.output.config(state=tk.NORMAL)
            if is_error or str(text).startswith("❌"):
                self.output.insert(tk.END, text + "\n", "ConsoleError")
            else:
                self.output.insert(tk.END, text + "\n")
            self.output.see(tk.END)
            self.output.config(state=tk.DISABLED)
        except tk.TclError:
            pass  # 窗口已经关闭了，静默忽略

    def _write_output_console_intro(self):
        self.print_output("========================================")
        self.print_output("【易码调试控制台】")
        self.print_output("作者：景磊")
        self.print_output("联系 QQ：395842972 / 97777315")
        self.print_output("========================================")

    def _clear_output_console(self, keep_intro=True):
        try:
            self.output.config(state=tk.NORMAL)
            self.output.delete("1.0", tk.END)
            self.output.config(state=tk.DISABLED)
        except tk.TclError:
            return
        if keep_intro:
            self._write_output_console_intro()

    # ==========================
    # 项目记录（上次项目 / 历史项目）
    # ==========================
    def _normalize_project_dir(self, path):
        if not path:
            return None
        try:
            normalized = os.path.abspath(os.path.expanduser(str(path).strip()))
        except Exception:
            return None
        return normalized if os.path.isdir(normalized) else None

    def _normalize_file_path(self, path):
        if not path:
            return None
        try:
            normalized = os.path.abspath(os.path.expanduser(str(path).strip()))
        except Exception:
            return None
        return normalized if os.path.isfile(normalized) else None

    def _load_project_state(self):
        try:
            if not os.path.exists(self._state_file):
                return
            with open(self._state_file, "r", encoding="utf-8") as f:
                state = json.load(f)
            if not isinstance(state, dict):
                return

            history = state.get("project_history", [])
            if isinstance(history, list):
                cleaned = []
                for item in history:
                    normalized = self._normalize_project_dir(item)
                    if normalized and normalized not in cleaned:
                        cleaned.append(normalized)
                self.recent_projects = cleaned[:20]

            self.last_project_dir = self._normalize_project_dir(state.get("last_project"))
            self.last_open_file = self._normalize_file_path(state.get("last_open_file"))
        except Exception as e:
            print(f"⚠️ 小提示：读取项目记录失败：{e}")

    def _save_project_state(self):
        try:
            os.makedirs(self._state_dir, exist_ok=True)
            state = {
                "last_project": self.last_project_dir if self.last_project_dir else "",
                "last_open_file": self.last_open_file if self.last_open_file else "",
                "project_history": self.recent_projects[:20],
            }
            with open(self._state_file, "w", encoding="utf-8") as f:
                json.dump(state, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"⚠️ 小提示：保存项目记录失败：{e}")

    def _remember_project(self, dir_path, active_file=None):
        normalized = self._normalize_project_dir(dir_path)
        if not normalized:
            return
        self.last_project_dir = normalized
        if normalized in self.recent_projects:
            self.recent_projects.remove(normalized)
        self.recent_projects.insert(0, normalized)
        self.recent_projects = self.recent_projects[:20]

        if active_file:
            file_path = self._normalize_file_path(active_file)
            if file_path:
                self.last_open_file = file_path

        self._save_project_state()

    def _current_open_file(self):
        tab_id = self._get_current_tab_id()
        if not tab_id or tab_id not in self.tabs_data:
            return None
        filepath = self.tabs_data[tab_id].get("filepath")
        if not filepath or filepath == "未命名代码.ym":
            return None
        return self._normalize_file_path(filepath)

    def _pick_project_entry_file(self, project_dir, preferred_file=None):
        root = self._normalize_project_dir(project_dir)
        if not root:
            return None

        if preferred_file:
            preferred_abs = self._normalize_file_path(preferred_file)
            if preferred_abs:
                try:
                    same_tree = os.path.commonpath([root, preferred_abs]) == root
                except ValueError:
                    same_tree = False
                if same_tree and os.path.basename(preferred_abs) == "主程序.ym" and os.path.isfile(preferred_abs):
                    return preferred_abs

        candidate = os.path.join(root, "主程序.ym")
        return candidate if os.path.isfile(candidate) else None

    def _初始化标准项目结构(self, project_dir):
        项目根目录 = self._normalize_project_dir(project_dir)
        if not 项目根目录:
            return False
        try:
            os.makedirs(项目根目录, exist_ok=True)
            os.makedirs(os.path.join(项目根目录, "界面"), exist_ok=True)
            os.makedirs(os.path.join(项目根目录, "业务"), exist_ok=True)
            os.makedirs(os.path.join(项目根目录, "数据"), exist_ok=True)

            模板文件 = {
                os.path.join(项目根目录, "主程序.ym"):
                    '# 易码标准项目入口\n'
                    '引入 "界面/界面层.ym" 叫做 界面\n'
                    '界面.启动()\n',
                os.path.join(项目根目录, "界面", "界面层.ym"):
                    '# 界面层：只负责展示与交互\n'
                    '引入 "../业务/业务层.ym" 叫做 业务\n\n'
                    '功能 启动()\n'
                    '    显示 "界面层已启动"\n'
                    '    业务.运行()\n',
                os.path.join(项目根目录, "业务", "业务层.ym"):
                    '# 业务层：负责规则与流程\n'
                    '引入 "../数据/数据层.ym" 叫做 数据\n\n'
                    '功能 运行()\n'
                    '    显示 "业务层执行中"\n'
                    '    数据.初始化()\n',
                os.path.join(项目根目录, "数据", "数据层.ym"):
                    '# 数据层：负责存储与读取\n'
                    '功能 初始化()\n'
                    '    显示 "数据层已就绪"\n',
            }

            for 文件路径, 内容 in 模板文件.items():
                if not os.path.exists(文件路径):
                    with open(文件路径, "w", encoding="utf-8") as f:
                        f.write(内容)
            return True
        except Exception as e:
            messagebox.showerror("项目初始化失败", f"无法创建标准项目结构：{e}")
            return False

    def _switch_project(self, dir_path, preferred_file=None, create_blank_if_empty=True):
        project_dir = self._normalize_project_dir(dir_path)
        if not project_dir:
            return False

        self.workspace_dir = project_dir
        self.refresh_file_tree()
        self._close_all_tabs_silently()

        entry_file = self._pick_project_entry_file(project_dir, preferred_file)
        if entry_file:
            try:
                with open(entry_file, "r", encoding="utf-8") as f:
                    content = f.read()
                self._create_editor_tab(entry_file, content)
                self._remember_project(project_dir, entry_file)
            except Exception as e:
                self.print_output(f"❌ 打开项目入口文件失败：{e}")
                self._create_editor_tab("未命名代码.ym", "")
                self._remember_project(project_dir)
        else:
            if create_blank_if_empty:
                if self._初始化标准项目结构(project_dir):
                    标准入口 = os.path.join(project_dir, "主程序.ym")
                    try:
                        with open(标准入口, "r", encoding="utf-8") as f:
                            content = f.read()
                        self._create_editor_tab(标准入口, content)
                        self._remember_project(project_dir, 标准入口)
                        self.status_main_var.set("已按标准结构初始化项目：主程序 + 界面/业务/数据")
                    except Exception as e:
                        self.print_output(f"❌ 打开标准入口失败：{e}")
                        self._create_editor_tab("未命名代码.ym", "")
                        self._remember_project(project_dir)
                else:
                    self._create_editor_tab("未命名代码.ym", "")
                    self._remember_project(project_dir)
            else:
                self._create_editor_tab("未命名代码.ym", "")
                self._remember_project(project_dir)
        return True

    def _try_restore_last_project(self):
        if not self.last_project_dir or not os.path.isdir(self.last_project_dir):
            return False
        return self._switch_project(
            self.last_project_dir,
            preferred_file=self.last_open_file,
            create_blank_if_empty=False,
        )

    def open_recent_project_menu(self):
        menu = tk.Menu(self.root, tearoff=0, font=self.font_ui)

        valid_history = []
        for project in self.recent_projects:
            normalized = self._normalize_project_dir(project)
            if normalized and normalized not in valid_history:
                valid_history.append(normalized)
        self.recent_projects = valid_history[:20]

        if not self.recent_projects:
            menu.add_command(label="（暂无历史项目）", state=tk.DISABLED)
        else:
            for idx, project in enumerate(self.recent_projects[:12], start=1):
                name = os.path.basename(project) or project
                menu.add_command(
                    label=f"{idx}. {name}  -  {project}",
                    command=lambda p=project: self._open_project_from_history(p),
                )
            menu.add_separator()
            menu.add_command(label="🗑️ 清空历史项目记录", command=self.clear_recent_projects)

        x = self.root.winfo_pointerx()
        y = self.root.winfo_pointery()
        try:
            menu.tk_popup(x, y)
        finally:
            menu.grab_release()

    def _open_project_from_history(self, project_dir):
        normalized = self._normalize_project_dir(project_dir)
        if not normalized:
            messagebox.showwarning("项目不存在", "这个历史项目路径已经失效，已自动移除。")
            self.recent_projects = [p for p in self.recent_projects if self._normalize_project_dir(p)]
            self._save_project_state()
            return
        if not self._confirm_close_all_dirty_tabs():
            return
        self._switch_project(normalized, create_blank_if_empty=True)

    def clear_recent_projects(self):
        self.recent_projects = []
        current_project = self._normalize_project_dir(self.workspace_dir)
        if current_project:
            self.last_project_dir = current_project
        self._save_project_state()
        self.status_main_var.set("历史项目记录已清空")

    # ==========================
    # 多标签与文件树管理
    # ==========================
    def refresh_file_tree(self):
        # 清空现有节点
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        # 添加根节点
        root_node = self.tree.insert("", "end", text="🚀 易码项目目录", open=True)
        
        longest_text = "🚀 易码项目目录" # 假定初始最长
        
        # 遍历工作目录
        try:
            for item in os.listdir(self.workspace_dir):
                path = os.path.join(self.workspace_dir, item)
                if os.path.isdir(path) and item not in [".venv", "__pycache__", ".git", ".idea", ".vscode"]:
                    # 文件夹
                    folder_name = f"📁 {item}"
                    if len(folder_name) > len(longest_text): longest_text = folder_name
                    folder_node = self.tree.insert(root_node, "end", text=folder_name, values=(path, "dir"), open=True)
                    # 仅深入一层
                    for sub_item in os.listdir(path):
                        sub_path = os.path.join(path, sub_item)
                        if sub_path.endswith(".ym"):
                            file_name = f"📄 {sub_item}"
                            # 带了小图标的，其实宽度更大一些，我们可以多算一点字符兜底
                            if len(file_name) > len(longest_text): longest_text = file_name
                            
                            if self.icon_file:
                                self.tree.insert(folder_node, "end", text=f" {sub_item}", image=self.icon_file, values=(sub_path, "file"))
                            else:
                                self.tree.insert(folder_node, "end", text=file_name, values=(sub_path, "file"))
                elif item.endswith(".ym"):
                    # 根目录下的源文件
                    file_name = f"📄 {item}"
                    if len(file_name) > len(longest_text): longest_text = file_name
                    if self.icon_file:
                        self.tree.insert(root_node, "end", text=f" {item}", image=self.icon_file, values=(path, "file"))
                    else:
                        self.tree.insert(root_node, "end", text=file_name, values=(path, "file"))
                        
            # 根据最长文本自适应调整树形视图的实际宽度
            # 要留点缩进的空隙和图标空间
            try:
                measure_font = tkfont.Font(font=self.font_ui)
                # 留出缩进的像素以及图标大致宽度 (大约 40 像素)
                max_pixel_width = measure_font.measure(longest_text) + int(50 * self.dpi_scale)
                self.tree.column("#0", width=max_pixel_width, minwidth=max_pixel_width, stretch=False)
            except Exception as fe:
                print(f"⚠️ 小提示：字体测量计算失败：{fe}")
                
        except Exception as e:
            self.print_output(f"刷新文件树出错: {e}")

    def _create_editor_tab(self, filename, content=""):
        # 检查是否已经打开
        for tab_id, data in self.tabs_data.items():
            if data["filepath"] == filename:
                self.notebook.select(tab_id)
                self._update_cursor_status()
                self._run_live_diagnose()
                self._refresh_outline()
                return
                
        # 创建新的 Tab 容器 (零边距，完全融合)
        tab_frame = tk.Frame(self.notebook, bg=self.theme_bg, borderwidth=0, highlightthickness=0)
        
        行间距上 = 5
        行间距中 = 0
        行间距下 = 5

        # 行号与编辑器（行距必须与编辑器一致，否则会肉眼错位）
        line_numbers = tk.Text(
            tab_frame,
            width=4,
            padx=4,
            pady=10,
            takefocus=0,
            borderwidth=0,
            highlightthickness=0,
            bg=self.theme_gutter_bg,
            fg=self.theme_gutter_fg,
            font=self.font_code,
            spacing1=行间距上,
            spacing2=行间距中,
            spacing3=行间距下,
            state=tk.DISABLED
        )
        line_numbers.pack(side=tk.LEFT, fill=tk.Y)
        
        # 缩进引导线画布 (窄带垂直线指示器)
        guide_canvas = tk.Canvas(tab_frame, width=30, bg=self.theme_gutter_bg, highlightthickness=0, borderwidth=0)
        guide_canvas.pack(side=tk.LEFT, fill=tk.Y)
        
        editor = scrolledtext.ScrolledText(
            tab_frame,
            font=self.font_code,
            undo=True,
            wrap=tk.NONE,
            bg=self.theme_bg,
            fg=self.theme_fg,
            insertbackground="white",
            padx=10,
            pady=10,
            selectbackground="#264F78",
            spacing1=行间距上,
            spacing2=行间距中,
            spacing3=行间距下,
            borderwidth=0,
            highlightthickness=0
        )
        editor.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self._style_scrolledtext_vbar(editor, parent=tab_frame)

        # 保证拖动滚动条、滚轮滚动、键盘滚动时行号始终同步
        def 同步纵向滚动(first, last):
            try:
                line_numbers.yview_moveto(float(first))
            except tk.TclError:
                return
            self._update_indent_guides()
            if hasattr(editor, "vbar"):
                editor.vbar.set(first, last)

        editor.configure(yscrollcommand=同步纵向滚动)

        def 左侧滚轮转发到编辑器(event):
            if hasattr(event, "num") and event.num == 4:
                editor.yview_scroll(-1, "units")
                return "break"
            if hasattr(event, "num") and event.num == 5:
                editor.yview_scroll(1, "units")
                return "break"

            delta = getattr(event, "delta", 0)
            if delta != 0:
                # Windows 常见 delta=120 的倍数；其他平台兜底按方向滚动
                步长 = int(-delta / 120) if abs(delta) >= 120 else (-1 if delta > 0 else 1)
                editor.yview_scroll(步长, "units")
                return "break"
            return None

        def 左侧点击同步光标(event):
            try:
                目标索引 = editor.index(f"@0,{event.y}")
            except tk.TclError:
                return "break"
            try:
                editor.focus_set()
                editor.mark_set("insert", 目标索引)
                editor.tag_remove("sel", "1.0", "end")
                self._hide_autocomplete()
                self._hide_calltip()
                self._highlight_current_line()
                self._update_cursor_status()
            except tk.TclError:
                pass
            return "break"

        for 左侧控件 in (line_numbers, guide_canvas):
            左侧控件.bind("<MouseWheel>", 左侧滚轮转发到编辑器)
            左侧控件.bind("<Button-4>", 左侧滚轮转发到编辑器)
            左侧控件.bind("<Button-5>", 左侧滚轮转发到编辑器)
            左侧控件.bind("<Button-1>", 左侧点击同步光标)
            左侧控件.bind("<ButtonRelease-1>", 左侧点击同步光标, add="+")
        
        # 插入内容
        editor.insert("1.0", content)
        
        # 添加到 Notebook
        # 提取文件名作为标签标题，并在末尾加上关闭符号
        tab_title = os.path.basename(filename) if filename != "未命名代码.ym" else filename
        self.notebook.add(tab_frame, text=f" {tab_title}   ✖ ")
        self.notebook.select(tab_frame)
        
        # 记录内部数据
        tab_id = self.notebook.select()
        self.tabs_data[tab_id] = {
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
            "multi_cursor": {"query": "", "stage": "ranges", "ranges": [], "points": [], "last_abs": -1}
        }
        self._update_tab_title(tab_id)
        editor.edit_modified(False)
        
        # 绑定事件并执行初始高亮
        self.bind_events(editor)
        self.setup_tags(editor)
        self.highlight(editor)
        self._update_line_numbers(None)
        self._update_cursor_status()
        self._run_live_diagnose()
        self._refresh_outline()

        real_path = self._normalize_file_path(filename)
        if real_path:
            self.last_open_file = real_path
        
    def on_tree_double_click(self, event):
        item = self.tree.selection()
        if not item: return
        item = item[0]
        values = self.tree.item(item, "values")
        
        if values and values[1] == "file":
            filepath = values[0]
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                self._create_editor_tab(filepath, content)
            except Exception as e:
                messagebox.showerror("打开失败", f"无法读取文件：{e}")
                
    def popup_tree_menu(self, event):
        """在树状图上点击右键弹出菜单"""
        # 可以尝试选中右键点击的项
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
            
        self.tree_menu.tk_popup(event.x_root, event.y_root)

    def _get_selected_dir_or_root(self):
        """获取当前选择的文件夹路径，没选或者选了文件就返回它的上级"""
        item = self.tree.selection()
        if not item:
            return self.workspace_dir
            
        item = item[0]
        values = self.tree.item(item, "values")
        if not values:
            return self.workspace_dir
            
        path, node_type = values[0], values[1]
        if node_type == "dir":
            return path
        else:
            return os.path.dirname(path)

    def create_new_file_in_tree(self):
        target_dir = self._get_selected_dir_or_root()
        new_name = simpledialog.askstring("新建代码", "请输入新的易码文件名称（不需要打后缀）：", parent=self.root)
        if not new_name: return
        
        if not new_name.endswith(".ym"):
            new_name += ".ym"
            
        new_path = os.path.join(target_dir, new_name)
        if os.path.exists(new_path):
            messagebox.showerror("冲突", "这个名字已经存在啦，换一个吧！")
            return
            
        try:
            with open(new_path, 'w', encoding='utf-8') as f:
                f.write("") # 创建空文件
            self.refresh_file_tree()
            self._create_editor_tab(new_path, "")
        except Exception as e:
            messagebox.showerror("错误", f"创建文件失败: {e}")
            
    def create_new_folder_in_tree(self):
        target_dir = self._get_selected_dir_or_root()
        new_name = simpledialog.askstring("新建文件夹", "请输入新的文件夹名称：", parent=self.root)
        if not new_name: return
        
        new_path = os.path.join(target_dir, new_name)
        if os.path.exists(new_path):
            messagebox.showerror("冲突", "这个文件夹已经存在啦！")
            return
            
        try:
            os.makedirs(new_path)
            self.refresh_file_tree()
        except Exception as e:
            messagebox.showerror("错误", f"创建文件夹失败: {e}")
            
    def delete_item_in_tree(self):
        item = self.tree.selection()
        if not item: return
        item = item[0]
        values = self.tree.item(item, "values")
        if not values: return
        
        path, node_type = values[0], values[1]
        name = os.path.basename(path)
        
        if not messagebox.askyesno("确认删除", f"你确定要永远删除【{name}】吗？\n删除后不可恢复！"):
            return
            
        try:
            if node_type == "dir":
                shutil.rmtree(path)
            else:
                os.remove(path)
                
            self.refresh_file_tree()
            
            # 检查是否有打开的标签卡是在删除的目录/文件里面，有的话关掉它
            tabs_to_close = []
            for tab_id, data in self.tabs_data.items():
                tab_file = data["filepath"]
                if tab_file == path or tab_file.startswith(path + os.sep):
                    tabs_to_close.append(tab_id)
            
            for tab_id in tabs_to_close:
                # 获取它在 tabs 中的 index 然后触发 close_tab
                tabs_list = self.notebook.tabs()
                if tab_id in tabs_list:
                    idx = tabs_list.index(tab_id)
                    self.close_tab(idx)
                    
        except Exception as e:
            messagebox.showerror("错误", f"删除失败: {e}")
                
    def on_tab_click(self, event):
        """处理标签页点击，实现点击 X 关闭标签"""
        try:
            index = self.notebook.index(f"@{event.x},{event.y}")
        except tk.TclError:
            return
            
        # 获取被点击标签的边界框
        x, y, width, height = self.notebook.bbox(index)
        
        # 判断点击位置是否在标签的最右侧（X 的位置）
        # 预留大概 25 * dpi_scale 像素作为关闭按钮区域
        close_area_width = int(25 * self.dpi_scale)
        if event.x > (x + width - close_area_width):
            self.close_tab(index)

    def close_tab(self, index):
        """关闭指定索引的标签页"""
        tabs = self.notebook.tabs()
        if index < 0 or index >= len(tabs):
            return
        tab_id = tabs[index]
        if not self._confirm_tab_close(tab_id):
            return

        self.notebook.forget(tab_id)
        
        # 销毁组件释放内存
        if tab_id in self.tabs_data:
            self.tabs_data[tab_id]["editor"].destroy()
            self.tabs_data[tab_id]["line_numbers"].destroy()
            if self.tabs_data[tab_id].get("guide_canvas"):
                self.tabs_data[tab_id]["guide_canvas"].destroy()
            del self.tabs_data[tab_id]
            
        # 如果所有标签都关完了，新建一个空白的
        if not self.notebook.tabs():
            self._create_editor_tab("未命名代码.ym", "")

    def _confirm_tab_close(self, tab_id):
        if tab_id not in self.tabs_data:
            return True
        data = self.tabs_data[tab_id]
        if not data.get("dirty"):
            return True

        filepath = data.get("filepath", "未命名代码.ym")
        display_name = os.path.basename(filepath) if filepath != "未命名代码.ym" else "未命名代码.ym"
        choice = messagebox.askyesnocancel("未保存修改", f"【{display_name}】有未保存内容，是否先保存？")
        if choice is None:
            return False
        if choice:
            current_tab = self._get_current_tab_id()
            try:
                self.notebook.select(tab_id)
            except tk.TclError:
                return False

            ok = self.save_file(show_message=False)
            if current_tab and current_tab in self.notebook.tabs():
                self.notebook.select(current_tab)
            return ok
        return True

    def on_app_close(self):
        # 逐个检查，确保不会误丢未保存内容
        for tab_id in list(self.notebook.tabs()):
            if not self._confirm_tab_close(tab_id):
                return
        current_file = self._current_open_file()
        self._remember_project(self.workspace_dir, current_file)
        self.root.destroy()
            
    def on_tab_changed(self, event):
        editor = self._get_current_editor()
        if editor:
            self.highlight()
            self._update_line_numbers()
            self._update_cursor_status()
            self._run_live_diagnose()
            self._highlight_find_matches()
            self._refresh_outline()
            self._render_multi_cursor_state()
            current_file = self._current_open_file()
            if current_file:
                self.last_open_file = current_file

    # ==========================
    # 顶部工具栏行为
    # ==========================
    def run_code(self):
        editor = self._get_current_editor()
        if not editor: return
        
        # 切换运行目录到当前文件所在位置
        tab_id = self._get_current_tab_id()
        filepath = self.tabs_data[tab_id]["filepath"]
        脚本路径 = filepath if filepath and os.path.isfile(filepath) else None
        original_cwd = os.getcwd()
        if 脚本路径:
            os.chdir(os.path.dirname(os.path.abspath(脚本路径)))
            
        # 清空上一次输出，并重新显示控制台用途说明
        self._clear_output_console(keep_intro=True)
        
        code = editor.get("1.0", "end-1c")
        if not code.strip():
            self.print_output("提示：当前标签页为空，无法运行。")
            self.status_main_var.set("运行取消：当前标签页为空")
            # 恢复工作目录
            if 脚本路径:
                os.chdir(original_cwd)
            return

        # 运行前先做一次语法诊断并刷新状态栏
        self._run_live_diagnose()
            
        # 劫持系统标准输出到内存里
        old_stdout = sys.stdout
        sys.stdout = io.StringIO()
        
        # 劫持系统输入，改为弹窗，以支持 `输入` 语句
        old_input = builtins.input
        class 用户取消输入(Exception):
            pass

        def 弹窗输入(提示语=""):
            对话框 = tk.Toplevel(self.root)
            对话框.title("易码需要你的回答")
            对话框.configure(bg=self.theme_sidebar_bg)
            对话框.resizable(False, False)
            对话框.transient(self.root)

            win_w = int(420 * self.dpi_scale)
            win_h = int(210 * self.dpi_scale)
            x = self.root.winfo_x() + (self.root.winfo_width() // 2) - (win_w // 2)
            y = self.root.winfo_y() + (self.root.winfo_height() // 2) - (win_h // 2)
            对话框.geometry(f"{win_w}x{win_h}+{x}+{y}")

            结果 = {"值": None}

            def 确认(*_):
                结果["值"] = 输入框.get()
                对话框.destroy()

            def 取消(*_):
                结果["值"] = None
                对话框.destroy()

            对话框.protocol("WM_DELETE_WINDOW", 取消)

            容器 = tk.Frame(对话框, bg=self.theme_sidebar_bg)
            容器.pack(fill=tk.BOTH, expand=True, padx=16, pady=14)

            提示文本 = str(提示语 or "").strip() or "请输入："
            tk.Label(
                容器,
                text=提示文本,
                font=("Microsoft YaHei", 12, "bold"),
                bg=self.theme_sidebar_bg,
                fg=self.theme_fg,
                anchor="w",
                justify="left",
            ).pack(fill=tk.X, pady=(0, 8))

            输入框 = tk.Entry(
                容器,
                font=("Microsoft YaHei", 12),
                bg=self.theme_bg,
                fg=self.theme_fg,
                insertbackground="#CCCCCC",
                relief="flat",
                highlightthickness=1,
                highlightbackground=self.theme_sash,
                highlightcolor="#0E639C",
            )
            输入框.pack(fill=tk.X, ipady=5, pady=(0, 12))

            按钮栏 = tk.Frame(容器, bg=self.theme_sidebar_bg)
            按钮栏.pack(fill=tk.X)

            tk.Button(
                按钮栏,
                text="OK",
                font=self.font_ui,
                command=确认,
                bg=self.theme_toolbar_bg,
                fg=self.theme_fg,
                activebackground="#505050",
                activeforeground="#FFFFFF",
                relief="flat",
                borderwidth=0,
                cursor="hand2",
                padx=14,
                pady=5,
            ).pack(side=tk.RIGHT, padx=(8, 0))

            tk.Button(
                按钮栏,
                text="Cancel",
                font=self.font_ui,
                command=取消,
                bg=self.theme_toolbar_bg,
                fg=self.theme_fg,
                activebackground="#505050",
                activeforeground="#FFFFFF",
                relief="flat",
                borderwidth=0,
                cursor="hand2",
                padx=14,
                pady=5,
            ).pack(side=tk.RIGHT)

            对话框.bind("<Return>", 确认)
            对话框.bind("<Escape>", 取消)

            输入框.focus_set()
            对话框.grab_set()
            try:
                self.root.wait_window(对话框)
            except tk.TclError:
                return None
            return 结果["值"]

        def gui_input(prompt=""):
            ans = 弹窗输入(prompt)
            if ans is None:
                raise 用户取消输入()
            return ans
        builtins.input = gui_input
        
        output_str = ""
        try:
            执行源码(code, interactive=False, 源码路径=脚本路径)
            output_str = sys.stdout.getvalue()
            if not output_str.strip():
                output_str = "代码已执行完成，但没有输出。可使用【显示】语句输出结果。"
        except 用户取消输入:
            output_str = "⏹ 你已取消输入，本次运行已停止。"
        except Exception as e:
            output_str = f"❌ 运行报错了: {e}"
        finally:
            sys.stdout = old_stdout
            builtins.input = old_input
            if 脚本路径:
                os.chdir(original_cwd)
        
        self.print_output(output_str, is_error=output_str.startswith("❌"))
        if output_str.startswith("⏹"):
            self.status_main_var.set("运行已取消")
        else:
            self.status_main_var.set("运行完成")

    def open_file(self):
        filepath = filedialog.askopenfilename(filetypes=[("易码源代码", "*.ym"), ("所有文件", "*.*")])
        if filepath:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            self._create_editor_tab(filepath, content)
            self.refresh_file_tree()
            
    def save_file(self, event=None, show_message=True):
        editor = self._get_current_editor()
        tab_id = self._get_current_tab_id()
        if not editor or not tab_id:
            return False
        
        current_filepath = self.tabs_data[tab_id]["filepath"]
        
        # 如果是未命名或者不存在，则要求另存为
        if current_filepath == "未命名代码.ym" or not os.path.exists(current_filepath):
            filepath = filedialog.asksaveasfilename(defaultextension=".ym", filetypes=[("易码源代码", "*.ym")])
            if not filepath:
                return False
            self.tabs_data[tab_id]["filepath"] = filepath
            self._update_tab_title(tab_id)
        else:
            filepath = current_filepath
            
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(editor.get("1.0", "end-1c"))
            self.tabs_data[tab_id]["dirty"] = False
            self._update_tab_title(tab_id)
            editor.edit_modified(False)
            self._update_status_main()
            if show_message:
                messagebox.showinfo("保存成功", f"代码已经稳稳地保存在：\n{filepath}")
            self.refresh_file_tree()
            return True
        except Exception as e:
            if show_message:
                messagebox.showerror("保存失败", f"无法保存文件：{e}")
            else:
                self.status_main_var.set(f"保存失败：{e}")
            return False
            
    def clear_code(self):
        base_name = "未命名代码"
        ext = ".ym"
        idx = ""
        counter = 1
        
        # 寻找一个没有被占用的名字（同时检查磁盘和已打开的标签页）
        while True:
            candidate_name = f"{base_name}{idx}{ext}"
            candidate_path = os.path.join(self.workspace_dir, candidate_name)
            
            # 检查文件是否已在磁盘上存在或者已被打开
            already_exists = os.path.exists(candidate_path)
            already_open = False
            for data in self.tabs_data.values():
                if data["filepath"] == candidate_path or data["filepath"] == candidate_name:
                    already_open = True
                    break
            
            if not already_exists and not already_open:
                # 在磁盘上创建空文件
                try:
                    with open(candidate_path, 'w', encoding='utf-8') as f:
                        f.write("")
                except Exception as e:
                    self.print_output(f"❌ 创建文件失败：{e}")
                    return
                # 打开这个真实文件的标签页
                self._create_editor_tab(candidate_path, "")
                # 刷新左侧文件树
                self.refresh_file_tree()
                break
            idx = f"-{counter}"
            counter += 1

    def _close_all_tabs_silently(self):
        # 默默关掉所有的 tab
        tabs = list(self.notebook.tabs())
        for t in tabs:
            tab_id = t
            self.notebook.forget(tab_id)
            if tab_id in self.tabs_data:
                self.tabs_data[tab_id]["editor"].destroy()
                self.tabs_data[tab_id]["line_numbers"].destroy()
                if self.tabs_data[tab_id].get("guide_canvas"):
                    self.tabs_data[tab_id]["guide_canvas"].destroy()
                del self.tabs_data[tab_id]

    def _confirm_close_all_dirty_tabs(self):
        for tab_id in list(self.notebook.tabs()):
            if not self._confirm_tab_close(tab_id):
                return False
        return True

    def open_project(self):
        initial_dir = self.last_project_dir if self.last_project_dir and os.path.isdir(self.last_project_dir) else self.workspace_dir
        dir_path = filedialog.askdirectory(title="选择易码项目文件夹", initialdir=initial_dir)
        if dir_path:
            if not self._confirm_close_all_dirty_tabs():
                return
            主程序路径 = os.path.join(dir_path, "主程序.ym")
            if not os.path.isfile(主程序路径):
                if not messagebox.askyesno(
                    "缺少主程序.ym",
                    "该目录不符合易码标准项目结构（缺少 主程序.ym）。\n是否立即按标准结构初始化？",
                ):
                    return
            self._switch_project(dir_path, create_blank_if_empty=True)

    def new_project(self):
        initial_dir = self.last_project_dir if self.last_project_dir and os.path.isdir(self.last_project_dir) else self.workspace_dir
        dir_path = filedialog.askdirectory(title="选择一个空文件夹作为新项目", initialdir=initial_dir)
        if dir_path:
            if not self._confirm_close_all_dirty_tabs():
                return
            if os.listdir(dir_path):
                if not messagebox.askyesno(
                    "确认初始化",
                    "这个目录不是空的。\n是否继续初始化标准结构（仅创建缺失文件，不覆盖现有文件）？",
                ):
                    return
            if not self._初始化标准项目结构(dir_path):
                return
            self._switch_project(dir_path, preferred_file=os.path.join(dir_path, "主程序.ym"), create_blank_if_empty=True)

    def export_exe(self):
        editor = self._get_current_editor()
        tab_id = self._get_current_tab_id()
        if not editor or not tab_id or tab_id not in self.tabs_data:
            return

        源码内容 = editor.get("1.0", "end-1c")
        if not 源码内容.strip():
            messagebox.showwarning("无法打包", "代码是空的，先写点啥吧！")
            return

        当前文件路径 = self.tabs_data[tab_id]["filepath"]
        if self.tabs_data[tab_id].get("dirty"):
            if not self.save_file(show_message=False):
                messagebox.showwarning("打包取消", "请先保存当前文件后再打包。")
                return
            当前文件路径 = self.tabs_data[tab_id]["filepath"]

        项目入口 = os.path.join(self.workspace_dir, "主程序.ym")
        如果入口存在 = os.path.isfile(项目入口)

        if 如果入口存在:
            源码入口 = 项目入口
            软件名称原始 = os.path.basename(os.path.abspath(self.workspace_dir)) or "易码生成软件"
        elif 当前文件路径 and 当前文件路径 != "未命名代码.ym" and os.path.isfile(当前文件路径):
            源码入口 = os.path.abspath(当前文件路径)
            软件名称原始 = os.path.splitext(os.path.basename(源码入口))[0]
        else:
            源码入口 = None
            软件名称原始 = "易码生成软件"

        def 清理软件名(名称):
            结果 = str(名称 or "").strip()
            if not 结果:
                结果 = "易码生成软件"
            for 坏字符 in '<>:"/\\|?*':
                结果 = 结果.replace(坏字符, "_")
            结果 = 结果.strip(" .")
            return 结果 if 结果 else "易码生成软件"

        默认图标 = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logo.ico")
        默认软件名 = 清理软件名(软件名称原始)
        默认输出目录 = os.path.join(self.workspace_dir, "易码_成品软件")
        默认输出路径 = os.path.join(默认输出目录, f"{默认软件名}.exe")
        默认图标路径 = 默认图标 if os.path.isfile(默认图标) else ""

        def 选择导出模式():
            模式窗口 = tk.Toplevel(self.root)
            模式窗口.title("导出模式")
            模式窗口.configure(bg=self.theme_toolbar_bg)
            模式窗口.resizable(False, False)
            模式窗口.transient(self.root)
            模式窗口.grab_set()
            标题字体 = getattr(self, "font_ui_bold", self.font_ui)

            结果容器 = {"值": None}

            def 设定模式(值):
                结果容器["值"] = 值
                模式窗口.destroy()

            主框 = tk.Frame(模式窗口, bg=self.theme_toolbar_bg, padx=16, pady=14)
            主框.pack(fill=tk.BOTH, expand=True)

            tk.Label(
                主框,
                text="请选择导出方式：",
                bg=self.theme_toolbar_bg,
                fg=self.theme_toolbar_fg,
                font=标题字体,
                anchor="w",
            ).pack(anchor="w")
            tk.Label(
                主框,
                text="快速版：一键打包（推荐）\n高级版：自定义名称/路径/图标/运行模式",
                bg=self.theme_toolbar_bg,
                fg=self.theme_toolbar_fg,
                font=self.font_ui,
                justify="left",
                anchor="w",
                pady=8,
            ).pack(anchor="w", fill=tk.X)

            按钮框 = tk.Frame(主框, bg=self.theme_toolbar_bg)
            按钮框.pack(fill=tk.X, pady=(8, 0))

            tk.Button(
                按钮框,
                text="快速版",
                command=lambda: 设定模式("quick"),
                font=self.font_ui,
                width=10,
                bg="#1E7BC8",
                fg="#FFFFFF",
            ).pack(side=tk.LEFT)
            tk.Button(
                按钮框,
                text="高级版",
                command=lambda: 设定模式("advanced"),
                font=self.font_ui,
                width=10,
            ).pack(side=tk.LEFT, padx=(8, 0))
            tk.Button(
                按钮框,
                text="取消",
                command=lambda: 设定模式(None),
                font=self.font_ui,
                width=10,
            ).pack(side=tk.RIGHT)

            模式窗口.bind("<Escape>", lambda e: 设定模式(None))
            模式窗口.bind("<Return>", lambda e: 设定模式("quick"))

            self.root.update_idletasks()
            模式窗口.update_idletasks()
            宽 = max(560, 主框.winfo_reqwidth() + 24)
            高 = max(220, 主框.winfo_reqheight() + 24)
            x = self.root.winfo_rootx() + max(20, (self.root.winfo_width() - 宽) // 2)
            y = self.root.winfo_rooty() + max(20, (self.root.winfo_height() - 高) // 2)
            模式窗口.geometry(f"{宽}x{高}+{x}+{y}")
            self.root.wait_window(模式窗口)
            return 结果容器["值"]

        导出模式 = 选择导出模式()
        if 导出模式 is None:
            return

        打包配置 = None

        if 导出模式 == "quick":
            打包配置 = {
                "软件名称": 默认软件名,
                "输出路径": 默认输出路径,
                "图标路径": 默认图标路径 or None,
                "隐藏黑框": True,
                "模式文本": "纯净窗口版（不显示黑框）",
                "模式标题": "一键打包",
            }
        elif 导出模式 == "advanced":
            高级窗口 = tk.Toplevel(self.root)
            高级窗口.title("导出软件（高级设置）")
            高级窗口.configure(bg=self.theme_toolbar_bg)
            高级窗口.resizable(False, False)
            高级窗口.transient(self.root)
            高级窗口.grab_set()

            名称变量 = tk.StringVar(value=默认软件名)
            路径变量 = tk.StringVar(value=默认输出路径)
            图标变量 = tk.StringVar(value=默认图标路径)
            模式变量 = tk.StringVar(value="windowed")
            结果容器 = {"值": None}

            主框 = tk.Frame(高级窗口, bg=self.theme_toolbar_bg, padx=14, pady=12)
            主框.pack(fill=tk.BOTH, expand=True)

            标签样式 = {"bg": self.theme_toolbar_bg, "fg": self.theme_toolbar_fg, "font": self.font_ui}
            输入样式 = {"font": self.font_ui, "bg": self.theme_bg, "fg": self.theme_fg, "insertbackground": self.theme_fg}

            tk.Label(主框, text="软件名称：", **标签样式).grid(row=0, column=0, sticky="w", pady=(0, 6))
            名称输入 = tk.Entry(主框, textvariable=名称变量, width=48, **输入样式)
            名称输入.grid(row=0, column=1, columnspan=2, sticky="we", padx=(8, 0), pady=(0, 6))

            tk.Label(主框, text="输出路径：", **标签样式).grid(row=1, column=0, sticky="w", pady=6)
            路径输入 = tk.Entry(主框, textvariable=路径变量, width=48, **输入样式)
            路径输入.grid(row=1, column=1, sticky="we", padx=(8, 8), pady=6)

            tk.Label(主框, text="图标文件：", **标签样式).grid(row=2, column=0, sticky="w", pady=6)
            图标输入 = tk.Entry(主框, textvariable=图标变量, width=48, **输入样式)
            图标输入.grid(row=2, column=1, sticky="we", padx=(8, 8), pady=6)

            tk.Label(主框, text="运行模式：", **标签样式).grid(row=3, column=0, sticky="nw", pady=(8, 2))
            模式框 = tk.Frame(主框, bg=self.theme_toolbar_bg)
            模式框.grid(row=3, column=1, columnspan=2, sticky="w", padx=(8, 0), pady=(8, 2))

            tk.Radiobutton(
                模式框,
                text="代码黑框版（调试）",
                variable=模式变量,
                value="console",
                bg=self.theme_toolbar_bg,
                fg=self.theme_toolbar_fg,
                selectcolor=self.theme_panel_bg,
                activebackground=self.theme_toolbar_bg,
                activeforeground=self.theme_toolbar_fg,
                font=self.font_ui,
            ).pack(anchor="w")
            tk.Radiobutton(
                模式框,
                text="纯净窗口版（发布）",
                variable=模式变量,
                value="windowed",
                bg=self.theme_toolbar_bg,
                fg=self.theme_toolbar_fg,
                selectcolor=self.theme_panel_bg,
                activebackground=self.theme_toolbar_bg,
                activeforeground=self.theme_toolbar_fg,
                font=self.font_ui,
            ).pack(anchor="w")

            提示文字 = tk.Label(
                主框,
                text="说明：可直接手动改路径；图标留空会使用默认 logo.ico（如存在）。",
                bg=self.theme_toolbar_bg,
                fg=self.theme_toolbar_muted,
                font=self.font_ui,
                anchor="w",
            )
            提示文字.grid(row=4, column=0, columnspan=3, sticky="we", pady=(8, 10))

            按钮框 = tk.Frame(主框, bg=self.theme_toolbar_bg)
            按钮框.grid(row=5, column=0, columnspan=3, sticky="e")

            def 选择输出路径():
                当前路径值 = 路径变量.get().strip()
                初始目录 = self.workspace_dir
                初始文件 = f"{清理软件名(名称变量.get())}.exe"
                if 当前路径值:
                    当前路径值 = os.path.abspath(os.path.expanduser(当前路径值))
                    if os.path.isdir(os.path.dirname(当前路径值)):
                        初始目录 = os.path.dirname(当前路径值)
                    基础名 = os.path.basename(当前路径值)
                    if 基础名:
                        初始文件 = 基础名
                选择结果 = filedialog.asksaveasfilename(
                    title="选择导出 EXE 路径",
                    parent=高级窗口,
                    initialdir=初始目录,
                    initialfile=初始文件,
                    defaultextension=".exe",
                    filetypes=[("Windows 可执行文件", "*.exe"), ("所有文件", "*.*")],
                )
                if 选择结果:
                    路径变量.set(选择结果)

            def 选择图标():
                当前图标值 = 图标变量.get().strip()
                初始目录 = self.workspace_dir
                if 当前图标值 and os.path.isdir(os.path.dirname(os.path.abspath(os.path.expanduser(当前图标值)))):
                    初始目录 = os.path.dirname(os.path.abspath(os.path.expanduser(当前图标值)))
                选择结果 = filedialog.askopenfilename(
                    title="选择图标文件（.ico）",
                    parent=高级窗口,
                    initialdir=初始目录,
                    filetypes=[("图标文件", "*.ico"), ("所有文件", "*.*")],
                )
                if 选择结果:
                    图标变量.set(选择结果)

            def 取消高级():
                高级窗口.destroy()

            def 确认高级():
                软件名 = 清理软件名(名称变量.get())
                输出路径 = str(路径变量.get() or "").strip()
                if not 输出路径:
                    输出路径 = os.path.join(默认输出目录, f"{软件名}.exe")
                else:
                    try:
                        当前绝对 = os.path.normcase(os.path.abspath(os.path.expanduser(输出路径)))
                        默认绝对 = os.path.normcase(os.path.abspath(默认输出路径))
                        if 当前绝对 == 默认绝对:
                            输出路径 = os.path.join(默认输出目录, f"{软件名}.exe")
                    except Exception:
                        pass
                输出路径 = os.path.abspath(os.path.expanduser(输出路径))
                if not 输出路径.lower().endswith(".exe"):
                    输出路径 += ".exe"

                图标值 = str(图标变量.get() or "").strip()
                图标值 = os.path.abspath(os.path.expanduser(图标值)) if 图标值 else None
                if 图标值 and not os.path.isfile(图标值):
                    messagebox.showwarning("图标无效", "图标文件不存在，请重新选择。", parent=高级窗口)
                    return

                隐藏黑框 = 模式变量.get() == "windowed"
                模式文本 = "纯净窗口版（不显示黑框）" if 隐藏黑框 else "代码黑框版（带日志窗口）"
                结果容器["值"] = {
                    "软件名称": 软件名,
                    "输出路径": 输出路径,
                    "图标路径": 图标值,
                    "隐藏黑框": 隐藏黑框,
                    "模式文本": 模式文本,
                    "模式标题": "高级导出",
                }
                高级窗口.destroy()

            浏览输出按钮 = tk.Button(主框, text="浏览...", command=选择输出路径, font=self.font_ui, width=10)
            浏览输出按钮.grid(row=1, column=2, sticky="e", pady=6)
            浏览图标按钮 = tk.Button(主框, text="浏览...", command=选择图标, font=self.font_ui, width=10)
            浏览图标按钮.grid(row=2, column=2, sticky="e", pady=6)

            tk.Button(按钮框, text="取消", command=取消高级, font=self.font_ui, width=10).pack(side=tk.RIGHT, padx=(8, 0))
            tk.Button(按钮框, text="开始打包", command=确认高级, font=self.font_ui, width=12, bg="#1E7BC8", fg="#FFFFFF").pack(side=tk.RIGHT)

            主框.grid_columnconfigure(1, weight=1)
            名称输入.focus_set()
            高级窗口.bind("<Return>", lambda e: 确认高级())
            高级窗口.bind("<Escape>", lambda e: 取消高级())

            self.root.update_idletasks()
            高级窗口.update_idletasks()
            宽 = max(860, 主框.winfo_reqwidth() + 28)
            高 = max(420, 主框.winfo_reqheight() + 28)
            x = self.root.winfo_rootx() + max(20, (self.root.winfo_width() - 宽) // 2)
            y = self.root.winfo_rooty() + max(20, (self.root.winfo_height() - 高) // 2)
            高级窗口.geometry(f"{宽}x{高}+{x}+{y}")
            self.root.wait_window(高级窗口)
            打包配置 = 结果容器["值"]

        if not 打包配置:
            return

        输出路径 = os.path.abspath(os.path.expanduser(打包配置["输出路径"]))
        if os.path.exists(输出路径):
            if not messagebox.askyesno("确认覆盖", f"目标文件已存在：\n{输出路径}\n\n是否覆盖？", parent=self.root):
                return

        提示文本 = (
            f"模式：{打包配置['模式标题']}\n"
            + f"入口：{os.path.basename(源码入口) if 源码入口 else '当前编辑内容'}\n"
            + f"软件名：{打包配置['软件名称']}\n"
            + f"输出路径：{输出路径}\n"
            + f"图标：{打包配置['图标路径'] if 打包配置['图标路径'] else '默认 logo.ico（如存在）'}\n"
            + f"运行模式：{打包配置['模式文本']}\n\n"
            + "确认开始打包吗？"
        )
        if not messagebox.askyesno("确认导出", 提示文本, parent=self.root):
            return

        self._clear_output_console(keep_intro=True)
        self.print_output(
            "=============================\n"
            + f"开始打包 EXE（{打包配置['模式标题']}）\n"
            + "============================="
        )

        import threading
        import tempfile

        def 打印进度(文字):
            self.root.after(0, lambda: self.print_output(文字))

        def 后台打包():
            原始目录 = os.getcwd()
            临时入口 = None
            try:
                if not 源码入口:
                    临时目录 = tempfile.gettempdir()
                    临时入口 = os.path.join(临时目录, "_易码源码编译缓冲.ym")
                    with open(临时入口, "w", encoding="utf-8") as f:
                        f.write(源码内容)
                    打包入口 = 临时入口
                else:
                    打包入口 = 源码入口

                os.chdir(self.workspace_dir)
                from 易码打包工具 import 编译并打包

                最终路径 = 编译并打包(
                    打包入口,
                    图标路径=打包配置["图标路径"],
                    隐藏黑框=打包配置["隐藏黑框"],
                    进度打印=打印进度,
                    软件名称=打包配置["软件名称"],
                    源码目录=self.workspace_dir,
                )
                最终绝对路径 = os.path.abspath(最终路径)
                目标绝对路径 = os.path.abspath(输出路径)

                if os.path.normcase(最终绝对路径) != os.path.normcase(目标绝对路径):
                    os.makedirs(os.path.dirname(目标绝对路径), exist_ok=True)
                    if os.path.exists(目标绝对路径):
                        os.remove(目标绝对路径)
                    shutil.move(最终绝对路径, 目标绝对路径)
                    最终绝对路径 = 目标绝对路径

                self.root.after(0, lambda p=最终绝对路径: self.print_output(f"打包成功：{p}"))
                self.root.after(0, lambda p=最终绝对路径: messagebox.showinfo("打包完成", f"可执行文件已生成：\n{p}"))
            except Exception as e:
                self.root.after(0, lambda msg=str(e): messagebox.showerror("打包失败", msg))
            finally:
                try:
                    os.chdir(原始目录)
                except Exception:
                    pass
                if 临时入口 and os.path.isfile(临时入口):
                    try:
                        os.remove(临时入口)
                    except Exception:
                        pass

        t = threading.Thread(target=后台打包, daemon=True)
        t.start()
if __name__ == "__main__":
    # 必须在初始化 Tk 之前宣告 DPI 感知，否则即使点数(pt)字体缩放了，Tkinter本身也会按照低分屏映射引发排版错乱
    try:
        from ctypes import windll
        windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass

    root = tk.Tk()

    app = 易码IDE(root)
    # 不再需要外部强行插入欢迎代码，逻辑已在 init 默认建 tab
    
    # 窗口居中
    root.update_idletasks()
    w = root.winfo_screenwidth()
    h = root.winfo_screenheight()
    size = tuple(int(_) for _ in root.geometry().split('+')[0].split('x'))
    x = w/2 - size[0]/2
    y = h/2 - size[1]/2
    root.geometry("%dx%d+%d+%d" % (size[0], size[1], x, y))
    
    try:
        root.mainloop()
    except KeyboardInterrupt:
        # 允许在终端用 Ctrl+C 结束，不打印 traceback。
        try:
            root.destroy()
        except Exception:
            pass


