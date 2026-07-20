"""Forwarding shim (v1299): renamed to minigpt.packet_chain_receipt_v999_artifacts."""
import sys

from minigpt import packet_chain_receipt_v999_artifacts as _target

sys.modules[__name__] = _target
