from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path
from typing import Sequence

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.model_capability_required_term_pair_readiness_objective_or_decoding_alternative_selector import (  # noqa: E402
    build_objective_or_decoding_alternative_selector,
    locate_objective_or_decoding_alternative_selector_source,
    read_json_report,
    resolve_exit_code,
)
from minigpt.model_capability_required_term_pair_readiness_objective_or_decoding_alternative_selector_artifacts import (  # noqa: E402
    render_objective_or_decoding_alternative_selector_text,
    write_objective_or_decoding_alternative_selector_outputs,
)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Select the next objective-or-decoding alternative after route closeout.")
    parser.add_argument("closeout", type=Path, help="Exact-surface repair route closeout JSON or output directory.")
    parser.add_argument("--out-dir", type=Path, default=ROOT / "runs" / "model-capability-required-term-pair-readiness-objective-or-decoding-alternative-selector")
    parser.add_argument("--require-pass", action="store_true", help="Return exit code 1 when selector checks fail.")
    parser.add_argument("--force", action="store_true", help="Delete an existing non-empty output directory first.")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    source = locate_objective_or_decoding_alternative_selector_source(args.closeout)
    prepare_output_dir(args.out_dir, force=args.force)
    report = build_objective_or_decoding_alternative_selector(read_json_report(source), source_path=source)
    outputs = write_objective_or_decoding_alternative_selector_outputs(report, args.out_dir)
    print(render_objective_or_decoding_alternative_selector_text(report), end="")
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
