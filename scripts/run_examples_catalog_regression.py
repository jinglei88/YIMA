#!/usr/bin/env python3
"""示例目录与分类回归（不依赖 GUI 事件）。"""

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

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from yima import editor_examples_flow as flow  # noqa: E402


def _assert_true(cond: bool, msg: str) -> None:
    if not cond:
        raise AssertionError(msg)


def check_builtin_sync() -> None:
    builtin = flow.BUILTIN_EXAMPLES_DIR
    local = flow.LOCAL_EXAMPLES_DIR
    _assert_true(builtin.is_dir(), f"内置示例目录不存在：{builtin}")
    builtin_count = len(list(builtin.rglob("*.ym")))
    _assert_true(builtin_count >= 40, f"内置示例数量偏少：{builtin_count}")
    if local.is_dir():
        local_count = len(list(local.rglob("*.ym")))
        _assert_true(
            builtin_count >= local_count,
            f"内置示例未同步最新本地示例：builtin={builtin_count}, local={local_count}",
        )
    print("[OK] 内置示例目录同步检查通过")


def check_manifest_integrity() -> None:
    manifest = flow.load_examples_manifest(force_reload=True)
    _assert_true(isinstance(manifest, dict) and manifest, "示例元数据清单为空或读取失败")

    builtin_rels = sorted(
        p.relative_to(flow.BUILTIN_EXAMPLES_DIR).as_posix()
        for p in flow.BUILTIN_EXAMPLES_DIR.rglob("*.ym")
    )
    manifest_rels = sorted(manifest.keys())

    missing = sorted(set(builtin_rels) - set(manifest_rels))
    _assert_true(not missing, f"元数据清单缺少示例条目：{missing}")

    extras = sorted(set(manifest_rels) - set(builtin_rels))
    _assert_true(not extras, f"元数据清单存在无效路径：{extras}")

    for rel in builtin_rels:
        meta = manifest.get(rel, {})
        _assert_true(isinstance(meta, dict), f"元数据格式错误（应为对象）：{rel}")

        title = str(meta.get("title", "")).strip()
        summary = str(meta.get("summary", "")).strip()
        expected = str(meta.get("expected", "")).strip()
        difficulty = str(meta.get("difficulty", "")).strip()
        domain = str(meta.get("domain", "")).strip()
        run_mode = str(meta.get("run_mode", "")).strip()

        _assert_true(bool(title), f"元数据缺少标题：{rel}")
        _assert_true(bool(summary), f"元数据缺少学习目标：{rel}")
        _assert_true(bool(expected), f"元数据缺少预期输出：{rel}")
        _assert_true("?" not in summary and "?" not in expected, f"元数据含占位问号：{rel}")
        _assert_true(len(summary) >= 14, f"学习目标过短，信息不足：{rel}")
        _assert_true(len(expected) >= 14, f"预期输出过短，信息不足：{rel}")
        _assert_true(difficulty in flow.DIFFICULTY_VALUES, f"元数据难度非法：{difficulty} @ {rel}")
        _assert_true(domain in flow.DOMAIN_VALUES, f"元数据能力域非法：{domain} @ {rel}")
        _assert_true(run_mode in flow.RUN_MODE_VALUES, f"元数据运行属性非法：{run_mode} @ {rel}")
        default_summary, default_expected = flow._default_summary_expected(title, domain, run_mode)
        _assert_true(summary != default_summary, f"学习目标退化为默认模板：{rel}")
        _assert_true(expected != default_expected, f"预期输出退化为默认模板：{rel}")
    print("[OK] 示例元数据清单完整性检查通过")


def check_catalog_items() -> list[dict]:
    items = flow._build_example_items()
    _assert_true(items, "示例目录为空，无法构建示例中心列表")

    rels = {str(item.get("rel", "")) for item in items}
    required = {
        "M10综合测试.ym",
        "M11模块化测试.ym",
        "M12容错测试.ym",
        "经典案例_图纸对象入门.ym",
    }
    missing = sorted(required - rels)
    _assert_true(not missing, f"缺少关键示例：{missing}")

    difficulty_set = set()
    domain_set = set()
    run_mode_set = set()
    for item in items:
        title = str(item.get("title", "")).strip()
        summary = str(item.get("summary", "")).strip()
        expected = str(item.get("expected", "")).strip()
        difficulty = str(item.get("difficulty", ""))
        domain = str(item.get("domain", ""))
        run_mode = str(item.get("run_mode", ""))
        _assert_true(bool(title), f"示例条目缺少标题：{item.get('rel')}")
        _assert_true(bool(summary), f"示例条目缺少学习目标：{item.get('rel')}")
        _assert_true(bool(expected), f"示例条目缺少预期输出：{item.get('rel')}")
        _assert_true(difficulty in flow.DIFFICULTY_VALUES, f"非法难度：{difficulty} @ {item.get('rel')}")
        _assert_true(domain in flow.DOMAIN_VALUES, f"非法能力域：{domain} @ {item.get('rel')}")
        _assert_true(run_mode in flow.RUN_MODE_VALUES, f"非法运行属性：{run_mode} @ {item.get('rel')}")
        difficulty_set.add(difficulty)
        domain_set.add(domain)
        run_mode_set.add(run_mode)

    _assert_true(len(difficulty_set) == 3, f"难度分层不完整：{sorted(difficulty_set)}")
    _assert_true(len(domain_set) >= 4, f"能力域覆盖不足：{sorted(domain_set)}")
    _assert_true("自动可跑" in run_mode_set, "应至少包含自动可跑示例")
    _assert_true("本地数据库" in run_mode_set, "应至少包含本地数据库示例")
    _assert_true("需要网络" in run_mode_set, "应至少包含需要网络示例")
    print("[OK] 示例分类元数据检查通过")
    return items


def check_filter_matcher(items: list[dict]) -> None:
    network_item = next((x for x in items if x.get("run_mode") == "需要网络"), None)
    _assert_true(network_item is not None, "未找到网络示例，无法验证运行属性筛选")
    rel = str(network_item.get("rel", ""))
    query = rel.split("/", 1)[-1].split(".", 1)[0][:3]
    _assert_true(
        flow._example_matches(network_item, query=query, run_mode="需要网络"),
        f"筛选匹配失败（网络示例应命中）：{rel}",
    )
    _assert_true(
        not flow._example_matches(network_item, query=query, run_mode="本地数据库"),
        f"筛选匹配失败（网络示例不应命中数据库过滤）：{rel}",
    )

    beginner_item = next((x for x in items if x.get("difficulty") == "入门"), None)
    _assert_true(beginner_item is not None, "未找到入门示例，无法验证难度筛选")
    _assert_true(
        flow._example_matches(beginner_item, difficulty="入门"),
        f"难度筛选失败（入门示例应命中）：{beginner_item.get('rel')}",
    )
    _assert_true(
        not flow._example_matches(beginner_item, difficulty="实战"),
        f"难度筛选失败（入门示例不应命中实战）：{beginner_item.get('rel')}",
    )
    print("[OK] 示例筛选匹配规则通过")


def main() -> int:
    print("=== 示例目录与分类回归开始 ===")
    check_builtin_sync()
    check_manifest_integrity()
    items = check_catalog_items()
    check_filter_matcher(items)
    print("=== 示例目录与分类回归完成：全部通过 ===")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as e:
        safe = str(e).encode("unicode_escape", errors="replace").decode("ascii", errors="replace")
        print(f"[FAIL] 示例目录与分类回归失败: {safe}")
        raise SystemExit(1)
