"""Forwarding shim (v1299): renamed to minigpt.packet_chain_check_v1000."""
import sys

from minigpt import packet_chain_check_v1000 as _target

sys.modules[__name__] = _target
