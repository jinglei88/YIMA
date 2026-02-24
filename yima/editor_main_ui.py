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
    self.issue_listbox.bind("<<ListboxSelect>>", self._issue_update_status, add="+")

    issue_detail_box = tk.Frame(issue_section, bg=self.theme_panel_bg, padx=8)
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
        wraplength=220,
    )
    self.issue_detail_label.pack(fill=tk.X)
    self.issue_detail_label.bind("<Configure>", self._update_issue_detail_wrap, add="+")
    
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
