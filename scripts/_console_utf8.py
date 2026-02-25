#!/usr/bin/env python3
"""Console encoding helpers for Windows/UTF-8 friendly output."""

from __future__ import annotations

import os
import sys


def setup_console_utf8() -> None:
    """Best-effort UTF-8 stdout/stderr setup.

    - Keeps output readable in UTF-8 terminals.
    - Sets env for child Python processes.
    """

    os.environ.setdefault("PYTHONUTF8", "1")
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")

    for stream_name in ("stdout", "stderr"):
        stream = getattr(sys, stream_name, None)
        if stream is None:
            continue
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass
