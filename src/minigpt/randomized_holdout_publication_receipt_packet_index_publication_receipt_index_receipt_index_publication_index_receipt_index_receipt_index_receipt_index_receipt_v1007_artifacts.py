"""Forwarding shim (v1298): renamed to minigpt.packet_chain_receipt_v1007_artifacts."""
import sys

from minigpt import packet_chain_receipt_v1007_artifacts as _target

sys.modules[__name__] = _target
