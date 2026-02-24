"""Examples center flow: browse bundled examples in-editor."""

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

import tkinter as tk
import json
from pathlib import Path
from tkinter import ttk


MODULE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = MODULE_DIR.parent
BUILTIN_EXAMPLES_DIR = MODULE_DIR / "builtin_examples"
LOCAL_EXAMPLES_DIR = PROJECT_ROOT / "示例"
MANIFEST_PATH = MODULE_DIR / "builtin_examples_manifest.json"

DIFFICULTY_VALUES = ("入门", "进阶", "实战")
DOMAIN_VALUES = ("语法基础", "模块组织", "图纸对象", "图形界面", "文件系统", "网络通信", "本地数据库", "综合实战")
RUN_MODE_VALUES = ("自动可跑", "手动交互", "需要网络", "本地数据库")

FILTER_ALL_DIFFICULTY = "全部难度"
FILTER_ALL_DOMAIN = "全部能力域"
FILTER_ALL_RUN_MODE = "全部运行属性"

_MANIFEST_CACHE: dict[str, dict] | None = None


def _preferred_examples_geometry(owner):
    try:
        owner.root.update_idletasks()
    except Exception:
        pass

    screen_w = max(1000, int(owner.root.winfo_screenwidth()))
    screen_h = max(760, int(owner.root.winfo_screenheight()))
    try:
        root_w = int(owner.root.winfo_width() or 0)
        root_h = int(owner.root.winfo_height() or 0)
    except Exception:
        root_w, root_h = 0, 0

    base_w = max(1120, int(root_w * 0.86)) if root_w > 0 else 1220
    base_h = max(760, int(root_h * 0.84)) if root_h > 0 else 800
    width = min(base_w, int(screen_w * 0.94))
    height = min(base_h, int(screen_h * 0.92))
    return max(1040, width), max(700, height)


def _center_to_owner(owner, win, width=None, height=None):
    try:
        owner.root.update_idletasks()
        win.update_idletasks()
    except Exception:
        pass

    if width is None or height is None:
        width, height = _preferred_examples_geometry(owner)

    try:
        root_x = int(owner.root.winfo_x() or 0)
        root_y = int(owner.root.winfo_y() or 0)
        root_w = int(owner.root.winfo_width() or width)
        root_h = int(owner.root.winfo_height() or height)
    except Exception:
        root_x, root_y = 0, 0
        root_w, root_h = width, height

    screen_w = max(width, int(owner.root.winfo_screenwidth()))
    screen_h = max(height, int(owner.root.winfo_screenheight()))
    x = root_x + max(0, (root_w - width) // 2)
    y = root_y + max(0, (root_h - height) // 2)
    x = max(0, min(x, screen_w - width))
    y = max(0, min(y, screen_h - height))
    try:
        win.geometry(f"{width}x{height}+{x}+{y}")
    except tk.TclError:
        pass


def _create_dark_entry(owner, parent, textvariable, width=None):
    kwargs = {
        "master": parent,
        "textvariable": textvariable,
        "font": owner.font_ui,
        "bg": owner.theme_panel_inner_bg,
        "fg": owner.theme_fg,
        "insertbackground": owner.theme_fg,
        "selectbackground": owner.theme_accent,
        "selectforeground": "#FFFFFF",
        "relief": "flat",
        "bd": 0,
        "highlightthickness": 1,
        "highlightbackground": owner.theme_toolbar_border,
        "highlightcolor": owner.theme_accent,
    }
    if width is not None:
        kwargs["width"] = int(width)
    entry = tk.Entry(**kwargs)

    def _on_focus_in(_event):
        try:
            entry.configure(highlightbackground=owner.theme_accent)
        except tk.TclError:
            pass

    def _on_focus_out(_event):
        try:
            entry.configure(highlightbackground=owner.theme_toolbar_border)
        except tk.TclError:
            pass

    entry.bind("<FocusIn>", _on_focus_in, add="+")
    entry.bind("<FocusOut>", _on_focus_out, add="+")
    return entry


def _source_dirs():
    pairs = []
    if BUILTIN_EXAMPLES_DIR.is_dir():
        pairs.append(("内置", BUILTIN_EXAMPLES_DIR))
    if LOCAL_EXAMPLES_DIR.is_dir():
        pairs.append(("本地", LOCAL_EXAMPLES_DIR))
    return pairs


def _default_summary_expected(title: str, domain: str, run_mode: str) -> tuple[str, str]:
    safe_title = str(title or "该示例").strip() or "该示例"
    safe_domain = str(domain or "语法基础").strip() or "语法基础"
    safe_run = str(run_mode or "自动可跑").strip() or "自动可跑"
    summary = f"通过《{safe_title}》学习「{safe_domain}」的核心用法，并理解在真实代码中的组织方式。"
    if safe_run == "手动交互":
        expected = "运行后会出现交互界面/输入流程；按提示操作且无报错即为通过。"
    elif safe_run == "需要网络":
        expected = "运行时需联网；请求成功并输出状态/结果且无报错即为通过。"
    elif safe_run == "本地数据库":
        expected = "运行后会创建或读写本地数据库文件，输出增删改查结果且无报错即为通过。"
    else:
        expected = "运行后应输出对应结果且无报错；输出细节以示例注释说明为准。"
    return summary, expected


def _normalize_manifest_meta(rel: str, raw: dict, fallback: dict) -> dict:
    meta = dict(fallback or {})
    title = str(raw.get("title", "")).strip() if isinstance(raw, dict) else ""
    summary = str(raw.get("summary", "")).strip() if isinstance(raw, dict) else ""
    expected = str(raw.get("expected", "")).strip() if isinstance(raw, dict) else ""
    difficulty = str(raw.get("difficulty", "")).strip() if isinstance(raw, dict) else ""
    domain = str(raw.get("domain", "")).strip() if isinstance(raw, dict) else ""
    run_mode = str(raw.get("run_mode", "")).strip() if isinstance(raw, dict) else ""

    if title:
        meta["title"] = title
    if difficulty in DIFFICULTY_VALUES:
        meta["difficulty"] = difficulty
    if domain in DOMAIN_VALUES:
        meta["domain"] = domain
    if run_mode in RUN_MODE_VALUES:
        meta["run_mode"] = run_mode

    if not summary or not expected:
        default_summary, default_expected = _default_summary_expected(
            meta.get("title", rel),
            meta.get("domain", "语法基础"),
            meta.get("run_mode", "自动可跑"),
        )
        summary = summary or default_summary
        expected = expected or default_expected

    meta["summary"] = summary
    meta["expected"] = expected
    return meta


def load_examples_manifest(force_reload: bool = False) -> dict[str, dict]:
    global _MANIFEST_CACHE
    if _MANIFEST_CACHE is not None and not force_reload:
        return dict(_MANIFEST_CACHE)

    if not MANIFEST_PATH.exists():
        _MANIFEST_CACHE = {}
        return {}
    try:
        data = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    except Exception:
        _MANIFEST_CACHE = {}
        return {}
    if not isinstance(data, dict):
        _MANIFEST_CACHE = {}
        return {}
    raw_examples = data.get("examples", {})
    if not isinstance(raw_examples, dict):
        _MANIFEST_CACHE = {}
        return {}

    manifest: dict[str, dict] = {}
    for rel, raw in raw_examples.items():
        rel_key = str(rel or "").strip().replace("\\", "/")
        if not rel_key or not isinstance(raw, dict):
            continue
        manifest[rel_key] = dict(raw)

    _MANIFEST_CACHE = manifest
    return dict(manifest)


def _infer_difficulty(rel: str, name: str) -> str:
    rel_text = str(rel or "").lower()
    stem = str(name or "").rsplit(".", 1)[0].lower()
    if stem.startswith("m") and len(stem) > 1 and stem[1].isdigit():
        number_text = []
        for ch in stem[1:]:
            if ch.isdigit():
                number_text.append(ch)
            else:
                break
        if number_text:
            num = int("".join(number_text))
            if num <= 5:
                return "入门"
            if num <= 12:
                return "进阶"
            return "实战"
    if any(k in rel_text for k in ("欢迎", "官方写法总览", "测试中文引号", "内置引入测试", "_测试列表", "数学库")):
        return "入门"
    if any(k in rel_text for k in ("完整演示", "点语法", "面向对象", "待办事项", "经典案例_图纸对象")):
        return "进阶"
    return "实战"


def _infer_domain(rel: str) -> str:
    rel_text = str(rel or "").lower()
    if any(k in rel_text for k in ("全量", "综合", "总览", "全模块", "实战_")):
        return "综合实战"
    if any(k in rel_text for k in ("界面", "gui", "画板", "贪吃蛇", "超级玛丽")):
        return "图形界面"
    if any(k in rel_text for k in ("数据库", "注册登录", "记账本", "任务协作")):
        return "本地数据库"
    if any(k in rel_text for k in ("网络", "下载", "http", "json")):
        return "网络通信"
    if any(k in rel_text for k in ("模块", "引入")):
        return "模块组织"
    if any(k in rel_text for k in ("图纸", "对象")):
        return "图纸对象"
    if any(k in rel_text for k in ("文件", "目录", "路径")):
        return "文件系统"
    return "语法基础"


def _infer_run_mode(rel: str) -> str:
    rel_text = str(rel or "").lower()
    if any(k in rel_text for k in ("手动", "交互", "游戏", "勇者", "贪吃蛇", "超级玛丽")):
        return "手动交互"
    if any(k in rel_text for k in ("网络", "下载", "http")):
        return "需要网络"
    if any(k in rel_text for k in ("数据库", "注册登录", "记账本", "任务协作")):
        return "本地数据库"
    return "自动可跑"


def _build_example_meta(rel: str, name: str) -> dict[str, str]:
    difficulty = _infer_difficulty(rel, name)
    if difficulty not in DIFFICULTY_VALUES:
        difficulty = "进阶"
    domain = _infer_domain(rel)
    if domain not in DOMAIN_VALUES:
        domain = "语法基础"
    run_mode = _infer_run_mode(rel)
    if run_mode not in RUN_MODE_VALUES:
        run_mode = "自动可跑"
    title = str(name or "").rsplit(".", 1)[0] or rel
    summary, expected = _default_summary_expected(title, domain, run_mode)
    return {
        "title": title,
        "difficulty": difficulty,
        "domain": domain,
        "run_mode": run_mode,
        "summary": summary,
        "expected": expected,
    }


def _build_example_items():
    items = []
    seen_rel = set()
    manifest = load_examples_manifest()
    for source_name, base_dir in _source_dirs():
        for path in sorted(base_dir.rglob("*.ym"), key=lambda p: p.as_posix().lower()):
            try:
                rel = path.relative_to(base_dir).as_posix()
            except Exception:
                rel = path.name
            rel_key = rel.lower()
            if rel_key in seen_rel:
                # 同名同路径优先采用内置版本
                continue
            seen_rel.add(rel_key)
            first = rel.split("/", 1)[0] if "/" in rel else "根目录"
            fallback_meta = _build_example_meta(rel, path.name)
            meta = _normalize_manifest_meta(rel, manifest.get(rel, {}), fallback_meta)
            difficulty = meta.get("difficulty", "进阶")
            domain = meta.get("domain", "语法基础")
            run_mode = meta.get("run_mode", "自动可跑")
            title = meta.get("title", path.stem)
            summary = meta.get("summary", "")
            expected = meta.get("expected", "")
            items.append(
                {
                    "source": source_name,
                    "path": str(path),
                    "rel": rel,
                    "group": first,
                    "name": path.name,
                    "title": title,
                    "difficulty": difficulty,
                    "domain": domain,
                    "run_mode": run_mode,
                    "summary": summary,
                    "expected": expected,
                    "display": _format_example_list_label(
                        title=title,
                        difficulty=difficulty,
                        domain=domain,
                        run_mode=run_mode,
                        group=first,
                        source=source_name,
                    ),
                    "content": None,
                }
            )
    return items


def _format_example_list_label(
    *,
    title: str,
    difficulty: str,
    domain: str,
    run_mode: str,
    group: str,
    source: str,
) -> str:
    raw_title = str(title or "").strip() or "未命名示例"
    # 左侧列表优先展示名称，其次展示分类，避免长路径挤占可读空间。
    tags = f"{difficulty}·{domain}·{run_mode}"
    group_text = str(group or "").strip()
    if not group_text or group_text == "根目录":
        return f"{raw_title}   [{tags}]   ({source})"
    return f"{raw_title}   [{tags}]   <{group_text}> ({source})"


def _selected_example(owner):
    listbox = getattr(owner, "_examples_listbox", None)
    visible = getattr(owner, "_examples_items_visible", None)
    if listbox is None or not isinstance(visible, list):
        return None
    sel = listbox.curselection()
    if not sel:
        return None
    idx = int(sel[0])
    if idx < 0 or idx >= len(visible):
        return None
    return visible[idx]


def _read_example_text(item):
    cached = item.get("content")
    if isinstance(cached, str):
        return cached
    path = Path(item.get("path", ""))
    try:
        text = path.read_text(encoding="utf-8")
    except Exception as e:
        text = f"读取示例失败：{e}\n路径：{path}"
    item["content"] = text
    return text


def _render_example_preview(owner, item):
    text_widget = getattr(owner, "_examples_preview", None)
    status_var = getattr(owner, "_examples_status_var", None)
    if text_widget is None or status_var is None:
        return
    if not item:
        text = "当前没有可预览示例。"
        status = "示例中心：暂无示例"
    else:
        code = _read_example_text(item)
        text = (
            f"# 标题：{item.get('title', item.get('name', ''))}\n"
            f"# 学习目标：{item.get('summary', '')}\n"
            f"# 预期输出：{item.get('expected', '')}\n"
            f"# 分类：{item.get('difficulty', '')} / {item.get('domain', '')} / {item.get('run_mode', '')}\n"
            f"# 来源：{item.get('source', '')} | 路径：{item.get('rel', '')}\n"
            "------------------------------------------------------------\n"
            f"{code}"
        )
        status = (
            f"示例：{item.get('rel', '')} | "
            f"难度：{item.get('difficulty', '')} | "
            f"能力域：{item.get('domain', '')} | "
            f"运行属性：{item.get('run_mode', '')} | "
            f"来源：{item.get('source', '')}"
        )
    try:
        text_widget.configure(state=tk.NORMAL)
        text_widget.delete("1.0", tk.END)
        text_widget.insert("1.0", text)
        text_widget.configure(state=tk.DISABLED)
        text_widget.see("1.0")
    except tk.TclError:
        return
    status_var.set(status)


def _render_example_list(owner, items):
    listbox = getattr(owner, "_examples_listbox", None)
    if listbox is None:
        return
    owner._examples_items_visible = list(items or [])
    try:
        listbox.delete(0, tk.END)
        for item in owner._examples_items_visible:
            listbox.insert(tk.END, item.get("display", item.get("rel", "")))
        if owner._examples_items_visible:
            listbox.selection_set(0)
            listbox.activate(0)
            _render_example_preview(owner, owner._examples_items_visible[0])
        else:
            _render_example_preview(owner, None)
    except tk.TclError:
        pass


def _example_matches(
    item: dict,
    *,
    query: str = "",
    difficulty: str = FILTER_ALL_DIFFICULTY,
    domain: str = FILTER_ALL_DOMAIN,
    run_mode: str = FILTER_ALL_RUN_MODE,
) -> bool:
    q = str(query or "").strip().lower()
    if q:
        haystack = " ".join(
            [
                str(item.get("rel", "")),
                str(item.get("group", "")),
                str(item.get("name", "")),
                str(item.get("title", "")),
                str(item.get("source", "")),
                str(item.get("difficulty", "")),
                str(item.get("domain", "")),
                str(item.get("run_mode", "")),
                str(item.get("summary", "")),
                str(item.get("expected", "")),
            ]
        ).lower()
        if q not in haystack:
            return False
    if difficulty and difficulty != FILTER_ALL_DIFFICULTY and str(item.get("difficulty", "")) != difficulty:
        return False
    if domain and domain != FILTER_ALL_DOMAIN and str(item.get("domain", "")) != domain:
        return False
    if run_mode and run_mode != FILTER_ALL_RUN_MODE and str(item.get("run_mode", "")) != run_mode:
        return False
    return True


def _apply_example_filter(owner):
    all_items = getattr(owner, "_examples_items_all", []) or []
    query_var = getattr(owner, "_examples_query_var", None)
    query = str(query_var.get()).strip().lower() if query_var is not None else ""
    difficulty_var = getattr(owner, "_examples_difficulty_var", None)
    domain_var = getattr(owner, "_examples_domain_var", None)
    run_mode_var = getattr(owner, "_examples_run_mode_var", None)
    difficulty = str(difficulty_var.get()).strip() if difficulty_var is not None else FILTER_ALL_DIFFICULTY
    domain = str(domain_var.get()).strip() if domain_var is not None else FILTER_ALL_DOMAIN
    run_mode = str(run_mode_var.get()).strip() if run_mode_var is not None else FILTER_ALL_RUN_MODE
    visible = [item for item in all_items if _example_matches(item, query=query, difficulty=difficulty, domain=domain, run_mode=run_mode)]
    _render_example_list(owner, visible)


def _update_examples_filter_status(owner):
    visible = getattr(owner, "_examples_items_visible", []) or []
    query = owner._examples_query_var.get().strip() if hasattr(owner, "_examples_query_var") else ""
    difficulty = owner._examples_difficulty_var.get().strip() if hasattr(owner, "_examples_difficulty_var") else FILTER_ALL_DIFFICULTY
    domain = owner._examples_domain_var.get().strip() if hasattr(owner, "_examples_domain_var") else FILTER_ALL_DOMAIN
    run_mode = owner._examples_run_mode_var.get().strip() if hasattr(owner, "_examples_run_mode_var") else FILTER_ALL_RUN_MODE
    if hasattr(owner, "status_main_var"):
        owner.status_main_var.set(
            "示例筛选："
            + (query if query else "（无关键字）")
            + f" | {difficulty} | {domain} | {run_mode}（命中 {len(visible)} 个）"
        )


def _on_examples_query_changed(owner, event=None):
    del event
    _apply_example_filter(owner)
    _update_examples_filter_status(owner)


def _on_examples_filter_changed(owner, event=None):
    del event
    _apply_example_filter(owner)
    _update_examples_filter_status(owner)


def _on_examples_select(owner, event=None):
    del event
    _render_example_preview(owner, _selected_example(owner))


def _open_selected_example_in_editor(owner, event=None):
    item = _selected_example(owner)
    if not item:
        if hasattr(owner, "status_main_var"):
            owner.status_main_var.set("请先在示例中心选择一个示例")
        return "break"
    path = str(item.get("path", ""))
    text = _read_example_text(item)
    owner._create_editor_tab(path, text)
    if hasattr(owner, "status_main_var"):
        owner.status_main_var.set(f"已打开示例：{item.get('rel', '')}")
    return "break" if event is not None else None


def _run_selected_example(owner, event=None):
    item = _selected_example(owner)
    if not item:
        if hasattr(owner, "status_main_var"):
            owner.status_main_var.set("请先在示例中心选择一个示例")
        return "break"
    _open_selected_example_in_editor(owner)
    owner.run_code()
    if hasattr(owner, "status_main_var"):
        owner.status_main_var.set(f"已运行示例：{item.get('rel', '')}")
    return "break" if event is not None else None


def _refresh_examples(owner, event=None):
    owner._examples_items_all = _build_example_items()
    _apply_example_filter(owner)
    total = len(owner._examples_items_all or [])
    if hasattr(owner, "status_main_var"):
        owner.status_main_var.set(f"示例中心已刷新（共 {total} 个）")
    return "break" if event is not None else None


def _ensure_examples_window(owner):
    win = getattr(owner, "_examples_window", None)
    if win is not None:
        try:
            if win.winfo_exists():
                return win
        except tk.TclError:
            pass

    win = tk.Toplevel(owner.root)
    win.title("易码示例中心")
    init_w, init_h = _preferred_examples_geometry(owner)
    _center_to_owner(owner, win, init_w, init_h)
    win.configure(bg=owner.theme_bg)
    try:
        win.minsize(1040, 700)
    except tk.TclError:
        pass
    win.protocol("WM_DELETE_WINDOW", win.withdraw)

    top = tk.Frame(win, bg=owner.theme_toolbar_bg, padx=10, pady=8)
    top.pack(fill=tk.X)

    tk.Label(
        top,
        text="示例中心 EXAMPLES",
        font=("Microsoft YaHei", 10, "bold"),
        bg=owner.theme_toolbar_bg,
        fg="#DFE6EE",
    ).pack(side=tk.LEFT)

    owner._examples_query_var = tk.StringVar(value="")
    query_entry = _create_dark_entry(owner, top, owner._examples_query_var, width=28)
    query_entry.pack(side=tk.RIGHT, padx=(8, 0))
    owner._examples_query_entry = query_entry

    owner._examples_run_mode_var = tk.StringVar(value=FILTER_ALL_RUN_MODE)
    run_mode_box = ttk.Combobox(
        top,
        textvariable=owner._examples_run_mode_var,
        state="readonly",
        values=(FILTER_ALL_RUN_MODE, *RUN_MODE_VALUES),
        width=10,
    )
    run_mode_box.pack(side=tk.RIGHT, padx=(8, 0))

    owner._examples_domain_var = tk.StringVar(value=FILTER_ALL_DOMAIN)
    domain_box = ttk.Combobox(
        top,
        textvariable=owner._examples_domain_var,
        state="readonly",
        values=(FILTER_ALL_DOMAIN, *DOMAIN_VALUES),
        width=10,
    )
    domain_box.pack(side=tk.RIGHT, padx=(8, 0))

    owner._examples_difficulty_var = tk.StringVar(value=FILTER_ALL_DIFFICULTY)
    difficulty_box = ttk.Combobox(
        top,
        textvariable=owner._examples_difficulty_var,
        state="readonly",
        values=(FILTER_ALL_DIFFICULTY, *DIFFICULTY_VALUES),
        width=8,
    )
    difficulty_box.pack(side=tk.RIGHT, padx=(8, 0))

    run_btn = tk.Button(
        top,
        text="运行示例",
        command=lambda: _run_selected_example(owner),
        font=("Microsoft YaHei", 8),
        bg=owner.theme_toolbar_group_bg,
        fg=owner.theme_toolbar_fg,
        activebackground=owner.theme_toolbar_hover,
        activeforeground="#FFFFFF",
        relief="flat",
        bd=0,
        padx=8,
        pady=2,
        cursor="hand2",
    )
    run_btn.pack(side=tk.RIGHT)

    open_btn = tk.Button(
        top,
        text="打开到编辑区",
        command=lambda: _open_selected_example_in_editor(owner),
        font=("Microsoft YaHei", 8),
        bg=owner.theme_toolbar_group_bg,
        fg=owner.theme_toolbar_fg,
        activebackground=owner.theme_toolbar_hover,
        activeforeground="#FFFFFF",
        relief="flat",
        bd=0,
        padx=8,
        pady=2,
        cursor="hand2",
    )
    open_btn.pack(side=tk.RIGHT, padx=(0, 6))

    refresh_btn = tk.Button(
        top,
        text="刷新",
        command=lambda: _refresh_examples(owner),
        font=("Microsoft YaHei", 8),
        bg=owner.theme_toolbar_group_bg,
        fg=owner.theme_toolbar_fg,
        activebackground=owner.theme_toolbar_hover,
        activeforeground="#FFFFFF",
        relief="flat",
        bd=0,
        padx=8,
        pady=2,
        cursor="hand2",
    )
    refresh_btn.pack(side=tk.RIGHT, padx=(0, 6))

    body = tk.PanedWindow(win, orient=tk.HORIZONTAL, sashwidth=5, bg=owner.theme_sash, borderwidth=0)
    body.pack(fill=tk.BOTH, expand=True)

    left = tk.Frame(body, bg=owner.theme_panel_bg, width=460)
    body.add(left, stretch="never", minsize=400)
    tk.Label(
        left,
        text="示例列表",
        font=("Microsoft YaHei", 9, "bold"),
        bg=owner.theme_panel_bg,
        fg="#9FB0C5",
        anchor="w",
        padx=10,
        pady=6,
    ).pack(fill=tk.X)
    tk.Label(
        left,
        text="单击查看详情，双击或回车打开到编辑区",
        font=("Microsoft YaHei", 8),
        bg=owner.theme_panel_bg,
        fg="#7F90A8",
        anchor="w",
        padx=10,
        pady=0,
    ).pack(fill=tk.X, pady=(0, 4))
    list_box = tk.Frame(left, bg=owner.theme_panel_bg, padx=8, pady=0)
    list_box.pack(fill=tk.BOTH, expand=True, pady=(0, 8))
    listbox = tk.Listbox(
        list_box,
        font=("Microsoft YaHei", 10),
        bg=owner.theme_panel_inner_bg,
        fg=owner.theme_fg,
        selectbackground=owner.theme_accent,
        selectforeground="#FFFFFF",
        borderwidth=0,
        highlightthickness=0,
        relief="flat",
    )
    list_vsb = ttk.Scrollbar(list_box, orient="vertical", command=listbox.yview)
    listbox.configure(yscrollcommand=list_vsb.set)
    listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    list_vsb.pack(side=tk.RIGHT, fill=tk.Y)
    owner._examples_listbox = listbox

    right = tk.Frame(body, bg=owner.theme_panel_bg)
    body.add(right, stretch="always", minsize=500)
    tk.Label(
        right,
        text="代码预览（只读）",
        font=("Microsoft YaHei", 9, "bold"),
        bg=owner.theme_panel_bg,
        fg="#9FB0C5",
        anchor="w",
        padx=10,
        pady=6,
    ).pack(fill=tk.X)
    preview_box = tk.Frame(right, bg=owner.theme_panel_bg, padx=8, pady=0)
    preview_box.pack(fill=tk.BOTH, expand=True, pady=(0, 8))
    preview = tk.Text(
        preview_box,
        wrap=tk.NONE,
        font=("Microsoft YaHei", 10),
        bg=owner.theme_bg,
        fg="#D7E0EC",
        insertbackground="#D7E0EC",
        borderwidth=0,
        highlightthickness=0,
        relief="flat",
        padx=10,
        pady=8,
    )
    p_vsb = ttk.Scrollbar(preview_box, orient="vertical", command=preview.yview)
    p_hsb = ttk.Scrollbar(preview_box, orient="horizontal", command=preview.xview)
    preview.configure(yscrollcommand=p_vsb.set, xscrollcommand=p_hsb.set, state=tk.DISABLED)
    preview.grid(column=0, row=0, sticky="nsew")
    p_vsb.grid(column=1, row=0, sticky="ns")
    p_hsb.grid(column=0, row=1, sticky="ew")
    preview_box.grid_columnconfigure(0, weight=1)
    preview_box.grid_rowconfigure(0, weight=1)
    owner._examples_preview = preview

    owner._examples_status_var = tk.StringVar(value="可按文件名/目录搜索示例，回车可直接打开。")
    tk.Label(
        win,
        textvariable=owner._examples_status_var,
        font=("Microsoft YaHei", 8),
        bg=owner.theme_toolbar_bg,
        fg="#9FB0C5",
        anchor="w",
        padx=10,
        pady=5,
    ).pack(fill=tk.X, side=tk.BOTTOM)

    query_entry.bind("<KeyRelease>", lambda e: _on_examples_query_changed(owner, e), add="+")
    query_entry.bind("<Return>", lambda e: _open_selected_example_in_editor(owner, e), add="+")
    difficulty_box.bind("<<ComboboxSelected>>", lambda e: _on_examples_filter_changed(owner, e), add="+")
    domain_box.bind("<<ComboboxSelected>>", lambda e: _on_examples_filter_changed(owner, e), add="+")
    run_mode_box.bind("<<ComboboxSelected>>", lambda e: _on_examples_filter_changed(owner, e), add="+")
    listbox.bind("<<ListboxSelect>>", lambda e: _on_examples_select(owner, e), add="+")
    listbox.bind("<Double-Button-1>", lambda e: _open_selected_example_in_editor(owner, e), add="+")
    listbox.bind("<Return>", lambda e: _open_selected_example_in_editor(owner, e), add="+")
    win.bind("<Escape>", lambda e: win.withdraw(), add="+")
    win.bind("<Control-f>", lambda e: owner._examples_query_entry.focus_set(), add="+")
    win.bind("<F5>", lambda e: _refresh_examples(owner, e), add="+")
    win.bind("<Control-r>", lambda e: _run_selected_example(owner, e), add="+")

    owner._examples_window = win
    owner._examples_items_all = []
    owner._examples_items_visible = []
    try:
        body.sash_place(0, 460, 1)
    except tk.TclError:
        pass
    return win


def open_examples(owner, event=None):
    win = _ensure_examples_window(owner)
    _refresh_examples(owner)
    try:
        cur_w, cur_h = _preferred_examples_geometry(owner)
        _center_to_owner(owner, win, cur_w, cur_h)
        win.deiconify()
        win.lift()
        win.focus_force()
        owner._examples_query_entry.focus_set()
    except tk.TclError:
        pass
    if hasattr(owner, "status_main_var"):
        owner.status_main_var.set("示例中心已打开（可搜索 / 双击打开 / 一键运行）")
    return "break" if event is not None else None
