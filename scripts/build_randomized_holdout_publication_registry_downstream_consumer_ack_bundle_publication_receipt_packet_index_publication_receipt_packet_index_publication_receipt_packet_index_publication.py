"""Forwarding shim (v1298): renamed to scripts/build_registry_ack_packet_pub.py."""
try:
    from scripts.build_registry_ack_packet_pub import main
except ModuleNotFoundError:  # direct script execution path
    from build_registry_ack_packet_pub import main  # type: ignore[no-redef]

if __name__ == "__main__":
    raise SystemExit(main())
