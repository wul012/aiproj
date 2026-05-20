from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.promoted_training_scale_seed_handoff_receipt import (  # noqa: E402
    check_promoted_training_scale_seed_handoff_automation_receipt,
    load_promoted_training_scale_seed_handoff_automation_receipt,
    render_promoted_training_scale_seed_handoff_automation_receipt_check,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check a MiniGPT promoted seed handoff automation receipt.")
    parser.add_argument("receipt", type=Path, help="promoted_training_scale_seed_handoff_automation_receipt.json")
    parser.add_argument(
        "--allow-stop",
        action="store_true",
        help="Return zero for a structurally valid stop receipt. Default treats stop as a failing automation outcome.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    receipt = load_promoted_training_scale_seed_handoff_automation_receipt(args.receipt)
    check = check_promoted_training_scale_seed_handoff_automation_receipt(receipt)
    print(render_promoted_training_scale_seed_handoff_automation_receipt_check(check), end="")
    if check["status"] != "pass":
        raise SystemExit(1)
    if check["decision"] == "stop" and not args.allow_stop:
        raise SystemExit(int(check.get("exit_code") or 1))


if __name__ == "__main__":
    main()
