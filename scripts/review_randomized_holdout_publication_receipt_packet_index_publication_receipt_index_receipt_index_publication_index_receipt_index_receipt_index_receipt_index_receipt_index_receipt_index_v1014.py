"""Forwarding shim (v1294): renamed to scripts/review_receipt_packet_index_v1014.py."""
try:
    from scripts.review_receipt_packet_index_v1014 import main
except ModuleNotFoundError:  # direct script execution path
    from review_receipt_packet_index_v1014 import main  # type: ignore[no-redef]

if __name__ == "__main__":
    raise SystemExit(main())
