"""Forwarding shim (v1299): renamed to scripts/record_packet_chain_receipt_v995.py."""
try:
    from scripts.record_packet_chain_receipt_v995 import main
except ModuleNotFoundError:  # direct script execution path
    from record_packet_chain_receipt_v995 import main  # type: ignore[no-redef]

if __name__ == "__main__":
    raise SystemExit(main())
