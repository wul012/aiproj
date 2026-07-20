"""Forwarding shim (v1297): renamed to minigpt.receipt_chain_v1095."""
import sys

from minigpt import receipt_chain_v1095 as _target

sys.modules[__name__] = _target
