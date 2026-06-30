from __future__ import annotations

from pathlib import Path

from scripts._bootstrap import PROJECT_ROOT, SRC_ROOT, ensure_src_path

ROOT: Path = PROJECT_ROOT
SRC: Path = SRC_ROOT

ensure_src_path()

__all__ = ["ROOT", "SRC", "ensure_src_path"]
