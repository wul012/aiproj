"""Forwarding shim (v1298): renamed to scripts/build_packet_chain_index_v1009.py."""
try:
    from scripts.build_packet_chain_index_v1009 import main
except ModuleNotFoundError:  # direct script execution path
    from build_packet_chain_index_v1009 import main  # type: ignore[no-redef]

if __name__ == "__main__":
    raise SystemExit(main())
