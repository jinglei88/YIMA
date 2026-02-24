#!/usr/bin/env python3
"""易码打包核心逻辑回归（无 PyInstaller 冒烟）。"""

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


import importlib.util
import json
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


FN_EXTRACT_IMPORTS = "_\u63d0\u53d6\u5f15\u5165\u6a21\u5757\u540d"
FN_LOCATE_LOCAL_MODULE = "_\u5b9a\u4f4d\u672c\u5730\u6613\u7801\u6a21\u5757"
FN_INFER_PY_MODULE = "_\u63a8\u65ad\u53ef\u6253\u5305Python\u6a21\u5757"
FN_BUILD_DEP_GRAPH = "_\u6784\u5efa\u6613\u7801\u4f9d\u8d56\u56fe"
FN_PRECHECK_SYNTAX = "_\u9884\u68c0\u67e5\u6613\u7801\u8bed\u6cd5"
FN_READ_MANIFEST = "_\u8bfb\u53d6\u6253\u5305\u6e05\u5355"
FN_ANALYZE_HIDDEN = "_\u5206\u6790\u9690\u5f0fPython\u4f9d\u8d56"
FN_SANITIZE_APP_NAME = "\u6e05\u7406\u8f6f\u4ef6\u540d"

KEY_LOCAL_FILES = "\u672c\u5730\u6e90\u7801\u6587\u4ef6"
KEY_PY_MODULES = "python\u6a21\u5757"
KEY_UNRESOLVED = "\u65e0\u6cd5\u89e3\u6790\u5f15\u5165"
FIELD_SOURCE_FILE = "\u6765\u6e90\u6587\u4ef6"
FIELD_MODULE_NAME = "\u6a21\u5757\u540d"

KW_IMPORT = "\u5f15\u5165"
KW_ALIAS = "\u53eb\u505a"
KW_SHOW = "\u663e\u793a"
KW_FUNC = "\u529f\u80fd"
KW_RETURN = "\u8fd4\u56de"
BUILTIN_SYSTEM = "\u7cfb\u7edf\u5de5\u5177"
DIR_EXAMPLES = "\u793a\u4f8b"
MANIFEST_NAME = "\u6613\u7801\u6253\u5305\u6e05\u5355.json"


def _assert_true(cond: bool, msg: str) -> None:
    if not cond:
        raise AssertionError(msg)


def _load_pack_module():
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))

    path = ROOT / "\u6613\u7801\u6253\u5305\u5de5\u5177.py"
    if not path.is_file():
        candidates = sorted(ROOT.glob("*\u6253\u5305\u5de5\u5177.py"))
        if not candidates:
            raise FileNotFoundError("未找到打包工具脚本。")
        path = candidates[0]

    spec = importlib.util.spec_from_file_location("yima_pack_regression_target", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"无法加载模块规格：{path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def check_import_extraction(mod) -> None:
    extract_imports = getattr(mod, FN_EXTRACT_IMPORTS)
    source = (
        "\ufeff"
        f'{KW_IMPORT} "A" {KW_ALIAS} A\n'
        f'{KW_IMPORT} "A" {KW_ALIAS} A2  # duplicate\n'
        f'{KW_IMPORT} "json"\n'
        f'{KW_IMPORT} "{BUILTIN_SYSTEM}" {KW_ALIAS} SYS\n'
        "引入 A 叫做 Bad\n"
        "# comment only\n"
    )
    got = extract_imports(source)
    _assert_true(got == ["A", "json", BUILTIN_SYSTEM], f"提取引入模块异常：{got}")
    print("[OK] 打包-引入提取规则通过")


def check_module_location(mod) -> None:
    locate_module = getattr(mod, FN_LOCATE_LOCAL_MODULE)
    with tempfile.TemporaryDirectory(prefix="yima_pack_locate_", dir=ROOT) as td:
        proj = Path(td)
        cur = proj / "src"
        examples = proj / DIR_EXAMPLES
        cur.mkdir(parents=True, exist_ok=True)
        examples.mkdir(parents=True, exist_ok=True)

        local_mod = proj / "A.ym"
        sample_mod = examples / "Demo.ym"
        abs_mod = proj / "Abs.ym"
        local_mod.write_text(f"{KW_SHOW} 1\n", encoding="utf-8")
        sample_mod.write_text(f"{KW_SHOW} 2\n", encoding="utf-8")
        abs_mod.write_text(f"{KW_SHOW} 3\n", encoding="utf-8")

        got_local = locate_module("A", str(cur), str(proj))
        got_sample = locate_module("Demo", str(cur), str(proj))
        got_abs = locate_module(str(abs_mod.with_suffix("")), str(cur), str(proj))
        got_missing = locate_module("MissingMod", str(cur), str(proj))

        _assert_true(Path(got_local).resolve() == local_mod.resolve(), f"本地模块定位失败：{got_local}")
        _assert_true(Path(got_sample).resolve() == sample_mod.resolve(), f"示例目录模块定位失败：{got_sample}")
        _assert_true(Path(got_abs).resolve() == abs_mod.resolve(), f"绝对模块定位失败：{got_abs}")
        _assert_true(got_missing is None, f"不存在模块应返回 None：{got_missing}")
    print("[OK] 打包-本地模块定位规则通过")


def check_python_module_inference(mod) -> None:
    infer_py = getattr(mod, FN_INFER_PY_MODULE)
    _assert_true("json" in infer_py("json"), "json 应被识别为 Python 模块")
    deep = infer_py("json.tool")
    _assert_true("json" in deep and "json.tool" in deep, f"层级模块推断异常：{deep}")
    _assert_true(not infer_py("pkg/mod"), "带路径分隔的模块名不应识别为 Python 模块")
    _assert_true(not infer_py("abc_no_such_module_xyz"), "不存在的 Python 模块不应被识别")
    print("[OK] 打包-Python 模块推断规则通过")


def check_dependency_graph(mod) -> None:
    build_graph = getattr(mod, FN_BUILD_DEP_GRAPH)
    with tempfile.TemporaryDirectory(prefix="yima_pack_graph_", dir=ROOT) as td:
        proj = Path(td)
        main = proj / "main.ym"
        mod_a = proj / "A.ym"
        mod_b = proj / "B.ym"

        main.write_text(
            f'{KW_IMPORT} "A" {KW_ALIAS} A\n'
            f'{KW_IMPORT} "json" {KW_ALIAS} J\n'
            f'{KW_IMPORT} "not_exists_abc" {KW_ALIAS} X\n'
            f'{KW_IMPORT} "{BUILTIN_SYSTEM}" {KW_ALIAS} SYS\n',
            encoding="utf-8",
        )
        mod_a.write_text(f'{KW_IMPORT} "B.ym" {KW_ALIAS} B\n', encoding="utf-8")
        mod_b.write_text(f"{KW_SHOW} 1\n", encoding="utf-8")

        graph = build_graph(str(main), str(proj))
        local_names = {Path(x).name for x in graph.get(KEY_LOCAL_FILES, [])}
        py_names = set(graph.get(KEY_PY_MODULES, []))
        unresolved = graph.get(KEY_UNRESOLVED, [])

        _assert_true({"main.ym", "A.ym", "B.ym"}.issubset(local_names), f"本地依赖图不完整：{local_names}")
        _assert_true("json" in py_names, f"Python 模块依赖缺失：{py_names}")
        _assert_true(len(unresolved) == 1, f"未解析模块数量异常：{unresolved}")
        _assert_true(unresolved[0].get(FIELD_MODULE_NAME) == "not_exists_abc", f"未解析模块名异常：{unresolved}")
        _assert_true(Path(unresolved[0].get(FIELD_SOURCE_FILE, "")).name == "main.ym", f"未解析来源异常：{unresolved}")
    print("[OK] 打包-依赖图构建规则通过")


def check_manifest_reader(mod) -> None:
    read_manifest = getattr(mod, FN_READ_MANIFEST)
    with tempfile.TemporaryDirectory(prefix="yima_pack_manifest_", dir=ROOT) as td:
        proj = Path(td)
        asset = proj / "asset.txt"
        asset2 = proj / "asset2.txt"
        asset.write_text("a", encoding="utf-8")
        asset2.write_text("b", encoding="utf-8")

        no_manifest = read_manifest(str(proj), lambda *_: None)
        _assert_true(no_manifest == {"path": None, "hidden_imports": [], "datas": []}, f"默认清单返回异常：{no_manifest}")

        pack_json = proj / "yima_pack.json"
        pack_json.write_text(
            json.dumps(
                {
                    "hidden_imports": ["json", "math"],
                    "datas": [
                        {"src": "asset.txt", "dest": "assets"},
                        {"src": "missing.txt", "dest": "assets"},
                        "asset2.txt",
                        123,
                    ],
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        loaded = read_manifest(str(proj), lambda *_: None)
        _assert_true(Path(loaded["path"]).name == "yima_pack.json", f"清单文件优先级异常：{loaded}")
        _assert_true(loaded["hidden_imports"] == ["json", "math"], f"hidden_imports 解析异常：{loaded}")
        data_items = loaded["datas"]
        _assert_true(len(data_items) == 2, f"datas 过滤异常：{data_items}")
        _assert_true(Path(data_items[0][0]).name == "asset.txt" and data_items[0][1] == "assets", f"datas[0] 异常：{data_items}")
        _assert_true(Path(data_items[1][0]).name == "asset2.txt" and data_items[1][1] == ".", f"datas[1] 异常：{data_items}")

        pack_json.unlink()
        official = proj / MANIFEST_NAME
        official.write_text(json.dumps(["bad-root"], ensure_ascii=False), encoding="utf-8")
        try:
            read_manifest(str(proj), lambda *_: None)
            raise AssertionError("根节点非法时应抛错")
        except RuntimeError as e:
            _assert_true("格式错误" in str(e), f"异常文案不符合预期：{e}")

        official.write_text(json.dumps({"hidden_imports": "json"}, ensure_ascii=False), encoding="utf-8")
        try:
            read_manifest(str(proj), lambda *_: None)
            raise AssertionError("hidden_imports 类型非法时应抛错")
        except RuntimeError as e:
            _assert_true("hidden_imports" in str(e), f"异常文案不符合预期：{e}")
    print("[OK] 打包-清单读取规则通过")


def check_hidden_dependency_analysis(mod) -> None:
    analyze_hidden = getattr(mod, FN_ANALYZE_HIDDEN)
    with tempfile.TemporaryDirectory(prefix="yima_pack_hidden_", dir=ROOT) as td:
        proj = Path(td)
        main = proj / "main.ym"
        helper = proj / "helper.ym"
        main.write_text(
            f'{KW_IMPORT} "helper" {KW_ALIAS} H\n'
            f'{KW_IMPORT} "json" {KW_ALIAS} J\n'
            f'{KW_IMPORT} "{BUILTIN_SYSTEM}" {KW_ALIAS} SYS\n',
            encoding="utf-8",
        )
        helper.write_text(
            f"{KW_FUNC} calc()\n"
            f'    {KW_IMPORT} "math" {KW_ALIAS} M\n'
            f"    {KW_RETURN} 1\n",
            encoding="utf-8",
        )
        deps = analyze_hidden([str(main), str(helper)], str(proj))
        _assert_true({"json", "math"}.issubset(set(deps)), f"隐式 Python 依赖分析异常：{deps}")
    print("[OK] 打包-隐式 Python 依赖分析规则通过")


def check_syntax_precheck(mod) -> None:
    precheck_syntax = getattr(mod, FN_PRECHECK_SYNTAX)
    with tempfile.TemporaryDirectory(prefix="yima_pack_syntax_", dir=ROOT) as td:
        proj = Path(td)
        good = proj / "good.ym"
        bad = proj / "bad.ym"
        good.write_text(f"{KW_SHOW} 1\n", encoding="utf-8")
        bad.write_text(f"{KW_SHOW} (1 + 2\n", encoding="utf-8")

        precheck_syntax([str(good)])
        try:
            precheck_syntax([str(good), str(bad)])
            raise AssertionError("语法预检查遇到坏文件应失败")
        except RuntimeError as e:
            text = str(e)
            _assert_true("语法错误" in text and "bad.ym" in text, f"语法预检查错误信息异常：{text}")
    print("[OK] 打包-语法预检查规则通过")


def check_name_sanitizer(mod) -> None:
    sanitize = getattr(mod, FN_SANITIZE_APP_NAME)
    _assert_true(sanitize("  A:B?*  ") == "A_B__", "软件名清洗规则异常")
    _assert_true(sanitize("CON") == "CON_app", "系统保留名处理异常")
    print("[OK] 打包-软件名清洗规则通过")


def main() -> int:
    mod = _load_pack_module()
    print("=== 打包专项回归开始 ===")
    check_import_extraction(mod)
    check_module_location(mod)
    check_python_module_inference(mod)
    check_dependency_graph(mod)
    check_manifest_reader(mod)
    check_hidden_dependency_analysis(mod)
    check_syntax_precheck(mod)
    check_name_sanitizer(mod)
    print("=== 打包专项回归完成：全部通过 ===")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as e:
        safe = str(e).encode("unicode_escape", errors="replace").decode("ascii", errors="replace")
        print(f"[FAIL] 打包专项回归失败: {safe}")
        raise SystemExit(1)
