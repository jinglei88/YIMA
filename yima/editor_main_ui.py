"""Main UI setup helper extracted from 易码编辑器.py."""

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

import sys
import tkinter as tk
from tkinter import scrolledtext, ttk

from yima.editor_ui_designer_flow import ensure_embedded_ui_designer


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
    # 顶部现代化工具栏（分组 + 主按钮）
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

    toolbar_item_height = max(30, int(32 * self.dpi_scale))

    left_actions = tk.Frame(toolbar, bg=self.theme_toolbar_bg)
    left_actions.pack(side=tk.LEFT, fill=tk.X, expand=True)
    quick_action_entries = []

    def create_menu_chip(parent, title, items, quick_items=None):
        outer = tk.Frame(
            parent,
            bg=self.theme_toolbar_group_bg,
            highlightthickness=1,
            highlightbackground=self.theme_toolbar_border,
            highlightcolor=self.theme_toolbar_border,
            bd=0,
        )
        outer.pack(side=tk.LEFT, padx=(0, 6))

        btn = tk.Menubutton(
            outer,
            text=f"{title} ▾",
            font=("Microsoft YaHei", 9, "bold"),
            bg=self.theme_toolbar_group_bg,
            fg=self.theme_toolbar_fg,
            activebackground=self.theme_toolbar_hover,
            activeforeground="#FFFFFF",
            relief="flat",
            borderwidth=0,
            padx=10,
            pady=4,
            cursor="hand2",
            takefocus=0,
            direction="below",
        )
        btn.pack(side=tk.LEFT, padx=(2, 0), pady=2)

        quick_buttons = []
        quick_list = list(quick_items or [])
        for q_text, q_cmd in quick_list[:2]:
            qbtn = create_tool_btn(
                outer,
                q_text,
                q_cmd,
                variant="subtle",
                compact=True,
                font=("Microsoft YaHei", 9),
            )
            qbtn.configure(pady=4)
            qbtn.pack(side=tk.LEFT, padx=(4, 2), pady=2)
            quick_buttons.append(qbtn)

        for qbtn in quick_buttons:
            quick_action_entries.append(
                {
                    "btn": qbtn,
                    "menu_btn": btn,
                    "shown": True,
                    "padx": (4, 2),
                    "pady": 2,
                }
            )

        menu = tk.Menu(
            btn,
            tearoff=0,
            font=("Microsoft YaHei", 9),
            bg=self.theme_panel_bg,
            fg=self.theme_fg,
            activebackground=self.theme_toolbar_hover,
            activeforeground="#FFFFFF",
            relief="flat",
            borderwidth=1,
        )
        for row in items:
            if row == "-":
                menu.add_separator()
                continue
            if len(row) == 2:
                label, cmd = row
                menu.add_command(label=label, command=cmd)
            else:
                label, cmd, accel = row
                menu.add_command(label=label, command=cmd, accelerator=accel)
        btn.configure(menu=menu)
        return outer

    right_actions = tk.Frame(toolbar, bg=self.theme_toolbar_bg)
    right_actions.pack(side=tk.RIGHT)
    top_action_shell = tk.Frame(
        right_actions,
        bg=self.theme_toolbar_group_bg,
        highlightthickness=1,
        highlightbackground=self.theme_toolbar_border,
        highlightcolor=self.theme_toolbar_border,
        bd=0,
        padx=2,
        pady=2,
    )
    top_action_shell.pack(side=tk.RIGHT)
    export_icon_size = max(14, int(16 * self.dpi_scale))
    run_icon_size = max(12, int(14 * self.dpi_scale))
    self._toolbar_run_icon = self._build_toolbar_icon("run", size=run_icon_size, color="#FFFFFF")
    self._toolbar_export_icon = self._build_toolbar_icon("export", size=export_icon_size, color="#FFFFFF")

    export_btn = create_tool_btn(
        top_action_shell,
        "导出软件",
        self.export_exe,
        variant="accent",
        font=("Microsoft YaHei", 9, "bold"),
        compact=True,
        icon_image=self._toolbar_export_icon,
    )
    export_btn.configure(padx=6, pady=4)
    export_btn.pack(side=tk.RIGHT, padx=(0, 0), pady=0)

    run_btn = create_tool_btn(
        top_action_shell,
        "运行代码",
        self.run_code,
        variant="run",
        font=("Microsoft YaHei", 9, "bold"),
        compact=True,
        icon_image=self._toolbar_run_icon,
    )
    run_btn.configure(padx=6, pady=4)
    run_btn.pack(side=tk.RIGHT, padx=(0, 4), pady=0)

    create_menu_chip(
        left_actions,
        "项目",
        [
            ("新建项目", self.new_project, "Ctrl+N"),
            ("打开项目", self.open_project),
            ("最近项目", self.open_recent_project_menu),
        ],
        quick_items=[("新建", self.new_project)],
    )
    create_menu_chip(
        left_actions,
        "文件",
        [
            ("打开单文件", self.open_file, "Ctrl+O"),
            ("保存代码", self.save_file, "Ctrl+S"),
        ],
        quick_items=[("保存", self.save_file)],
    )
    create_menu_chip(
        left_actions,
        "编辑",
        [
            ("查找替换", self.open_find_dialog, "Ctrl+F / Ctrl+H"),
            ("跳转定义", self.goto_symbol_definition, "Ctrl+B"),
            ("查找引用", self.find_symbol_references, "Shift+F12"),
            ("全局引用", self.find_symbol_references_project, "Ctrl+Shift+F12"),
            "-",
            ("重命名", self.rename_symbol, "Ctrl+Shift+R"),
            ("全局重命名", self.rename_symbol_project, "Ctrl+Alt+R"),
            ("同词多光标", self.multi_cursor_add_next, "Ctrl+D"),
        ],
        quick_items=[("查找", self.open_find_dialog)],
    )
    create_menu_chip(
        left_actions,
        "文档",
        [
            ("速查表", self.open_cheatsheet, "F1"),
            ("示例中心", self.open_examples),
            ("界面设计器", self.open_ui_designer),
        ],
        quick_items=[("速查", self.open_cheatsheet)],
    )
    create_menu_chip(
        left_actions,
        "运维",
        [
            ("诊断中心", self.open_runtime_diagnostics, "Ctrl+Shift+D"),
            ("运行日志", self.open_runtime_log),
            "-",
            ("恢复最近备份", self.restore_latest_rename_backup, "Ctrl+Alt+B"),
            ("备份历史", self.open_rename_backup_history, "Ctrl+Alt+H"),
            "-",
            ("最近恢复报告", self.open_latest_restore_report, "Ctrl+Alt+J"),
            ("恢复报告历史", self.open_restore_report_history, "Ctrl+Alt+K"),
            ("恢复报告目录", self.open_restore_report_dir),
        ],
        quick_items=[("诊断", self.open_runtime_diagnostics)],
    )

    def _update_toolbar_density(_event=None):
        width = int(toolbar_shell.winfo_width() or self.root.winfo_width() or 0)
        hide_threshold = int(max(1050, 1120 * float(self.dpi_scale)))
        show_quick = width >= hide_threshold
        for item in quick_action_entries:
            btn = item["btn"]
            menu_btn = item["menu_btn"]
            shown = bool(item["shown"])
            if show_quick and not shown:
                try:
                    btn.pack(side=tk.LEFT, padx=item["padx"], pady=item["pady"])
                    item["shown"] = True
                except tk.TclError:
                    pass
            elif (not show_quick) and shown:
                try:
                    btn.pack_forget()
                    item["shown"] = False
                except tk.TclError:
                    pass

    toolbar_shell.bind("<Configure>", _update_toolbar_density, add="+")
    self.root.after(0, _update_toolbar_density)


    tk.Frame(self.root, height=1, bg=self.theme_toolbar_border, bd=0).pack(fill=tk.X)

    # 主分割区（左侧边栏 + 右侧主工作区）
    # 分割线保持较细，减少视觉干扰
    self.main_paned = tk.PanedWindow(self.root, orient=tk.HORIZONTAL, sashwidth=1, bg=self.theme_sash, borderwidth=0)
    self.main_paned.pack(fill=tk.BOTH, expand=True)
    # 最左侧：模式边栏（仅图标）
    mode_rail_width = int(42 * self.dpi_scale)
    mode_rail = tk.Frame(
        self.main_paned,
        bg=self.theme_toolbar_bg,
        width=mode_rail_width,
        highlightthickness=1,
        highlightbackground=self.theme_toolbar_border,
        highlightcolor=self.theme_toolbar_border,
        bd=0,
    )
    self.mode_rail = mode_rail
    mode_rail.pack_propagate(False)
    self.main_paned.add(mode_rail, stretch="never", minsize=mode_rail_width)
    self.workspace_mode = "code"

    mode_icon_size = max(20, int(20 * self.dpi_scale))
    self._mode_code_icon_active = self._build_toolbar_icon("code", size=mode_icon_size, color="#FFFFFF")
    self._mode_code_icon_idle = self._build_toolbar_icon("code", size=mode_icon_size, color="#9FB0C5")
    self._mode_design_icon_active = self._build_toolbar_icon("design", size=mode_icon_size, color="#FFFFFF")
    self._mode_design_icon_idle = self._build_toolbar_icon("design", size=mode_icon_size, color="#9FB0C5")

    slot_size = int(36 * self.dpi_scale)
    top_gap = int(10 * self.dpi_scale)
    between_gap = int(14 * self.dpi_scale)

    code_slot = tk.Frame(mode_rail, bg=self.theme_toolbar_bg, width=slot_size, height=slot_size)
    code_slot.pack(padx=3, pady=(top_gap, between_gap))
    code_slot.pack_propagate(False)
    self.mode_btn_code = tk.Button(
        code_slot,
        image=self._mode_code_icon_active,
        text="",
        command=lambda: self._switch_workspace_mode("code"),
        bg="#0E639C",
        activebackground="#1577B8",
        relief="flat",
        bd=0,
        padx=0,
        pady=0,
        cursor="hand2",
        takefocus=0,
    )
    self.mode_btn_code.pack(fill=tk.BOTH, expand=True)

    designer_slot = tk.Frame(mode_rail, bg=self.theme_toolbar_bg, width=slot_size, height=slot_size)
    designer_slot.pack(padx=3, pady=(0, between_gap))
    designer_slot.pack_propagate(False)
    self.mode_btn_designer = tk.Button(
        designer_slot,
        image=self._mode_design_icon_idle,
        text="",
        command=lambda: self._switch_workspace_mode("designer"),
        bg=self.theme_panel_bg,
        activebackground=self.theme_toolbar_hover,
        relief="flat",
        bd=0,
        padx=0,
        pady=0,
        cursor="hand2",
        takefocus=0,
    )
    self.mode_btn_designer.pack(fill=tk.BOTH, expand=True)
    
    # 左侧：资源管理器（Sidebar）
    sidebar_frame = tk.Frame(self.main_paned, bg=self.theme_sidebar_bg)
    self.sidebar_frame = sidebar_frame

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
    # 文件树容器（卡片化）
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

    # 滚动条（垂直 + 水平）
    vsb = ttk.Scrollbar(tree_container, orient="vertical", command=self.tree.yview)
    hsb = ttk.Scrollbar(tree_container, orient="horizontal", command=self.tree.xview)
    self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

    self.tree.grid(column=0, row=0, sticky="nsew")
    vsb.grid(column=1, row=0, sticky="ns")
    hsb.grid(column=0, row=1, sticky="ew")

    tree_container.grid_columnconfigure(0, weight=1)
    tree_container.grid_rowconfigure(0, weight=1)

    # 代码大纲区（功能 / 图纸导航 + 折叠）
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

    # 速查卡片：高频写法入口，支持筛选与一键插入
    self._setup_cheatsheet_quick_section(sidebar_frame, create_tool_btn)
    
    # 给左侧预留足够宽度，避免文字被遮挡
    sidebar_default_width = int(250 * self.dpi_scale)
    self.sidebar_default_width = sidebar_default_width
    self.main_paned.add(sidebar_frame, stretch="never", minsize=sidebar_default_width)
    
    # 右侧：上下分割（上代码，下反馈）
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
    self.right_paned_minsize = 600
    
    # 代码多标签区（Notebook）/ 可视化设计区（同位切换）
    self.workspace_switch_frame = tk.Frame(self.right_paned, bg=self.theme_bg, borderwidth=0)
    self.code_view_frame = tk.Frame(self.workspace_switch_frame, bg=self.theme_bg, borderwidth=0)
    self.designer_view_frame = tk.Frame(self.workspace_switch_frame, bg=self.theme_bg, borderwidth=0)

    editor_frame = self.code_view_frame
    self.notebook = ttk.Notebook(editor_frame, padding=0)
    try:
        # 某些 Tk 版本会让 PanedWindow 的 sashcursor 影响子控件，这里显式重置
        self.notebook.configure(cursor="arrow")
    except tk.TclError:
        pass
    self.notebook.pack(fill=tk.BOTH, expand=True)
    self.notebook.bind("<Enter>", lambda _e: self.notebook.configure(cursor="arrow"), add="+")
    self.notebook.bind("<Leave>", lambda _e: self.notebook.configure(cursor=""), add="+")
    self.notebook.bind("<Button-1>", self.on_tab_click)
    self.notebook.bind("<Button-2>", self.on_tab_middle_click, add="+")
    self.notebook.bind("<ButtonRelease-2>", self.on_tab_middle_click, add="+")
    
    self.code_view_frame.pack(fill=tk.BOTH, expand=True)
    self.right_paned.add(self.workspace_switch_frame, stretch="always", minsize=400)
    
    # 底部反馈区（控制台 / 问题 / 提示）
    output_frame = tk.Frame(
        self.right_paned,
        bg=self.theme_bg,
        highlightthickness=1,
        highlightbackground=self.theme_toolbar_border,
        highlightcolor=self.theme_toolbar_border,
        bd=0,
    )
    self.output_frame = output_frame

    self.feedback_notebook = ttk.Notebook(output_frame, padding=0)
    try:
        self.feedback_notebook.configure(cursor="arrow")
    except tk.TclError:
        pass
    self.feedback_notebook.pack(fill=tk.BOTH, expand=True)

    # 反馈页签右上角操作区：根据当前页签显示对应动作
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

    # 问题页（列表 + 详情）
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

    # 提示页（快速查看）
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
    self._feedback_tab_red_dot = "●"
    self._feedback_tab_dot_image = _build_feedback_dot_image(
        size=max(10, int(11 * self.dpi_scale)),
        fill_color="#FF4D4F",
        border_color="#D23537",
    )
    self.feedback_notebook.bind("<<NotebookTabChanged>>", self._on_feedback_tab_changed, add="+")

    self.right_paned.add(output_frame, stretch="never", minsize=160)
    self.designer_workspace_frame = tk.Frame(self.main_paned, bg=self.theme_bg, borderwidth=0)
    self.feedback_notebook.select(console_tab)
    self._refresh_feedback_tab_badges()
    update_feedback_action_bar(self)
    self._clear_output_console(keep_intro=True)

    # 底部状态栏（当前状态 / 诊断 / 光标位置）
    # 外层包裹容器用于保持稳定视觉层级
    status_wrap = tk.Frame(
        self.root,
        bg=self.theme_bg,
        padx=6,
        pady=0,
        bd=0,
        highlightthickness=0,
    )
    status_wrap.pack(side=tk.BOTTOM, fill=tk.X, pady=(2, 4))
    # 关键：调整 pack 顺序，确保状态栏固定在底部
    try:
        self.main_paned.pack_forget()
    except tk.TclError:
        pass
    self.main_paned.pack(fill=tk.BOTH, expand=True)

    status_bar = tk.Frame(
        status_wrap,
        bg="#171C23",
        height=int(28 * self.dpi_scale),
        highlightthickness=1,
        highlightbackground=self.theme_toolbar_border,
        highlightcolor=self.theme_toolbar_border,
        bd=0,
    )
    status_bar.pack(fill=tk.X)
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
    
    # 文件树右键菜单
    self.tree_menu = tk.Menu(self.root, tearoff=0, font=self.font_ui)
    self.tree_menu.add_command(label="📝 新建代码文件", command=self.create_new_file_in_tree)
    self.tree_menu.add_command(label="📁 新建文件夹", command=self.create_new_folder_in_tree)
    self.tree_menu.add_separator()
    self.tree_menu.add_command(label="🗑️ 删除", command=self.delete_item_in_tree)
    
    # 智能补全弹窗（双列：类型 + 候选）
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
    
    # 初始化后优先恢复上次项目；失败则创建默认标签页
    if not self._try_restore_last_project():
        self.refresh_file_tree()
        self._create_editor_tab("未命名代码.ym")
    self._refresh_quick_view()
    switch_workspace_mode(self, "code")


def _refresh_workspace_mode_buttons(owner):
    mode = str(getattr(owner, "workspace_mode", "code") or "code")
    code_btn = getattr(owner, "mode_btn_code", None)
    designer_btn = getattr(owner, "mode_btn_designer", None)
    if code_btn is None or designer_btn is None:
        return

    try:
        if mode == "designer":
            code_btn.configure(
                bg=owner.theme_panel_bg,
                activebackground=owner.theme_toolbar_hover,
                image=getattr(owner, "_mode_code_icon_idle", ""),
            )
            designer_btn.configure(
                bg="#0E639C",
                activebackground="#1577B8",
                image=getattr(owner, "_mode_design_icon_active", ""),
            )
        else:
            code_btn.configure(
                bg="#0E639C",
                activebackground="#1577B8",
                image=getattr(owner, "_mode_code_icon_active", ""),
            )
            designer_btn.configure(
                bg=owner.theme_panel_bg,
                activebackground=owner.theme_toolbar_hover,
                image=getattr(owner, "_mode_design_icon_idle", ""),
            )
    except tk.TclError:
        return


def switch_workspace_mode(owner, mode="code"):
    target = "designer" if str(mode).strip().lower() in {"designer", "design", "ui", "visual", "可视化"} else "code"
    current = str(getattr(owner, "workspace_mode", "code") or "code")

    main_paned = getattr(owner, "main_paned", None)
    sidebar_frame = getattr(owner, "sidebar_frame", None)
    right_paned = getattr(owner, "right_paned", None)
    workspace_host = getattr(owner, "workspace_switch_frame", None)
    output_frame = getattr(owner, "output_frame", None)
    designer_full_frame = getattr(owner, "designer_workspace_frame", None)
    code_frame = getattr(owner, "code_view_frame", None)
    if None in {main_paned, sidebar_frame, right_paned, workspace_host, output_frame, designer_full_frame, code_frame}:
        owner.workspace_mode = target
        _refresh_workspace_mode_buttons(owner)
        return

    def _pane_exists(paned, widget):
        try:
            panes = list(paned.panes() or [])
        except tk.TclError:
            return False
        return str(widget) in {str(item) for item in panes}

    if target == "designer":
        if _pane_exists(main_paned, sidebar_frame):
            try:
                main_paned.forget(sidebar_frame)
            except tk.TclError:
                pass
        if _pane_exists(main_paned, right_paned):
            try:
                main_paned.forget(right_paned)
            except tk.TclError:
                pass
        if not _pane_exists(main_paned, designer_full_frame):
            try:
                main_paned.add(designer_full_frame, stretch="always", minsize=640)
            except tk.TclError:
                pass

        panel = ensure_embedded_ui_designer(owner, designer_full_frame)
        try:
            panel.pack(fill=tk.BOTH, expand=True)
        except tk.TclError:
            pass
        owner.workspace_mode = "designer"
        if hasattr(owner, "status_main_var"):
            owner.status_main_var.set("已切换到可视化界面设计模式")
    else:
        if _pane_exists(main_paned, designer_full_frame):
            try:
                main_paned.forget(designer_full_frame)
            except tk.TclError:
                pass

        if not _pane_exists(main_paned, sidebar_frame):
            try:
                main_paned.add(
                    sidebar_frame,
                    stretch="never",
                    minsize=int(getattr(owner, "sidebar_default_width", int(250 * owner.dpi_scale)) or int(250 * owner.dpi_scale)),
                )
            except tk.TclError:
                pass
        if not _pane_exists(main_paned, right_paned):
            try:
                main_paned.add(
                    right_paned,
                    stretch="always",
                    minsize=int(getattr(owner, "right_paned_minsize", 600) or 600),
                )
            except tk.TclError:
                pass

        if not _pane_exists(right_paned, workspace_host):
            try:
                right_paned.add(workspace_host, stretch="always", minsize=400)
            except tk.TclError:
                pass
        if not _pane_exists(right_paned, output_frame):
            try:
                right_paned.add(output_frame, stretch="never", minsize=160)
            except tk.TclError:
                pass

        panel = getattr(owner, "_ui_designer_embedded_panel", None)
        if panel is not None and current == "designer":
            try:
                panel.pack_forget()
            except tk.TclError:
                pass
        try:
            code_frame.pack(fill=tk.BOTH, expand=True)
        except tk.TclError:
            pass
        designer_frame = getattr(owner, "designer_view_frame", None)
        if designer_frame is not None:
            try:
                designer_frame.pack_forget()
            except tk.TclError:
                pass
        owner.workspace_mode = "code"
        if hasattr(owner, "status_main_var"):
            owner.status_main_var.set("已切换到代码编辑模式")
        editor_getter = getattr(owner, "_get_current_editor", None)
        if callable(editor_getter):
            editor = editor_getter()
            if editor is not None:
                try:
                    editor.focus_set()
                except tk.TclError:
                    pass

    _refresh_workspace_mode_buttons(owner)


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

    dot = str(getattr(owner, "_feedback_tab_red_dot", "●") or "●")
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
    # 当前就在该页签时视为已读，不显示红点
    if _feedback_selected_key(owner) == tab_key:
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
