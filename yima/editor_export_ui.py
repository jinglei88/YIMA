"""Export dialog UI helpers extracted from 易码编辑器.py."""

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
from tkinter import filedialog, messagebox
from typing import Any, Callable


def _center_dialog(owner, window: tk.Toplevel, content: tk.Widget, min_width: int, min_height: int) -> None:
    owner.root.update_idletasks()
    window.update_idletasks()
    width = max(int(min_width), int(content.winfo_reqwidth() + 24))
    height = max(int(min_height), int(content.winfo_reqheight() + 24))
    x = owner.root.winfo_rootx() + max(20, (owner.root.winfo_width() - width) // 2)
    y = owner.root.winfo_rooty() + max(20, (owner.root.winfo_height() - height) // 2)
    window.geometry(f"{width}x{height}+{x}+{y}")


def choose_export_mode_dialog(owner) -> str | None:
    mode_window = tk.Toplevel(owner.root)
    mode_window.title("导出模式")
    mode_window.configure(bg=owner.theme_toolbar_bg)
    mode_window.resizable(False, False)
    mode_window.transient(owner.root)
    mode_window.grab_set()
    title_font = getattr(owner, "font_ui_bold", owner.font_ui)

    result = {"value": None}

    def set_mode(value):
        result["value"] = value
        mode_window.destroy()

    main = tk.Frame(mode_window, bg=owner.theme_toolbar_bg, padx=16, pady=14)
    main.pack(fill=tk.BOTH, expand=True)

    tk.Label(
        main,
        text="请选择导出方式：",
        bg=owner.theme_toolbar_bg,
        fg=owner.theme_toolbar_fg,
        font=title_font,
        anchor="w",
    ).pack(anchor="w")
    tk.Label(
        main,
        text="快速版：一键打包（推荐）\n高级版：自定义名称/路径/图标/运行模式",
        bg=owner.theme_toolbar_bg,
        fg=owner.theme_toolbar_fg,
        font=owner.font_ui,
        justify="left",
        anchor="w",
        pady=8,
    ).pack(anchor="w", fill=tk.X)

    buttons = tk.Frame(main, bg=owner.theme_toolbar_bg)
    buttons.pack(fill=tk.X, pady=(8, 0))

    tk.Button(
        buttons,
        text="快速版",
        command=lambda: set_mode("quick"),
        font=owner.font_ui,
        width=10,
        bg="#1E7BC8",
        fg="#FFFFFF",
    ).pack(side=tk.LEFT)
    tk.Button(
        buttons,
        text="高级版",
        command=lambda: set_mode("advanced"),
        font=owner.font_ui,
        width=10,
    ).pack(side=tk.LEFT, padx=(8, 0))
    tk.Button(
        buttons,
        text="取消",
        command=lambda: set_mode(None),
        font=owner.font_ui,
        width=10,
    ).pack(side=tk.RIGHT)

    mode_window.bind("<Escape>", lambda _e: set_mode(None))
    mode_window.bind("<Return>", lambda _e: set_mode("quick"))
    _center_dialog(owner, mode_window, main, min_width=560, min_height=220)
    owner.root.wait_window(mode_window)
    return result["value"]


def advanced_export_config_dialog(
    owner,
    default_values: dict[str, Any],
    build_advanced_export_config_func: Callable[[str, str, str, str, str, str], dict[str, Any]],
) -> dict[str, Any] | None:
    default_app_name = str(default_values.get("软件名称", "") or "")
    default_output_path = str(default_values.get("输出路径", "") or "")
    default_icon_path = str(default_values.get("图标路径", "") or "")
    default_output_dir = str(default_values.get("输出目录", "") or owner.workspace_dir)
    default_file_name = str(default_values.get("默认软件文件名", f"{default_app_name}.exe") or f"{default_app_name}.exe")

    advanced_window = tk.Toplevel(owner.root)
    advanced_window.title("导出软件（高级设置）")
    advanced_window.configure(bg=owner.theme_toolbar_bg)
    advanced_window.resizable(False, False)
    advanced_window.transient(owner.root)
    advanced_window.grab_set()

    name_var = tk.StringVar(value=default_app_name)
    path_var = tk.StringVar(value=default_output_path)
    icon_var = tk.StringVar(value=default_icon_path)
    mode_var = tk.StringVar(value="windowed")
    result = {"value": None}

    main = tk.Frame(advanced_window, bg=owner.theme_toolbar_bg, padx=14, pady=12)
    main.pack(fill=tk.BOTH, expand=True)

    label_style = {"bg": owner.theme_toolbar_bg, "fg": owner.theme_toolbar_fg, "font": owner.font_ui}
    input_style = {"font": owner.font_ui, "bg": owner.theme_bg, "fg": owner.theme_fg, "insertbackground": owner.theme_fg}

    tk.Label(main, text="软件名称：", **label_style).grid(row=0, column=0, sticky="w", pady=(0, 6))
    name_input = tk.Entry(main, textvariable=name_var, width=48, **input_style)
    name_input.grid(row=0, column=1, columnspan=2, sticky="we", padx=(8, 0), pady=(0, 6))

    tk.Label(main, text="输出路径：", **label_style).grid(row=1, column=0, sticky="w", pady=6)
    path_input = tk.Entry(main, textvariable=path_var, width=48, **input_style)
    path_input.grid(row=1, column=1, sticky="we", padx=(8, 8), pady=6)

    tk.Label(main, text="图标文件：", **label_style).grid(row=2, column=0, sticky="w", pady=6)
    icon_input = tk.Entry(main, textvariable=icon_var, width=48, **input_style)
    icon_input.grid(row=2, column=1, sticky="we", padx=(8, 8), pady=6)

    tk.Label(main, text="运行模式：", **label_style).grid(row=3, column=0, sticky="nw", pady=(8, 2))
    mode_frame = tk.Frame(main, bg=owner.theme_toolbar_bg)
    mode_frame.grid(row=3, column=1, columnspan=2, sticky="w", padx=(8, 0), pady=(8, 2))

    tk.Radiobutton(
        mode_frame,
        text="代码黑框版（调试）",
        variable=mode_var,
        value="console",
        bg=owner.theme_toolbar_bg,
        fg=owner.theme_toolbar_fg,
        selectcolor=owner.theme_panel_bg,
        activebackground=owner.theme_toolbar_bg,
        activeforeground=owner.theme_toolbar_fg,
        font=owner.font_ui,
    ).pack(anchor="w")
    tk.Radiobutton(
        mode_frame,
        text="纯净窗口版（发布）",
        variable=mode_var,
        value="windowed",
        bg=owner.theme_toolbar_bg,
        fg=owner.theme_toolbar_fg,
        selectcolor=owner.theme_panel_bg,
        activebackground=owner.theme_toolbar_bg,
        activeforeground=owner.theme_toolbar_fg,
        font=owner.font_ui,
    ).pack(anchor="w")

    tk.Label(
        main,
        text="说明：可直接手动改路径；图标留空会使用默认 logo.ico（如存在）。",
        bg=owner.theme_toolbar_bg,
        fg=owner.theme_toolbar_muted,
        font=owner.font_ui,
        anchor="w",
    ).grid(row=4, column=0, columnspan=3, sticky="we", pady=(8, 10))

    action_frame = tk.Frame(main, bg=owner.theme_toolbar_bg)
    action_frame.grid(row=5, column=0, columnspan=3, sticky="e")

    def browse_output_path():
        current = path_var.get().strip()
        initial_dir = owner.workspace_dir
        initial_file = f"{owner._sanitize_export_name(name_var.get())}.exe"
        if current:
            current = os.path.abspath(os.path.expanduser(current))
            if os.path.isdir(os.path.dirname(current)):
                initial_dir = os.path.dirname(current)
            base_name = os.path.basename(current)
            if base_name:
                initial_file = base_name
        selected = filedialog.asksaveasfilename(
            title="选择导出 EXE 路径",
            parent=advanced_window,
            initialdir=initial_dir,
            initialfile=initial_file,
            defaultextension=".exe",
            filetypes=[("Windows 可执行文件", "*.exe"), ("所有文件", "*.*")],
        )
        if selected:
            path_var.set(selected)

    def browse_icon():
        current = icon_var.get().strip()
        initial_dir = owner.workspace_dir
        if current and os.path.isdir(os.path.dirname(os.path.abspath(os.path.expanduser(current)))):
            initial_dir = os.path.dirname(os.path.abspath(os.path.expanduser(current)))
        selected = filedialog.askopenfilename(
            title="选择图标文件（.ico）",
            parent=advanced_window,
            initialdir=initial_dir,
            filetypes=[("图标文件", "*.ico"), ("所有文件", "*.*")],
        )
        if selected:
            icon_var.set(selected)

    def cancel_dialog():
        advanced_window.destroy()

    def confirm_dialog():
        candidate = build_advanced_export_config_func(
            name_var.get(),
            path_var.get(),
            icon_var.get(),
            mode_var.get(),
            default_output_dir,
            default_file_name,
        )

        icon_path = candidate.get("图标路径")
        if icon_path and not os.path.isfile(icon_path):
            messagebox.showwarning("图标无效", "图标文件不存在，请重新选择。", parent=advanced_window)
            return

        result["value"] = candidate
        advanced_window.destroy()

    tk.Button(main, text="浏览...", command=browse_output_path, font=owner.font_ui, width=10).grid(row=1, column=2, sticky="e", pady=6)
    tk.Button(main, text="浏览...", command=browse_icon, font=owner.font_ui, width=10).grid(row=2, column=2, sticky="e", pady=6)

    tk.Button(action_frame, text="取消", command=cancel_dialog, font=owner.font_ui, width=10).pack(side=tk.RIGHT, padx=(8, 0))
    tk.Button(action_frame, text="开始打包", command=confirm_dialog, font=owner.font_ui, width=12, bg="#1E7BC8", fg="#FFFFFF").pack(side=tk.RIGHT)

    main.grid_columnconfigure(1, weight=1)
    name_input.focus_set()
    advanced_window.bind("<Return>", lambda _e: confirm_dialog())
    advanced_window.bind("<Escape>", lambda _e: cancel_dialog())

    _center_dialog(owner, advanced_window, main, min_width=860, min_height=420)
    owner.root.wait_window(advanced_window)
    return result["value"]
