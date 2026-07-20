"""Forwarding shim (v1298): renamed to minigpt.packet_chain_receipt_v1003."""
import sys

from minigpt import packet_chain_receipt_v1003 as _target

sys.modules[__name__] = _target
