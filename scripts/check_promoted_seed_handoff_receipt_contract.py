from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.promoted_training_scale_seed_handoff_receipt_contract import (  # noqa: E402
    build_promoted_training_scale_seed_handoff_receipt_contract_summary,
    render_promoted_training_scale_seed_handoff_receipt_contract_summary_text,
    write_promoted_training_scale_seed_handoff_receipt_contract_summary_outputs,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Summarize MiniGPT promoted seed handoff receipt contract readiness."
    )
    parser.add_argument(
        "handoff_report",
        type=Path,
        help="promoted_training_scale_seed_handoff.json file or handoff output directory",
    )
    parser.add_argument("--out-dir", type=Path, default=None, help="Optional directory for JSON/text/Markdown/HTML outputs.")
    parser.add_argument(
        "--allow-stop",
        action="store_true",
        help="Return zero for a consistent stop handoff. Default treats stop as a failing automation outcome.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    summary = build_promoted_training_scale_seed_handoff_receipt_contract_summary(args.handoff_report)
    print(render_promoted_training_scale_seed_handoff_receipt_contract_summary_text(summary), end="")
    if args.out_dir is not None:
        outputs = write_promoted_training_scale_seed_handoff_receipt_contract_summary_outputs(summary, args.out_dir)
        print(f"receipt_contract_json={outputs['json']}")
        print(f"receipt_contract_text={outputs['text']}")
        print(f"receipt_contract_markdown={outputs['markdown']}")
        print(f"receipt_contract_html={outputs['html']}")
    if summary["status"] != "pass":
        raise SystemExit(1)
    if summary["decision"] == "stop" and not args.allow_stop:
        raise SystemExit(int(summary.get("checker_exit_code") or 1))


if __name__ == "__main__":
    main()
