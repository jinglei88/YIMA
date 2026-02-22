#!/usr/bin/env python3
"""易码发布回归脚本（发布前一键检查）。

默认执行：
1. scripts/run_regression.py
2. M16 自动回归
3. 打包冒烟（含打包清单机制）
"""

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

import argparse
import locale
import os
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PY = sys.executable
SYS_ENCODING = locale.getpreferredencoding(False) or "utf-8"


def decode_output(raw: bytes) -> str:
    for enc in ("utf-8", SYS_ENCODING):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="replace")


def run_cmd(args: list[str], *, cwd: Path | None = None, env: dict[str, str] | None = None) -> str:
    merged_env = dict(os.environ)
    merged_env.setdefault("PYTHONIOENCODING", "utf-8")
    merged_env.setdefault("PYTHONUTF8", "1")
    if env:
        merged_env.update(env)

    proc = subprocess.run(
        args,
        cwd=str(cwd or ROOT),
        env=merged_env,
        capture_output=True,
        text=False,
    )
    output = decode_output(proc.stdout or b"") + decode_output(proc.stderr or b"")
    if proc.returncode != 0:
        raise RuntimeError(f"命令失败: {' '.join(args)}\n{output}")
    return output


def assert_contains(text: str, needle: str, label: str) -> None:
    if needle not in text:
        safe = text.encode("unicode_escape", errors="replace").decode("ascii", errors="replace")
        raise AssertionError(f"{label} 失败：未找到【{needle}】\n{safe}")


def regression_base() -> None:
    run_cmd([PY, "scripts/run_regression.py"])
    print("[OK] 基础回归通过")


def regression_m16() -> None:
    out = run_cmd([PY, "易码.py", "示例/M16全量能力测试项目/主程序.ym"])
    assert_contains(out, "自动回归全部通过", "M16 自动回归")
    print("[OK] M16 自动回归通过")


def regression_pack_smoke() -> None:
    logo = ROOT / "logo.ico"
    if not logo.exists():
        raise FileNotFoundError(f"缺少图标文件：{logo}")

    with tempfile.TemporaryDirectory(prefix="yima_release_smoke_", dir=ROOT) as td:
        proj = Path(td)
        main_ym = proj / "主程序.ym"
        helper_ym = proj / "助手.ym"
        asset = proj / "asset.txt"
        manifest = proj / "易码打包清单.json"

        helper_ym.write_text(
            "功能 问候()\n"
            "    返回 \"OK\"\n",
            encoding="utf-8",
        )
        main_ym.write_text(
            "引入 \"助手.ym\" 叫做 助手\n"
            "引入 \"math\" 叫做 数学\n"
            "显示 助手.问候()\n"
            "显示 数学.sqrt(9)\n",
            encoding="utf-8",
        )
        asset.write_text("release-smoke", encoding="utf-8")
        manifest.write_text(
            "{\n"
            "  \"hidden_imports\": [\"json\"],\n"
            "  \"datas\": [\n"
            "    {\"src\": \"asset.txt\", \"dest\": \"assets\"}\n"
            "  ]\n"
            "}\n",
            encoding="utf-8",
        )

        env = dict(os.environ)
        env["PYTHONIOENCODING"] = "utf-8"

        out = run_cmd(
            [
                PY,
                str(ROOT / "易码打包工具.py"),
                str(main_ym),
                str(logo),
                "发布回归_冒烟",
            ],
            cwd=proj,
            env=env,
        )
        assert_contains(out, "发现打包清单", "打包清单读取")
        assert_contains(out, "自动识别 Python 依赖", "自动依赖识别")
        exe = proj / "易码_成品软件" / "发布回归_冒烟.exe"
        if not exe.exists():
            raise AssertionError(f"打包冒烟失败：未找到 EXE {exe}")
    print("[OK] 打包冒烟通过（含打包清单）")


def main() -> int:
    parser = argparse.ArgumentParser(description="易码发布回归")
    parser.add_argument("--skip-pack", action="store_true", help="跳过打包冒烟（更快）")
    args = parser.parse_args()

    print("=== 易码发布回归开始 ===")
    regression_base()
    regression_m16()
    if args.skip_pack:
        print("[SKIP] 已跳过打包冒烟")
    else:
        regression_pack_smoke()
    print("=== 易码发布回归完成：全部通过 ===")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as e:
        safe = str(e).encode("unicode_escape", errors="replace").decode("ascii", errors="replace")
        print(f"[FAIL] 发布回归失败: {safe}")
        raise SystemExit(1)
