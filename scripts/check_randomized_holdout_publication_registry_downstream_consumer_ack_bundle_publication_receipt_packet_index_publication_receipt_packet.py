"""Forwarding shim (v1299): renamed to scripts/check_ack_bundle_packet.py."""
try:
    from scripts.check_ack_bundle_packet import main
except ModuleNotFoundError:  # direct script execution path
    from check_ack_bundle_packet import main  # type: ignore[no-redef]

if __name__ == "__main__":
    raise SystemExit(main())
