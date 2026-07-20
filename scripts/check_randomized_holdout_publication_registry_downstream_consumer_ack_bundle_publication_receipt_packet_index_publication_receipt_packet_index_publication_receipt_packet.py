"""Forwarding shim (v1298): renamed to scripts/check_registry_ack_packet.py."""
try:
    from scripts.check_registry_ack_packet import main
except ModuleNotFoundError:  # direct script execution path
    from check_registry_ack_packet import main  # type: ignore[no-redef]

if __name__ == "__main__":
    raise SystemExit(main())
