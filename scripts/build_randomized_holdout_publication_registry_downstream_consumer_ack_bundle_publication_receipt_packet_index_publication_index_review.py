"""Forwarding shim (v1299): renamed to scripts/build_ack_bundle_review.py."""
try:
    from scripts.build_ack_bundle_review import main
except ModuleNotFoundError:  # direct script execution path
    from build_ack_bundle_review import main  # type: ignore[no-redef]

if __name__ == "__main__":
    raise SystemExit(main())
