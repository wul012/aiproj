from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from minigpt.ptq_candidate_v1177 import (  # noqa: E402
    PtqCandidatePolicy,
    build_ptq_candidate_report,
    resolve_exit_code,
    write_ptq_candidate_outputs,
)
from minigpt.readability_report_artifacts import render_readability_text  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Select a bounded MiniGPT PTQ deployment candidate from v1175 evidence.")
    parser.add_argument("ptq_report", type=Path, help="Path to ptq_v1175.json or its output directory.")
    parser.add_argument("--out-dir", type=Path, default=ROOT / "runs" / "ptq-candidate-v1177")
    parser.add_argument("--max-dce-nats", type=float, default=PtqCandidatePolicy.max_dce_nats)
    parser.add_argument("--max-exact-match-drop", type=float, default=PtqCandidatePolicy.max_exact_match_drop)
    parser.add_argument("--max-kl-nats", type=float, default=PtqCandidatePolicy.max_kl_nats)
    parser.add_argument("--require-pass", action="store_true")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args(argv)

    prepare_output_dir(args.out_dir, force=args.force)
    policy = PtqCandidatePolicy(
        max_dce_nats=args.max_dce_nats,
        max_exact_match_drop=args.max_exact_match_drop,
        max_kl_nats=args.max_kl_nats,
    )
    report = build_ptq_candidate_report(args.ptq_report, policy=policy)
    outputs = write_ptq_candidate_outputs(report, args.out_dir)
    print(render_readability_text(report), end="")
    print("outputs=" + json.dumps(outputs, ensure_ascii=False))
    return resolve_exit_code(report, require_pass=args.require_pass)


def prepare_output_dir(out_dir: Path, *, force: bool) -> None:
    if out_dir.exists() and any(out_dir.iterdir()):
        if not force:
            raise SystemExit(f"Output directory already exists: {out_dir}")
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)


if __name__ == "__main__":
    raise SystemExit(main())
