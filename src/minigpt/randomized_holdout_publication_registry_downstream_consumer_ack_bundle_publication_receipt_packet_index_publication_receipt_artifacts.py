"""Forwarding shim (v1299): renamed to minigpt.ack_bundle_receipt_artifacts."""
import sys

from minigpt import ack_bundle_receipt_artifacts as _target

sys.modules[__name__] = _target
