#!/usr/bin/env python3
"""Example matrix runner with tiered classification.

Modes:
- automated: execute only automated examples; skip manual examples.
- full: execute all examples. Manual examples can be marked as expected timeout.
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
import json
import locale
import os
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PY = sys.executable
DEFAULT_MANIFEST = ROOT / "scripts" / "example_matrix_manifest.json"
SYS_ENCODING = locale.getpreferredencoding(False) or "utf-8"


@dataclass
class ExampleConfig:
    path: Path
    rel_path: str
    tier: str
    expected: str
    timeout_sec: int
    isolate_cwd: bool
    note: str


def load_manifest(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"version": 1, "defaults": {"timeout_sec": 25}, "overrides": {}}
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"Invalid manifest root: {path}")
    data.setdefault("defaults", {})
    data.setdefault("overrides", {})
    if not isinstance(data["defaults"], dict) or not isinstance(data["overrides"], dict):
        raise ValueError(f"Invalid manifest format: {path}")
    return data


def discover_examples() -> list[Path]:
    examples_dir = ROOT / "示例"
    if not examples_dir.exists():
        return []
    return sorted(examples_dir.rglob("*.ym"))


def normalize_rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def build_example_configs(
    examples: list[Path],
    manifest: dict[str, Any],
    timeout_override: int | None = None,
) -> list[ExampleConfig]:
    defaults = manifest.get("defaults", {})
    overrides = manifest.get("overrides", {})
    default_timeout = int(defaults.get("timeout_sec", 25))
    timeout_base = int(timeout_override) if timeout_override is not None else default_timeout

    valid_rels = {normalize_rel(p) for p in examples}
    unknown_overrides = sorted(set(overrides.keys()) - valid_rels)
    if unknown_overrides:
        joined = "\n".join(unknown_overrides)
        raise ValueError(f"Manifest contains unknown example paths:\n{joined}")

    configs: list[ExampleConfig] = []
    for path in examples:
        rel = normalize_rel(path)
        raw = overrides.get(rel, {}) or {}
        if not isinstance(raw, dict):
            raise ValueError(f"Manifest override must be object: {rel}")
        tier = str(raw.get("tier", "automated")).strip().lower() or "automated"
        if tier not in {"automated", "manual"}:
            raise ValueError(f"Invalid tier for {rel}: {tier}")
        expected = str(raw.get("expected", "")).strip().lower()
        isolate_cwd = bool(raw.get("isolate_cwd", False))
        note = str(raw.get("note", "")).strip()
        timeout_sec = int(raw.get("timeout_sec", timeout_base))
        if timeout_sec <= 0:
            raise ValueError(f"Invalid timeout for {rel}: {timeout_sec}")

        configs.append(
            ExampleConfig(
                path=path,
                rel_path=rel,
                tier=tier,
                expected=expected,
                timeout_sec=timeout_sec,
                isolate_cwd=isolate_cwd,
                note=note,
            )
        )
    return configs


def tail_text(text: str, max_lines: int = 8) -> str:
    lines = [ln for ln in (text or "").splitlines() if ln.strip()]
    return "\n".join(lines[-max_lines:])


def run_single_example(config: ExampleConfig) -> dict[str, Any]:
    cmd = [PY, str(ROOT / "易码.py"), str(config.path)]
    start = time.perf_counter()
    cwd = ROOT
    temp_dir_obj: tempfile.TemporaryDirectory[str] | None = None
    if config.isolate_cwd:
        temp_dir_obj = tempfile.TemporaryDirectory(prefix="yima_example_", dir=ROOT)
        cwd = Path(temp_dir_obj.name)

    try:
        proc = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            encoding=SYS_ENCODING,
            errors="replace",
            timeout=config.timeout_sec,
            env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1"),
        )
        elapsed = round(time.perf_counter() - start, 3)
        output = (proc.stdout or "") + (proc.stderr or "")
        return {
            "raw": "pass" if proc.returncode == 0 else "fail",
            "returncode": proc.returncode,
            "elapsed_sec": elapsed,
            "output_tail": tail_text(output),
        }
    except subprocess.TimeoutExpired as e:
        elapsed = round(time.perf_counter() - start, 3)
        out = (e.stdout or "") + (e.stderr or "")
        return {
            "raw": "timeout",
            "returncode": None,
            "elapsed_sec": elapsed,
            "output_tail": tail_text(out),
        }
    finally:
        if temp_dir_obj is not None:
            temp_dir_obj.cleanup()


def evaluate(mode: str, config: ExampleConfig, raw_result: dict[str, Any]) -> tuple[str, bool]:
    raw = raw_result["raw"]
    if raw == "pass":
        return "pass", True
    if raw == "fail":
        return "fail", False
    if raw == "timeout":
        if mode == "full" and config.expected == "timeout":
            return "expected_timeout", True
        return "timeout", False
    return "fail", False


def summarize(results: list[dict[str, Any]]) -> dict[str, int]:
    summary = {
        "total": len(results),
        "automated": 0,
        "manual": 0,
        "executed": 0,
        "skipped_manual": 0,
        "pass": 0,
        "fail": 0,
        "timeout": 0,
        "expected_timeout": 0,
    }
    for item in results:
        tier = item["tier"]
        summary[tier] += 1
        final = item["final_status"]
        if final == "skipped_manual":
            summary["skipped_manual"] += 1
            continue
        summary["executed"] += 1
        summary[final] += 1
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description="Run tiered example matrix for 易码.")
    parser.add_argument(
        "--mode",
        choices=("automated", "full"),
        default="automated",
        help="automated: run automated tier only; full: run all tiers.",
    )
    parser.add_argument(
        "--manifest",
        default=str(DEFAULT_MANIFEST),
        help="Path to matrix manifest JSON.",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=None,
        help="Global timeout override in seconds.",
    )
    parser.add_argument(
        "--json-out",
        default="",
        help="Optional path for JSON report output.",
    )
    args = parser.parse_args()

    manifest = load_manifest(Path(args.manifest))
    examples = discover_examples()
    configs = build_example_configs(examples, manifest, timeout_override=args.timeout)

    print(f"=== Example Matrix Start ({args.mode}) ===")
    print(f"[INFO] examples discovered: {len(configs)}")

    results: list[dict[str, Any]] = []
    for cfg in configs:
        if args.mode == "automated" and cfg.tier == "manual":
            item = {
                "path": cfg.rel_path,
                "tier": cfg.tier,
                "expected": cfg.expected,
                "timeout_sec": cfg.timeout_sec,
                "isolate_cwd": cfg.isolate_cwd,
                "note": cfg.note,
                "final_status": "skipped_manual",
                "raw_status": "skipped",
                "returncode": None,
                "elapsed_sec": 0.0,
                "output_tail": "",
            }
            results.append(item)
            continue

        raw = run_single_example(cfg)
        final_status, _ok = evaluate(args.mode, cfg, raw)
        item = {
            "path": cfg.rel_path,
            "tier": cfg.tier,
            "expected": cfg.expected,
            "timeout_sec": cfg.timeout_sec,
            "isolate_cwd": cfg.isolate_cwd,
            "note": cfg.note,
            "final_status": final_status,
            "raw_status": raw["raw"],
            "returncode": raw["returncode"],
            "elapsed_sec": raw["elapsed_sec"],
            "output_tail": raw["output_tail"],
        }
        results.append(item)

        if final_status == "pass":
            print(f"[OK] {cfg.rel_path}")
        elif final_status == "expected_timeout":
            print(f"[OK] expected-timeout {cfg.rel_path}")
        elif final_status == "timeout":
            print(f"[FAIL] timeout {cfg.rel_path}")
        else:
            print(f"[FAIL] {cfg.rel_path}")

    summary = summarize(results)
    print("=== Example Matrix Summary ===")
    print(json.dumps(summary, ensure_ascii=False))

    problems = [r for r in results if r["final_status"] in {"fail", "timeout"}]
    for row in problems:
        print("---")
        print(f"{row['final_status']}: {row['path']}")
        if row["output_tail"]:
            print(row["output_tail"])

    report = {
        "mode": args.mode,
        "manifest": str(Path(args.manifest)),
        "summary": summary,
        "results": results,
    }
    if args.json_out:
        out_path = Path(args.json_out)
        if not out_path.is_absolute():
            out_path = ROOT / out_path
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"[INFO] json report: {out_path}")

    if summary["fail"] > 0 or summary["timeout"] > 0:
        print("=== Example Matrix End: FAILED ===")
        return 1
    print("=== Example Matrix End: PASSED ===")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as e:
        safe = str(e).encode("unicode_escape", errors="replace").decode("ascii", errors="replace")
        print(f"[FAIL] example matrix crashed: {safe}")
        raise SystemExit(1)
