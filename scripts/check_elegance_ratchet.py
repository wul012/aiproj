from __future__ import annotations

import argparse
import json
from pathlib import Path

try:
    from scripts._bootstrap import PROJECT_ROOT, ensure_src_path
except ModuleNotFoundError:  # pragma: no cover - direct script execution path
    from _bootstrap import PROJECT_ROOT, ensure_src_path  # type: ignore[import-not-found,no-redef]

ensure_src_path()

from minigpt.elegance_ratchet import (  # noqa: E402
    DEFAULT_BASELINE_PATH,
    METRIC_KEYS,
    build_elegance_ratchet_report,
    resolve_exit_code,
    update_baseline,
    write_elegance_ratchet_outputs,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Check the MiniGPT whole-codebase elegance ratchet.")
    parser.add_argument("--baseline", type=Path, default=DEFAULT_BASELINE_PATH)
    parser.add_argument("--project-root", type=Path, default=PROJECT_ROOT)
    parser.add_argument("--out-dir", type=Path,
                        default=PROJECT_ROOT / "runs" / "elegance-ratchet")
    parser.add_argument("--update-baseline", action="store_true",
                        help="Tighten the baseline to current values "
                             "(refused unless the check passes).")
    parser.add_argument("--no-fail", action="store_true",
                        help="Always return 0 after writing outputs.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    report = build_elegance_ratchet_report(args.baseline,
                                           project_root=args.project_root)
    outputs = write_elegance_ratchet_outputs(report, args.out_dir)
    print(f"status={report['status']}")
    for key in METRIC_KEYS:
        print(f"{key}={report['metrics'][key]}"
              f" (baseline {report['baseline'][key]})")
    if args.update_baseline:
        print(f"baseline_updated={update_baseline(report, args.baseline)}")
    print(f"outputs={json.dumps(outputs, ensure_ascii=False)}")
    if args.no_fail:
        return 0
    return resolve_exit_code(report, require_pass=True)


if __name__ == "__main__":
    raise SystemExit(main())
