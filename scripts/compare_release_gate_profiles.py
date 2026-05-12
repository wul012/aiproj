from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.release_gate import release_gate_policy_profiles
from minigpt.release_gate_comparison import (
    DEFAULT_COMPARISON_PROFILES,
    build_release_gate_profile_comparison,
    write_release_gate_profile_comparison_outputs,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compare MiniGPT release gate policy profiles.")
    parser.add_argument(
        "--bundle",
        type=Path,
        action="append",
        default=None,
        help="Release bundle JSON. Repeat to compare multiple bundles.",
    )
    parser.add_argument("--out-dir", type=Path, default=None, help="Output directory, defaults to runs/release-gate-profiles")
    parser.add_argument(
        "--profiles",
        nargs="+",
        choices=sorted(release_gate_policy_profiles()),
        default=None,
        help="Policy profiles to compare. Defaults to standard review strict legacy.",
    )
    parser.add_argument("--min-audit-score", type=float, default=None, help="Override every selected policy profile")
    parser.add_argument("--min-ready-runs", type=int, default=None, help="Override every selected policy profile")
    parser.add_argument(
        "--allow-missing-generation-quality",
        action="store_true",
        help="Override every selected policy profile and do not require generation quality audit checks",
    )
    parser.add_argument("--title", type=str, default="MiniGPT release gate profile comparison")
    parser.add_argument("--fail-on-blocked", action="store_true", help="Exit non-zero if any compared profile blocks")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    bundles = args.bundle or [ROOT / "runs" / "release-bundle" / "release_bundle.json"]
    out_dir = args.out_dir or ROOT / "runs" / "release-gate-profiles"
    require_generation_quality = False if args.allow_missing_generation_quality else None
    profiles = args.profiles or list(DEFAULT_COMPARISON_PROFILES)
    report = build_release_gate_profile_comparison(
        bundles,
        policy_profiles=profiles,
        minimum_audit_score=args.min_audit_score,
        minimum_ready_runs=args.min_ready_runs,
        require_generation_quality=require_generation_quality,
        title=args.title,
    )
    outputs = write_release_gate_profile_comparison_outputs(report, out_dir)
    summary = report["summary"]

    print("bundles=" + str(summary["bundle_count"]))
    print("profiles=" + ",".join(report["policy_profiles"]))
    print(f"rows={summary['row_count']}")
    print(f"approved={summary['approved_count']}")
    print(f"needs_review={summary['needs_review_count']}")
    print(f"blocked={summary['blocked_count']}")
    print("outputs=" + json.dumps(outputs, ensure_ascii=False))
    if args.fail_on_blocked and summary["blocked_count"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
