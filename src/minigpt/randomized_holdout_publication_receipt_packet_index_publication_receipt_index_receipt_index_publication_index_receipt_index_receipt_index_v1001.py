"""Forwarding shim (v1299): renamed to minigpt.packet_chain_index_v1001."""
import sys

from minigpt import packet_chain_index_v1001 as _target

sys.modules[__name__] = _target
