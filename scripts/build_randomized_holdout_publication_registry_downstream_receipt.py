from __future__ import annotations

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.randomized_holdout_publication_registry_downstream_receipt import (  # noqa: E402
    build_randomized_holdout_publication_registry_downstream_receipt,
    locate_randomized_holdout_publication_registry_downstream_guard,
    read_json_report,
    resolve_exit_code,
)
from minigpt.randomized_holdout_publication_registry_downstream_receipt_artifacts import (  # noqa: E402
    write_randomized_holdout_publication_registry_downstream_receipt_outputs,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Record a downstream governance lookup receipt from a randomized holdout publication registry guard.")
    parser.add_argument("--guard", required=True, help="Path to downstream guard JSON or output directory.")
    parser.add_argument("--out-dir", required=True, help="Directory for receipt outputs.")
    parser.add_argument("--consumer-name", default="publication_registry_governance_lookup_reader")
    parser.add_argument("--requested-use", default="downstream_governance_lookup_only")
    parser.add_argument("--require-receipt-ready", action="store_true")
    parser.add_argument("--require-promotion-ready", action="store_true")
    parser.add_argument("--force", action="store_true", help="Overwrite an existing output directory.")
    args = parser.parse_args(argv)

    out_dir = Path(args.out_dir)
    if out_dir.exists() and any(out_dir.iterdir()) and not args.force:
        raise FileExistsError(f"output directory is not empty: {out_dir}")

    guard_path = locate_randomized_holdout_publication_registry_downstream_guard(args.guard)
    guard_report = read_json_report(guard_path)
    report = build_randomized_holdout_publication_registry_downstream_receipt(
        guard_report,
        downstream_guard_path=guard_path,
        consumer_name=args.consumer_name,
        requested_use=args.requested_use,
    )
    outputs = write_randomized_holdout_publication_registry_downstream_receipt_outputs(report, out_dir)
    summary = report["summary"]
    print(f"status={report['status']}")
    print(f"decision={report['decision']}")
    print(f"failed_count={report['failed_count']}")
    print(f"randomized_holdout_publication_registry_downstream_receipt_ready={summary['randomized_holdout_publication_registry_downstream_receipt_ready']}")
    print(f"receipt_id={summary['receipt_id']}")
    print(f"receipt_status={summary['receipt_status']}")
    print(f"consumer_name={summary['consumer_name']}")
    print(f"granted_use={summary['granted_use']}")
    print(f"entry_count={summary['entry_count']}")
    print(f"lookup_key_count={summary['lookup_key_count']}")
    print(f"promotion_ready={summary['promotion_ready']}")
    print(f"blocked_uses={summary['blocked_uses']}")
    print(f"next_step={summary['next_step']}")
    print(f"passed_check_count={summary['passed_check_count']}")
    print(f"failed_check_count={summary['failed_check_count']}")
    print(f"outputs={outputs}")
    return resolve_exit_code(
        report,
        require_receipt_ready=args.require_receipt_ready,
        require_promotion_ready=args.require_promotion_ready,
    )


if __name__ == "__main__":
    raise SystemExit(main())
