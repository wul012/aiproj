from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.promoted_training_scale_seed_handoff_assurance import (  # noqa: E402
    check_promoted_training_scale_seed_handoff_assurance,
    render_promoted_training_scale_seed_handoff_assurance_check,
    write_promoted_training_scale_seed_handoff_assurance_check_outputs,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check full MiniGPT promoted seed handoff receipt and embedded sidecar assurance."
    )
    parser.add_argument(
        "handoff_report",
        type=Path,
        help="promoted_training_scale_seed_handoff.json file or handoff output directory",
    )
    parser.add_argument("--out-dir", type=Path, default=None, help="Optional directory for assurance JSON/text outputs.")
    parser.add_argument(
        "--allow-stop",
        action="store_true",
        help="Return zero for a consistent stop handoff. Default treats stop as a failing automation outcome.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    check = check_promoted_training_scale_seed_handoff_assurance(args.handoff_report)
    print(render_promoted_training_scale_seed_handoff_assurance_check(check), end="")
    if args.out_dir is not None:
        outputs = write_promoted_training_scale_seed_handoff_assurance_check_outputs(check, args.out_dir)
        print(f"handoff_assurance_json={outputs['json']}")
        print(f"handoff_assurance_text={outputs['text']}")
    if check["status"] != "pass":
        raise SystemExit(1)
    if check["decision"] == "stop" and not args.allow_stop:
        raise SystemExit(int(check.get("exit_code") or 1))


if __name__ == "__main__":
    main()
