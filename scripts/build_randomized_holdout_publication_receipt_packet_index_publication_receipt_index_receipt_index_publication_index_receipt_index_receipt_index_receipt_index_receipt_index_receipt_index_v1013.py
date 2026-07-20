"""Forwarding shim (v1294): renamed to scripts/build_receipt_packet_index_v1013.py."""
try:
    from scripts.build_receipt_packet_index_v1013 import main
except ModuleNotFoundError:  # direct script execution path
    from build_receipt_packet_index_v1013 import main  # type: ignore[no-redef]

if __name__ == "__main__":
    raise SystemExit(main())
