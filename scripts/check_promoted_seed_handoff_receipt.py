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
    resolve_promoted_training_scale_seed_handoff_automation_receipt_path,
    write_promoted_training_scale_seed_handoff_automation_receipt_check_outputs,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check a MiniGPT promoted seed handoff automation receipt.")
    parser.add_argument(
        "receipt",
        type=Path,
        help="promoted_training_scale_seed_handoff_automation_receipt.json file or handoff output directory",
    )
    parser.add_argument("--out-dir", type=Path, default=None, help="Optional directory for receipt check JSON/text outputs.")
    parser.add_argument(
        "--allow-stop",
        action="store_true",
        help="Return zero for a structurally valid stop receipt. Default treats stop as a failing automation outcome.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    receipt_path = resolve_promoted_training_scale_seed_handoff_automation_receipt_path(args.receipt)
    receipt = load_promoted_training_scale_seed_handoff_automation_receipt(receipt_path)
    check = check_promoted_training_scale_seed_handoff_automation_receipt(receipt)
    check["receipt_path"] = str(receipt_path)
    print(render_promoted_training_scale_seed_handoff_automation_receipt_check(check), end="")
    print(f"receipt_path={receipt_path}")
    if args.out_dir is not None:
        outputs = write_promoted_training_scale_seed_handoff_automation_receipt_check_outputs(check, args.out_dir)
        print(f"receipt_check_json={outputs['json']}")
        print(f"receipt_check_text={outputs['text']}")
    if check["status"] != "pass":
        raise SystemExit(1)
    if check["decision"] == "stop" and not args.allow_stop:
        raise SystemExit(int(check.get("exit_code") or 1))


if __name__ == "__main__":
    main()
