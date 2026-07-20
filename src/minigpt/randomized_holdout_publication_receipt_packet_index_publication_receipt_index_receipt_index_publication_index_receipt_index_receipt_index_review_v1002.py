"""Forwarding shim (v1299): renamed to minigpt.packet_chain_review_v1002."""
import sys

from minigpt import packet_chain_review_v1002 as _target

sys.modules[__name__] = _target
