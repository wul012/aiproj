from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.promoted_training_scale_seed_handoff_receipt import (  # noqa: E402
    check_promoted_training_scale_seed_handoff_embedded_receipt_check,
    load_promoted_training_scale_seed_handoff_report,
    render_promoted_training_scale_seed_handoff_embedded_receipt_check,
    resolve_promoted_training_scale_seed_handoff_report_path,
    write_promoted_training_scale_seed_handoff_embedded_receipt_check_outputs,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check embedded receipt-check fields in a MiniGPT promoted seed handoff report."
    )
    parser.add_argument(
        "handoff_report",
        type=Path,
        help="promoted_training_scale_seed_handoff.json file or handoff output directory",
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=None,
        help="Optional directory for embedded receipt-check JSON/text outputs.",
    )
    parser.add_argument(
        "--allow-stop",
        action="store_true",
        help="Return zero for a consistent embedded stop receipt-check. Default treats stop as a failing outcome.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    report_path = resolve_promoted_training_scale_seed_handoff_report_path(args.handoff_report)
    report = load_promoted_training_scale_seed_handoff_report(report_path)
    check = check_promoted_training_scale_seed_handoff_embedded_receipt_check(report)
    check["handoff_report_path"] = str(report_path)
    print(render_promoted_training_scale_seed_handoff_embedded_receipt_check(check), end="")
    print(f"handoff_report_path={report_path}")
    if args.out_dir is not None:
        outputs = write_promoted_training_scale_seed_handoff_embedded_receipt_check_outputs(check, args.out_dir)
        print(f"embedded_receipt_check_output_json={outputs['json']}")
        print(f"embedded_receipt_check_output_text={outputs['text']}")
    if check["status"] != "pass":
        raise SystemExit(1)
    if check["decision"] == "stop" and not args.allow_stop:
        raise SystemExit(int(check.get("exit_code") or 1))


if __name__ == "__main__":
    main()
