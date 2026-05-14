from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.training_portfolio_comparison import (  # noqa: E402
    build_training_portfolio_comparison,
    write_training_portfolio_comparison_outputs,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compare multiple MiniGPT training portfolio reports.")
    parser.add_argument("portfolios", type=Path, nargs="+", help="training_portfolio.json path or directory")
    parser.add_argument("--name", action="append", default=[], help="Optional display name, repeat once per portfolio")
    parser.add_argument("--baseline", type=str, default=None, help="Baseline name, path, run_name, or 1-based index")
    parser.add_argument("--out-dir", type=Path, default=None, help="Output directory; defaults near the first portfolio")
    parser.add_argument("--title", type=str, default="MiniGPT training portfolio comparison")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    names = args.name or None
    if names is not None and len(names) != len(args.portfolios):
        raise ValueError("--name must be repeated exactly once per portfolio")

    out_dir = args.out_dir or _default_out_dir(args.portfolios[0])
    report = build_training_portfolio_comparison(
        args.portfolios,
        names=names,
        baseline=args.baseline,
        title=args.title,
    )
    outputs = write_training_portfolio_comparison_outputs(report, out_dir)
    print(f"portfolio_count={report['portfolio_count']}")
    print("baseline=" + json.dumps(report["baseline"], ensure_ascii=False))
    print("best_by_overall_score=" + json.dumps(report["best_by_overall_score"], ensure_ascii=False))
    print("best_by_final_val_loss=" + json.dumps(report["best_by_final_val_loss"], ensure_ascii=False))
    print("summary=" + json.dumps(report["summary"], ensure_ascii=False))
    for key, path in outputs.items():
        print(f"saved_{key}={path}")


def _default_out_dir(path: Path) -> Path:
    if path.is_dir():
        return path.parent / "training-portfolio-comparison"
    if path.name == "training_portfolio.json":
        return path.parent.parent / "training-portfolio-comparison"
    return path.parent / "training-portfolio-comparison"


if __name__ == "__main__":
    main()
