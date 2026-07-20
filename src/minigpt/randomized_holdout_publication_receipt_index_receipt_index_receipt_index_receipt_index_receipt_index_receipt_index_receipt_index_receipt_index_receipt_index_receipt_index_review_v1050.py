"""Forwarding shim (v1297): renamed to minigpt.receipt_chain_review_v1050."""
import sys

from minigpt import receipt_chain_review_v1050 as _target

sys.modules[__name__] = _target
