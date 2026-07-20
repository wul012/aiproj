"""Forwarding shim (v1297): renamed to minigpt.receipt_chain_v1043."""
import sys

from minigpt import receipt_chain_v1043 as _target

sys.modules[__name__] = _target
