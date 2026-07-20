"""Forwarding shim (v1299): renamed to scripts/build_packet_chain_index_v997.py."""
try:
    from scripts.build_packet_chain_index_v997 import main
except ModuleNotFoundError:  # direct script execution path
    from build_packet_chain_index_v997 import main  # type: ignore[no-redef]

if __name__ == "__main__":
    raise SystemExit(main())
