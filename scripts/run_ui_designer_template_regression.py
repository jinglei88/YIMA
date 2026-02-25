#!/usr/bin/env python3
"""UI designer template regression checks (no GUI interaction)."""

from __future__ import annotations

import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))
from _console_utf8 import setup_console_utf8

setup_console_utf8()

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from yima.editor_ui_designer_flow import (  # noqa: E402
    BUTTON_COMPONENT_KINDS,
    COMPONENT_KIND_SET,
    QUICK_START_SCENES,
    QUICK_START_SCENE_SPECS,
    WINDOW_COMPONENT_KIND,
    _auto_fix_design_components_for_export,
    _apply_quick_start_scene,
    _collect_design_export_context,
    _ensure_state,
    _find_missing_logic_functions,
    _generate_layered_ym_codes,
    _new_component,
    _remember_recent_quick_start_scene,
    _resolve_quick_start_scene,
)


def _assert_true(cond: bool, msg: str) -> None:
    if not cond:
        raise AssertionError(msg)


class _DummyVar:
    def __init__(self):
        self.value = ""

    def set(self, value):
        self.value = str(value)


class _Harness:
    pass


def _new_owner() -> _Harness:
    owner = _Harness()
    owner.status_main_var = _DummyVar()
    owner._ui_designer_canvas = None
    owner._ui_designer_prop_vars = {}
    owner._ui_designer_prop_widgets = {}
    owner._ui_designer_step_labels = []
    owner._ui_designer_step_hint_var = None
    owner.theme_panel_bg = "#1f1f1f"
    owner.theme_toolbar_fg = "#dddddd"
    owner.theme_toolbar_border = "#333333"
    owner._ui_designer_mode = "novice"
    owner._ui_designer_novice_guide = None
    owner._ui_designer_body_paned = None
    _ensure_state(owner)
    return owner


def check_template_catalog_consistency() -> None:
    scene_keys = {str(item.get("key", "")) for item in QUICK_START_SCENES}
    spec_keys = set(QUICK_START_SCENE_SPECS.keys())
    _assert_true(scene_keys == spec_keys, f"scene keys mismatch: scenes={scene_keys} specs={spec_keys}")

    for key, spec in QUICK_START_SCENE_SPECS.items():
        _assert_true(str(spec.get("key", "")) == key, f"spec key mismatch: {key} -> {spec.get('key')}")
        _assert_true(bool(str(spec.get("title", "")).strip()), f"missing title: {key}")
        window = spec.get("window") or {}
        _assert_true(bool(str(window.get("text", "")).strip()), f"missing window text: {key}")
        _assert_true(int(window.get("w", 0)) >= 360, f"window width invalid: {key}")
        _assert_true(int(window.get("h", 0)) >= 240, f"window height invalid: {key}")

        comps = list(spec.get("components", []) or [])
        seen_names = set()
        for comp in comps:
            kind = str(comp.get("kind", ""))
            _assert_true(kind in COMPONENT_KIND_SET, f"unknown kind in {key}: {kind}")
            name = str(comp.get("name", "")).strip()
            _assert_true(bool(name), f"component missing name in {key}: {comp}")
            _assert_true(name not in seen_names, f"duplicate component name in {key}: {name}")
            seen_names.add(name)
            if kind in BUTTON_COMPONENT_KINDS or kind in {"登录模板", "列表模板"}:
                _assert_true(bool(str(comp.get("event", "")).strip()), f"missing event in {key}: {name}")

    for scene in QUICK_START_SCENES:
        _assert_true(bool(str(scene.get("category", "")).strip()), f"scene missing category: {scene}")

    print("[OK] ui designer template catalog consistency passed")


def check_template_apply_flow() -> None:
    owner = _new_owner()
    for item in QUICK_START_SCENES:
        key = str(item.get("key", ""))
        scene = _resolve_quick_start_scene(key)
        _apply_quick_start_scene(owner, key, clear_existing=True)

        comps = list(getattr(owner, "_ui_designer_components", []) or [])
        window_count = sum(1 for c in comps if str(c.get("kind", "")) == WINDOW_COMPONENT_KIND)
        expected_count = 1 + len(list(scene.get("components", []) or []))
        _assert_true(window_count == 1, f"window count mismatch after apply {key}: {window_count}")
        _assert_true(len(comps) == expected_count, f"component count mismatch {key}: {len(comps)} != {expected_count}")

        selected_uid = int(getattr(owner, "_ui_designer_selected_uid", 0) or 0)
        all_uids = {int(c.get("uid", -1)) for c in comps}
        _assert_true(selected_uid in all_uids, f"selected uid invalid for {key}: {selected_uid}")

    print("[OK] ui designer template apply flow passed")


def check_layered_function_coverage() -> None:
    owner = _new_owner()
    for item in QUICK_START_SCENES:
        key = str(item.get("key", ""))
        _apply_quick_start_scene(owner, key, clear_existing=True)
        ui_code, logic_code, _data_code = _generate_layered_ym_codes(owner, data_backend="sqlite")
        missing = _find_missing_logic_functions(ui_code, logic_code)
        _assert_true(not missing, f"missing logic functions for {key}: {missing}")
    print("[OK] ui designer layered function coverage passed")


def check_export_autofix() -> None:
    owner = _new_owner()
    _apply_quick_start_scene(owner, "blank", clear_existing=True)
    button = _new_component(owner, "按钮", x=120, y=120)
    button["name"] = "测试按钮"
    button["text"] = "提交"
    button["event"] = ""
    owner._ui_designer_components.append(button)

    table = _new_component(owner, "表格", x=120, y=180)
    table["name"] = "测试表格"
    table["columns"] = ""
    table["rows"] = 1
    owner._ui_designer_components.append(table)

    fixes = _auto_fix_design_components_for_export(owner)
    _assert_true(len(fixes) >= 2, f"autofix did not run enough fixes: {fixes}")

    context = _collect_design_export_context(owner)
    names = [str(x.get("name", "")) for x in context.get("items", [])]
    idx = names.index("测试按钮") if "测试按钮" in names else -1
    _assert_true(idx >= 0, "autofix target button not found")
    item = context["items"][idx]
    _assert_true(bool(str(item.get("event_fn", "")).strip()), "autofix should generate event function")

    tidx = names.index("测试表格") if "测试表格" in names else -1
    _assert_true(tidx >= 0, "autofix target table not found")
    titem = context["items"][tidx]
    _assert_true(len(list(titem.get("columns", []) or [])) >= 2, "autofix should normalize table columns")
    _assert_true(int(titem.get("rows", 0)) >= 3, "autofix should raise table rows to >=3")
    print("[OK] ui designer export autofix rules passed")


def check_export_position_normalization() -> None:
    owner = _new_owner()
    _apply_quick_start_scene(owner, "blank", clear_existing=True)
    comps = list(getattr(owner, "_ui_designer_components", []) or [])
    win = comps[0]
    win["x"] = 300
    win["y"] = 220
    win["w"] = 960
    win["h"] = 640

    btn = _new_component(owner, "按钮", x=420, y=360)
    btn["name"] = "定位按钮"
    owner._ui_designer_components.append(btn)

    ctx = _collect_design_export_context(owner)
    items = list(ctx.get("items", []) or [])
    hit = None
    for item in items:
        if str(item.get("name", "")) == "定位按钮":
            hit = item
            break
    _assert_true(hit is not None, "normalized export item not found")
    _assert_true(int(hit.get("x", -1)) == 120, f"x should be relative to window: {hit}")
    _assert_true(int(hit.get("y", -1)) == 140, f"y should be relative to window: {hit}")
    print("[OK] ui designer export position normalization passed")


def check_template_tags_and_naming_rules() -> None:
    for scene in QUICK_START_SCENES:
        tags = scene.get("tags", [])
        _assert_true(isinstance(tags, list) and len(tags) >= 1, f"scene tags missing: {scene}")

    owner = _new_owner()
    owner._ui_designer_name_suggest_prefix = "审批工作台"
    _apply_quick_start_scene(owner, "approval", clear_existing=True)
    comp = _new_component(owner, "按钮", x=120, y=120)
    owner._ui_designer_components.append(comp)
    _assert_true(str(comp.get("name", "")).startswith("审批工作台_"), f"suggested name prefix mismatch: {comp}")

    _remember_recent_quick_start_scene(owner, "query")
    _remember_recent_quick_start_scene(owner, "login")
    recents = list(getattr(owner, "_ui_designer_recent_scenes", []) or [])
    _assert_true(recents[:2] == ["login", "query"], f"recent scenes order mismatch: {recents}")
    print("[OK] ui designer tags and naming rules passed")


def main() -> int:
    print("=== 可视化模板回归开始 ===")
    check_template_catalog_consistency()
    check_template_apply_flow()
    check_layered_function_coverage()
    check_export_autofix()
    check_export_position_normalization()
    check_template_tags_and_naming_rules()
    print("=== 可视化模板回归完成：全部通过 ===")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
