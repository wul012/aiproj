"""Forwarding shim (v1299): renamed to scripts/check_registry_ack_pub.py."""
try:
    from scripts.check_registry_ack_pub import main
except ModuleNotFoundError:  # direct script execution path
    from check_registry_ack_pub import main  # type: ignore[no-redef]

if __name__ == "__main__":
    raise SystemExit(main())
