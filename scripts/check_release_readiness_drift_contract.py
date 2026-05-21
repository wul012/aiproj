from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.release_readiness_drift_contract import (  # noqa: E402
    check_release_readiness_drift_contract,
    load_release_readiness_comparison,
    render_release_readiness_drift_contract_check,
    resolve_release_readiness_comparison_path,
    write_release_readiness_drift_contract_outputs,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate release readiness comparison failed-reason drift fields against their source reason lists."
    )
    parser.add_argument(
        "comparison",
        type=Path,
        nargs="?",
        default=ROOT / "runs" / "release-readiness-comparison",
        help="Path to release_readiness_comparison.json or its output directory.",
    )
    parser.add_argument("--out-dir", type=Path, default=ROOT / "runs" / "release-readiness-drift-contract-check")
    parser.add_argument("--no-fail", action="store_true", help="Write check outputs but do not exit non-zero on fail.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    comparison_path = resolve_release_readiness_comparison_path(args.comparison)
    comparison = load_release_readiness_comparison(comparison_path)
    report = check_release_readiness_drift_contract(comparison, comparison_path=comparison_path)
    outputs = write_release_readiness_drift_contract_outputs(report, args.out_dir)
    print(render_release_readiness_drift_contract_check(report), end="")
    print("outputs=" + json.dumps(outputs, ensure_ascii=False))
    if report["status"] == "fail" and not args.no_fail:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
