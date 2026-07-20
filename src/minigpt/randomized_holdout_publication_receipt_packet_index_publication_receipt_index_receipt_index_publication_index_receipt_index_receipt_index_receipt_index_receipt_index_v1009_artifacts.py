"""Forwarding shim (v1298): renamed to minigpt.packet_chain_index_v1009_artifacts."""
import sys

from minigpt import packet_chain_index_v1009_artifacts as _target

sys.modules[__name__] = _target
