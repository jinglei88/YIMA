#!/usr/bin/env python3
"""Quick quality gate for editor changes.

Runs:
1) py_compile for key editor scripts
2) editor logic regression
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))
from _console_utf8 import setup_console_utf8

setup_console_utf8()

ROOT = Path(__file__).resolve().parents[1]


def _run(cmd: list[str]) -> None:
    print(f"[RUN] {' '.join(cmd)}", flush=True)
    result = subprocess.run(cmd, cwd=str(ROOT))
    if result.returncode != 0:
        raise SystemExit(result.returncode)


def main() -> int:
    print("=== 快速检查开始 ===", flush=True)
    _run(
        [
            sys.executable,
            "-m",
            "py_compile",
            "易码编辑器.py",
            "yima/editor_binding_flow.py",
            "yima/editor_cheatsheet_flow.py",
            "yima/editor_export_flow.py",
            "yima/editor_main_ui.py",
            "yima/editor_runtime_guard.py",
            "yima/editor_search_flow.py",
            "yima/editor_shortcuts_flow.py",
            "scripts/run_editor_logic_regression.py",
            "scripts/_console_utf8.py",
        ]
    )
    print("[OK] py_compile 通过", flush=True)
    _run([sys.executable, "scripts/run_editor_logic_regression.py"])
    print("=== 快速检查完成：全部通过 ===", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
