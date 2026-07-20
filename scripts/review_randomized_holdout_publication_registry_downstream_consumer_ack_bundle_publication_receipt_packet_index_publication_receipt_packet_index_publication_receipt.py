"""Forwarding shim (v1298): renamed to scripts/review_registry_ack_pub_receipt.py."""
try:
    from scripts.review_registry_ack_pub_receipt import main
except ModuleNotFoundError:  # direct script execution path
    from review_registry_ack_pub_receipt import main  # type: ignore[no-redef]

if __name__ == "__main__":
    raise SystemExit(main())
