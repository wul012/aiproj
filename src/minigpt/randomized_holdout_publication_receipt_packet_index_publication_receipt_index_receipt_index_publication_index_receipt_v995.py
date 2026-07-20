"""Forwarding shim (v1299): renamed to minigpt.packet_chain_receipt_v995."""
import sys

from minigpt import packet_chain_receipt_v995 as _target

sys.modules[__name__] = _target
