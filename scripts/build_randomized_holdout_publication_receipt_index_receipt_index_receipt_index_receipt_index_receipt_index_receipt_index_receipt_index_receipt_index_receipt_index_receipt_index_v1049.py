"""Forwarding shim (v1297): renamed to scripts/build_receipt_chain_v1049.py."""
try:
    from scripts.build_receipt_chain_v1049 import main
except ModuleNotFoundError:  # direct script execution path
    from build_receipt_chain_v1049 import main  # type: ignore[no-redef]

if __name__ == "__main__":
    raise SystemExit(main())
