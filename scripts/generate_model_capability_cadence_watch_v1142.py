from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from minigpt.model_capability_cadence import (  # noqa: E402
    DEFAULT_MAX_NON_CAPABILITY_RUN,
    build_model_capability_cadence_report,
    resolve_exit_code,
    write_model_capability_cadence_watch_outputs,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Publish the MiniGPT model capability cadence watch report.")
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--out-dir", type=Path, default=ROOT / "runs" / "model-capability-cadence-watch-v1142")
    parser.add_argument("--max-non-capability-run", type=int, default=DEFAULT_MAX_NON_CAPABILITY_RUN)
    parser.add_argument("--require-ready", action="store_true")
    parser.add_argument("--require-within-cadence", action="store_true")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args(argv)

    if args.out_dir.exists():
        if not args.force:
            raise SystemExit(f"Output directory already exists: {args.out_dir}")
        shutil.rmtree(args.out_dir)

    report = build_model_capability_cadence_report(args.root, max_non_capability_run=args.max_non_capability_run)
    outputs = write_model_capability_cadence_watch_outputs(report, args.out_dir)
    summary = report["summary"]
    print(f"status={report['status']}")
    print(f"decision={report['decision']}")
    print(f"leading_non_capability_run={summary['leading_non_capability_run']}")
    print(f"max_non_capability_run={summary['max_non_capability_run']}")
    print(f"latest_model_capability_version={summary['latest_model_capability_version']}")
    print(f"latest_refactor_version={summary['latest_refactor_version']}")
    print(f"versions_since_last_refactor={summary['versions_since_last_refactor']}")
    print(f"latest_explanation_version={summary['latest_explanation_version']}")
    print(f"versions_since_last_explanation={summary['versions_since_last_explanation']}")
    print(f"latest_evidence_version={summary['latest_evidence_version']}")
    print(f"versions_since_last_evidence={summary['versions_since_last_evidence']}")
    print(f"due_count={summary['due_count']}")
    print(f"due_list={summary['due_list']}")
    print(f"next_action={summary['next_action']}")
    print(f"outputs={outputs}")
    return resolve_exit_code(
        report,
        require_ready=args.require_ready,
        require_within_cadence=args.require_within_cadence,
    )


if __name__ == "__main__":
    raise SystemExit(main())
