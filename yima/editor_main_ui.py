"""Main UI setup helper extracted from ?????.py."""

from __future__ import annotations

#
# Ownership Marker (Open Source Prep)
# Author: ?? (Jing Lei)
# Copyright (c) 2026 ??
# Project: ?? / Yima
# Marker-ID: YIMA-JINGLEI-CORE

__author__ = "??"
__copyright__ = "Copyright (c) 2026 ??"
__marker_id__ = "YIMA-JINGLEI-CORE"

import sys
import tkinter as tk
from tkinter import scrolledtext, ttk


def _build_feedback_dot_image(size=11, fill_color="#FF4D4F", border_color="#C83335"):
    size = max(8, int(size))
    img = tk.PhotoImage(width=size, height=size)
    cx = (size - 1) / 2.0
    cy = (size - 1) / 2.0
    outer_radius = max(3.0, (size / 2.0) - 0.8)
    inner_radius = max(2.0, outer_radius - 1.2)
    outer_r2 = outer_radius * outer_radius
    inner_r2 = inner_radius * inner_radius
    for y in range(size):
        for x in range(size):
            dx = x - cx
            dy = y - cy
            dist2 = dx * dx + dy * dy
            if dist2 <= inner_r2:
                img.put(fill_color, (x, y))
            elif dist2 <= outer_r2:
                img.put(border_color, (x, y))
    return img


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

    def create_tool_btn(parent, text, cmd, variant="ghost", font=None, compact=False, width=None, icon_image=None):
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
        btn_kwargs = {
            "master": parent,
            "text": text,
            "command": cmd,
            "font": font or self.font_ui,
            "bg": conf["bg"],
            "fg": conf["fg"],
            "activebackground": conf["hover_bg"],
            "activeforeground": conf["hover_fg"],
            "relief": "flat",
            "borderwidth": 0,
            "highlightthickness": 1,
            "highlightbackground": conf["border"],
            "highlightcolor": conf["border"],
            "cursor": "hand2",
            "padx": pad_x,
            "pady": pad_y,
            "takefocus": 0,
        }
        if width is not None:
            btn_kwargs["width"] = int(width)
        if icon_image is not None:
            btn_kwargs["image"] = icon_image
            btn_kwargs["compound"] = tk.LEFT
        btn = tk.Button(**btn_kwargs)
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
    图标尺寸 = max(14, int(16 * self.dpi_scale))
    self._toolbar_run_icon = self._build_toolbar_icon("run", size=图标尺寸, color="#FFFFFF")
    self._toolbar_export_icon = self._build_toolbar_icon("export", size=图标尺寸, color="#FFFFFF")

    # 固定槽位确保右上角两个按钮视觉同宽同高
    顶栏按钮宽 = max(116, int(124 * self.dpi_scale))
    顶栏按钮高 = max(30, int(32 * self.dpi_scale))

    运行槽 = tk.Frame(right_actions, bg=self.theme_toolbar_bg, width=顶栏按钮宽, height=顶栏按钮高)
    运行槽.pack(side=tk.RIGHT, padx=(0, 0))
    运行槽.pack_propagate(False)

    导出槽 = tk.Frame(right_actions, bg=self.theme_toolbar_bg, width=顶栏按钮宽, height=顶栏按钮高)
    导出槽.pack(side=tk.RIGHT, padx=(0, 6))
    导出槽.pack_propagate(False)

    create_tool_btn(
        导出槽,
        "导出软件(exe)",
        self.export_exe,
        variant="accent",
        font=("Microsoft YaHei", 9, "bold"),
        compact=True,
        icon_image=self._toolbar_export_icon,
    ).pack(fill=tk.BOTH, expand=True)

    create_tool_btn(
        运行槽,
        "运行代码",
        self.run_code,
        variant="run",
        font=("Microsoft YaHei", 9, "bold"),
        compact=True,
        icon_image=self._toolbar_run_icon,
    ).pack(fill=tk.BOTH, expand=True)

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
    create_tool_group("文档", [
        ("速查表", self.open_cheatsheet),
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
    title_line = tk.Frame(title_wrap, bg=self.theme_sidebar_bg)
    title_line.pack(fill=tk.X)
    tk.Label(
        title_line,
        text="资源管理器",
        font=("Microsoft YaHei", 10, "bold"),
        bg=self.theme_sidebar_bg,
        fg="#E7EDF7",
        anchor="w",
    ).pack(side=tk.LEFT)
    tk.Label(
        title_line,
        text="EXPLORER",
        font=("Microsoft YaHei", 8),
        bg=self.theme_sidebar_bg,
        fg="#8FA1B8",
        anchor="w",
    ).pack(side=tk.LEFT, padx=(6, 0))
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
        height=6,
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

    # 速查卡：从速查表提炼高频写法，支持筛选和一键插入
    self._setup_cheatsheet_quick_section(sidebar_frame, create_tool_btn)
    
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
    
    # 底部反馈区（控制台 / 问题 / 提示）
    output_frame = tk.Frame(
        self.right_paned,
        bg=self.theme_bg,
        highlightthickness=1,
        highlightbackground=self.theme_toolbar_border,
        highlightcolor=self.theme_toolbar_border,
        bd=0,
    )

    self.feedback_notebook = ttk.Notebook(output_frame, padding=0)
    self.feedback_notebook.pack(fill=tk.BOTH, expand=True)

    # 反馈页签右上角操作区：利用页签右侧空白，按当前页签展示操作
    self.feedback_action_bar = tk.Frame(output_frame, bg=self.theme_bg)
    self.feedback_action_bar.place(relx=1.0, x=-8, y=4, anchor="ne")
    self.feedback_action_hint_var = tk.StringVar(value="")
    self.feedback_action_hint = tk.Label(
        self.feedback_action_bar,
        textvariable=self.feedback_action_hint_var,
        font=("Microsoft YaHei", 8),
        bg=self.theme_bg,
        fg="#8FA1B8",
        anchor="e",
    )
    self.feedback_action_hint.pack(side=tk.RIGHT)
    self.feedback_action_btn = create_tool_btn(
        self.feedback_action_bar,
        text="",
        cmd=lambda: None,
        variant="subtle",
        compact=True,
        font=("Microsoft YaHei", 8),
    )
    self.feedback_action_btn.pack(side=tk.RIGHT, padx=(0, 6))

    # 控制台页
    console_tab = tk.Frame(self.feedback_notebook, bg=self.theme_bg, borderwidth=0)
    self.feedback_notebook.add(console_tab, text=" 控制台 ")

    out_top = tk.Frame(console_tab, bg=self.theme_panel_bg, padx=2, pady=1)
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

    terminal_font = ("Consolas" if sys.platform == "win32" else "Courier New", 11)
    self.output = scrolledtext.ScrolledText(
        console_tab,
        font=terminal_font,
        height=9,
        bg=self.theme_bg,
        fg="#A8C7FA",
        state=tk.DISABLED,
        padx=15,
        pady=5,
        spacing1=3,
        borderwidth=0,
        relief="flat",
        highlightthickness=0,
        insertbackground="#CCCCCC",
    )
    self.output.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    self._style_scrolledtext_vbar(self.output, parent=console_tab)

    # 问题页（原左侧问题列表 + 详情）
    issue_tab = tk.Frame(self.feedback_notebook, bg=self.theme_panel_bg, borderwidth=0)
    self.feedback_notebook.add(issue_tab, text=" 问题 ")

    issue_top = tk.Frame(issue_tab, bg=self.theme_panel_bg, padx=8, pady=6)
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

    issue_container = tk.Frame(issue_tab, bg=self.theme_panel_bg, padx=8)
    issue_container.pack(fill=tk.BOTH, expand=True, pady=(0, 6))
    self.issue_listbox = tk.Listbox(
        issue_container,
        height=8,
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
    self.issue_listbox.bind("<<ListboxSelect>>", self._issue_update_status, add="+")

    issue_detail_box = tk.Frame(issue_tab, bg=self.theme_panel_bg, padx=8)
    issue_detail_box.pack(fill=tk.X, pady=(0, 8))
    tk.Label(
        issue_detail_box,
        text="问题详情",
        font=("Microsoft YaHei", 8, "bold"),
        bg=self.theme_panel_bg,
        fg="#8FA1B8",
        anchor="w",
    ).pack(fill=tk.X, pady=(0, 4))
    self.issue_detail_var = tk.StringVar(value="（当前文件无语法/语义问题）")
    self.issue_detail_label = tk.Label(
        issue_detail_box,
        textvariable=self.issue_detail_var,
        font=("Microsoft YaHei", 8),
        bg=self.theme_panel_inner_bg,
        fg="#9FB0C5",
        anchor="nw",
        justify="left",
        padx=8,
        pady=6,
        wraplength=420,
    )
    self.issue_detail_label.pack(fill=tk.X)
    self.issue_detail_label.bind("<Configure>", self._update_issue_detail_wrap, add="+")

    # 提示页（原左侧快速查看）
    quick_tab = tk.Frame(self.feedback_notebook, bg=self.theme_panel_bg, borderwidth=0)
    self.feedback_notebook.add(quick_tab, text=" 提示 ")

    quick_top = tk.Frame(quick_tab, bg=self.theme_panel_bg, padx=8, pady=6)
    quick_top.pack(fill=tk.X)
    tk.Label(
        quick_top,
        text="快速查看 QUICK VIEW",
        font=("Microsoft YaHei", 8, "bold"),
        bg=self.theme_panel_bg,
        fg="#8FA1B8",
        anchor="w",
    ).pack(side=tk.LEFT, fill=tk.X, expand=True)

    quick_detail_box = tk.Frame(quick_tab, bg=self.theme_panel_bg, padx=8, pady=0)
    quick_detail_box.pack(fill=tk.BOTH, expand=True, pady=(0, 8))
    self.quick_view_var = tk.StringVar(value="（把光标放到代码中可快速查看）")
    self.quick_view_label = tk.Label(
        quick_detail_box,
        textvariable=self.quick_view_var,
        font=("Microsoft YaHei", 8),
        bg=self.theme_panel_inner_bg,
        fg="#9FB0C5",
        anchor="nw",
        justify="left",
        padx=8,
        pady=8,
        wraplength=420,
    )
    self.quick_view_label.pack(fill=tk.BOTH, expand=True)
    self.quick_view_label.bind("<Configure>", self._update_quick_view_wrap, add="+")

    self._feedback_tab_base_text = {
        "console": "控制台",
        "issue": "问题",
        "quick": "提示",
    }
    self._feedback_tab_widgets = {
        "console": console_tab,
        "issue": issue_tab,
        "quick": quick_tab,
    }
    self._feedback_tab_unread = {
        "console": False,
        "issue": False,
        "quick": False,
    }
    self._feedback_tab_red_dot = "•"
    self._feedback_tab_dot_image = _build_feedback_dot_image(
        size=max(10, int(11 * self.dpi_scale)),
        fill_color="#FF4D4F",
        border_color="#D23537",
    )
    self.feedback_notebook.bind("<<NotebookTabChanged>>", self._on_feedback_tab_changed, add="+")

    self.right_paned.add(output_frame, stretch="never", minsize=160)
    self.feedback_notebook.select(console_tab)
    self._refresh_feedback_tab_badges()
    update_feedback_action_bar(self)
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
    self._refresh_quick_view()


def _feedback_selected_key(owner):
    notebook = getattr(owner, "feedback_notebook", None)
    tab_widgets = getattr(owner, "_feedback_tab_widgets", {}) or {}
    if notebook is None or not tab_widgets:
        return None
    try:
        selected = str(notebook.select())
    except tk.TclError:
        return None
    for key, widget in tab_widgets.items():
        if str(widget) == selected:
            return key
    return None


def update_feedback_action_bar(owner):
    action_btn = getattr(owner, "feedback_action_btn", None)
    hint_var = getattr(owner, "feedback_action_hint_var", None)
    if action_btn is None or hint_var is None:
        return
    current = _feedback_selected_key(owner)

    try:
        if current == "console":
            action_btn.configure(text="清空", command=owner._clear_output_console, state=tk.NORMAL)
            hint_var.set("调试日志")
        elif current == "issue":
            action_btn.configure(text="定位下一个", command=owner.jump_to_diagnostic, state=tk.NORMAL)
            count_var = getattr(owner, "issue_count_var", None)
            count_text = str(count_var.get()) if count_var is not None else "0"
            hint_var.set(f"问题 {count_text}")
        elif current == "quick":
            action_btn.configure(text="刷新", command=owner._refresh_quick_view, state=tk.NORMAL)
            hint_var.set("快速查看")
        else:
            action_btn.configure(text="", command=lambda: None, state=tk.DISABLED)
            hint_var.set("")
    except tk.TclError:
        pass


def refresh_feedback_tab_badges(owner):
    notebook = getattr(owner, "feedback_notebook", None)
    tab_widgets = getattr(owner, "_feedback_tab_widgets", {}) or {}
    base_text = getattr(owner, "_feedback_tab_base_text", {}) or {}
    unread = getattr(owner, "_feedback_tab_unread", {}) or {}
    if notebook is None or not tab_widgets or not base_text or not unread:
        return

    current = _feedback_selected_key(owner)

    dot = str(getattr(owner, "_feedback_tab_red_dot", "•") or "•")
    dot_image = getattr(owner, "_feedback_tab_dot_image", None)
    for key, title in base_text.items():
        widget = tab_widgets.get(key)
        if widget is None:
            continue
        show_dot = bool(unread.get(key)) and key != current
        try:
            if show_dot and dot_image is not None:
                notebook.tab(widget, text=f" {title} ", image=dot_image, compound=tk.LEFT)
            elif show_dot:
                notebook.tab(widget, text=f" {dot} {title} ", image="", compound=tk.NONE)
            else:
                notebook.tab(widget, text=f" {title} ", image="", compound=tk.NONE)
        except tk.TclError:
            pass
    update_feedback_action_bar(owner)


def mark_feedback_tab(owner, tab_key, active=True):
    unread = getattr(owner, "_feedback_tab_unread", None)
    if not isinstance(unread, dict) or tab_key not in unread:
        return
    if not active:
        unread[tab_key] = False
        refresh_feedback_tab_badges(owner)
        return
    unread[tab_key] = True
    refresh_feedback_tab_badges(owner)


def clear_feedback_tab(owner, tab_key=None):
    unread = getattr(owner, "_feedback_tab_unread", None)
    if not isinstance(unread, dict):
        return
    if tab_key is None:
        for key in list(unread.keys()):
            unread[key] = False
    elif tab_key in unread:
        unread[tab_key] = False
    refresh_feedback_tab_badges(owner)


def on_feedback_tab_changed(owner, event=None):
    del event
    refresh_feedback_tab_badges(owner)
