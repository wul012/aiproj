"""Forwarding shim (v1298): renamed to scripts/record_packet_chain_receipt_v1003.py."""
try:
    from scripts.record_packet_chain_receipt_v1003 import main
except ModuleNotFoundError:  # direct script execution path
    from record_packet_chain_receipt_v1003 import main  # type: ignore[no-redef]

if __name__ == "__main__":
    raise SystemExit(main())
