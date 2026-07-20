"""Forwarding shim (v1298): renamed to minigpt.packet_chain_check_v1008."""
import sys

from minigpt import packet_chain_check_v1008 as _target

sys.modules[__name__] = _target
