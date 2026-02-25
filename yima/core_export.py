"""Core export/path/config helper functions."""

from __future__ import annotations

import importlib.util
import glob
import os
import time
from typing import Any, Callable

from .core_completion import extract_import_alias_map


def _module_exists(module_name: str, module_exists_checker: Callable[[str], bool] | None = None) -> bool:
    try:
        if module_exists_checker is not None:
            return bool(module_exists_checker(str(module_name or "").strip()))
        return importlib.util.find_spec(str(module_name or "").strip()) is not None
    except Exception:
        return False


RUNTIME_CORE_REQUIRED_FILES = (
    "解释器.py",
    "语法分析.py",
    "词法分析.py",
    "语法树.py",
    "错误.py",
    "信号.py",
    "环境.py",
)


def _runtime_core_complete(runtime_core_dir: str) -> bool:
    if not os.path.isdir(runtime_core_dir):
        return False
    for filename in RUNTIME_CORE_REQUIRED_FILES:
        source_path = os.path.join(runtime_core_dir, filename)
        if os.path.isfile(source_path):
            continue
        stem = os.path.splitext(filename)[0]
        pyc_candidates = glob.glob(os.path.join(runtime_core_dir, "__pycache__", f"{stem}.cpython-*.pyc"))
        if not pyc_candidates:
            return False
    return True


def sanitize_export_name(name: str, default_name: str = "易码生成软件") -> str:
    cleaned = str(name or "").strip()
    if not cleaned:
        cleaned = default_name
    for bad_char in '<>:"/\\|?*':
        cleaned = cleaned.replace(bad_char, "_")
    cleaned = cleaned.strip(" .")
    return cleaned if cleaned else default_name


def directory_in_workspace(workspace_dir: str, target_dir: str) -> bool:
    try:
        workspace = os.path.abspath(workspace_dir or "")
        target = os.path.abspath(target_dir or "")
        if not workspace or not target:
            return False
        return os.path.commonpath([workspace, target]) == workspace
    except Exception:
        return False


def nearest_main_entry(current_file_path: str, workspace_dir: str) -> tuple[str | None, str | None]:
    if not current_file_path:
        return (None, None)
    try:
        current_dir = os.path.dirname(os.path.abspath(current_file_path))
    except Exception:
        return (None, None)

    while True:
        if not directory_in_workspace(workspace_dir, current_dir):
            break
        candidate = os.path.join(current_dir, "主程序.ym")
        if os.path.isfile(candidate):
            return (os.path.abspath(candidate), current_dir)
        parent = os.path.dirname(current_dir)
        if parent == current_dir:
            break
        current_dir = parent
    return (None, None)


def resolve_export_entry(current_file_path: str, workspace_dir: str) -> tuple[str | None, str, str]:
    current_abs = None
    if current_file_path and current_file_path != "未命名代码.ym" and os.path.isfile(current_file_path):
        current_abs = os.path.abspath(current_file_path)

    if current_abs:
        if os.path.basename(current_abs) == "主程序.ym":
            project_dir = os.path.dirname(current_abs)
            app_name = os.path.basename(os.path.abspath(project_dir)) or "易码生成软件"
            return (current_abs, project_dir, app_name)

        nearest_entry, project_dir = nearest_main_entry(current_abs, workspace_dir)
        if nearest_entry and project_dir:
            workspace_root = os.path.normcase(os.path.abspath(workspace_dir or ""))
            project_dir_abs = os.path.normcase(os.path.abspath(project_dir))
            current_dir_abs = os.path.normcase(os.path.dirname(current_abs))
            if not (project_dir_abs == workspace_root and current_dir_abs != project_dir_abs):
                app_name = os.path.basename(os.path.abspath(project_dir)) or "易码生成软件"
                return (nearest_entry, project_dir, app_name)

        file_dir = os.path.dirname(current_abs)
        app_name = os.path.splitext(os.path.basename(current_abs))[0] or "易码生成软件"
        return (current_abs, file_dir, app_name)

    workspace_entry = os.path.join(workspace_dir, "主程序.ym")
    if os.path.isfile(workspace_entry):
        app_name = os.path.basename(os.path.abspath(workspace_dir)) or "易码生成软件"
        return (workspace_entry, workspace_dir, app_name)

    return (None, workspace_dir, "易码生成软件")


def export_preflight_check(
    source_entry: str | None,
    package_config: dict[str, Any] | None,
    output_path: str,
    workspace_dir: str,
    tool_root_dir: str,
    sanitize_export_name_func: Callable[[str], str] | None = None,
    builtin_module_names: set[str] | None = None,
    module_locator: Callable[[str], str | None] | None = None,
    python_module_exists: Callable[[str], bool] | None = None,
) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []

    entry_path = os.path.abspath(str(source_entry or "").strip()) if source_entry else ""
    if not entry_path or not os.path.isfile(entry_path):
        errors.append("入口脚本不存在，请先保存并确认主程序路径。")

    if not workspace_dir or not os.path.isdir(workspace_dir):
        errors.append("当前项目目录无效，请先打开一个有效项目目录。")

    tool_root = os.path.abspath(str(tool_root_dir or ""))
    packaging_tool_path = os.path.join(tool_root, "易码打包工具.py")
    runtime_core_dir = os.path.join(tool_root, "yima")
    packaging_tool_ready = os.path.isfile(packaging_tool_path) or _module_exists("易码打包工具", python_module_exists)
    runtime_core_ready = _runtime_core_complete(runtime_core_dir)
    if not packaging_tool_ready:
        errors.append("缺少打包工具文件：易码打包工具.py")
    if not runtime_core_ready:
        errors.append(
            "缺少完整运行时核心目录：yima（需包含解释器.py、语法分析.py、词法分析.py 等核心文件）"
        )

    output_abs = os.path.abspath(os.path.expanduser(str(output_path or "").strip()))
    output_dir = os.path.dirname(output_abs) or workspace_dir
    if not output_abs.lower().endswith(".exe"):
        errors.append("输出路径必须以 .exe 结尾。")
    try:
        os.makedirs(output_dir, exist_ok=True)
    except Exception as e:
        errors.append(f"无法创建输出目录：{output_dir}（{e}）")

    if os.path.isdir(output_dir):
        probe_file = os.path.join(output_dir, f".yima_export_probe_{int(time.time() * 1000)}.tmp")
        try:
            with open(probe_file, "w", encoding="utf-8") as f:
                f.write("ok")
            os.remove(probe_file)
        except Exception as e:
            errors.append(f"输出目录不可写：{output_dir}（{e}）")

    icon_path = str((package_config or {}).get("图标路径") or "").strip()
    if icon_path:
        icon_abs = os.path.abspath(os.path.expanduser(icon_path))
        if not os.path.isfile(icon_abs):
            errors.append(f"图标文件不存在：{icon_abs}")
        elif not icon_abs.lower().endswith(".ico"):
            warnings.append("图标建议使用 .ico 格式，其他格式在部分系统上可能不稳定。")

    app_name = str((package_config or {}).get("软件名称") or "").strip()
    sanitize_func = sanitize_export_name_func or sanitize_export_name
    if not app_name:
        errors.append("软件名称不能为空。")
    elif app_name != sanitize_func(app_name):
        warnings.append("软件名称包含非法字符，实际文件名会被自动清理。")

    try:
        if entry_path and os.path.isfile(entry_path):
            with open(entry_path, "r", encoding="utf-8") as f:
                entry_source = f.read()
            import_alias_map = extract_import_alias_map(entry_source)
            builtin_names = set(builtin_module_names or set())
            missing_modules = []
            for module_name in sorted(set(import_alias_map.values())):
                name = str(module_name or "").strip()
                if not name or name in builtin_names:
                    continue
                local_module_path = module_locator(name) if module_locator else None
                if local_module_path:
                    continue
                try:
                    if python_module_exists:
                        exists = bool(python_module_exists(name))
                    else:
                        exists = importlib.util.find_spec(name) is not None
                except Exception:
                    exists = False
                if exists:
                    continue
                missing_modules.append(name)
            if missing_modules:
                errors.append("入口引入中存在无法解析的模块：" + "、".join(missing_modules))
    except Exception as e:
        warnings.append(f"未完成依赖预扫描：{e}")

    return errors, warnings


def build_export_defaults(
    workspace_dir: str,
    source_dir: str | None,
    raw_app_name: str,
    tool_root_dir: str,
) -> dict[str, str]:
    app_name = sanitize_export_name(raw_app_name)
    base_dir = str(source_dir or workspace_dir or ".")
    output_dir = os.path.join(base_dir, "易码_成品软件")
    output_path = os.path.join(output_dir, f"{app_name}.exe")

    icon_candidate = os.path.join(str(tool_root_dir or ""), "logo.ico")
    icon_path = icon_candidate if os.path.isfile(icon_candidate) else ""
    return {
        "软件名称": app_name,
        "输出目录": output_dir,
        "输出路径": output_path,
        "图标路径": icon_path,
        "默认软件文件名": f"{app_name}.exe",
    }


def normalize_export_output_path(
    raw_output_path: str,
    app_name: str,
    default_output_dir: str,
    default_file_name: str,
) -> str:
    output_path = str(raw_output_path or "").strip()
    if not output_path:
        return os.path.join(default_output_dir, f"{app_name}.exe")

    output_path = os.path.abspath(os.path.expanduser(output_path))
    if os.path.isdir(output_path) or output_path.endswith(("\\", "/")):
        output_path = os.path.join(output_path, f"{app_name}.exe")
    if not output_path.lower().endswith(".exe"):
        output_path += ".exe"

    current_name = os.path.basename(output_path)
    if current_name.lower() == str(default_file_name or "").lower():
        output_dir = os.path.dirname(output_path) or default_output_dir
        output_path = os.path.join(output_dir, f"{app_name}.exe")
    return output_path


def normalize_optional_export_icon_path(raw_icon_path: str) -> str | None:
    icon_value = str(raw_icon_path or "").strip()
    return os.path.abspath(os.path.expanduser(icon_value)) if icon_value else None


def build_quick_export_config(default_app_name: str, default_output_path: str, default_icon_path: str) -> dict[str, Any]:
    return {
        "软件名称": str(default_app_name or ""),
        "输出路径": str(default_output_path or ""),
        "图标路径": str(default_icon_path or "").strip() or None,
        "隐藏黑框": True,
        "模式文本": "纯净窗口版（不显示黑框）",
        "模式标题": "一键打包",
    }


def build_advanced_export_config(
    raw_name: str,
    raw_output_path: str,
    raw_icon_path: str,
    mode_value: str,
    default_output_dir: str,
    default_file_name: str,
) -> dict[str, Any]:
    app_name = sanitize_export_name(raw_name)
    output_path = normalize_export_output_path(
        raw_output_path,
        app_name,
        default_output_dir,
        default_file_name,
    )
    icon_path = normalize_optional_export_icon_path(raw_icon_path)
    hide_console = str(mode_value or "").strip() == "windowed"
    mode_text = "纯净窗口版（不显示黑框）" if hide_console else "代码黑框版（带日志窗口）"
    return {
        "软件名称": app_name,
        "输出路径": output_path,
        "图标路径": icon_path,
        "隐藏黑框": hide_console,
        "模式文本": mode_text,
        "模式标题": "高级导出",
    }


def format_numbered_messages(items) -> str:
    return "\n".join(f"{i}. {item}" for i, item in enumerate(list(items or []), 1))


def build_export_confirmation_text(package_config: dict[str, Any], source_entry: str | None, output_path: str) -> str:
    cfg = dict(package_config or {})
    entry_name = os.path.basename(str(source_entry or "").strip()) if source_entry else "当前编辑内容"
    icon_text = str(cfg.get("图标路径") or "").strip() or "默认 logo.ico（如存在）"
    return (
        f"模式：{cfg.get('模式标题', '')}\n"
        + f"入口：{entry_name}\n"
        + f"软件名：{cfg.get('软件名称', '')}\n"
        + f"输出路径：{str(output_path or '')}\n"
        + f"图标：{icon_text}\n"
        + f"运行模式：{cfg.get('模式文本', '')}\n\n"
        + "确认开始打包吗？"
    )



__all__ = [
    "sanitize_export_name",
    "directory_in_workspace",
    "nearest_main_entry",
    "resolve_export_entry",
    "export_preflight_check",
    "build_export_defaults",
    "normalize_export_output_path",
    "normalize_optional_export_icon_path",
    "build_quick_export_config",
    "build_advanced_export_config",
    "format_numbered_messages",
    "build_export_confirmation_text",
]
