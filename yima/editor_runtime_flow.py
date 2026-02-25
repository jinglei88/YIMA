"""Runtime domain: run flow + output console flow."""

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

import builtins
import io
import os
import sys
import tkinter as tk

from 易码 import 执行源码


class UserCancelledInput(Exception):
    """Raised when user cancels interactive input dialog."""


def print_output(owner, text, is_error=False, notify=True):
    try:
        owner.output.config(state=tk.NORMAL)
        content = str(text or "")
        if is_error or content.startswith("❌"):
            owner.output.insert(tk.END, content + "\n", "ConsoleError")
        else:
            owner.output.insert(tk.END, content + "\n")
        owner.output.see(tk.END)
        owner.output.config(state=tk.DISABLED)
        if notify and hasattr(owner, "_mark_feedback_tab"):
            owner._mark_feedback_tab("console", active=True)
    except tk.TclError:
        pass


def write_output_console_intro(owner):
    # 启动时的控制台欢迎文案不计为“未读消息”，避免默认红点。
    print_output(owner, "========================================", notify=False)
    print_output(owner, "【易码调试控制台】", notify=False)
    print_output(owner, "作者：景磊", notify=False)
    print_output(owner, "联系 QQ：95842972 / 97777315", notify=False)
    print_output(owner, "========================================", notify=False)


def clear_output_console(owner, keep_intro=True):
    try:
        owner.output.config(state=tk.NORMAL)
        owner.output.delete("1.0", tk.END)
        owner.output.config(state=tk.DISABLED)
    except tk.TclError:
        return
    if hasattr(owner, "_clear_feedback_tab"):
        owner._clear_feedback_tab("console")
    if keep_intro:
        write_output_console_intro(owner)


def _prompt_input_dialog(owner, prompt_text: str = ""):
    dialog = tk.Toplevel(owner.root)
    dialog.title("易码需要你的回答")
    dialog.configure(bg=owner.theme_sidebar_bg)
    dialog.resizable(False, False)
    dialog.transient(owner.root)

    win_w = int(420 * owner.dpi_scale)
    win_h = int(210 * owner.dpi_scale)
    x = owner.root.winfo_x() + (owner.root.winfo_width() // 2) - (win_w // 2)
    y = owner.root.winfo_y() + (owner.root.winfo_height() // 2) - (win_h // 2)
    dialog.geometry(f"{win_w}x{win_h}+{x}+{y}")

    result: list[str | None] = [None]

    def confirm(*_):
        result[0] = input_entry.get()
        dialog.destroy()

    def cancel(*_):
        result[0] = None
        dialog.destroy()

    dialog.protocol("WM_DELETE_WINDOW", cancel)

    container = tk.Frame(dialog, bg=owner.theme_sidebar_bg)
    container.pack(fill=tk.BOTH, expand=True, padx=16, pady=14)

    text = str(prompt_text or "").strip() or "请输入："
    tk.Label(
        container,
        text=text,
        font=("Microsoft YaHei", 12, "bold"),
        bg=owner.theme_sidebar_bg,
        fg=owner.theme_fg,
        anchor="w",
        justify="left",
    ).pack(fill=tk.X, pady=(0, 8))

    input_entry = tk.Entry(
        container,
        font=("Microsoft YaHei", 12),
        bg=owner.theme_bg,
        fg=owner.theme_fg,
        insertbackground="#CCCCCC",
        relief="flat",
        highlightthickness=1,
        highlightbackground=owner.theme_sash,
        highlightcolor="#0E639C",
    )
    input_entry.pack(fill=tk.X, ipady=5, pady=(0, 12))

    button_row = tk.Frame(container, bg=owner.theme_sidebar_bg)
    button_row.pack(fill=tk.X)

    tk.Button(
        button_row,
        text="OK",
        font=owner.font_ui,
        command=confirm,
        bg=owner.theme_toolbar_bg,
        fg=owner.theme_fg,
        activebackground="#505050",
        activeforeground="#FFFFFF",
        relief="flat",
        borderwidth=0,
        cursor="hand2",
        padx=14,
        pady=5,
    ).pack(side=tk.RIGHT, padx=(8, 0))

    tk.Button(
        button_row,
        text="Cancel",
        font=owner.font_ui,
        command=cancel,
        bg=owner.theme_toolbar_bg,
        fg=owner.theme_fg,
        activebackground="#505050",
        activeforeground="#FFFFFF",
        relief="flat",
        borderwidth=0,
        cursor="hand2",
        padx=14,
        pady=5,
    ).pack(side=tk.RIGHT)

    dialog.bind("<Return>", confirm)
    dialog.bind("<Escape>", cancel)

    input_entry.focus_set()
    dialog.grab_set()
    try:
        owner.root.wait_window(dialog)
    except tk.TclError:
        return None
    return result[0]


def run_code(owner):
    editor = owner._get_current_editor()
    if not editor:
        try:
            owner.print_output("提示：当前没有可运行的代码标签页。", notify=True)
        except Exception:
            pass
        if hasattr(owner, "status_main_var"):
            try:
                owner.status_main_var.set("运行取消：未找到代码标签页")
            except Exception:
                pass
        return

    tab_id = owner._get_current_tab_id()
    filepath = owner.tabs_data[tab_id]["filepath"]
    script_path = filepath if filepath and os.path.isfile(filepath) else None
    original_cwd = os.getcwd()
    if script_path:
        os.chdir(os.path.dirname(os.path.abspath(script_path)))

    owner._clear_output_console(keep_intro=True)

    code = editor.get("1.0", "end-1c")
    if not code.strip():
        owner.print_output("提示：当前标签页为空，无法运行。")
        owner.status_main_var.set("运行取消：当前标签页为空")
        if script_path:
            os.chdir(original_cwd)
        return

    owner._run_live_diagnose()

    old_stdout = sys.stdout
    sys.stdout = io.StringIO()

    old_input = builtins.input

    def gui_input(prompt=""):
        ans = _prompt_input_dialog(owner, prompt)
        if ans is None:
            raise UserCancelledInput()
        return ans

    builtins.input = gui_input

    output_str = ""
    try:
        执行源码(code, interactive=False, 源码路径=script_path)
        output_str = sys.stdout.getvalue()
        if not output_str.strip():
            output_str = "代码已执行完成，但没有输出。可使用【显示】语句输出结果。"
    except KeyboardInterrupt:
        output_str = "⚠️ 运行被中断（KeyboardInterrupt）。"
    except UserCancelledInput:
        output_str = "⚠️ 你已取消输入，本次运行已停止。"
    except Exception as e:
        output_str = f"❌ 运行报错了: {e}"
    finally:
        sys.stdout = old_stdout
        builtins.input = old_input
        if script_path:
            os.chdir(original_cwd)

    owner.print_output(output_str, is_error=output_str.startswith("❌"))
    if output_str.startswith("⚠️"):
        owner.status_main_var.set("运行已取消")
    else:
        owner.status_main_var.set("运行完成")
