"""v1295: rebase the name-budget baseline across file renames — only when
the rename is provably neutral (identical violation stock modulo path).

Example:
    python scripts/rebase_name_budget_renames.py --old-ref HEAD~1
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
from pathlib import Path

try:
    from scripts._bootstrap import PROJECT_ROOT, ensure_src_path
except ModuleNotFoundError:  # pragma: no cover - direct script execution path
    from _bootstrap import PROJECT_ROOT, ensure_src_path  # type: ignore[import-not-found,no-redef]

ensure_src_path()

import json  # noqa: E402

from minigpt.name_budget import (  # noqa: E402
    DEFAULT_BASELINE,
    DEFAULT_TARGETS,
    rebase_renamed_paths,
    scan_names,
    write_name_baseline,
)
from minigpt.report_utils import utc_now  # noqa: E402


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Rename-neutral rebase of the name-budget baseline.")
    parser.add_argument("--old-ref", default="HEAD~1", help="Git ref of the pre-rename tree.")
    parser.add_argument("--baseline", type=Path, default=PROJECT_ROOT / DEFAULT_BASELINE)
    parser.add_argument("--project-root", type=Path, default=PROJECT_ROOT)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    payload = json.loads(args.baseline.read_text(encoding="utf-8"))
    baseline_digests = set(payload["digests"])
    # A short sibling path: the archived tree holds paths that overflow
    # Windows MAX_PATH under a deep temp-directory prefix.
    old_root = args.project_root.parent / "_nb_rebase_old_tree"
    if old_root.exists():
        shutil.rmtree(old_root)
    # core.longpaths per-invocation: the archived tree sits near MAX_PATH.
    subprocess.run(
        ["git", "-c", "core.longpaths=true", "worktree", "add", "--detach", str(old_root), args.old_ref],
        check=True,
        capture_output=True,
        cwd=args.project_root,
    )
    try:
        old_items = scan_names(old_root, targets=list(DEFAULT_TARGETS))["items"]
    finally:
        subprocess.run(
            ["git", "-c", "core.longpaths=true", "worktree", "remove", "--force", str(old_root)],
            check=True,
            capture_output=True,
            cwd=args.project_root,
        )
    current_items = scan_names(args.project_root, targets=list(DEFAULT_TARGETS))["items"]
    rebased = rebase_renamed_paths(old_items, current_items, baseline_digests)
    if rebased is None:
        print("status=refused (rename is not provably neutral)")
        return 1
    write_name_baseline(args.baseline, targets=list(DEFAULT_TARGETS), items=rebased, generated_at=utc_now())
    print(f"status=rebased violation_count={len(rebased)} (was {len(baseline_digests)})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
