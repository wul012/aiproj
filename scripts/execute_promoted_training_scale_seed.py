from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.promoted_training_scale_seed_handoff import (  # noqa: E402
    build_promoted_training_scale_seed_handoff,
    write_promoted_training_scale_seed_handoff_outputs,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate or execute a MiniGPT promoted training scale seed plan command.")
    parser.add_argument("seed", type=Path, help="promoted_training_scale_seed.json file or seed directory")
    parser.add_argument("--out-dir", type=Path, default=None, help="Output directory; defaults to <seed>/handoff")
    parser.add_argument("--execute", action="store_true", help="Run the generated next-cycle plan command. Default only validates it.")
    parser.add_argument("--no-allow-review", action="store_true", help="Block review-status seeds instead of allowing their plan command.")
    parser.add_argument("--timeout-seconds", type=int, default=900)
    parser.add_argument("--title", type=str, default="MiniGPT promoted training scale seed handoff")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    seed_path = Path(args.seed)
    out_dir = args.out_dir or _default_out_dir(seed_path)
    report = build_promoted_training_scale_seed_handoff(
        seed_path,
        execute=args.execute,
        allow_review=not args.no_allow_review,
        timeout_seconds=args.timeout_seconds,
        title=args.title,
    )
    outputs = write_promoted_training_scale_seed_handoff_outputs(report, out_dir)
    summary = report["summary"]
    execution = report["execution"]
    print(f"handoff_status={summary.get('handoff_status')}")
    print(f"seed_status={report.get('seed_status')}")
    print(f"decision_status={summary.get('decision_status')}")
    print(f"execute={report.get('execute')}")
    print(f"returncode={execution.get('returncode')}")
    print(f"available_artifacts={summary.get('available_artifact_count')}/{summary.get('artifact_count')}")
    print(f"plan_status={summary.get('plan_status')}")
    print(f"next_batch_command_available={summary.get('next_batch_command_available')}")
    print("summary=" + json.dumps(summary, ensure_ascii=False))
    print(f"command={report.get('command_text')}")
    print(f"next_batch_command={report.get('next_batch_command_text')}")
    print("outputs=" + json.dumps(outputs, ensure_ascii=False))
    if summary.get("handoff_status") in {"blocked", "failed", "timeout"}:
        raise SystemExit(1)


def _default_out_dir(path: Path) -> Path:
    if path.is_dir():
        return path / "handoff"
    return path.parent / "handoff"


if __name__ == "__main__":
    main()
