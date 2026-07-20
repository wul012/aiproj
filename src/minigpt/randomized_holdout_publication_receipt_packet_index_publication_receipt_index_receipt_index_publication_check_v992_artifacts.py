"""Forwarding shim (v1299): renamed to minigpt.packet_chain_check_v992_artifacts."""
import sys

from minigpt import packet_chain_check_v992_artifacts as _target

sys.modules[__name__] = _target
