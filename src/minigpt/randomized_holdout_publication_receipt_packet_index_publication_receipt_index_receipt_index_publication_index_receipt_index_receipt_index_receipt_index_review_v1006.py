"""Forwarding shim (v1298): renamed to minigpt.packet_chain_review_v1006."""
import sys

from minigpt import packet_chain_review_v1006 as _target

sys.modules[__name__] = _target
