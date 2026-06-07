from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path
from typing import Sequence

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.randomized_holdout_publication_registry_downstream_consumer_ack_bundle import (  # noqa: E402
    build_randomized_holdout_publication_registry_downstream_consumer_ack_bundle,
    locate_randomized_holdout_publication_registry_downstream_consumer_ack,
    locate_randomized_holdout_publication_registry_downstream_consumer_ack_check,
    read_json_report,
    resolve_exit_code,
)
from minigpt.randomized_holdout_publication_registry_downstream_consumer_ack_bundle_artifacts import (  # noqa: E402
    render_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_text,
    write_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_outputs,
)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a randomized holdout publication registry downstream consumer acknowledgement bundle.")
    parser.add_argument("--consumer-ack", type=Path, required=True, help="Downstream consumer ack JSON or output directory.")
    parser.add_argument("--consumer-ack-check", type=Path, required=True, help="Downstream consumer ack contract check JSON or output directory.")
    parser.add_argument("--out-dir", type=Path, default=ROOT / "runs" / "randomized-holdout-publication-registry-downstream-consumer-ack-bundle")
    parser.add_argument("--require-bundle-ready", action="store_true")
    parser.add_argument("--require-lookup-ready", action="store_true")
    parser.add_argument("--require-promotion-ready", action="store_true")
    parser.add_argument("--force", action="store_true")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    ack_path = locate_randomized_holdout_publication_registry_downstream_consumer_ack(args.consumer_ack)
    ack_check_path = locate_randomized_holdout_publication_registry_downstream_consumer_ack_check(args.consumer_ack_check)
    prepare_output_dir(args.out_dir, force=args.force)
    report = build_randomized_holdout_publication_registry_downstream_consumer_ack_bundle(
        read_json_report(ack_path),
        read_json_report(ack_check_path),
        consumer_ack_path=ack_path,
        consumer_ack_check_path=ack_check_path,
    )
    outputs = write_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_outputs(report, args.out_dir)
    print(render_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_text(report), end="")
    print("outputs=" + json.dumps(outputs, ensure_ascii=True))
    code = resolve_exit_code(
        report,
        require_bundle_ready=args.require_bundle_ready,
        require_lookup_ready=args.require_lookup_ready,
        require_promotion_ready=args.require_promotion_ready,
    )
    if code:
        raise SystemExit(code)


def prepare_output_dir(out_dir: Path, *, force: bool) -> None:
    if out_dir.exists() and any(out_dir.iterdir()):
        if not force:
            raise SystemExit(f"output directory is not empty; pass --force to replace it: {out_dir}")
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)


if __name__ == "__main__":
    main()
