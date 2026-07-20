"""Forwarding shim (v1299): renamed to scripts/build_ack_bundle_receipt.py."""
try:
    from scripts.build_ack_bundle_receipt import main
except ModuleNotFoundError:  # direct script execution path
    from build_ack_bundle_receipt import main  # type: ignore[no-redef]

if __name__ == "__main__":
    raise SystemExit(main())
