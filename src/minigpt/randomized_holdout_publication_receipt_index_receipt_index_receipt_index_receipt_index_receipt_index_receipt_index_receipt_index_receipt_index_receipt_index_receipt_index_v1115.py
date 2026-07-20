"""Forwarding shim (v1297): renamed to minigpt.receipt_chain_v1115."""
import sys

from minigpt import receipt_chain_v1115 as _target

sys.modules[__name__] = _target
