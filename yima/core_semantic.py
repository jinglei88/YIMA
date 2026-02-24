"""Core semantic and module-analysis helper functions."""

from __future__ import annotations

import os
import re

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

__all__ = [
    "default_module_alias",
    "collect_block_declarations",
    "semantic_module_search_paths",
    "semantic_locate_yima_module",
    "semantic_regex_fallback_exports",
    "semantic_read_module_exports",
    "semantic_read_module_export_details",
    "semantic_read_module_export_signatures",
    "semantic_analyze",
]
