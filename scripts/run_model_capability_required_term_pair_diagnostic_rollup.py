from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path
from typing import Sequence

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.model_capability_required_term_pair_diagnostic_rollup import (  # noqa: E402
    build_model_capability_required_term_pair_diagnostic_rollup,
    collect_required_term_pair_diagnostic_reports,
    resolve_exit_code,
)
from minigpt.model_capability_required_term_pair_diagnostic_rollup_artifacts import (  # noqa: E402
    render_model_capability_required_term_pair_diagnostic_rollup_text,
    write_model_capability_required_term_pair_diagnostic_rollup_outputs,
)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Roll up v503-v508 required-term pair diagnostics.")
    parser.add_argument("evidence_root", type=Path, help="Root directory containing e/503..e/508 evidence.")
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=ROOT / "runs" / "model-capability-required-term-pair-diagnostic-rollup",
    )
    parser.add_argument("--require-pass", action="store_true", help="Return exit code 1 when the report fails structurally.")
    parser.add_argument("--force", action="store_true", help="Delete an existing non-empty output directory first.")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    prepare_output_dir(args.out_dir, force=args.force)
    reports, paths = collect_required_term_pair_diagnostic_reports(args.evidence_root)
    report = build_model_capability_required_term_pair_diagnostic_rollup(
        reports,
        out_dir=args.out_dir,
        source_paths=paths,
    )
    outputs = write_model_capability_required_term_pair_diagnostic_rollup_outputs(report, args.out_dir)
    print(render_model_capability_required_term_pair_diagnostic_rollup_text(report), end="")
    print("outputs=" + json.dumps(outputs, ensure_ascii=True))
    if resolve_exit_code(report, require_pass=args.require_pass):
        raise SystemExit(1)


def prepare_output_dir(out_dir: Path, *, force: bool) -> None:
    if out_dir.exists() and any(out_dir.iterdir()):
        if not force:
            raise SystemExit(f"output directory is not empty; pass --force to replace it: {out_dir}")
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)


if __name__ == "__main__":
    main()
