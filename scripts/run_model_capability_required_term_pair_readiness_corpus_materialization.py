from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path
from typing import Sequence

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.model_capability_required_term_pair_readiness_corpus_materialization import (  # noqa: E402
    build_pair_readiness_corpus_materialization,
    locate_pair_readiness_corpus_materialization_source,
    read_json_report,
    resolve_exit_code,
    write_materialized_pair_readiness_inputs,
)
from minigpt.model_capability_required_term_pair_readiness_corpus_materialization_artifacts import (  # noqa: E402
    render_pair_readiness_corpus_materialization_text,
    write_pair_readiness_corpus_materialization_outputs,
)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Materialize pair-readiness training corpus and heldout fixture.")
    parser.add_argument("contract", type=Path, help="Pair-readiness split contract JSON or output directory.")
    parser.add_argument("--out-dir", type=Path, default=ROOT / "runs" / "model-capability-required-term-pair-readiness-corpus-materialization")
    parser.add_argument("--repeat", type=int, default=320)
    parser.add_argument("--require-pass", action="store_true", help="Return exit code 1 when materialization checks fail.")
    parser.add_argument("--force", action="store_true", help="Delete an existing non-empty output directory first.")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    prepare_output_dir(args.out_dir, force=args.force)
    source = locate_pair_readiness_corpus_materialization_source(args.contract)
    report = build_pair_readiness_corpus_materialization(
        read_json_report(source),
        out_dir=args.out_dir,
        repeat=args.repeat,
        source_path=source,
    )
    if report.get("status") == "pass":
        write_materialized_pair_readiness_inputs(report)
    outputs = write_pair_readiness_corpus_materialization_outputs(report, args.out_dir)
    print(render_pair_readiness_corpus_materialization_text(report), end="")
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
