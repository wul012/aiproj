from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.promoted_training_scale_seed_handoff_receipt_contract_check_failure_smoke import (  # noqa: E402
    render_failure_smoke_text,
    run_promoted_training_scale_seed_handoff_receipt_contract_check_failure_smoke,
    write_failure_smoke_outputs,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run controlled failure-family smoke scenarios for receipt contract summary-check outputs."
    )
    parser.add_argument(
        "summary",
        type=Path,
        help="Contract summary JSON file or directory containing promoted_training_scale_seed_handoff_receipt_contract_summary.json",
    )
    parser.add_argument("--out-dir", type=Path, required=True, help="Output directory for failure smoke artifacts.")
    parser.add_argument("--force", action="store_true", help="Delete an existing non-empty output directory first.")
    parser.add_argument("--no-fail", action="store_true", help="Always return zero after writing artifacts.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.out_dir.exists() and any(args.out_dir.iterdir()):
        if not args.force:
            raise SystemExit(f"output directory is not empty; pass --force to replace it: {args.out_dir}")
        shutil.rmtree(args.out_dir)
    smoke = run_promoted_training_scale_seed_handoff_receipt_contract_check_failure_smoke(
        args.summary,
        args.out_dir,
        force=False,
    )
    outputs = write_failure_smoke_outputs(smoke, args.out_dir)
    print(render_failure_smoke_text(smoke), end="")
    print(f"receipt_contract_summary_check_failure_smoke_json={outputs['json']}")
    print(f"receipt_contract_summary_check_failure_smoke_csv={outputs['csv']}")
    print(f"receipt_contract_summary_check_failure_smoke_text={outputs['text']}")
    print(f"receipt_contract_summary_check_failure_smoke_markdown={outputs['markdown']}")
    print(f"receipt_contract_summary_check_failure_smoke_html={outputs['html']}")
    if smoke["status"] != "pass" and not args.no_fail:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
