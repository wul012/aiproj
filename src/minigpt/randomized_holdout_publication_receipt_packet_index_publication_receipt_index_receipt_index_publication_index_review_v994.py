"""Forwarding shim (v1299): renamed to minigpt.packet_chain_review_v994."""
import sys

from minigpt import packet_chain_review_v994 as _target

sys.modules[__name__] = _target
