"""Export flow helpers extracted from 易码编辑器.py."""

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
import tempfile
import threading
from tkinter import messagebox
from typing import Any, Callable


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

    confirm_text = build_confirmation_text_func(package_config, source_entry, output_path)
    if not messagebox.askyesno("确认导出", confirm_text, parent=owner.root):
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

    def print_progress(text):
        line = str(text or "")
        # 打包工具内部会先打印一次“中间产物”成功路径，最终路径由编辑器统一打印，避免重复误导。
        if line.startswith("打包成功："):
            return
        owner.root.after(0, lambda t=line: owner.print_output(t))

    def run_packaging():
        original_dir = os.getcwd()
        temp_entry = None
        try:
            if not source_entry:
                temp_entry = os.path.join(tempfile.gettempdir(), "_易码源码编译缓冲.ym")
                with open(temp_entry, "w", encoding="utf-8") as f:
                    f.write(source_code)
                package_entry = temp_entry
            else:
                package_entry = source_entry

            os.chdir(source_dir or owner.workspace_dir)
            from 易码打包工具 import 编译并打包

            final_path = 编译并打包(
                package_entry,
                图标路径=package_config["图标路径"],
                隐藏黑框=package_config["隐藏黑框"],
                进度打字机=print_progress,
                软件名称=package_config["软件名称"],
                源码目录=source_dir or owner.workspace_dir,
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
