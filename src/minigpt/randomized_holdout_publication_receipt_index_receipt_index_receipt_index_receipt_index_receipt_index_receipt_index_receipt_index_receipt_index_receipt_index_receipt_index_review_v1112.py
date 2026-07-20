"""Forwarding shim (v1297): renamed to minigpt.receipt_chain_review_v1112."""
import sys

from minigpt import receipt_chain_review_v1112 as _target

sys.modules[__name__] = _target
