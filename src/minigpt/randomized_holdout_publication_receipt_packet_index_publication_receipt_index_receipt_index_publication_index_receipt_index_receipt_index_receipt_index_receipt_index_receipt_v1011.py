"""Forwarding shim (v1298): renamed to minigpt.packet_chain_receipt_v1011."""
import sys

from minigpt import packet_chain_receipt_v1011 as _target

sys.modules[__name__] = _target
