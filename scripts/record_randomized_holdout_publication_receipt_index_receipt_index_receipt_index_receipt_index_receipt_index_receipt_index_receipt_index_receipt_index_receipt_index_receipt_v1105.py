"""Forwarding shim (v1297): renamed to scripts/record_receipt_chain_v1105.py."""
try:
    from scripts.record_receipt_chain_v1105 import main
except ModuleNotFoundError:  # direct script execution path
    from record_receipt_chain_v1105 import main  # type: ignore[no-redef]

if __name__ == "__main__":
    raise SystemExit(main())
