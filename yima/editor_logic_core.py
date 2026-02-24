"""Core editor logic helpers extracted from 易码编辑器.py.

These functions are UI-agnostic and can be reused by scripts/tests.
"""

from __future__ import annotations
import importlib.util
import os
import re
import time
from typing import Any, Callable


BUILTIN_WORDS = [
    "新列表",
    "加入",
    "插入",
    "长度",
    "删除",
    "转数字",
    "转文字",
    "取随机数",
    "所有键",
    "所有值",
    "存在",
    "截取",
    "查找",
    "替换",
    "分割",
    "去空格",
    "包含",
    "读文件",
    "写文件",
    "追加文件",
    "文件存在",
    "目录存在",
    "创建目录",
    "列出目录",
    "删除文件",
    "删除目录",
    "复制文件",
    "移动文件",
    "重命名",
    "遍历文件",
    "复制目录",
    "压缩目录",
    "解压缩",
    "哈希文本",
    "哈希文件",
    "下载文件",
    "匹配文件",
    "文件信息",
    "目录大小",
    "格式时间",
    "解析时间",
    "写日志",
    "读日志",
    "睡眠",
    "拼路径",
    "绝对路径",
    "当前目录",
    "读环境变量",
    "写环境变量",
    "执行命令",
    "解析JSON",
    "生成JSON",
    "读JSON",
    "写JSON",
    "读CSV",
    "写CSV",
    "读INI",
    "写INI",
    "发起请求",
    "发GET",
    "发POST",
    "读响应JSON",
    "发GET_JSON",
    "发POST_JSON",
    "打开数据库",
    "执行SQL",
    "查询SQL",
    "开始事务",
    "提交事务",
    "回滚事务",
    "关闭数据库",
    "排序",
    "倒序",
    "去重",
    "合并",
    "最大值",
    "最小值",
    "绝对值",
    "四舍五入",
    "现在时间",
    "时间戳",
    "类型",
    "显示",
    "输入",
    "建窗口",
    "加文字",
    "加输入框",
    "加按钮",
    "读输入",
    "改文字",
    "弹窗",
    "弹窗输入",
    "打开界面",
    "加表格",
    "表格加行",
    "表格清空",
    "表格所有行",
    "表格选中行",
    "表格选中序号",
    "表格删行",
    "表格改行",
    "画布",
    "标题",
    "图标",
    "向前走",
    "向后走",
    "左转",
    "右转",
    "抬笔",
    "落笔",
    "画笔颜色",
    "背景颜色",
    "去",
    "笔粗",
    "画圆",
    "停一下",
    "定格",
    "速度",
    "隐藏画笔",
    "关闭动画",
    "刷新画面",
    "清除",
    "写字",
    "开始监听",
    "绑定按键",
    "计算距离",
    "当前X",
    "当前Y",
]


BUILTIN_MODULE_EXPORTS = {
    "文件管理": ["读文件", "写文件", "追加文件"],
    "系统工具": [
        "文件存在",
        "目录存在",
        "创建目录",
        "列出目录",
        "删除文件",
        "删除目录",
        "复制文件",
        "移动文件",
        "重命名",
        "遍历文件",
        "复制目录",
        "压缩目录",
        "解压缩",
        "哈希文本",
        "哈希文件",
        "下载文件",
        "匹配文件",
        "文件信息",
        "目录大小",
        "格式时间",
        "解析时间",
        "写日志",
        "读日志",
        "睡眠",
        "拼路径",
        "绝对路径",
        "当前目录",
        "读环境变量",
        "写环境变量",
        "执行命令",
    ],
    "数据工具": ["解析JSON", "生成JSON", "读JSON", "写JSON", "读CSV", "写CSV", "读INI", "写INI"],
    "网络请求": ["发起请求", "发GET", "发POST", "读响应JSON", "发GET_JSON", "发POST_JSON"],
    "本地数据库": ["打开数据库", "执行SQL", "查询SQL", "关闭数据库", "开始事务", "提交事务", "回滚事务"],
    "图形界面": [
        "建窗口",
        "加文字",
        "加输入框",
        "读输入",
        "改文字",
        "加按钮",
        "弹窗",
        "弹窗输入",
        "打开界面",
        "加表格",
        "表格加行",
        "表格清空",
        "表格所有行",
        "表格选中行",
        "表格选中序号",
        "表格删行",
        "表格改行",
    ],
    "画板": [
        "画布",
        "标题",
        "图标",
        "向前走",
        "向后走",
        "左转",
        "右转",
        "抬笔",
        "落笔",
        "画笔颜色",
        "背景颜色",
        "去",
        "笔粗",
        "画圆",
        "停一下",
        "定格",
        "速度",
        "隐藏画笔",
        "关闭动画",
        "刷新画面",
        "清除",
        "写字",
        "开始监听",
        "绑定按键",
        "计算距离",
        "当前X",
        "当前Y",
    ],
}


AUTOCOMPLETE_SOURCE_PRIORITY = {
    "function": 0,
    "blueprint": 0,
    "variable": 0,
    "alias": 0,
    "module": 0,
    "member": 1,
    "member_func": 1,
    "member_blueprint": 1,
    "member_class": 1,
    "member_var": 1,
    "member_alias": 1,
    "imported": 1,
    "imported_func": 1,
    "imported_blueprint": 1,
    "imported_class": 1,
    "imported_var": 1,
    "imported_alias": 1,
    "builtin": 2,
    "builtin_func": 2,
    "keyword": 3,
    "snippet": 4,
}


IMPORT_SOURCE_GROUP = {
    "function": ("current", "当前文件"),
    "blueprint": ("current", "当前文件"),
    "variable": ("current", "当前文件"),
    "alias": ("current", "当前文件"),
    "module": ("current", "当前文件"),
    "member": ("imported", "已引入"),
    "member_func": ("imported", "已引入"),
    "member_blueprint": ("imported", "已引入"),
    "member_class": ("imported", "已引入"),
    "member_var": ("imported", "已引入"),
    "member_alias": ("imported", "已引入"),
    "imported": ("imported", "已引入"),
    "imported_func": ("imported", "已引入"),
    "imported_blueprint": ("imported", "已引入"),
    "imported_class": ("imported", "已引入"),
    "imported_var": ("imported", "已引入"),
    "imported_alias": ("imported", "已引入"),
    "builtin": ("builtin", "内置能力"),
    "builtin_func": ("builtin", "内置能力"),
    "keyword": ("keyword", "关键字"),
    "snippet": ("snippet", "模板"),
}


def builtin_word_catalog() -> list[str]:
    return list(BUILTIN_WORDS)


def builtin_module_exports(builtin_words: list[str] | None = None) -> dict[str, list[str]]:
    exports = {name: list(items) for name, items in BUILTIN_MODULE_EXPORTS.items()}
    exports["魔法生态库"] = sorted(list(builtin_words or []))
    return exports


def autocomplete_match(candidate: str, prefix: str, fuzzy_enabled: bool = False) -> bool:
    if not candidate:
        return False
    if not prefix:
        return True
    text = str(candidate or "")
    needle = str(prefix or "")
    if text == needle:
        return True
    if text.startswith(needle):
        return True
    if fuzzy_enabled and len(needle) >= 2:
        return needle in text
    return False


def autocomplete_source_priority(source: str) -> int:
    return AUTOCOMPLETE_SOURCE_PRIORITY.get(str(source or "").strip(), 9)


def autocomplete_source_group(source: str) -> tuple[str, str]:
    return IMPORT_SOURCE_GROUP.get(str(source or "").strip(), ("other", "其他"))


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
    if not os.path.isfile(packaging_tool_path):
        errors.append("缺少打包工具文件：易码打包工具.py")
    if not os.path.isdir(runtime_core_dir):
        errors.append("缺少运行时核心目录：yima")

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


def line_indent_width(line_text: str) -> int:
    line = str(line_text or "").replace("\t", "    ")
    return len(line) - len(line.lstrip(" "))


def split_signature_params(signature: str) -> list[str]:
    signature_text = str(signature or "").strip()
    if not signature_text.startswith("(") or not signature_text.endswith(")"):
        return []
    content = signature_text[1:-1]
    if not content.strip():
        return []

    parts = []
    current = []
    paren_level = 0
    bracket_level = 0
    brace_level = 0
    string_quote = ""
    escaped = False

    for ch in content:
        if string_quote:
            current.append(ch)
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == string_quote:
                string_quote = ""
            continue

        if ch in ("'", '"'):
            string_quote = ch
            current.append(ch)
            continue
        if ch == "(":
            paren_level += 1
        elif ch == ")" and paren_level > 0:
            paren_level -= 1
        elif ch == "[":
            bracket_level += 1
        elif ch == "]" and bracket_level > 0:
            bracket_level -= 1
        elif ch == "{":
            brace_level += 1
        elif ch == "}" and brace_level > 0:
            brace_level -= 1
        if ch == "," and paren_level == 0 and bracket_level == 0 and brace_level == 0:
            parts.append("".join(current).strip())
            current = []
            continue
        current.append(ch)

    if current:
        parts.append("".join(current).strip())
    return [part for part in parts if part != ""]


def highlight_current_signature_param(signature: str, param_index: Any) -> tuple[str, int, int, str]:
    signature_text = str(signature or "").strip()
    if not signature_text:
        return "()", 0, 0, ""

    params = split_signature_params(signature_text)
    if not params:
        return signature_text, 0, 0, ""

    try:
        idx = max(0, int(param_index) - 1)
    except Exception:
        idx = 0
    if idx >= len(params):
        idx = len(params) - 1

    current_param_name = str(params[idx] or "").strip()
    params[idx] = f"<<{params[idx]}>>"
    return "(" + ", ".join(params) + ")", idx + 1, len(params), current_param_name


def normalize_completion_signature(signature: str) -> str:
    signature_text = str(signature or "").strip()
    if not signature_text:
        return "()"
    if not (signature_text.startswith("(") and signature_text.endswith(")")):
        return "()"

    params = split_signature_params(signature_text)
    cleaned = []
    ident_pattern = re.compile(r"^[\u4e00-\u9fa5A-Za-z_][\u4e00-\u9fa5A-Za-z0-9_]*$")

    for raw_param in params:
        param = str(raw_param or "").strip()
        if not param:
            continue
        if param in {"self", "cls", "/", "*"}:
            continue
        if param.startswith("**"):
            param = param[2:].strip()
        elif param.startswith("*"):
            param = param[1:].strip()
        if ":" in param:
            param = param.split(":", 1)[0].strip()
        if "=" in param:
            param = param.split("=", 1)[0].strip()
        if not param:
            continue
        if not ident_pattern.match(param):
            return "()"
        cleaned.append(param)

    if not cleaned:
        return "()"
    return "(" + ", ".join(cleaned) + ")"


def first_argument_span_offset(call_snippet: str) -> tuple[int, int] | None:
    text = str(call_snippet or "")
    if not text.startswith("("):
        return None
    end_index = text.find(")")
    if end_index <= 1:
        return None
    comma_index = text.find(",", 1, end_index)
    arg_end = comma_index if comma_index > 0 else end_index
    if arg_end <= 1:
        return None
    return (1, arg_end)


def extract_definition_signatures(code: str, format_signature) -> tuple[dict[str, str], dict[str, str]]:
    ident_pattern = r"[\u4e00-\u9fa5A-Za-z_][\u4e00-\u9fa5A-Za-z0-9_]*"
    content = code or ""
    function_signatures: dict[str, str] = {}
    blueprint_signatures: dict[str, str] = {}

    fn_pattern = re.compile(
        rf"^\s*功能\s+({ident_pattern})\s*(?:\((.*?)\))?",
        re.MULTILINE,
    )
    bp_pattern = re.compile(
        rf"^\s*定义图纸\s+({ident_pattern})\s*(?:\((.*?)\))?",
        re.MULTILINE,
    )

    for name, params_text in fn_pattern.findall(content):
        params = [p.strip() for p in str(params_text or "").split(",") if p.strip()]
        function_signatures[str(name)] = format_signature(params)
    for name, params_text in bp_pattern.findall(content):
        params = [p.strip() for p in str(params_text or "").split(",") if p.strip()]
        blueprint_signatures[str(name)] = format_signature(params)
    return function_signatures, blueprint_signatures


def extract_blueprint_members(
    code: str,
    format_signature,
) -> tuple[dict[str, set[str]], dict[str, dict[str, str]], dict[str, dict[str, str]]]:
    ident_pattern = r"[\u4e00-\u9fa5A-Za-z_][\u4e00-\u9fa5A-Za-z0-9_]*"
    lines = (code or "").splitlines()

    members_map: dict[str, set[str]] = {}
    members_type_map: dict[str, dict[str, str]] = {}
    members_signature_map: dict[str, dict[str, str]] = {}

    bp_header_pattern = re.compile(rf"^\s*定义图纸\s+({ident_pattern})\s*(?:\((.*?)\))?")
    fn_header_pattern = re.compile(rf"^\s*功能\s+({ident_pattern})\s*(?:\((.*?)\))?")
    self_attr_pattern = re.compile(rf"^\s*它的\s+({ident_pattern})\b")

    i = 0
    while i < len(lines):
        line = lines[i]
        bp_match = bp_header_pattern.match(line)
        if not bp_match:
            i += 1
            continue

        blueprint_name = str(bp_match.group(1) or "").strip()
        if not blueprint_name:
            i += 1
            continue

        blueprint_indent = line_indent_width(line)
        members = set(members_map.get(blueprint_name, set()))
        type_table = dict(members_type_map.get(blueprint_name, {}))
        signature_table = dict(members_signature_map.get(blueprint_name, {}))

        i += 1
        while i < len(lines):
            child_line = lines[i]
            stripped = child_line.strip()
            if not stripped or stripped.startswith("#"):
                i += 1
                continue

            child_indent = line_indent_width(child_line)
            if child_indent <= blueprint_indent:
                break

            fn_match = fn_header_pattern.match(child_line)
            if fn_match:
                member_name = str(fn_match.group(1) or "").strip()
                params_text = str(fn_match.group(2) or "")
                params = [p.strip() for p in params_text.split(",") if p.strip()]
                if member_name:
                    members.add(member_name)
                    type_table[member_name] = "function"
                    signature_table[member_name] = format_signature(params)
                i += 1
                continue

            attr_match = self_attr_pattern.match(child_line)
            if attr_match:
                member_name = str(attr_match.group(1) or "").strip()
                if member_name:
                    members.add(member_name)
                    type_table[member_name] = "variable"
                i += 1
                continue

            i += 1

        members_map[blueprint_name] = members
        members_type_map[blueprint_name] = type_table
        members_signature_map[blueprint_name] = signature_table

    return members_map, members_type_map, members_signature_map


def extract_instance_map(code: str) -> dict[str, str]:
    ident_pattern = r"[\u4e00-\u9fa5A-Za-z_][\u4e00-\u9fa5A-Za-z0-9_]*"
    mapping: dict[str, str] = {}
    pattern = re.compile(
        rf"^\s*({ident_pattern})\s*=\s*造一个\s+({ident_pattern})\b",
        re.MULTILINE,
    )
    for object_name, blueprint_name in pattern.findall(code or ""):
        object_name = str(object_name or "").strip()
        blueprint_name = str(blueprint_name or "").strip()
        if object_name and blueprint_name:
            mapping[object_name] = blueprint_name
    return mapping


def extract_scope_locals(code: str, cursor_line) -> set[str]:
    ident_pattern = r"[\u4e00-\u9fa5A-Za-z_][\u4e00-\u9fa5A-Za-z0-9_]*"
    content = code or ""
    lines = content.splitlines()
    if not lines:
        return set()

    try:
        target_line = int(cursor_line or 1)
    except (TypeError, ValueError):
        target_line = 1
    target_line = max(1, min(target_line, len(lines)))

    scope_stack = []
    fn_header_pattern = re.compile(rf"^\s*功能\s+({ident_pattern})\s*(?:\((.*?)\))?")
    bp_header_pattern = re.compile(rf"^\s*定义图纸\s+({ident_pattern})\s*(?:\((.*?)\))?")

    for line_no in range(1, target_line + 1):
        line_text = lines[line_no - 1]
        stripped = line_text.strip()
        if not stripped or stripped.startswith("#"):
            continue

        indent = line_indent_width(line_text)
        while scope_stack and line_no > scope_stack[-1]["line"] and indent <= scope_stack[-1]["indent"]:
            scope_stack.pop()

        match = fn_header_pattern.match(line_text) or bp_header_pattern.match(line_text)
        if match:
            params_text = str(match.group(2) or "")
            params = [p.strip() for p in params_text.split(",") if p.strip()]
            scope_stack.append({
                "line": line_no,
                "indent": indent,
                "params": params,
            })

    if not scope_stack:
        return set()

    current_scope = scope_stack[-1]
    locals_set = set(current_scope.get("params", []))
    assign_pattern = re.compile(rf"^\s*({ident_pattern})\s*=")
    iter_pattern = re.compile(rf"^\s*遍历\b.*?\b叫做\s+({ident_pattern})\b")
    repeat_pattern = re.compile(rf"^\s*重复\b.*?\b次\s+叫做\s+({ident_pattern})\b")
    catch_pattern = re.compile(rf"^\s*如果出错\s+叫做\s+({ident_pattern})\b")

    for line_no in range(current_scope["line"] + 1, target_line + 1):
        line_text = lines[line_no - 1]
        stripped = line_text.strip()
        if not stripped or stripped.startswith("#"):
            continue

        indent = line_indent_width(line_text)
        if indent <= current_scope["indent"]:
            break

        assign_match = assign_pattern.match(line_text)
        if assign_match:
            locals_set.add(assign_match.group(1))
        iter_match = iter_pattern.match(line_text)
        if iter_match:
            locals_set.add(iter_match.group(1))
        repeat_match = repeat_pattern.match(line_text)
        if repeat_match:
            locals_set.add(repeat_match.group(1))
        catch_match = catch_pattern.match(line_text)
        if catch_match:
            locals_set.add(catch_match.group(1))

    return locals_set


def extract_import_alias_map(code: str) -> dict[str, str]:
    mapping = {}
    pattern = re.compile(
        r'^\s*引入\s*["“](.+?)["”]\s*叫做\s*([\u4e00-\u9fa5A-Za-z_][\u4e00-\u9fa5A-Za-z0-9_]*)',
        re.MULTILINE,
    )
    for module_name, alias in pattern.findall(code or ""):
        module_name = str(module_name).strip()
        alias = str(alias).strip()
        if module_name and alias:
            mapping[alias] = module_name
    return mapping


def extract_object_member_history(code: str) -> dict[str, set[str]]:
    ident_pattern = r"[\u4e00-\u9fa5A-Za-z_][\u4e00-\u9fa5A-Za-z0-9_]*"
    mapping: dict[str, set[str]] = {}
    for object_name, member_name in re.findall(rf"({ident_pattern})\.({ident_pattern})", code or ""):
        if not object_name or not member_name:
            continue
        mapping.setdefault(str(object_name), set()).add(str(member_name))
    return mapping


def collect_autocomplete_context(
    code: str,
    format_signature,
    module_member_details_resolver: Callable[[str, Any], dict[str, str]] | None = None,
    module_member_signatures_resolver: Callable[[str, Any], dict[str, str]] | None = None,
    module_members_resolver: Callable[[str, Any], set[str]] | None = None,
    tab_id: Any = None,
    cursor_line: Any = None,
) -> dict[str, Any]:
    ident_pattern = r"[\u4e00-\u9fa5A-Za-z_][\u4e00-\u9fa5A-Za-z0-9_]*"
    content = code or ""

    local_words = set(re.findall(r"[\u4e00-\u9fa5A-Za-z0-9_]{2,}", content))
    function_names = set(re.findall(rf"^\s*功能\s+({ident_pattern})", content, re.MULTILINE))
    blueprint_names = set(re.findall(rf"^\s*定义图纸\s+({ident_pattern})", content, re.MULTILINE))
    variable_names = set(re.findall(rf"^\s*({ident_pattern})\s*=", content, re.MULTILINE))

    function_signatures, blueprint_signatures = extract_definition_signatures(content, format_signature)
    import_aliases = extract_import_alias_map(content)
    import_module_names = {str(name).strip() for name in import_aliases.values() if str(name).strip()}
    object_member_history = extract_object_member_history(content)

    current_scope_locals = extract_scope_locals(content, cursor_line)
    blueprint_members, blueprint_member_types, blueprint_member_signatures = extract_blueprint_members(
        content,
        format_signature,
    )
    instance_map = extract_instance_map(content)

    alias_member_map: dict[str, set[str]] = {}
    alias_member_type_map: dict[str, dict[str, str]] = {}
    alias_member_signature_map: dict[str, dict[str, str]] = {}
    imported_flatten = set()
    imported_types: dict[str, str] = {}
    imported_signatures: dict[str, str] = {}
    kind_priority = {"function": 5, "blueprint": 4, "class": 3, "alias": 2, "variable": 1, "member": 0, "builtin": 0}

    def merge_imported_kind(name: str, kind: str) -> None:
        if not name:
            return
        old_kind = imported_types.get(name, "member")
        if kind_priority.get(kind, 0) >= kind_priority.get(old_kind, 0):
            imported_types[name] = kind

    def merge_imported_signature(name: str, signature: str) -> None:
        if name and signature and not imported_signatures.get(name):
            imported_signatures[name] = signature

    details_resolver = module_member_details_resolver or (lambda _module_name, _tab_id=None: {})
    signatures_resolver = module_member_signatures_resolver or (lambda _module_name, _tab_id=None: {})
    members_resolver = module_members_resolver or (lambda _module_name, _tab_id=None: set())

    for alias, module_name in import_aliases.items():
        member_details = details_resolver(module_name, tab_id) or {}
        member_signatures = signatures_resolver(module_name, tab_id) or {}
        if member_details:
            alias_member_type_map[alias] = dict(member_details)
            members = set(member_details.keys())
            alias_member_map[alias] = members
            alias_member_signature_map[alias] = dict(member_signatures)
            imported_flatten.update(members)
            for member_name, member_kind in member_details.items():
                merge_imported_kind(member_name, member_kind)
                merge_imported_signature(member_name, str(member_signatures.get(member_name, "") or ""))
            continue

        members = set(members_resolver(module_name, tab_id) or set())
        if members:
            alias_member_map[alias] = members
            alias_member_signature_map[alias] = dict(member_signatures)
            imported_flatten.update(members)
            for member_name in members:
                merge_imported_kind(member_name, "member")
                merge_imported_signature(member_name, str(member_signatures.get(member_name, "") or ""))

    for object_name, blueprint_type_name in instance_map.items():
        members = set(blueprint_members.get(blueprint_type_name, set()))
        type_table = dict(blueprint_member_types.get(blueprint_type_name, {}))
        signature_table = dict(blueprint_member_signatures.get(blueprint_type_name, {}))
        if not members:
            continue
        alias_member_map.setdefault(object_name, set()).update(members)
        if type_table:
            alias_member_type_map.setdefault(object_name, {}).update(type_table)
        if signature_table:
            alias_member_signature_map.setdefault(object_name, {}).update(signature_table)

    return {
        "局部词": local_words,
        "功能名": function_names,
        "图纸名": blueprint_names,
        "变量名": variable_names,
        "当前局部变量": current_scope_locals,
        "功能签名": function_signatures,
        "图纸签名": blueprint_signatures,
        "引入别名": import_aliases,
        "引入模块名": import_module_names,
        "别名成员映射": alias_member_map,
        "别名成员类型映射": alias_member_type_map,
        "别名成员签名映射": alias_member_signature_map,
        "对象成员历史": object_member_history,
        "导入导出平铺": imported_flatten,
        "导入导出类型": imported_types,
        "导入导出签名": imported_signatures,
    }


def extract_member_completion_target(line_text: str) -> tuple[str, str] | None:
    ident_pattern = r"[\u4e00-\u9fa5A-Za-z_][\u4e00-\u9fa5A-Za-z0-9_]*"
    match = re.search(rf"({ident_pattern})\.([\u4e00-\u9fa5A-Za-z0-9_]*)$", str(line_text or ""))
    if not match:
        return None
    object_name = str(match.group(1) or "").strip()
    member_prefix = str(match.group(2) or "")
    if not object_name:
        return None
    return object_name, member_prefix


def member_completion_seed(
    context: dict[str, Any] | None,
    object_name: str,
) -> tuple[set[str], dict[str, str], dict[str, str]]:
    ctx = dict(context or {})
    obj = str(object_name or "").strip()
    members = set(ctx.get("别名成员映射", {}).get(obj, set()))
    members.update(ctx.get("对象成员历史", {}).get(obj, set()))
    member_types = dict(ctx.get("别名成员类型映射", {}).get(obj, {}))
    member_signatures = dict(ctx.get("别名成员签名映射", {}).get(obj, {}))
    return members, member_types, member_signatures


def merge_member_completion_fallback(
    members: set[str],
    member_types: dict[str, str],
    member_signatures: dict[str, str],
    *,
    fallback_details: dict[str, str] | None = None,
    fallback_signatures: dict[str, str] | None = None,
    fallback_members: set[str] | None = None,
) -> tuple[set[str], dict[str, str], dict[str, str]]:
    merged_members = set(members or set())
    merged_types = dict(member_types or {})
    merged_signatures = dict(member_signatures or {})

    details = dict(fallback_details or {})
    signatures = dict(fallback_signatures or {})
    extra_members = set(fallback_members or set())

    if details:
        merged_members.update(details.keys())
        merged_types.update(details)
        if signatures:
            merged_signatures.update(signatures)
        return merged_members, merged_types, merged_signatures

    if extra_members:
        merged_members.update(extra_members)
    if signatures:
        merged_signatures.update(signatures)
    return merged_members, merged_types, merged_signatures


def rank_member_completion_candidates(
    members: set[str],
    member_prefix: str,
    member_types: dict[str, str] | None,
    member_signatures: dict[str, str] | None,
    autocomplete_match,
) -> list[dict[str, Any]]:
    type_to_source = {
        "function": "member_func",
        "blueprint": "member_blueprint",
        "class": "member_class",
        "variable": "member_var",
        "alias": "member_alias",
    }
    prefix = str(member_prefix or "")
    type_table = dict(member_types or {})
    signature_table = dict(member_signatures or {})
    ranked: list[dict[str, Any]] = []

    for member_name in sorted(set(members or set())):
        if not autocomplete_match(member_name, prefix):
            continue
        base_score = 0 if (prefix and str(member_name).startswith(prefix)) else (0.2 if not prefix else 1.8)
        member_kind = type_table.get(member_name, "member")
        source = type_to_source.get(member_kind, "member")
        ranked.append({
            "score": base_score + len(str(member_name)) / 260.0,
            "source": source,
            "insert": str(member_name),
            "sig": str(signature_table.get(member_name, "") or ""),
            "callable": member_kind in {"function", "class"},
        })
    return ranked


def extract_word_completion_prefix(line_text: str) -> str | None:
    ident_pattern = r"[\u4e00-\u9fa5A-Za-z_][\u4e00-\u9fa5A-Za-z0-9_]*"
    match = re.search(rf"({ident_pattern})$", str(line_text or ""))
    if not match:
        return None
    word = str(match.group(1) or "")
    if len(word) < 1:
        return None
    return word


def rank_word_completion_candidates(
    current_word: str,
    context: dict[str, Any] | None,
    autocomplete_words,
    snippets,
    builtin_words,
    builtin_signature_resolver,
    autocomplete_match,
    context_snippets: set[str] | None = None,
) -> list[dict[str, Any]]:
    ctx = dict(context or {})
    word = str(current_word or "")
    if not word:
        return []

    function_signatures = dict(ctx.get("功能签名", {}))
    blueprint_signatures = dict(ctx.get("图纸签名", {}))
    imported_signatures = dict(ctx.get("导入导出签名", {}))
    current_scope_locals = set(ctx.get("当前局部变量", set()) or set())

    snippet_words = set((snippets or {}).keys()) if isinstance(snippets, dict) else set(snippets or set())
    builtin_word_set = set(builtin_words or [])
    context_hint_set = set(context_snippets or set())

    candidate_map: dict[str, dict[str, Any]] = {}

    def add_candidate(item_word, source, base_score, signature="", callable_flag=False):
        item_text = str(item_word or "")
        if not autocomplete_match(item_text, word):
            return

        score = float(base_score)
        if item_text == word:
            score -= 1.1
        elif item_text.startswith(word):
            score -= 0.4
        score += len(item_text) / 260.0

        old = candidate_map.get(item_text)
        new_item = {
            "score": score,
            "source": str(source or ""),
            "insert": item_text,
            "sig": str(signature or ""),
            "callable": bool(callable_flag),
        }
        if old is None or score < float(old.get("score", 999999)):
            candidate_map[item_text] = new_item
        elif old is not None:
            if (not old.get("sig")) and new_item.get("sig"):
                old["sig"] = new_item["sig"]
            if new_item.get("callable") and not old.get("callable"):
                old["callable"] = True

    for item_word in autocomplete_words or []:
        item_text = str(item_word or "")
        if item_text in snippet_words:
            score = -1.5 if item_text in context_hint_set else -0.2
            add_candidate(item_text, "snippet", score, callable_flag=False)
        elif item_text in builtin_word_set:
            add_candidate(item_text, "builtin_func", 0.08, signature=builtin_signature_resolver(item_text), callable_flag=True)
        else:
            score = -1.5 if item_text in context_hint_set else 0.26
            add_candidate(item_text, "keyword", score, callable_flag=False)

    for item_word in set(ctx.get("功能名", set()) or set()):
        add_candidate(item_word, "function", 0.05, signature=function_signatures.get(item_word, "()"), callable_flag=True)
    for item_word in set(ctx.get("图纸名", set()) or set()):
        add_candidate(item_word, "blueprint", 0.09, signature=blueprint_signatures.get(item_word, "()"), callable_flag=False)
    for item_word in set(ctx.get("变量名", set()) or set()):
        weight = 0.02 if item_word in current_scope_locals else 0.35
        add_candidate(item_word, "variable", weight, callable_flag=False)
    for item_word in dict(ctx.get("引入别名", {}) or {}).keys():
        add_candidate(item_word, "alias", 0.12, callable_flag=False)
    for item_word in set(ctx.get("引入模块名", set()) or set()):
        add_candidate(item_word, "module", 0.22, callable_flag=False)

    imported_types = dict(ctx.get("导入导出类型", {}) or {})
    imported_type_to_source = {
        "function": "imported_func",
        "blueprint": "imported_blueprint",
        "class": "imported_class",
        "variable": "imported_var",
        "alias": "imported_alias",
    }
    for item_word in set(ctx.get("导入导出平铺", set()) or set()):
        item_kind = imported_types.get(item_word, "member")
        source = imported_type_to_source.get(item_kind, "imported")
        callable_flag = item_kind in {"function", "class"}
        add_candidate(item_word, source, 0.46, signature=imported_signatures.get(item_word, ""), callable_flag=callable_flag)

    return list(candidate_map.values())


def collect_context_snippet_hints(
    code: str,
    cursor_line: int | None,
    context_rules: dict[str, set[str]] | None = None,
    scan_back_limit: int = 30,
) -> set[str]:
    lines = str(code or "").splitlines()
    if not lines:
        return set()

    try:
        line_no = int(cursor_line or 1)
    except (TypeError, ValueError):
        line_no = 1
    line_no = max(1, min(line_no, len(lines)))

    rules = context_rules or {
        "如果": {"否则如果", "不然"},
        "否则如果": {"否则如果", "不然"},
        "尝试": {"如果出错"},
    }

    try:
        current_indent = line_indent_width(lines[line_no - 1])
    except Exception:
        current_indent = 0

    lower_bound = max(1, line_no - max(1, int(scan_back_limit or 30)))
    for i in range(line_no - 1, lower_bound - 1, -1):
        line_text = lines[i - 1]
        stripped = line_text.strip()
        if not stripped:
            continue

        line_indent = line_indent_width(line_text)
        if line_indent <= current_indent:
            for keyword, hints in rules.items():
                if stripped.startswith(str(keyword)):
                    return set(hints or set())
            break

    return set()


def extract_call_context(line_prefix_text: str) -> dict[str, Any] | None:
    text = str(line_prefix_text or "")
    if not text:
        return None

    paren_level = 0
    bracket_level = 0
    brace_level = 0
    open_paren_index = -1
    for i in range(len(text) - 1, -1, -1):
        ch = text[i]
        if ch == ")":
            paren_level += 1
            continue
        if ch == "]":
            bracket_level += 1
            continue
        if ch == "}":
            brace_level += 1
            continue
        if ch == "(":
            if paren_level == 0 and bracket_level == 0 and brace_level == 0:
                open_paren_index = i
                break
            if paren_level > 0:
                paren_level -= 1
            continue
        if ch == "[" and bracket_level > 0:
            bracket_level -= 1
            continue
        if ch == "{" and brace_level > 0:
            brace_level -= 1
            continue
    if open_paren_index < 0:
        return None

    ident_pattern = r"[\u4e00-\u9fa5A-Za-z_][\u4e00-\u9fa5A-Za-z0-9_]*"
    left_text = text[:open_paren_index]
    name_match = re.search(rf"({ident_pattern}(?:\.{ident_pattern})*)\s*$", left_text)
    if not name_match:
        return None
    call_name = str(name_match.group(1) or "")
    if not call_name:
        return None

    arg_region = text[open_paren_index + 1:]
    comma_count = 0
    paren_level = 0
    bracket_level = 0
    brace_level = 0
    string_quote = ""
    escaped = False
    for ch in arg_region:
        if string_quote:
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == string_quote:
                string_quote = ""
            continue
        if ch in ("'", '"'):
            string_quote = ch
            continue
        if ch == "(":
            paren_level += 1
            continue
        if ch == ")" and paren_level > 0:
            paren_level -= 1
            continue
        if ch == "[":
            bracket_level += 1
            continue
        if ch == "]" and bracket_level > 0:
            bracket_level -= 1
            continue
        if ch == "{":
            brace_level += 1
            continue
        if ch == "}" and brace_level > 0:
            brace_level -= 1
            continue
        if ch == "," and paren_level == 0 and bracket_level == 0 and brace_level == 0:
            comma_count += 1

    arg_index = 1 if not arg_region.strip() else (comma_count + 1)
    return {"调用名": call_name, "参数序号": arg_index}


def resolve_call_expression_signature(
    call_expression: str,
    context: dict[str, Any] | None,
    builtin_words,
    builtin_signature_resolver,
    cross_tab_alias_resolver: Callable[[str, Any], str | None] | None = None,
    module_member_signature_resolver: Callable[[str, Any], dict[str, str]] | None = None,
    tab_id: Any = None,
) -> str:
    name = str(call_expression or "").strip()
    if not name:
        return ""

    ctx = dict(context or {})
    function_signatures = dict(ctx.get("功能签名", {}) or {})
    blueprint_signatures = dict(ctx.get("图纸签名", {}) or {})
    imported_signatures = dict(ctx.get("导入导出签名", {}) or {})
    alias_member_signature_map = dict(ctx.get("别名成员签名映射", {}) or {})
    import_alias_map = dict(ctx.get("引入别名", {}) or {})
    builtin_word_set = set(builtin_words or [])

    if name in function_signatures:
        return str(function_signatures.get(name) or "")
    if name in blueprint_signatures:
        return str(blueprint_signatures.get(name) or "")
    if name in imported_signatures:
        return str(imported_signatures.get(name) or "")
    if name in builtin_word_set:
        try:
            return str((builtin_signature_resolver or (lambda _name: "()"))(name) or "()")
        except Exception:
            return "()"

    if "." in name:
        segments = name.split(".")
        object_name = str(segments[0] or "").strip()
        member_name = str(segments[-1] or "").strip()
        if not object_name or not member_name:
            return ""

        member_signatures = dict(alias_member_signature_map.get(object_name, {}) or {})
        if member_name in member_signatures:
            return str(member_signatures.get(member_name) or "()")

        module_name = import_alias_map.get(object_name, None)
        if not module_name and cross_tab_alias_resolver is not None:
            try:
                module_name = cross_tab_alias_resolver(object_name, tab_id)
            except Exception:
                module_name = None

        if module_name and module_member_signature_resolver is not None:
            try:
                signature_table = dict(module_member_signature_resolver(str(module_name), tab_id) or {})
            except Exception:
                signature_table = {}
            if member_name in signature_table:
                return str(signature_table.get(member_name) or "()")

        if member_name in builtin_word_set:
            try:
                return str((builtin_signature_resolver or (lambda _name: "()"))(member_name) or "()")
            except Exception:
                return "()"

    return ""


def default_module_alias(module_name: str) -> str:
    name = str(module_name or "").replace("\\", "/").rstrip("/")
    if not name:
        return "模块"
    name = name.split("/")[-1]
    if name.endswith(".ym"):
        name = name[:-3]
    return name or "模块"


def collect_block_declarations(statements, default_alias_resolver=default_module_alias):
    names = set()
    function_signatures = {}
    for statement in statements or []:
        node_type = type(statement).__name__
        if node_type == "变量设定节点":
            names.add(getattr(statement, "名称", ""))
        elif node_type == "定义函数节点":
            function_name = getattr(statement, "函数名", "")
            if function_name:
                names.add(function_name)
                function_signatures[function_name] = len(getattr(statement, "参数列表", []) or [])
        elif node_type == "图纸定义节点":
            blueprint_name = getattr(statement, "图纸名", "")
            if blueprint_name:
                names.add(blueprint_name)
        elif node_type == "引入语句节点":
            alias = getattr(statement, "别名", None) or default_alias_resolver(getattr(statement, "模块名", ""))
            if alias:
                names.add(alias)
        elif node_type == "重复循环节点":
            loop_var = getattr(statement, "循环变量名", None)
            if loop_var:
                names.add(loop_var)
        elif node_type == "遍历循环节点":
            element_name = getattr(statement, "元素名", "")
            if element_name:
                names.add(element_name)
        elif node_type == "尝试语句节点":
            err_name = getattr(statement, "错误捕获名", None)
            if err_name:
                names.add(err_name)
    names.discard("")
    return names, function_signatures


def semantic_module_search_paths(
    workspace_dir: str,
    tabs_data: dict | None = None,
    tab_id: str | None = None,
    current_workdir: str | None = None,
) -> list[str]:
    path_list = []

    if tab_id and tabs_data and tab_id in tabs_data:
        file_path = tabs_data[tab_id].get("filepath")
        if file_path and os.path.isfile(file_path):
            base_dir = os.path.dirname(os.path.abspath(file_path))
            path_list.extend([base_dir, os.path.join(base_dir, "示例")])

    cwd = current_workdir or os.getcwd()
    path_list.extend([
        workspace_dir,
        os.path.join(workspace_dir, "示例"),
        cwd,
        os.path.join(cwd, "示例"),
    ])

    dedupe_paths = []
    for path in path_list:
        if not path:
            continue
        abs_path = os.path.abspath(path)
        if abs_path not in dedupe_paths:
            dedupe_paths.append(abs_path)
    return dedupe_paths


def semantic_locate_yima_module(module_name: str, search_paths: list[str]) -> str | None:
    name = str(module_name or "").strip().replace("\\", "/")
    if not name:
        return None

    if os.path.isabs(name):
        if os.path.isfile(name):
            return os.path.abspath(name)
        if os.path.isfile(name + ".ym"):
            return os.path.abspath(name + ".ym")
        return None

    with_suffix = name if name.endswith(".ym") else f"{name}.ym"
    for base_path in search_paths or []:
        candidates = [
            os.path.join(base_path, with_suffix),
            os.path.join(base_path, name),
        ]
        for candidate in candidates:
            if os.path.isfile(candidate):
                return os.path.abspath(candidate)
    return None


def semantic_regex_fallback_exports(code: str, format_signature, default_alias_resolver=default_module_alias):
    ident_pattern = r"[\u4e00-\u9fa5A-Za-z_][\u4e00-\u9fa5A-Za-z0-9_]*"
    exported_symbols = set()
    exported_kinds = {}
    exported_signatures = {}
    kind_priority = {"function": 5, "blueprint": 4, "class": 3, "alias": 2, "variable": 1, "member": 0}

    def remember_export(name, kind, signature=""):
        name_text = str(name or "").strip()
        if not name_text:
            return
        exported_symbols.add(name_text)
        old_kind = exported_kinds.get(name_text, "member")
        if kind_priority.get(kind, 0) >= kind_priority.get(old_kind, 0):
            exported_kinds[name_text] = kind
        signature_text = str(signature or "").strip()
        if signature_text and not exported_signatures.get(name_text):
            exported_signatures[name_text] = signature_text

    code_text = str(code or "")
    fn_line_pattern = re.compile(rf"^\s*功能\s+({ident_pattern})(.*)$")
    bp_line_pattern = re.compile(rf"^\s*定义图纸\s+({ident_pattern})(.*)$")
    var_line_pattern = re.compile(rf"^\s*({ident_pattern})\s*=")
    import_line_pattern = re.compile(rf'^\s*引入\s*["“](.+?)["”]\s*(?:叫做\s*({ident_pattern}))?\s*$')

    for line in code_text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        fn_match = fn_line_pattern.match(line)
        if fn_match:
            name = fn_match.group(1)
            tail = str(fn_match.group(2) or "").strip()
            params = []
            if tail.startswith("(") and ")" in tail:
                param_text = tail[1:tail.find(")")]
                params = [p.strip() for p in str(param_text).split(",") if p.strip()]
            else:
                need_match = re.search(rf"\b需要\b\s*(.*)$", tail)
                if need_match:
                    param_text = str(need_match.group(1) or "").strip()
                    params = [p.strip() for p in re.split(r"[,\s]+", param_text) if p.strip()]
            remember_export(name, "function", format_signature(params))
            continue

        bp_match = bp_line_pattern.match(line)
        if bp_match:
            name = bp_match.group(1)
            tail = str(bp_match.group(2) or "").strip()
            params = []
            if tail.startswith("(") and ")" in tail:
                param_text = tail[1:tail.find(")")]
                params = [p.strip() for p in str(param_text).split(",") if p.strip()]
            else:
                need_match = re.search(rf"\b需要\b\s*(.*)$", tail)
                if need_match:
                    param_text = str(need_match.group(1) or "").strip()
                    params = [p.strip() for p in re.split(r"[,\s]+", param_text) if p.strip()]
            remember_export(name, "blueprint", format_signature(params))
            continue

        var_match = var_line_pattern.match(line)
        if var_match:
            remember_export(var_match.group(1), "variable")
            continue

        import_match = import_line_pattern.match(line)
        if import_match:
            module_name = str(import_match.group(1) or "").strip()
            alias = str(import_match.group(2) or "").strip()
            name = alias if alias else default_alias_resolver(module_name)
            remember_export(name, "alias")

    return exported_symbols, exported_kinds, exported_signatures


def semantic_read_module_exports(
    module_path: str,
    semantic_module_cache: dict,
    format_signature,
    default_alias_resolver=default_module_alias,
):
    abs_path = os.path.abspath(str(module_path))
    try:
        mtime = os.stat(abs_path).st_mtime_ns
    except OSError as e:
        return None, f"读取模块信息失败：{e}"

    cache_item = semantic_module_cache.get(abs_path)
    if cache_item and cache_item.get("mtime") == mtime:
        return set(cache_item.get("symbols", set())), cache_item.get("error")

    code = ""
    try:
        with open(abs_path, "r", encoding="utf-8") as f:
            code = f.read()
        from yima.词法分析 import 词法分析器
        from yima.语法分析 import 语法分析器

        syntax_tree = 语法分析器(词法分析器(code).分析()).解析()
    except Exception as e:
        error_text = f"模块解析失败：{e}"
        fallback_symbols, fallback_kinds, fallback_signatures = semantic_regex_fallback_exports(
            code,
            format_signature,
            default_alias_resolver=default_alias_resolver,
        )
        if fallback_symbols:
            semantic_module_cache[abs_path] = {
                "mtime": mtime,
                "symbols": set(fallback_symbols),
                "symbol_kinds": dict(fallback_kinds),
                "symbol_signatures": dict(fallback_signatures),
                "error": error_text,
            }
            return set(fallback_symbols), None
        semantic_module_cache[abs_path] = {
            "mtime": mtime,
            "symbols": set(),
            "symbol_kinds": {},
            "symbol_signatures": {},
            "error": error_text,
        }
        return None, error_text

    exported_symbols = set()
    exported_kinds = {}
    exported_signatures = {}
    kind_priority = {"function": 5, "blueprint": 4, "class": 3, "alias": 2, "variable": 1, "member": 0}

    def remember_export(name, kind, signature=""):
        if not name:
            return
        exported_symbols.add(name)
        old_kind = exported_kinds.get(name, "member")
        if kind_priority.get(kind, 0) >= kind_priority.get(old_kind, 0):
            exported_kinds[name] = kind
        if signature and (not exported_signatures.get(name)):
            exported_signatures[name] = signature

    for statement in getattr(syntax_tree, "语句列表", []) or []:
        node_type = type(statement).__name__
        if node_type == "变量设定节点":
            name = getattr(statement, "名称", "")
            remember_export(name, "variable")
        elif node_type == "定义函数节点":
            name = getattr(statement, "函数名", "")
            params = list(getattr(statement, "参数列表", []) or [])
            remember_export(name, "function", format_signature(params))
        elif node_type == "图纸定义节点":
            name = getattr(statement, "图纸名", "")
            params = list(getattr(statement, "参数列表", []) or [])
            remember_export(name, "blueprint", format_signature(params))
        elif node_type == "引入语句节点":
            name = getattr(statement, "别名", None) or default_alias_resolver(getattr(statement, "模块名", ""))
            remember_export(name, "alias")

    semantic_module_cache[abs_path] = {
        "mtime": mtime,
        "symbols": set(exported_symbols),
        "symbol_kinds": dict(exported_kinds),
        "symbol_signatures": dict(exported_signatures),
        "error": None,
    }
    return exported_symbols, None


def semantic_read_module_export_details(
    module_path: str,
    semantic_module_cache: dict,
    format_signature,
    default_alias_resolver=default_module_alias,
):
    abs_path = os.path.abspath(str(module_path))
    symbols, error = semantic_read_module_exports(
        abs_path,
        semantic_module_cache,
        format_signature,
        default_alias_resolver=default_alias_resolver,
    )
    if error:
        return {}, error
    cache_item = semantic_module_cache.get(abs_path) or {}
    kind_table = dict(cache_item.get("symbol_kinds", {}))
    if not kind_table and symbols:
        kind_table = {name: "member" for name in symbols}
    return kind_table, None


def semantic_read_module_export_signatures(
    module_path: str,
    semantic_module_cache: dict,
    format_signature,
    default_alias_resolver=default_module_alias,
):
    abs_path = os.path.abspath(str(module_path))
    _, error = semantic_read_module_exports(
        abs_path,
        semantic_module_cache,
        format_signature,
        default_alias_resolver=default_alias_resolver,
    )
    if error:
        return {}, error
    cache_item = semantic_module_cache.get(abs_path) or {}
    signature_table = dict(cache_item.get("symbol_signatures", {}))
    return signature_table, None


def semantic_analyze(
    syntax_tree,
    builtin_words,
    default_alias_resolver=default_module_alias,
    collect_block_declarations_func=collect_block_declarations,
):
    warnings = []
    dedupe = set()
    builtin_names = set(builtin_words or [])
    builtin_names.update({"对", "错", "空"})

    def add_warning(line_no, message, col_no=None, category="语义"):
        try:
            line_value = max(1, int(line_no or 1))
        except (ValueError, TypeError):
            line_value = 1
        try:
            col_value = int(col_no) if col_no else None
        except (ValueError, TypeError):
            col_value = None
        category_value = str(category or "语义")
        key = (line_value, col_value, message, category_value)
        if key in dedupe:
            return
        dedupe.add(key)
        warnings.append({
            "line": line_value,
            "col": col_value,
            "message": message,
            "type": "语义提示",
            "category": category_value,
        })

    def name_defined(name, scope_stack):
        if not name:
            return True
        if name in builtin_names:
            return True
        for scope in reversed(scope_stack):
            if name in scope:
                return True
        return False

    def get_param_count(name, function_stack):
        for fn_dict in reversed(function_stack):
            if name in fn_dict:
                return fn_dict[name]
        return None

    def statement_definition_info(statement):
        node_type = type(statement).__name__
        if node_type == "定义函数节点":
            name = getattr(statement, "函数名", "")
            return (name, "功能", getattr(statement, "行号", 1)) if name else None
        if node_type == "图纸定义节点":
            name = getattr(statement, "图纸名", "")
            return (name, "图纸", getattr(statement, "行号", 1)) if name else None
        if node_type == "引入语句节点":
            name = getattr(statement, "别名", None) or default_alias_resolver(getattr(statement, "模块名", ""))
            return (name, "模块别名", getattr(statement, "行号", 1)) if name else None
        return None

    def check_duplicate_params(param_list, function_name, line_no, type_label):
        seen = set()
        for param in param_list or []:
            if param in seen:
                add_warning(line_no, f"{type_label}【{function_name}】的参数【{param}】重复定义。")
            else:
                seen.add(param)

    def collect_must_assigned_names(statement_list):
        must_assigned = set()
        for statement in statement_list or []:
            node_type = type(statement).__name__
            if node_type == "变量设定节点":
                name = getattr(statement, "名称", "")
                if name:
                    must_assigned.add(name)
                continue

            if node_type == "如果语句节点":
                branch_result = []
                for _, branch_code in getattr(statement, "条件分支列表", []) or []:
                    branch_result.append(collect_must_assigned_names(branch_code))

                else_branch = getattr(statement, "否则分支列表", None)
                if else_branch is None:
                    continue

                branch_result.append(collect_must_assigned_names(else_branch))
                if branch_result:
                    must_assigned.update(set.intersection(*branch_result))
        return must_assigned

    def analyze_expr(node, scope_stack, function_stack, in_blueprint=False):
        if node is None:
            return
        node_type = type(node).__name__

        if node_type == "变量访问节点":
            name = getattr(node, "名称", "")
            if not name_defined(name, scope_stack):
                add_warning(getattr(node, "行号", 1), f"名称【{name}】在当前上下文可能未定义。")
            return

        if node_type == "函数调用节点":
            name = getattr(node, "函数名", "")
            params = getattr(node, "参数列表", []) or []
            if not name_defined(name, scope_stack):
                add_warning(getattr(node, "行号", 1), f"调用目标【{name}】可能未定义。")
            else:
                expected_count = get_param_count(name, function_stack)
                if expected_count is not None and expected_count != len(params):
                    add_warning(getattr(node, "行号", 1), f"功能【{name}】参数个数可能不匹配：期望 {expected_count}，实际 {len(params)}。")
            for param in params:
                analyze_expr(param, scope_stack, function_stack, in_blueprint=in_blueprint)
            return

        if node_type == "动态调用节点":
            analyze_expr(getattr(node, "目标节点", None), scope_stack, function_stack, in_blueprint=in_blueprint)
            for param in getattr(node, "参数列表", []) or []:
                analyze_expr(param, scope_stack, function_stack, in_blueprint=in_blueprint)
            return

        if node_type == "二元运算节点":
            analyze_expr(getattr(node, "左边", None), scope_stack, function_stack, in_blueprint=in_blueprint)
            analyze_expr(getattr(node, "右边", None), scope_stack, function_stack, in_blueprint=in_blueprint)
            return

        if node_type == "一元运算节点":
            analyze_expr(getattr(node, "操作数", None), scope_stack, function_stack, in_blueprint=in_blueprint)
            return

        if node_type == "属性访问节点":
            analyze_expr(getattr(node, "对象节点", None), scope_stack, function_stack, in_blueprint=in_blueprint)
            return

        if node_type == "属性设置节点":
            analyze_expr(getattr(node, "对象节点", None), scope_stack, function_stack, in_blueprint=in_blueprint)
            analyze_expr(getattr(node, "值节点", None), scope_stack, function_stack, in_blueprint=in_blueprint)
            return

        if node_type == "索引访问节点":
            analyze_expr(getattr(node, "对象节点", None), scope_stack, function_stack, in_blueprint=in_blueprint)
            analyze_expr(getattr(node, "索引节点", None), scope_stack, function_stack, in_blueprint=in_blueprint)
            return

        if node_type == "索引设置节点":
            analyze_expr(getattr(node, "对象节点", None), scope_stack, function_stack, in_blueprint=in_blueprint)
            analyze_expr(getattr(node, "索引节点", None), scope_stack, function_stack, in_blueprint=in_blueprint)
            analyze_expr(getattr(node, "值节点", None), scope_stack, function_stack, in_blueprint=in_blueprint)
            return

        if node_type == "列表字面量节点":
            for item in getattr(node, "元素列表", []) or []:
                analyze_expr(item, scope_stack, function_stack, in_blueprint=in_blueprint)
            return

        if node_type == "字典字面量节点":
            for key_node, value_node in getattr(node, "键值对列表", []) or []:
                analyze_expr(key_node, scope_stack, function_stack, in_blueprint=in_blueprint)
                analyze_expr(value_node, scope_stack, function_stack, in_blueprint=in_blueprint)
            return

        if node_type == "输入表达式节点":
            analyze_expr(getattr(node, "提示语句表达式", None), scope_stack, function_stack, in_blueprint=in_blueprint)
            return

        if node_type == "实例化节点":
            blueprint_name = getattr(node, "图纸名", "")
            if blueprint_name and not name_defined(blueprint_name, scope_stack):
                add_warning(getattr(node, "行号", 1), f"图纸【{blueprint_name}】可能未定义。")
            for param in getattr(node, "参数列表", []) or []:
                analyze_expr(param, scope_stack, function_stack, in_blueprint=in_blueprint)
            return

        if node_type == "自身属性访问节点":
            if not in_blueprint:
                add_warning(getattr(node, "行号", 1), "【它的】建议只在图纸定义内部使用。")
            return

        if node_type == "自身属性设置节点":
            if not in_blueprint:
                add_warning(getattr(node, "行号", 1), "【它的】建议只在图纸定义内部使用。")
            analyze_expr(getattr(node, "值节点", None), scope_stack, function_stack, in_blueprint=in_blueprint)
            return

    def analyze_block(
        statement_list,
        parent_scope_stack,
        parent_function_stack,
        extra_names=None,
        extra_function_signatures=None,
        in_function=False,
        loop_level=0,
        in_blueprint=False,
    ):
        block_declared_names, block_function_sigs = collect_block_declarations_func(statement_list)
        local_scope = set(block_declared_names)
        if extra_names:
            local_scope.update(extra_names)
        local_function_sig = dict(block_function_sigs)
        if extra_function_signatures:
            local_function_sig.update(extra_function_signatures)
        scope_stack = list(parent_scope_stack) + [local_scope]
        function_stack = list(parent_function_stack) + [local_function_sig]

        same_block_defined = {}
        for statement in statement_list or []:
            info = statement_definition_info(statement)
            if not info:
                continue
            name, define_type, line_no = info
            if name in same_block_defined:
                prev_type, prev_line = same_block_defined[name]
                add_warning(line_no, f"名称【{name}】在同一代码块重复定义（前一次：第 {prev_line} 行，类型：{prev_type}）。")
            else:
                same_block_defined[name] = (define_type, line_no)

        for statement in statement_list or []:
            node_type = type(statement).__name__
            if node_type == "显示语句节点":
                analyze_expr(getattr(statement, "表达式", None), scope_stack, function_stack, in_blueprint=in_blueprint)
            elif node_type == "变量设定节点":
                analyze_expr(getattr(statement, "表达式", None), scope_stack, function_stack, in_blueprint=in_blueprint)
            elif node_type == "如果语句节点":
                branch_assigned_list = []
                for condition, branch in getattr(statement, "条件分支列表", []) or []:
                    analyze_expr(condition, scope_stack, function_stack, in_blueprint=in_blueprint)
                    analyze_block(branch, scope_stack, function_stack, in_function=in_function, loop_level=loop_level, in_blueprint=in_blueprint)
                    branch_assigned_list.append(collect_must_assigned_names(branch))
                else_branch = getattr(statement, "否则分支列表", None)
                has_else = else_branch is not None
                if has_else:
                    analyze_block(else_branch, scope_stack, function_stack, in_function=in_function, loop_level=loop_level, in_blueprint=in_blueprint)
                    branch_assigned_list.append(collect_must_assigned_names(else_branch))
                if has_else and branch_assigned_list:
                    must_assign = set.intersection(*branch_assigned_list)
                    if must_assign:
                        scope_stack[-1].update(must_assign)
            elif node_type == "当循环节点":
                analyze_expr(getattr(statement, "条件", None), scope_stack, function_stack, in_blueprint=in_blueprint)
                analyze_block(
                    getattr(statement, "循环体", []),
                    scope_stack,
                    function_stack,
                    in_function=in_function,
                    loop_level=loop_level + 1,
                    in_blueprint=in_blueprint,
                )
            elif node_type == "重复循环节点":
                analyze_expr(getattr(statement, "次数表达式", None), scope_stack, function_stack, in_blueprint=in_blueprint)
                extra = set()
                loop_var = getattr(statement, "循环变量名", None)
                if loop_var:
                    extra.add(loop_var)
                analyze_block(
                    getattr(statement, "循环体", []),
                    scope_stack,
                    function_stack,
                    extra_names=extra,
                    in_function=in_function,
                    loop_level=loop_level + 1,
                    in_blueprint=in_blueprint,
                )
            elif node_type == "遍历循环节点":
                analyze_expr(getattr(statement, "列表表达式", None), scope_stack, function_stack, in_blueprint=in_blueprint)
                extra = set()
                element_name = getattr(statement, "元素名", "")
                if element_name:
                    extra.add(element_name)
                analyze_block(
                    getattr(statement, "循环体", []),
                    scope_stack,
                    function_stack,
                    extra_names=extra,
                    in_function=in_function,
                    loop_level=loop_level + 1,
                    in_blueprint=in_blueprint,
                )
            elif node_type == "尝试语句节点":
                analyze_block(
                    getattr(statement, "尝试代码块", []),
                    scope_stack,
                    function_stack,
                    in_function=in_function,
                    loop_level=loop_level,
                    in_blueprint=in_blueprint,
                )
                extra = set()
                err_name = getattr(statement, "错误捕获名", None)
                if err_name:
                    extra.add(err_name)
                analyze_block(
                    getattr(statement, "出错代码块", []),
                    scope_stack,
                    function_stack,
                    extra_names=extra,
                    in_function=in_function,
                    loop_level=loop_level,
                    in_blueprint=in_blueprint,
                )
            elif node_type == "定义函数节点":
                fn_name = getattr(statement, "函数名", "")
                param_list = list(getattr(statement, "参数列表", []) or [])
                check_duplicate_params(param_list, fn_name or "匿名功能", getattr(statement, "行号", 1), "功能")
                param_names = set(param_list)
                analyze_block(
                    getattr(statement, "代码块", []),
                    scope_stack,
                    function_stack,
                    extra_names=param_names,
                    in_function=True,
                    loop_level=0,
                    in_blueprint=in_blueprint,
                )
            elif node_type == "图纸定义节点":
                bp_name = getattr(statement, "图纸名", "")
                param_list = list(getattr(statement, "参数列表", []) or [])
                check_duplicate_params(param_list, bp_name or "匿名图纸", getattr(statement, "行号", 1), "图纸")
                param_names = set(param_list)
                analyze_block(
                    getattr(statement, "代码块", []),
                    scope_stack,
                    function_stack,
                    extra_names=param_names,
                    in_function=False,
                    loop_level=0,
                    in_blueprint=True,
                )
            elif node_type == "返回语句节点":
                if not in_function:
                    add_warning(getattr(statement, "行号", 1), "【返回】建议只在功能内部使用。")
                analyze_expr(getattr(statement, "表达式", None), scope_stack, function_stack, in_blueprint=in_blueprint)
            elif node_type == "跳出语句节点":
                if loop_level <= 0:
                    add_warning(getattr(statement, "行号", 1), "【停下】建议只在循环内部使用。")
            elif node_type == "继续语句节点":
                if loop_level <= 0:
                    add_warning(getattr(statement, "行号", 1), "【略过】建议只在循环内部使用。")
            elif node_type == "引入语句节点":
                continue
            else:
                analyze_expr(statement, scope_stack, function_stack, in_blueprint=in_blueprint)

    top_level = getattr(syntax_tree, "语句列表", []) or []
    analyze_block(top_level, [set(builtin_names)], [dict()], in_function=False, loop_level=0, in_blueprint=False)
    warnings.sort(key=lambda x: (x.get("line") or 1, x.get("col") or 0))
    return warnings
