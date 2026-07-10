from __future__ import annotations

import argparse
import json
from collections.abc import Sequence
from pathlib import Path

try:
    from scripts._bootstrap import PROJECT_ROOT, ensure_src_path
except ModuleNotFoundError:  # pragma: no cover - direct script execution path
    from _bootstrap import PROJECT_ROOT, ensure_src_path

ROOT = PROJECT_ROOT
ensure_src_path()

from minigpt.evaluation.generation_quality import build_generation_quality_report, write_generation_quality_outputs  # noqa: E402


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Analyze MiniGPT generation quality from eval suite or sampling outputs.")
    parser.add_argument("--input", type=Path, default=ROOT / "runs" / "minigpt" / "eval_suite" / "eval_suite.json")
    parser.add_argument("--source-type", choices=["auto", "eval_suite", "sample_lab", "generic_results"], default="auto")
    parser.add_argument("--out-dir", type=Path, default=None, help="Output directory, defaults to input parent/generation-quality")
    parser.add_argument("--min-continuation-chars", type=int, default=8)
    parser.add_argument("--min-unique-ratio", type=float, default=0.25)
    parser.add_argument("--max-repeat-run", type=int, default=8)
    parser.add_argument("--max-repeated-ngram-ratio", type=float, default=0.65)
    parser.add_argument("--ngram-size", type=int, default=2)
    parser.add_argument("--title", type=str, default="MiniGPT generation quality report")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    out_dir = args.out_dir or args.input.parent / "generation-quality"
    report = build_generation_quality_report(
        args.input,
        source_type=args.source_type,
        min_continuation_chars=args.min_continuation_chars,
        min_unique_ratio=args.min_unique_ratio,
        max_repeat_run=args.max_repeat_run,
        max_repeated_ngram_ratio=args.max_repeated_ngram_ratio,
        ngram_size=args.ngram_size,
        title=args.title,
    )
    outputs = write_generation_quality_outputs(report, out_dir)
    summary = report["summary"]

    print(f"input={args.input}")
    print(f"source_type={report['source_type']}")
    print(f"overall_status={summary['overall_status']}")
    print(f"cases={summary['case_count']}")
    print(f"checks={summary['pass_count']} pass/{summary['warn_count']} warn/{summary['fail_count']} fail")
    print(f"avg_unique_ratio={summary['avg_unique_ratio']}")
    flag_summary = summary.get("flag_summary") if isinstance(summary.get("flag_summary"), dict) else {}
    flag_id_counts = flag_summary.get("flag_id_counts") if isinstance(flag_summary.get("flag_id_counts"), dict) else {}
    dominant_flag = max(flag_id_counts.items(), key=lambda item: (int(item[1]), item[0]), default=None)
    print(f"flags={flag_summary.get('total_flags', 0)}")
    if dominant_flag:
        print(f"dominant_flag={dominant_flag[0]}:{dominant_flag[1]}")
    print("outputs=" + json.dumps(outputs, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
