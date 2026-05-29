from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path
from typing import Sequence

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.model_capability_required_term_uptake import (  # noqa: E402
    build_model_capability_required_term_uptake,
    locate_model_capability_required_term_coverage,
    read_json_report,
)
from minigpt.model_capability_required_term_uptake_artifacts import (  # noqa: E402
    render_model_capability_required_term_uptake_text,
    write_model_capability_required_term_uptake_outputs,
)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit required-term uptake in archived tiny generations.")
    parser.add_argument(
        "required_term_coverage",
        type=Path,
        help="Path to model_capability_required_term_coverage.json or its directory.",
    )
    parser.add_argument("--out-dir", type=Path, default=ROOT / "runs" / "model-capability-required-term-uptake")
    parser.add_argument("--require-pass", action="store_true", help="Return exit code 1 when the audit fails.")
    parser.add_argument("--force", action="store_true", help="Delete an existing non-empty output directory first.")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    source = locate_model_capability_required_term_coverage(args.required_term_coverage)
    prepare_output_dir(args.out_dir, force=args.force)
    report = build_model_capability_required_term_uptake(
        read_json_report(source),
        out_dir=args.out_dir,
        source_path=source,
        search_base=ROOT,
    )
    outputs = write_model_capability_required_term_uptake_outputs(report, args.out_dir)
    print(render_model_capability_required_term_uptake_text(report), end="")
    print("outputs=" + json.dumps(outputs, ensure_ascii=True))
    if resolve_exit_code(report, require_pass=args.require_pass):
        raise SystemExit(1)


def prepare_output_dir(out_dir: Path, *, force: bool) -> None:
    if out_dir.exists() and any(out_dir.iterdir()):
        if not force:
            raise SystemExit(f"output directory is not empty; pass --force to replace it: {out_dir}")
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)


def resolve_exit_code(report: dict[str, object], *, require_pass: bool) -> int:
    if require_pass and report.get("status") != "pass":
        return 1
    return 0


if __name__ == "__main__":
    main()
