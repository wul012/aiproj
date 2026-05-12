from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.release_gate import build_release_gate, exit_code_for_gate, write_release_gate_outputs


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check a MiniGPT release bundle against release gate policy.")
    parser.add_argument("--bundle", type=Path, default=ROOT / "runs" / "release-bundle" / "release_bundle.json")
    parser.add_argument("--out-dir", type=Path, default=None, help="Output directory, defaults to runs/release-gate")
    parser.add_argument("--min-audit-score", type=float, default=90.0)
    parser.add_argument("--min-ready-runs", type=int, default=1)
    parser.add_argument("--title", type=str, default="MiniGPT release gate")
    parser.add_argument(
        "--allow-missing-generation-quality",
        action="store_true",
        help="Do not require generation_quality and non_pass_generation_quality audit checks",
    )
    parser.add_argument("--fail-on-warn", action="store_true", help="Exit non-zero for warn as well as fail")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    out_dir = args.out_dir or args.bundle.parent.parent / "release-gate"
    gate = build_release_gate(
        args.bundle,
        minimum_audit_score=args.min_audit_score,
        minimum_ready_runs=args.min_ready_runs,
        require_generation_quality=not args.allow_missing_generation_quality,
        title=args.title,
    )
    outputs = write_release_gate_outputs(gate, out_dir)
    summary = gate["summary"]

    print(f"bundle={args.bundle}")
    print(f"gate_status={summary['gate_status']}")
    print(f"decision={summary['decision']}")
    print(f"checks={summary['pass_count']} pass/{summary['warn_count']} warn/{summary['fail_count']} fail")
    print(f"release_status={summary['release_status']}")
    print(f"audit_status={summary['audit_status']}")
    print(f"require_generation_quality={gate['policy']['require_generation_quality_audit_checks']}")
    print("outputs=" + json.dumps(outputs, ensure_ascii=False))
    if gate["warnings"]:
        print("warnings=" + json.dumps(gate["warnings"], ensure_ascii=False))
    raise SystemExit(exit_code_for_gate(gate, fail_on_warn=args.fail_on_warn))


if __name__ == "__main__":
    main()
