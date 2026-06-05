from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path
from typing import Sequence

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.target_hidden_semantic_holdout_suite import (  # noqa: E402
    build_target_hidden_semantic_holdout_suite,
    locate_replay_review,
    locate_source_holdout_suite,
    read_json_report,
    resolve_exit_code,
)
from minigpt.target_hidden_semantic_holdout_suite_artifacts import (  # noqa: E402
    render_target_hidden_semantic_holdout_suite_text,
    write_target_hidden_semantic_holdout_suite_outputs,
)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a semantic-paraphrase target-hidden tokenizer-covered holdout suite.")
    parser.add_argument("--replay-review", type=Path, required=True, help="v905 replay review JSON or output directory.")
    parser.add_argument("--source-holdout-suite", type=Path, required=True, help="v902 source holdout suite JSON or output directory.")
    parser.add_argument("--tokenizer", type=Path, required=True, help="Tokenizer JSON whose vocabulary must cover candidate prompts.")
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=ROOT / "runs" / "target-hidden-semantic-holdout-suite",
    )
    parser.add_argument("--require-suite-ready", action="store_true", help="Return exit code 1 when suite construction fails.")
    parser.add_argument("--force", action="store_true", help="Delete an existing non-empty output directory first.")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    review_path = locate_replay_review(args.replay_review)
    suite_path = locate_source_holdout_suite(args.source_holdout_suite)
    prepare_output_dir(args.out_dir, force=args.force)
    report = build_target_hidden_semantic_holdout_suite(
        read_json_report(review_path),
        read_json_report(suite_path),
        tokenizer_path=args.tokenizer,
        replay_review_path=review_path,
        source_holdout_suite_path=suite_path,
    )
    outputs = write_target_hidden_semantic_holdout_suite_outputs(report, args.out_dir)
    print(render_target_hidden_semantic_holdout_suite_text(report), end="")
    print("outputs=" + json.dumps(outputs, ensure_ascii=True))
    if resolve_exit_code(report, require_suite_ready=args.require_suite_ready):
        raise SystemExit(1)


def prepare_output_dir(out_dir: Path, *, force: bool) -> None:
    if out_dir.exists() and any(out_dir.iterdir()):
        if not force:
            raise SystemExit(f"output directory is not empty; pass --force to replace it: {out_dir}")
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)


if __name__ == "__main__":
    main()
