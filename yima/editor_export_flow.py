"""Export domain: dialog, precheck, packaging, and entry orchestration."""

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
import shutil
import subprocess
import sys
import tempfile
import threading
import tkinter as tk
from tkinter import filedialog, messagebox
from typing import Any, Callable

from yima.editor_logic_core import (
    build_advanced_export_config as core_build_advanced_export_config,
    build_export_confirmation_text as core_build_export_confirmation_text,
    build_export_defaults as core_build_export_defaults,
    build_quick_export_config as core_build_quick_export_config,
    format_numbered_messages as core_format_numbered_messages,
)


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

    result_value: str | None = None

    def set_mode(value):
        nonlocal result_value
        result_value = value
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
    return result_value


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
    result_value: dict[str, Any] | None = None

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
        nonlocal result_value
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

        result_value = candidate
        advanced_window.destroy()

    tk.Button(main, text="浏览...", command=browse_output_path, font=owner.font_ui, width=10).grid(
        row=1, column=2, sticky="e", pady=6
    )
    tk.Button(main, text="浏览...", command=browse_icon, font=owner.font_ui, width=10).grid(
        row=2, column=2, sticky="e", pady=6
    )

    tk.Button(action_frame, text="取消", command=cancel_dialog, font=owner.font_ui, width=10).pack(
        side=tk.RIGHT, padx=(8, 0)
    )
    tk.Button(
        action_frame,
        text="开始打包",
        command=confirm_dialog,
        font=owner.font_ui,
        width=12,
        bg="#1E7BC8",
        fg="#FFFFFF",
    ).pack(side=tk.RIGHT)

    main.grid_columnconfigure(1, weight=1)
    name_input.focus_set()
    advanced_window.bind("<Return>", lambda _e: confirm_dialog())
    advanced_window.bind("<Escape>", lambda _e: cancel_dialog())

    _center_dialog(owner, advanced_window, main, min_width=860, min_height=420)
    owner.root.wait_window(advanced_window)
    return result_value


def export_config_pages_dialog(
    owner,
    default_values: dict[str, Any],
    build_advanced_export_config_func: Callable[[str, str, str, str, str, str], dict[str, Any]],
) -> dict[str, Any] | None:
    default_app_name = str(default_values.get("软件名称", "") or "")
    default_output_path = str(default_values.get("输出路径", "") or "")
    default_icon_path = str(default_values.get("图标路径", "") or "")
    default_output_dir = str(default_values.get("输出目录", "") or owner.workspace_dir)
    default_file_name = str(default_values.get("默认软件文件名", f"{default_app_name}.exe") or f"{default_app_name}.exe")

    window = tk.Toplevel(owner.root)
    window.title("导出软件")
    window.configure(bg=owner.theme_toolbar_bg)
    window.resizable(False, False)
    window.transient(owner.root)
    window.grab_set()

    mode_var = tk.StringVar(value="quick")
    name_var = tk.StringVar(value=default_app_name)
    path_var = tk.StringVar(value=default_output_path)
    icon_var = tk.StringVar(value=default_icon_path)
    run_mode_var = tk.StringVar(value="windowed")
    result_value: dict[str, Any] | None = None

    main = tk.Frame(window, bg=owner.theme_toolbar_bg, padx=14, pady=12)
    main.pack(fill=tk.BOTH, expand=True)

    tk.Label(
        main,
        text="导出软件",
        bg=owner.theme_toolbar_bg,
        fg=owner.theme_toolbar_fg,
        font=getattr(owner, "font_ui_bold", owner.font_ui),
        anchor="w",
    ).pack(fill=tk.X)

    switch_row = tk.Frame(main, bg=owner.theme_toolbar_bg)
    switch_row.pack(fill=tk.X, pady=(8, 8))

    pages_holder = tk.Frame(main, bg=owner.theme_toolbar_bg)
    pages_holder.pack(fill=tk.BOTH, expand=True)
    quick_page = tk.Frame(pages_holder, bg=owner.theme_toolbar_bg)
    advanced_page = tk.Frame(pages_holder, bg=owner.theme_toolbar_bg)

    def _switch_mode(target: str):
        mode_var.set(target)
        if target == "quick":
            advanced_page.pack_forget()
            quick_page.pack(fill=tk.BOTH, expand=True)
            btn_quick.configure(bg="#0E639C", fg="#FFFFFF")
            btn_adv.configure(bg=owner.theme_panel_bg, fg=owner.theme_toolbar_fg)
        else:
            quick_page.pack_forget()
            advanced_page.pack(fill=tk.BOTH, expand=True)
            btn_adv.configure(bg="#0E639C", fg="#FFFFFF")
            btn_quick.configure(bg=owner.theme_panel_bg, fg=owner.theme_toolbar_fg)
        _center_dialog(owner, window, main, min_width=920, min_height=500)

    btn_quick = tk.Button(
        switch_row,
        text="快速打包",
        command=lambda: _switch_mode("quick"),
        font=owner.font_ui,
        relief="flat",
        borderwidth=0,
        padx=10,
        pady=4,
        cursor="hand2",
    )
    btn_quick.pack(side=tk.LEFT)
    btn_adv = tk.Button(
        switch_row,
        text="高级设置",
        command=lambda: _switch_mode("advanced"),
        font=owner.font_ui,
        relief="flat",
        borderwidth=0,
        padx=10,
        pady=4,
        cursor="hand2",
    )
    btn_adv.pack(side=tk.LEFT, padx=(6, 0))

    quick_box = tk.Frame(
        quick_page,
        bg=owner.theme_panel_bg,
        highlightthickness=1,
        highlightbackground=owner.theme_toolbar_border,
        highlightcolor=owner.theme_toolbar_border,
        bd=0,
        padx=12,
        pady=10,
    )
    quick_box.pack(fill=tk.BOTH, expand=True)
    tk.Label(
        quick_box,
        text="一键打包（推荐）",
        bg=owner.theme_panel_bg,
        fg="#DDEBFF",
        font=getattr(owner, "font_ui_bold", owner.font_ui),
        anchor="w",
    ).pack(fill=tk.X)
    tk.Label(
        quick_box,
        text=f"软件名称：{default_app_name}\n输出路径：{default_output_path}\n图标：{default_icon_path or '默认 logo.ico（若存在）'}",
        bg=owner.theme_panel_bg,
        fg=owner.theme_toolbar_fg,
        font=owner.font_ui,
        justify="left",
        anchor="w",
        pady=8,
    ).pack(fill=tk.X)

    adv = advanced_page
    label_style = {"bg": owner.theme_toolbar_bg, "fg": owner.theme_toolbar_fg, "font": owner.font_ui}
    input_style = {"font": owner.font_ui, "bg": owner.theme_bg, "fg": owner.theme_fg, "insertbackground": owner.theme_fg}
    tk.Label(adv, text="软件名称：", **label_style).grid(row=0, column=0, sticky="w", pady=(0, 6))
    tk.Entry(adv, textvariable=name_var, width=48, **input_style).grid(row=0, column=1, columnspan=2, sticky="we", padx=(8, 0), pady=(0, 6))
    tk.Label(adv, text="输出路径：", **label_style).grid(row=1, column=0, sticky="w", pady=6)
    tk.Entry(adv, textvariable=path_var, width=48, **input_style).grid(row=1, column=1, sticky="we", padx=(8, 8), pady=6)
    tk.Label(adv, text="图标文件：", **label_style).grid(row=2, column=0, sticky="w", pady=6)
    tk.Entry(adv, textvariable=icon_var, width=48, **input_style).grid(row=2, column=1, sticky="we", padx=(8, 8), pady=6)

    mode_frame = tk.Frame(adv, bg=owner.theme_toolbar_bg)
    mode_frame.grid(row=3, column=1, columnspan=2, sticky="w", padx=(8, 0), pady=(8, 2))
    tk.Label(adv, text="运行模式：", **label_style).grid(row=3, column=0, sticky="nw", pady=(8, 2))
    tk.Radiobutton(
        mode_frame, text="代码黑框版（调试）", variable=run_mode_var, value="console",
        bg=owner.theme_toolbar_bg, fg=owner.theme_toolbar_fg, selectcolor=owner.theme_panel_bg,
        activebackground=owner.theme_toolbar_bg, activeforeground=owner.theme_toolbar_fg, font=owner.font_ui,
    ).pack(anchor="w")
    tk.Radiobutton(
        mode_frame, text="纯净窗口版（发布）", variable=run_mode_var, value="windowed",
        bg=owner.theme_toolbar_bg, fg=owner.theme_toolbar_fg, selectcolor=owner.theme_panel_bg,
        activebackground=owner.theme_toolbar_bg, activeforeground=owner.theme_toolbar_fg, font=owner.font_ui,
    ).pack(anchor="w")

    def _browse_output_path():
        selected = filedialog.asksaveasfilename(
            title="选择导出 EXE 路径",
            parent=window,
            initialdir=owner.workspace_dir,
            initialfile=f"{owner._sanitize_export_name(name_var.get())}.exe",
            defaultextension=".exe",
            filetypes=[("Windows 可执行文件", "*.exe"), ("所有文件", "*.*")],
        )
        if selected:
            path_var.set(selected)

    def _browse_icon():
        selected = filedialog.askopenfilename(
            title="选择图标文件（.ico）",
            parent=window,
            initialdir=owner.workspace_dir,
            filetypes=[("图标文件", "*.ico"), ("所有文件", "*.*")],
        )
        if selected:
            icon_var.set(selected)

    tk.Button(adv, text="浏览...", command=_browse_output_path, font=owner.font_ui, width=10).grid(row=1, column=2, sticky="e", pady=6)
    tk.Button(adv, text="浏览...", command=_browse_icon, font=owner.font_ui, width=10).grid(row=2, column=2, sticky="e", pady=6)
    adv.grid_columnconfigure(1, weight=1)

    action = tk.Frame(main, bg=owner.theme_toolbar_bg)
    action.pack(fill=tk.X, pady=(10, 0))

    def _cancel():
        window.destroy()

    def _confirm():
        nonlocal result_value
        if mode_var.get() == "quick":
            result_value = core_build_quick_export_config(default_app_name, default_output_path, default_icon_path)
            window.destroy()
            return

        candidate = build_advanced_export_config_func(
            name_var.get(),
            path_var.get(),
            icon_var.get(),
            run_mode_var.get(),
            default_output_dir,
            default_file_name,
        )
        icon_path = candidate.get("图标路径")
        if icon_path and not os.path.isfile(icon_path):
            messagebox.showwarning("图标无效", "图标文件不存在，请重新选择。", parent=window)
            return
        result_value = candidate
        window.destroy()

    tk.Button(action, text="取消", command=_cancel, font=owner.font_ui, width=10).pack(side=tk.RIGHT)
    tk.Button(
        action,
        text="开始打包",
        command=_confirm,
        font=owner.font_ui,
        width=12,
        bg="#1E7BC8",
        fg="#FFFFFF",
    ).pack(side=tk.RIGHT, padx=(0, 8))

    _switch_mode("quick")
    window.bind("<Escape>", lambda _e: _cancel())
    window.bind("<Return>", lambda _e: _confirm())
    _center_dialog(owner, window, main, min_width=920, min_height=500)
    owner.root.wait_window(window)
    return result_value


def export_precheck_and_confirm(
    owner,
    source_entry: str | None,
    package_config: dict[str, Any],
    preflight_checker: Callable[[str | None, dict[str, Any], str], tuple[list[str], list[str]]],
    format_numbered_messages_func: Callable[[list[str]], str],
    build_confirmation_text_func: Callable[[dict[str, Any], str | None, str], str],
) -> str | None:
    output_path = os.path.abspath(os.path.expanduser(package_config["输出路径"]))
    errors, warnings = preflight_checker(source_entry, package_config, output_path)
    if errors:
        error_text = format_numbered_messages_func(errors)
        messagebox.showerror("无法开始打包", f"导出前检查未通过：\n\n{error_text}", parent=owner.root)
        return None
    if warnings:
        warning_text = format_numbered_messages_func(warnings)
        if not messagebox.askyesno("导出前提醒", f"发现以下风险：\n\n{warning_text}\n\n是否继续打包？", parent=owner.root):
            return None
    if os.path.exists(output_path):
        if not messagebox.askyesno("确认覆盖", f"目标文件已存在：\n{output_path}\n\n是否覆盖？", parent=owner.root):
            return None

    return output_path


def start_export_packaging_task(
    owner,
    source_code: str,
    source_entry: str | None,
    source_dir: str | None,
    package_config: dict[str, Any],
    output_path: str,
) -> None:
    owner._clear_output_console(keep_intro=True)
    owner.print_output(
        "=============================\n"
        + f"开始打包 EXE（{package_config['模式标题']}）\n"
        + "============================="
    )

    mode_title = str(package_config.get("模式标题") or "").strip()
    hide_console = bool(package_config.get("隐藏黑框"))
    if mode_title == "一键打包":
        # Quick export should always be production-like: no console window.
        hide_console = True
    owner.print_output(
        f"[配置] 运行模式：{'纯净窗口版（无黑窗）' if hide_console else '代码黑框版（调试）'}"
    )

    def print_progress(text):
        line = str(text or "")
        if line.startswith("打包成功："):
            return
        owner.root.after(0, lambda t=line: owner.print_output(t))

    def _open_output_folder(exe_path: str) -> None:
        folder = os.path.dirname(os.path.abspath(exe_path))
        if not folder:
            return
        try:
            if os.name == "nt":
                os.startfile(folder)  # type: ignore[attr-defined]
                return
            opener = "open" if sys.platform == "darwin" else "xdg-open"
            subprocess.Popen([opener, folder])
        except Exception as exc:
            owner.print_output(f"[WARN] Packaging succeeded, but cannot open output folder: {folder} ({exc})")

    def run_packaging():
        original_dir = os.getcwd()
        temp_entry = None
        try:
            if not source_entry:
                temp_entry = os.path.join(tempfile.gettempdir(), "_易码源码编译缓存.ym")
                with open(temp_entry, "w", encoding="utf-8") as f:
                    f.write(source_code)
                package_entry = temp_entry
            else:
                package_entry = source_entry

            os.chdir(source_dir or owner.workspace_dir)
            from 易码打包工具 import 编译并打包

            final_path = 编译并打包(
                package_entry,
                package_config["图标路径"],
                hide_console,
                print_progress,
                package_config["软件名称"],
                source_dir or owner.workspace_dir,
            )
            final_abs = os.path.abspath(final_path)
            target_abs = os.path.abspath(output_path)

            if os.path.normcase(final_abs) != os.path.normcase(target_abs):
                os.makedirs(os.path.dirname(target_abs), exist_ok=True)
                if os.path.exists(target_abs):
                    os.remove(target_abs)
                shutil.move(final_abs, target_abs)
                final_abs = target_abs

            owner.root.after(0, lambda p=final_abs: owner.print_output(f"打包成功：{p}"))
            owner.root.after(0, lambda p=final_abs: messagebox.showinfo("打包完成", f"可执行文件已生成：\n{p}"))
            owner.root.after(0, lambda p=final_abs: _open_output_folder(p))
        except Exception as e:
            owner.root.after(0, lambda msg=str(e): messagebox.showerror("打包失败", msg))
        finally:
            try:
                os.chdir(original_dir)
            except Exception:
                pass
            if temp_entry and os.path.isfile(temp_entry):
                try:
                    os.remove(temp_entry)
                except Exception:
                    pass

    threading.Thread(target=run_packaging, daemon=True).start()


def export_exe(owner):
    editor = owner._get_current_editor()
    tab_id = owner._get_current_tab_id()
    if not editor or not tab_id or tab_id not in owner.tabs_data:
        return

    source_code = editor.get("1.0", "end-1c")
    if not source_code.strip():
        messagebox.showwarning("无法打包", "代码是空的，先写点啥吧！")
        return

    current_filepath = owner.tabs_data[tab_id]["filepath"]
    if owner.tabs_data[tab_id].get("dirty"):
        if not owner.save_file(show_message=False):
            messagebox.showwarning("打包取消", "请先保存当前文件后再打包。")
            return
        current_filepath = owner.tabs_data[tab_id]["filepath"]

    source_entry, source_dir, raw_app_name = owner._解析导出入口(current_filepath)

    defaults = core_build_export_defaults(
        workspace_dir=owner.workspace_dir,
        source_dir=source_dir,
        raw_app_name=raw_app_name,
        tool_root_dir=owner.tool_root_dir,
    )

    package_config = export_config_pages_dialog(owner, defaults, core_build_advanced_export_config)

    if not package_config:
        return

    output_path = export_precheck_and_confirm(
        owner,
        source_entry,
        package_config,
        preflight_checker=owner._导出前置检查,
        format_numbered_messages_func=core_format_numbered_messages,
        build_confirmation_text_func=core_build_export_confirmation_text,
    )
    if not output_path:
        return

    start_export_packaging_task(owner, source_code, source_entry, source_dir, package_config, output_path)
