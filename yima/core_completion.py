"""Core autocomplete/calltip/completion helper functions."""

from __future__ import annotations

import re
from typing import Any, Callable

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



__all__ = [
    "line_indent_width",
    "split_signature_params",
    "highlight_current_signature_param",
    "normalize_completion_signature",
    "first_argument_span_offset",
    "extract_definition_signatures",
    "extract_blueprint_members",
    "extract_instance_map",
    "extract_scope_locals",
    "extract_import_alias_map",
    "extract_object_member_history",
    "collect_autocomplete_context",
    "extract_member_completion_target",
    "member_completion_seed",
    "merge_member_completion_fallback",
    "rank_member_completion_candidates",
    "extract_word_completion_prefix",
    "rank_word_completion_candidates",
    "collect_context_snippet_hints",
    "extract_call_context",
    "resolve_call_expression_signature",
]
