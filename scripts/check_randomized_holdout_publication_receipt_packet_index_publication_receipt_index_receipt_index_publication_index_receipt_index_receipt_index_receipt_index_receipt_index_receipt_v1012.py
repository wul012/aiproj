"""Forwarding shim (v1294): renamed to scripts/check_receipt_packet_index_v1012.py."""
try:
    from scripts.check_receipt_packet_index_v1012 import main
except ModuleNotFoundError:  # direct script execution path
    from check_receipt_packet_index_v1012 import main  # type: ignore[no-redef]

if __name__ == "__main__":
    raise SystemExit(main())
