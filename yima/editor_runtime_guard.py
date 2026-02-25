"""Runtime guard for editor reliability: logging, crash snapshot, recovery hint."""

from __future__ import annotations

import json
import logging
import os
import shutil
import sys
import threading
import time
import traceback
from difflib import SequenceMatcher
from datetime import datetime
from logging.handlers import RotatingFileHandler
from pathlib import Path
import tkinter as tk
from tkinter import messagebox


def _now_text() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _safe_text(value, max_len: int = 8000) -> str:
    text = str(value or "")
    if len(text) > max_len:
        return text[:max_len] + " ...[truncated]"
    return text


def _ensure_dir(path: str) -> str:
    Path(path).mkdir(parents=True, exist_ok=True)
    return path


def _configure_logger(log_dir: str) -> tuple[logging.Logger, str]:
    _ensure_dir(log_dir)
    log_file = str(Path(log_dir) / "editor.log")
    logger = logging.getLogger("yima.ide")
    logger.setLevel(logging.INFO)
    logger.propagate = False
    if not any(getattr(h, "baseFilename", "") == os.path.abspath(log_file) for h in logger.handlers):
        handler = RotatingFileHandler(
            log_file,
            maxBytes=2 * 1024 * 1024,
            backupCount=5,
            encoding="utf-8",
        )
        handler.setLevel(logging.INFO)
        handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
        logger.addHandler(handler)
    return logger, log_file


def _collect_open_tabs(owner, max_count: int = 20) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    tabs_data = getattr(owner, "tabs_data", {})
    for tab_id, data in list(tabs_data.items())[: max(1, int(max_count))]:
        filepath = str(data.get("filepath") or "")
        item = {
            "tab_id": str(tab_id),
            "filepath": filepath,
            "dirty": bool(data.get("dirty")),
        }
        rows.append(item)
    return rows


def _dump_recovery_snapshot(owner, reason: str, trace_text: str) -> str | None:
    recovery_root = getattr(owner, "_recovery_dir", "")
    if not recovery_root:
        return None

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    target = Path(recovery_root) / f"snapshot_{timestamp}"
    target.mkdir(parents=True, exist_ok=True)

    metadata = {
        "created_at": _now_text(),
        "reason": _safe_text(reason, 400),
        "trace": _safe_text(trace_text, 12000),
        "workspace_dir": str(getattr(owner, "workspace_dir", "") or ""),
        "last_open_file": str(getattr(owner, "last_open_file", "") or ""),
        "open_tabs": _collect_open_tabs(owner),
        "files": [],
    }

    tabs_data = getattr(owner, "tabs_data", {})
    seq = 0
    for _tab_id, data in tabs_data.items():
        editor = data.get("editor")
        if editor is None:
            continue
        try:
            content = editor.get("1.0", "end-1c")
        except Exception:
            continue
        seq += 1
        src_name = str(data.get("filepath") or f"untitled-{seq}.ym")
        safe_name = Path(src_name).name or f"untitled-{seq}.ym"
        out_name = f"{seq:02d}_{safe_name}.recover"
        out_path = target / out_name
        try:
            out_path.write_text(str(content), encoding="utf-8")
            metadata["files"].append({"source": src_name, "snapshot": out_name})
        except Exception:
            continue

    (target / "meta.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
    return str(target)


def _write_latest_recovery(owner, reason: str, trace_text: str, snapshot_dir: str | None) -> None:
    info_file = getattr(owner, "_recovery_info_file", "")
    if not info_file:
        return
    payload = {
        "created_at": _now_text(),
        "reason": _safe_text(reason, 400),
        "trace": _safe_text(trace_text, 12000),
        "snapshot_dir": str(snapshot_dir or ""),
        "log_file": str(getattr(owner, "_log_file", "") or ""),
    }
    Path(info_file).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _clear_latest_recovery(owner) -> None:
    info_file = getattr(owner, "_recovery_info_file", "")
    if not info_file:
        return
    try:
        Path(info_file).unlink(missing_ok=True)
    except Exception:
        pass


def _report_unhandled_exception(owner, reason: str, exc_type, exc_value, exc_tb) -> None:
    trace_text = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
    logger = getattr(owner, "_logger", None)
    if logger is not None:
        logger.error("Unhandled exception (%s):\n%s", reason, trace_text)

    snapshot_dir = _dump_recovery_snapshot(owner, reason, trace_text)
    _write_latest_recovery(owner, reason, trace_text, snapshot_dir)

    try:
        saver = getattr(owner, "_save_project_state", None)
        if callable(saver):
            saver()
    except Exception:
        pass

    root = getattr(owner, "root", None)
    if root is not None and not getattr(owner, "_error_dialog_showing", False):
        owner._error_dialog_showing = True
        detail = f"异常已记录到日志：\n{getattr(owner, '_log_file', '')}"
        if snapshot_dir:
            detail += f"\n恢复快照目录：\n{snapshot_dir}"
        detail += "\n\n建议重启编辑器后继续工作。"
        try:
            messagebox.showerror("易码编辑器异常", detail, parent=root)
        except Exception:
            pass
        finally:
            owner._error_dialog_showing = False


def setup_runtime_guard(owner) -> None:
    state_dir = str(getattr(owner, "_state_dir", "") or "")
    if not state_dir:
        state_dir = str(Path.home() / ".yima_ide")
        owner._state_dir = state_dir
    log_dir = _ensure_dir(str(Path(state_dir) / "logs"))
    recovery_dir = _ensure_dir(str(Path(state_dir) / "recovery"))
    recovery_info_file = str(Path(state_dir) / "last_recovery.json")

    logger, log_file = _configure_logger(log_dir)
    owner._logger = logger
    owner._log_file = log_file
    owner._recovery_dir = recovery_dir
    owner._recovery_info_file = recovery_info_file
    owner._error_dialog_showing = False

    logger.info("Editor started. pid=%s python=%s", os.getpid(), sys.version.split()[0])

    old_sys_hook = sys.excepthook

    def _sys_hook(exc_type, exc_value, exc_tb):
        _report_unhandled_exception(owner, "sys.excepthook", exc_type, exc_value, exc_tb)
        try:
            old_sys_hook(exc_type, exc_value, exc_tb)
        except Exception:
            pass

    sys.excepthook = _sys_hook

    if hasattr(threading, "excepthook"):
        old_thread_hook = threading.excepthook

        def _thread_hook(args):
            _report_unhandled_exception(
                owner,
                f"threading.excepthook:{getattr(args, 'thread', None)}",
                args.exc_type,
                args.exc_value,
                args.exc_traceback,
            )
            try:
                old_thread_hook(args)
            except Exception:
                pass

        threading.excepthook = _thread_hook

    root = getattr(owner, "root", None)
    if root is not None:
        def _tk_hook(exc_type, exc_value, exc_tb):
            _report_unhandled_exception(owner, "tk.callback", exc_type, exc_value, exc_tb)

        root.report_callback_exception = _tk_hook


def announce_last_recovery(owner) -> None:
    info_file = getattr(owner, "_recovery_info_file", "")
    if not info_file or not os.path.isfile(info_file):
        return
    try:
        raw = Path(info_file).read_text(encoding="utf-8")
        data = json.loads(raw)
    except Exception:
        return
    if not isinstance(data, dict):
        return

    created_at = str(data.get("created_at") or "未知时间")
    snapshot_dir = str(data.get("snapshot_dir") or "")
    log_file = str(data.get("log_file") or getattr(owner, "_log_file", ""))
    lines = [f"检测到上次运行异常（{created_at}）。"]
    if snapshot_dir:
        lines.append(f"恢复快照：{snapshot_dir}")
    if log_file:
        lines.append(f"日志文件：{log_file}")
    lines.append("已保留恢复数据，你可以按需手动恢复。")
    message = "\n".join(lines)

    root = getattr(owner, "root", None)
    try:
        if root is not None:
            messagebox.showwarning("检测到异常恢复信息", message, parent=root)
        else:
            messagebox.showwarning("检测到异常恢复信息", message)
    except Exception:
        pass


def mark_clean_exit(owner) -> None:
    logger = getattr(owner, "_logger", None)
    if logger is not None:
        logger.info("Editor exited normally.")
    _clear_latest_recovery(owner)


def log_owner_event(owner, level: str, message: str) -> None:
    logger = getattr(owner, "_logger", None)
    if logger is None:
        return
    text = _safe_text(message, 4000)
    lv = str(level or "info").strip().lower()
    if lv == "error":
        logger.error(text)
    elif lv == "warning":
        logger.warning(text)
    else:
        logger.info(text)


def _load_last_recovery(owner) -> dict:
    info_file = str(getattr(owner, "_recovery_info_file", "") or "")
    if not info_file or not os.path.isfile(info_file):
        return {}
    try:
        raw = Path(info_file).read_text(encoding="utf-8")
        data = json.loads(raw)
    except Exception:
        return {}
    return data if isinstance(data, dict) else {}


def _open_path_in_system(path: str) -> bool:
    target = str(path or "").strip()
    if not target:
        return False
    try:
        if os.name == "nt":
            os.startfile(target)
            return True
        return False
    except Exception:
        return False


def _restore_report_dir(owner) -> str:
    state_dir = str(getattr(owner, "_state_dir", "") or "").strip()
    if not state_dir:
        return ""
    path = Path(state_dir) / "audit" / "restore_reports"
    return str(path)


def _list_restore_reports(owner, max_count: int = 80) -> list[str]:
    report_dir = _restore_report_dir(owner)
    if not report_dir:
        return []
    root = Path(report_dir)
    if not root.is_dir():
        return []
    files = [p for p in root.iterdir() if p.is_file() and p.suffix.lower() == ".json"]
    files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return [str(p) for p in files[: max(1, int(max_count))]]


def _latest_restore_report_summary(owner) -> dict:
    reports = _list_restore_reports(owner, max_count=1)
    if not reports:
        return {}
    path = reports[0]
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except Exception:
        return {}
    if not isinstance(data, dict):
        return {}
    diff = data.get("diff") or {}
    if not isinstance(diff, dict):
        diff = {}
    return {
        "path": path,
        "created_at": str(data.get("created_at") or "未知"),
        "old_name": str(data.get("old_name") or ""),
        "new_name": str(data.get("new_name") or ""),
        "success": int(data.get("success") or 0),
        "failed": int(data.get("failed") or 0),
        "changed_files": int(diff.get("changed_files") or 0),
        "changed_lines": int(diff.get("changed_lines") or 0),
    }


def _write_audit_event(owner, event_type: str, payload: dict | None = None) -> None:
    state_dir = str(getattr(owner, "_state_dir", "") or "").strip()
    if not state_dir:
        return
    audit_dir = Path(state_dir) / "audit"
    audit_dir.mkdir(parents=True, exist_ok=True)
    row = {
        "time": datetime.now().isoformat(timespec="seconds"),
        "event": str(event_type or "unknown"),
        "workspace_dir": str(getattr(owner, "workspace_dir", "") or ""),
        "payload": payload if isinstance(payload, dict) else {},
    }
    try:
        with open(audit_dir / "editor_audit.jsonl", "a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    except Exception:
        pass


def _list_rename_backups(owner, max_count: int = 40) -> list[dict]:
    state_dir = str(getattr(owner, "_state_dir", "") or "").strip()
    if not state_dir:
        return []
    base = Path(state_dir) / "rename_backups"
    if not base.is_dir():
        return []

    rows = []
    for item in sorted(base.iterdir(), key=lambda p: p.stat().st_mtime, reverse=True):
        if not item.is_dir():
            continue
        manifest_path = item / "manifest.json"
        if not manifest_path.is_file():
            continue
        try:
            data = json.loads(manifest_path.read_text(encoding="utf-8"))
        except Exception:
            continue
        if not isinstance(data, dict):
            continue
        files = data.get("files") or []
        if not isinstance(files, list):
            files = []
        rows.append(
            {
                "dir": str(item),
                "manifest": str(manifest_path),
                "created_at": str(data.get("created_at") or "未知"),
                "old_name": str(data.get("old_name") or ""),
                "new_name": str(data.get("new_name") or ""),
                "files": files,
                "file_count": len(files),
                "replace_count": int(sum(int(x.get("count", 0)) for x in files if isinstance(x, dict))),
            }
        )
        if len(rows) >= max(1, int(max_count)):
            break
    return rows


def _restore_backup_manifest(
    owner,
    manifest_row: dict,
    selected_sources: set[str] | None = None,
    result_rows: list[dict] | None = None,
) -> tuple[int, int]:
    files = manifest_row.get("files") or []
    if not isinstance(files, list):
        return 0, 0
    selected = set(selected_sources or [])
    ok = 0
    fail = 0
    for row in files:
        if not isinstance(row, dict):
            continue
        src = str(row.get("source") or "").strip()
        bak = str(row.get("backup") or "").strip()
        rel = str(row.get("relative") or src)
        if selected and src not in selected:
            continue
        if not src or not bak:
            fail += 1
            if isinstance(result_rows, list):
                result_rows.append({"source": src, "relative": rel, "status": "failed", "reason": "missing-path"})
            continue
        try:
            Path(src).parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(bak, src)
            ok += 1
            if isinstance(result_rows, list):
                result_rows.append({"source": src, "relative": rel, "status": "restored"})
            tab_id = None
            tabs_data = getattr(owner, "tabs_data", {})
            for tid, data in tabs_data.items():
                tab_path = str(data.get("filepath") or "")
                if os.path.normcase(tab_path) == os.path.normcase(src):
                    tab_id = tid
                    break
            if tab_id and tab_id in tabs_data:
                data = tabs_data[tab_id]
                editor = data.get("editor")
                if editor is not None:
                    text = Path(src).read_text(encoding="utf-8")
                    editor.delete("1.0", "end")
                    editor.insert("1.0", text)
                    editor.edit_modified(False)
                data["dirty"] = False
                updater = getattr(owner, "_update_tab_title", None)
                if callable(updater):
                    updater(tab_id)
        except Exception:
            fail += 1
            if isinstance(result_rows, list):
                result_rows.append({"source": src, "relative": rel, "status": "failed", "reason": "exception"})
            continue

    refresher = getattr(owner, "refresh_file_tree", None)
    if callable(refresher):
        try:
            refresher()
        except Exception:
            pass
    if callable(getattr(owner, "_update_status_main", None)):
        try:
            owner._update_status_main()
        except Exception:
            pass
    if callable(getattr(owner, "_schedule_diagnose", None)):
        try:
            owner._schedule_diagnose()
        except Exception:
            pass
    if callable(getattr(owner, "_schedule_outline_update", None)):
        try:
            owner._schedule_outline_update()
        except Exception:
            pass
    return ok, fail


def _write_restore_report(
    owner,
    row: dict,
    selected_sources: set[str],
    diff: dict,
    ok: int,
    fail: int,
    result_rows: list[dict],
) -> str:
    state_dir = str(getattr(owner, "_state_dir", "") or "").strip()
    if not state_dir:
        return ""
    report_dir = Path(state_dir) / "audit" / "restore_reports"
    report_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    old_name = str(row.get("old_name") or "")
    new_name = str(row.get("new_name") or "")
    safe_old = old_name.replace("/", "_").replace("\\", "_")[:40] or "unknown"
    safe_new = new_name.replace("/", "_").replace("\\", "_")[:40] or "unknown"
    report_path = report_dir / f"restore_{stamp}_{safe_old}_to_{safe_new}.json"

    payload = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "workspace_dir": str(getattr(owner, "workspace_dir", "") or ""),
        "backup_created_at": str(row.get("created_at") or ""),
        "old_name": old_name,
        "new_name": new_name,
        "selected_files": int(len(selected_sources)),
        "success": int(ok),
        "failed": int(fail),
        "diff": {
            "changed_files": int(diff.get("changed_files", 0)),
            "changed_lines": int(diff.get("changed_lines", 0)),
            "unchanged_files": int(diff.get("unchanged_files", 0)),
            "missing_files": int(diff.get("missing_files", 0)),
        },
        "results": result_rows if isinstance(result_rows, list) else [],
    }
    try:
        report_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return str(report_path)
    except Exception:
        return ""


def _pick_restore_files(owner, row: dict) -> tuple[bool, set[str]]:
    files = row.get("files") or []
    file_rows = [x for x in files if isinstance(x, dict) and str(x.get("source") or "").strip()]
    if not file_rows:
        return False, set()

    win = tk.Toplevel(owner.root)
    win.title("选择要恢复的文件")
    win.configure(bg=owner.theme_sidebar_bg)
    win.transient(owner.root)
    try:
        win.resizable(True, True)
    except tk.TclError:
        pass

    width = int(max(760, 840 * float(getattr(owner, "dpi_scale", 1.0))))
    height = int(max(460, 520 * float(getattr(owner, "dpi_scale", 1.0))))
    x = owner.root.winfo_x() + 32
    y = owner.root.winfo_y() + 42
    win.geometry(f"{width}x{height}+{x}+{y}")

    state = {"ok": False, "selected": set()}

    box = tk.Frame(win, bg=owner.theme_sidebar_bg, padx=12, pady=10)
    box.pack(fill=tk.BOTH, expand=True)

    tk.Label(
        box,
        text="请选择需要恢复的文件（默认全选）",
        bg=owner.theme_sidebar_bg,
        fg=owner.theme_fg,
        font=owner.font_ui_bold,
        anchor="w",
    ).pack(fill=tk.X, pady=(0, 8))

    listbox = tk.Listbox(
        box,
        bg=owner.theme_bg,
        fg=owner.theme_fg,
        selectbackground="#264F78",
        selectforeground="#FFFFFF",
        font=owner.font_code,
        activestyle="none",
        selectmode=tk.EXTENDED,
    )
    listbox.pack(fill=tk.BOTH, expand=True)

    for idx, item in enumerate(file_rows, start=1):
        rel = str(item.get("relative") or item.get("source") or "")
        cnt = int(item.get("count", 0))
        listbox.insert(tk.END, f"{idx:03d}. {rel}  ({cnt}处)")
    listbox.selection_set(0, tk.END)

    def _select_all():
        listbox.selection_set(0, tk.END)

    def _invert():
        selected_idx = {int(i) for i in listbox.curselection()}
        listbox.selection_clear(0, tk.END)
        for i in range(len(file_rows)):
            if i not in selected_idx:
                listbox.selection_set(i)

    def _confirm(_event=None):
        indexes = [int(i) for i in listbox.curselection()]
        if not indexes:
            messagebox.showwarning("恢复备份", "请至少选择一个文件。", parent=win)
            return
        selected = set()
        for i in indexes:
            if 0 <= i < len(file_rows):
                selected.add(str(file_rows[i].get("source") or ""))
        state["selected"] = selected
        state["ok"] = True
        win.destroy()

    def _cancel(_event=None):
        state["ok"] = False
        win.destroy()

    row_btn = tk.Frame(box, bg=owner.theme_sidebar_bg)
    row_btn.pack(fill=tk.X, pady=(8, 0))
    tk.Button(
        row_btn,
        text="全选",
        command=_select_all,
        font=owner.font_ui,
        bg=owner.theme_toolbar_bg,
        fg=owner.theme_fg,
        relief="flat",
        borderwidth=0,
        padx=10,
        pady=4,
        cursor="hand2",
    ).pack(side=tk.LEFT, padx=(0, 6))
    tk.Button(
        row_btn,
        text="反选",
        command=_invert,
        font=owner.font_ui,
        bg=owner.theme_toolbar_bg,
        fg=owner.theme_fg,
        relief="flat",
        borderwidth=0,
        padx=10,
        pady=4,
        cursor="hand2",
    ).pack(side=tk.LEFT)
    tk.Button(
        row_btn,
        text="继续",
        command=_confirm,
        font=owner.font_ui,
        bg="#2E7D32",
        fg="#FFFFFF",
        activebackground="#3D9742",
        activeforeground="#FFFFFF",
        relief="flat",
        borderwidth=0,
        padx=12,
        pady=5,
        cursor="hand2",
    ).pack(side=tk.RIGHT)
    tk.Button(
        row_btn,
        text="取消",
        command=_cancel,
        font=owner.font_ui,
        bg=owner.theme_toolbar_bg,
        fg=owner.theme_fg,
        relief="flat",
        borderwidth=0,
        padx=10,
        pady=4,
        cursor="hand2",
    ).pack(side=tk.RIGHT, padx=(0, 8))

    win.bind("<Return>", _confirm)
    win.bind("<Escape>", _cancel)
    win.protocol("WM_DELETE_WINDOW", _cancel)
    try:
        win.grab_set()
    except tk.TclError:
        pass
    owner.root.wait_window(win)
    return bool(state["ok"]), set(state["selected"])


def _row_subset(row: dict, selected_sources: set[str]) -> dict:
    selected = set(selected_sources or [])
    files = row.get("files") or []
    subset_files = []
    for item in files:
        if not isinstance(item, dict):
            continue
        src = str(item.get("source") or "")
        if selected and src not in selected:
            continue
        subset_files.append(item)
    subset = dict(row)
    subset["files"] = subset_files
    subset["file_count"] = len(subset_files)
    subset["replace_count"] = int(sum(int(x.get("count", 0)) for x in subset_files if isinstance(x, dict)))
    return subset


def _estimate_changed_lines(old_text: str, new_text: str) -> int:
    a = str(old_text or "").splitlines()
    b = str(new_text or "").splitlines()
    total = 0
    for tag, i1, i2, j1, j2 in SequenceMatcher(a=a, b=b, autojunk=False).get_opcodes():
        if tag == "equal":
            continue
        total += max(i2 - i1, j2 - j1)
    return int(total)


def _backup_diff_summary(manifest_row: dict, max_files: int = 200) -> dict:
    files = manifest_row.get("files") or []
    if not isinstance(files, list):
        files = []

    checked = 0
    changed_files = 0
    unchanged_files = 0
    missing_files = 0
    changed_lines = 0
    top_changes = []

    for item in files[: max(1, int(max_files))]:
        if not isinstance(item, dict):
            continue
        src = str(item.get("source") or "").strip()
        bak = str(item.get("backup") or "").strip()
        if not src or not bak:
            continue
        checked += 1
        try:
            old_text = Path(bak).read_text(encoding="utf-8")
        except Exception:
            old_text = ""
        if not Path(src).is_file():
            missing_files += 1
            continue
        try:
            new_text = Path(src).read_text(encoding="utf-8")
        except Exception:
            missing_files += 1
            continue
        if old_text == new_text:
            unchanged_files += 1
            continue
        delta = _estimate_changed_lines(old_text, new_text)
        changed_files += 1
        changed_lines += int(delta)
        rel = str(item.get("relative") or src)
        top_changes.append((int(delta), rel))

    top_changes.sort(key=lambda x: x[0], reverse=True)
    return {
        "checked": checked,
        "changed_files": changed_files,
        "unchanged_files": unchanged_files,
        "missing_files": missing_files,
        "changed_lines": changed_lines,
        "top_changes": top_changes[:8],
    }


def _restore_backup_row(owner, row: dict) -> tuple[int, int]:
    picked, selected_sources = _pick_restore_files(owner, row)
    if not picked:
        return 0, 0
    work_row = _row_subset(row, selected_sources)
    if int(work_row.get("file_count", 0)) <= 0:
        owner.status_main_var.set("恢复已取消：未选择文件")
        return 0, 0

    old_name = str(row.get("old_name") or "")
    new_name = str(row.get("new_name") or "")
    created_at = str(row.get("created_at") or "未知")
    file_count = int(work_row.get("file_count") or 0)
    diff = _backup_diff_summary(work_row)
    diff_text = (
        f"当前与备份差异：{diff['changed_files']} 文件，约 {diff['changed_lines']} 行；"
        f"未变化 {diff['unchanged_files']}，缺失 {diff['missing_files']}"
    )
    if not messagebox.askyesno(
        "恢复重命名备份",
        f"将恢复备份记录：\n"
        f"时间：{created_at}\n"
        f"变更：{old_name} -> {new_name}\n"
        f"文件数：{file_count}\n\n"
        f"{diff_text}\n\n"
        f"是否继续？",
        parent=owner.root,
    ):
        return 0, 0

    result_rows = []
    ok, fail = _restore_backup_manifest(owner, work_row, selected_sources=selected_sources, result_rows=result_rows)
    report_path = _write_restore_report(owner, work_row, selected_sources, diff, ok, fail, result_rows)
    owner.status_main_var.set(
        f"备份恢复完成：成功 {ok}，失败 {fail}" + (f"，报告：{report_path}" if report_path else "")
    )
    log_owner_event(owner, "info", f"恢复重命名备份：成功 {ok}，失败 {fail}")
    _write_audit_event(
        owner,
        "restore_rename_backup",
        {
            "created_at": created_at,
            "old_name": old_name,
            "new_name": new_name,
            "selected_files": int(file_count),
            "success": ok,
            "failed": fail,
            "diff_changed_files": int(diff.get("changed_files", 0)),
            "diff_changed_lines": int(diff.get("changed_lines", 0)),
            "manifest": str(row.get("manifest") or ""),
            "report": report_path,
        },
    )
    return ok, fail


def restore_latest_rename_backup(owner, event=None):
    del event
    backups = _list_rename_backups(owner, max_count=10)
    if not backups:
        messagebox.showinfo("恢复重命名备份", "未找到可恢复的重命名备份。", parent=owner.root)
        return "break"
    latest = backups[0]
    _restore_backup_row(owner, latest)
    return "break"


def open_rename_backup_history(owner, event=None):
    del event
    backups = _list_rename_backups(owner, max_count=120)
    if not backups:
        messagebox.showinfo("重命名备份历史", "暂无重命名备份记录。", parent=owner.root)
        return "break"

    win = tk.Toplevel(owner.root)
    win.title("重命名备份历史")
    win.configure(bg=owner.theme_sidebar_bg)
    win.transient(owner.root)
    try:
        win.resizable(True, True)
    except tk.TclError:
        pass

    width = int(max(820, 900 * float(getattr(owner, "dpi_scale", 1.0))))
    height = int(max(520, 560 * float(getattr(owner, "dpi_scale", 1.0))))
    x = owner.root.winfo_x() + 24
    y = owner.root.winfo_y() + 36
    win.geometry(f"{width}x{height}+{x}+{y}")

    box = tk.Frame(win, bg=owner.theme_sidebar_bg, padx=12, pady=10)
    box.pack(fill=tk.BOTH, expand=True)

    tk.Label(
        box,
        text=f"共 {len(backups)} 条重命名备份记录（按时间倒序）",
        bg=owner.theme_sidebar_bg,
        fg=owner.theme_fg,
        font=owner.font_ui_bold,
        anchor="w",
    ).pack(fill=tk.X, pady=(0, 8))

    pane = tk.PanedWindow(box, orient=tk.HORIZONTAL, sashwidth=4, bg=owner.theme_sash, borderwidth=0)
    pane.pack(fill=tk.BOTH, expand=True)

    left = tk.Frame(pane, bg=owner.theme_bg)
    right = tk.Frame(pane, bg=owner.theme_bg)
    pane.add(left, stretch="always", minsize=420)
    pane.add(right, stretch="always", minsize=280)

    listbox = tk.Listbox(
        left,
        bg=owner.theme_bg,
        fg=owner.theme_fg,
        selectbackground="#264F78",
        selectforeground="#FFFFFF",
        font=owner.font_code,
        activestyle="none",
    )
    listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    sb = tk.Scrollbar(left, orient="vertical", command=listbox.yview)
    sb.pack(side=tk.RIGHT, fill=tk.Y)
    listbox.configure(yscrollcommand=sb.set)

    detail = tk.Text(
        right,
        bg=owner.theme_bg,
        fg=owner.theme_fg,
        insertbackground=owner.theme_fg,
        font=owner.font_code,
        relief="flat",
        borderwidth=0,
        highlightthickness=1,
        highlightbackground=owner.theme_sash,
        highlightcolor=owner.theme_accent,
        wrap=tk.WORD,
    )
    detail.pack(fill=tk.BOTH, expand=True)
    detail.configure(state="disabled")

    for i, row in enumerate(backups, start=1):
        listbox.insert(
            tk.END,
            f"{i:03d}. {row['created_at']}   {row['old_name']} -> {row['new_name']}   ({row['file_count']}文件/{row['replace_count']}处)",
        )
    listbox.selection_set(0)

    def _set_detail(index: int):
        if index < 0 or index >= len(backups):
            return
        row = backups[index]
        lines = [
            f"时间：{row.get('created_at', '未知')}",
            f"变更：{row.get('old_name', '')} -> {row.get('new_name', '')}",
            f"文件数：{row.get('file_count', 0)}",
            f"替换处数：{row.get('replace_count', 0)}",
            f"备份目录：{row.get('dir', '')}",
            "",
            "差异预览：计算中...",
            "",
            "文件预览：",
        ]
        files = row.get("files") or []
        for item in files[:30]:
            if not isinstance(item, dict):
                continue
            rel = str(item.get("relative") or item.get("source") or "")
            cnt = int(item.get("count", 0))
            lines.append(f"- {rel}  ({cnt}处)")
        if len(files) > 30:
            lines.append(f"- ... 其余 {len(files) - 30} 个文件")

        diff = _backup_diff_summary(row)
        lines[6] = (
            f"差异预览：{diff['changed_files']} 文件，约 {diff['changed_lines']} 行；"
            f"未变化 {diff['unchanged_files']}，缺失 {diff['missing_files']}"
        )
        if diff.get("top_changes"):
            lines.append("")
            lines.append("变化最大的文件：")
            for delta, rel in diff["top_changes"]:
                lines.append(f"- {rel}  (~{delta}行)")

        detail.configure(state="normal")
        detail.delete("1.0", "end")
        detail.insert("1.0", "\n".join(lines))
        detail.configure(state="disabled")

    def _on_select(_event=None):
        sel = listbox.curselection()
        if not sel:
            return
        _set_detail(int(sel[0]))

    def _restore_selected(_event=None):
        sel = listbox.curselection()
        if not sel:
            return
        row = backups[int(sel[0])]
        ok, fail = _restore_backup_row(owner, row)
        if ok > 0 or fail > 0:
            try:
                win.destroy()
            except tk.TclError:
                pass

    _set_detail(0)
    listbox.bind("<<ListboxSelect>>", _on_select)
    listbox.bind("<Double-Button-1>", _restore_selected)
    win.bind("<Return>", _restore_selected)
    win.bind("<Escape>", lambda _e: win.destroy())

    btn_row = tk.Frame(box, bg=owner.theme_sidebar_bg)
    btn_row.pack(fill=tk.X, pady=(8, 0))
    tk.Button(
        btn_row,
        text="恢复选中记录",
        command=_restore_selected,
        font=owner.font_ui,
        bg="#2E7D32",
        fg="#FFFFFF",
        activebackground="#3D9742",
        activeforeground="#FFFFFF",
        relief="flat",
        borderwidth=0,
        padx=10,
        pady=4,
        cursor="hand2",
    ).pack(side=tk.LEFT)
    tk.Button(
        btn_row,
        text="关闭",
        command=win.destroy,
        font=owner.font_ui,
        bg=owner.theme_toolbar_bg,
        fg=owner.theme_fg,
        activebackground="#505050",
        activeforeground="#FFFFFF",
        relief="flat",
        borderwidth=0,
        padx=10,
        pady=4,
        cursor="hand2",
    ).pack(side=tk.RIGHT)

    try:
        win.grab_set()
    except tk.TclError:
        pass
    _write_audit_event(owner, "open_rename_backup_history", {"count": len(backups)})
    return "break"


def open_runtime_log(owner, event=None):
    del event
    log_path = str(getattr(owner, "_log_file", "") or "")
    if not log_path:
        messagebox.showinfo("日志不可用", "当前会话尚未初始化日志路径。", parent=owner.root)
        return "break"

    if not os.path.isfile(log_path):
        messagebox.showinfo("日志不可用", f"日志文件尚未生成：\n{log_path}", parent=owner.root)
        return "break"

    try:
        with open(log_path, "r", encoding="utf-8") as f:
            content = f.read()
        owner._create_editor_tab(log_path, content)
        owner.status_main_var.set("已打开运行日志")
        log_owner_event(owner, "info", "用户打开运行日志。")
    except Exception as e:
        messagebox.showerror("打开日志失败", f"无法读取日志：{e}", parent=owner.root)
    return "break"


def open_restore_report_dir(owner, event=None):
    del event
    report_dir = _restore_report_dir(owner)
    if not report_dir:
        messagebox.showinfo("恢复报告", "当前状态目录未初始化。", parent=owner.root)
        return "break"
    Path(report_dir).mkdir(parents=True, exist_ok=True)
    if not _open_path_in_system(report_dir):
        messagebox.showinfo("恢复报告", f"无法打开目录：\n{report_dir}", parent=owner.root)
        return "break"
    log_owner_event(owner, "info", "用户打开恢复报告目录。")
    return "break"


def open_latest_restore_report(owner, event=None):
    del event
    reports = _list_restore_reports(owner, max_count=1)
    if not reports:
        messagebox.showinfo("恢复报告", "暂无恢复报告。", parent=owner.root)
        return "break"
    path = reports[0]
    try:
        content = Path(path).read_text(encoding="utf-8")
        owner._create_editor_tab(path, content)
        owner.status_main_var.set("已打开最近恢复报告")
        _write_audit_event(owner, "open_latest_restore_report", {"path": path})
    except Exception as e:
        messagebox.showerror("恢复报告", f"打开报告失败：{e}", parent=owner.root)
    return "break"


def open_restore_report_history(owner, event=None):
    del event
    reports = _list_restore_reports(owner, max_count=120)
    if not reports:
        messagebox.showinfo("恢复报告历史", "暂无恢复报告。", parent=owner.root)
        return "break"

    win = tk.Toplevel(owner.root)
    win.title("恢复报告历史")
    win.configure(bg=owner.theme_sidebar_bg)
    win.transient(owner.root)
    try:
        win.resizable(True, True)
    except tk.TclError:
        pass
    width = int(max(780, 860 * float(getattr(owner, "dpi_scale", 1.0))))
    height = int(max(500, 540 * float(getattr(owner, "dpi_scale", 1.0))))
    x = owner.root.winfo_x() + 28
    y = owner.root.winfo_y() + 38
    win.geometry(f"{width}x{height}+{x}+{y}")

    box = tk.Frame(win, bg=owner.theme_sidebar_bg, padx=12, pady=10)
    box.pack(fill=tk.BOTH, expand=True)
    tk.Label(
        box,
        text=f"共 {len(reports)} 份恢复报告（按时间倒序）",
        bg=owner.theme_sidebar_bg,
        fg=owner.theme_fg,
        font=owner.font_ui_bold,
        anchor="w",
    ).pack(fill=tk.X, pady=(0, 8))

    listbox = tk.Listbox(
        box,
        bg=owner.theme_bg,
        fg=owner.theme_fg,
        selectbackground="#264F78",
        selectforeground="#FFFFFF",
        font=owner.font_code,
        activestyle="none",
    )
    listbox.pack(fill=tk.BOTH, expand=True)
    for idx, path in enumerate(reports, start=1):
        listbox.insert(tk.END, f"{idx:03d}. {Path(path).name}")
    listbox.selection_set(0)

    def _open_selected(_event=None):
        sel = listbox.curselection()
        if not sel:
            return
        path = reports[int(sel[0])]
        try:
            content = Path(path).read_text(encoding="utf-8")
            owner._create_editor_tab(path, content)
            owner.status_main_var.set("已打开恢复报告")
            _write_audit_event(owner, "open_restore_report", {"path": path})
            win.destroy()
        except Exception as e:
            messagebox.showerror("恢复报告", f"打开报告失败：{e}", parent=win)

    btn_row = tk.Frame(box, bg=owner.theme_sidebar_bg)
    btn_row.pack(fill=tk.X, pady=(8, 0))
    tk.Button(
        btn_row,
        text="打开选中报告",
        command=_open_selected,
        font=owner.font_ui,
        bg=owner.theme_toolbar_bg,
        fg=owner.theme_fg,
        activebackground="#505050",
        activeforeground="#FFFFFF",
        relief="flat",
        borderwidth=0,
        padx=10,
        pady=4,
        cursor="hand2",
    ).pack(side=tk.LEFT)
    tk.Button(
        btn_row,
        text="打开报告目录",
        command=lambda: open_restore_report_dir(owner),
        font=owner.font_ui,
        bg=owner.theme_toolbar_bg,
        fg=owner.theme_fg,
        activebackground="#505050",
        activeforeground="#FFFFFF",
        relief="flat",
        borderwidth=0,
        padx=10,
        pady=4,
        cursor="hand2",
    ).pack(side=tk.LEFT, padx=(8, 0))
    tk.Button(
        btn_row,
        text="关闭",
        command=win.destroy,
        font=owner.font_ui,
        bg=owner.theme_toolbar_bg,
        fg=owner.theme_fg,
        activebackground="#505050",
        activeforeground="#FFFFFF",
        relief="flat",
        borderwidth=0,
        padx=10,
        pady=4,
        cursor="hand2",
    ).pack(side=tk.RIGHT)

    listbox.bind("<Double-Button-1>", _open_selected)
    win.bind("<Return>", _open_selected)
    win.bind("<Escape>", lambda _e: win.destroy())
    try:
        win.grab_set()
    except tk.TclError:
        pass
    _write_audit_event(owner, "open_restore_report_history", {"count": len(reports)})
    return "break"


def open_runtime_diagnostics(owner, event=None):
    del event
    win = tk.Toplevel(owner.root)
    win.title("运行诊断中心")
    win.configure(bg=owner.theme_sidebar_bg)
    win.transient(owner.root)
    try:
        win.resizable(True, True)
    except tk.TclError:
        pass

    width = int(max(680, 720 * float(getattr(owner, "dpi_scale", 1.0))))
    height = int(max(440, 480 * float(getattr(owner, "dpi_scale", 1.0))))
    x = owner.root.winfo_x() + max(24, int(30 * float(getattr(owner, "dpi_scale", 1.0))))
    y = owner.root.winfo_y() + max(36, int(36 * float(getattr(owner, "dpi_scale", 1.0))))
    win.geometry(f"{width}x{height}+{x}+{y}")

    box = tk.Frame(win, bg=owner.theme_sidebar_bg, padx=12, pady=10)
    box.pack(fill=tk.BOTH, expand=True)

    title = tk.Label(
        box,
        text="编辑器运行诊断",
        bg=owner.theme_sidebar_bg,
        fg="#FFFFFF",
        font=("Microsoft YaHei", 12, "bold"),
        anchor="w",
    )
    title.pack(fill=tk.X)

    info_text = tk.Text(
        box,
        bg=owner.theme_bg,
        fg=owner.theme_fg,
        insertbackground=owner.theme_fg,
        font=owner.font_code,
        relief="flat",
        borderwidth=0,
        highlightthickness=1,
        highlightbackground=owner.theme_sash,
        highlightcolor=owner.theme_accent,
        wrap=tk.WORD,
    )
    info_text.pack(fill=tk.BOTH, expand=True, pady=(10, 10))

    log_file = str(getattr(owner, "_log_file", "") or "")
    state_dir = str(getattr(owner, "_state_dir", "") or "")
    recovery_dir = str(getattr(owner, "_recovery_dir", "") or "")
    last = _load_last_recovery(owner)
    latest_report = _latest_restore_report_summary(owner)

    lines = [
        f"当前时间：{_now_text()}",
        f"工作区：{getattr(owner, 'workspace_dir', '')}",
        f"状态目录：{state_dir}",
        f"日志文件：{log_file or '（未初始化）'}",
        f"恢复目录：{recovery_dir or '（未初始化）'}",
        "",
        "最近异常记录：",
    ]
    if last:
        lines.append(f"- 时间：{last.get('created_at', '未知')}")
        lines.append(f"- 原因：{last.get('reason', '未知')}")
        snap = str(last.get("snapshot_dir") or "")
        if snap:
            lines.append(f"- 快照：{snap}")
    else:
        lines.append("- 最近没有检测到崩溃记录。")

    lines.extend(["", "最近恢复摘要："])
    if latest_report:
        lines.append(f"- 时间：{latest_report.get('created_at', '未知')}")
        lines.append(
            f"- 变更：{latest_report.get('old_name', '')} -> {latest_report.get('new_name', '')}"
        )
        lines.append(
            f"- 结果：成功 {latest_report.get('success', 0)}，失败 {latest_report.get('failed', 0)}"
        )
        lines.append(
            f"- 差异：{latest_report.get('changed_files', 0)} 文件 / 约 {latest_report.get('changed_lines', 0)} 行"
        )
    else:
        lines.append("- 暂无恢复报告。")

    info_text.insert("1.0", "\n".join(lines))
    info_text.configure(state="disabled")

    btn_row = tk.Frame(box, bg=owner.theme_sidebar_bg)
    btn_row.pack(fill=tk.X)

    def _btn(text, cmd):
        return tk.Button(
            btn_row,
            text=text,
            command=cmd,
            font=owner.font_ui,
            bg=owner.theme_toolbar_bg,
            fg=owner.theme_fg,
            activebackground="#505050",
            activeforeground="#FFFFFF",
            relief="flat",
            borderwidth=0,
            padx=9,
            pady=5,
            cursor="hand2",
        )

    _btn("打开日志", lambda: open_runtime_log(owner)).pack(side=tk.LEFT, padx=(0, 6))
    _btn("最近恢复报告", lambda: open_latest_restore_report(owner)).pack(side=tk.LEFT, padx=(0, 6))
    _btn("报告历史", lambda: open_restore_report_history(owner)).pack(side=tk.LEFT, padx=(0, 6))
    _btn("报告目录", lambda: open_restore_report_dir(owner)).pack(side=tk.LEFT, padx=(0, 6))
    _btn("恢复最近备份", lambda: restore_latest_rename_backup(owner)).pack(side=tk.LEFT, padx=(0, 6))
    _btn("备份历史", lambda: open_rename_backup_history(owner)).pack(side=tk.LEFT, padx=(0, 6))
    _btn("打开状态目录", lambda: _open_path_in_system(state_dir)).pack(side=tk.LEFT, padx=(0, 6))
    _btn("打开恢复目录", lambda: _open_path_in_system(recovery_dir)).pack(side=tk.LEFT, padx=(0, 6))
    _btn("关闭", win.destroy).pack(side=tk.RIGHT)

    try:
        win.grab_set()
    except tk.TclError:
        pass
    log_owner_event(owner, "info", "用户打开运行诊断中心。")
    return "break"
