from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.promoted_training_scale_seed_handoff_receipt_contract_check import (  # noqa: E402
    check_promoted_training_scale_seed_handoff_receipt_contract_summary,
    render_promoted_training_scale_seed_handoff_receipt_contract_summary_check_text,
    write_promoted_training_scale_seed_handoff_receipt_contract_summary_check_outputs,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check MiniGPT promoted seed handoff receipt contract summary artifacts."
    )
    parser.add_argument(
        "summary",
        type=Path,
        help="Contract summary JSON file or directory containing promoted_training_scale_seed_handoff_receipt_contract_summary.json",
    )
    parser.add_argument(
        "--handoff",
        type=Path,
        default=None,
        help="Optional promoted seed handoff report or directory. Defaults to handoff_report_path in the summary JSON.",
    )
    parser.add_argument("--out-dir", type=Path, default=None, help="Optional directory for JSON/text/Markdown/HTML check outputs.")
    parser.add_argument(
        "--allow-stop",
        action="store_true",
        help="Return zero for a consistent stop handoff. Default treats stop as a failing automation outcome.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    check = check_promoted_training_scale_seed_handoff_receipt_contract_summary(
        args.summary,
        handoff_path=args.handoff,
    )
    print(render_promoted_training_scale_seed_handoff_receipt_contract_summary_check_text(check), end="")
    if args.out_dir is not None:
        outputs = write_promoted_training_scale_seed_handoff_receipt_contract_summary_check_outputs(check, args.out_dir)
        print(f"receipt_contract_summary_check_json={outputs['json']}")
        print(f"receipt_contract_summary_check_text={outputs['text']}")
        print(f"receipt_contract_summary_check_markdown={outputs['markdown']}")
        print(f"receipt_contract_summary_check_html={outputs['html']}")
    if check["status"] != "pass":
        raise SystemExit(1)
    if check["decision"] == "stop" and not args.allow_stop:
        raise SystemExit(int(check.get("checker_exit_code") or 1))


if __name__ == "__main__":
    main()
