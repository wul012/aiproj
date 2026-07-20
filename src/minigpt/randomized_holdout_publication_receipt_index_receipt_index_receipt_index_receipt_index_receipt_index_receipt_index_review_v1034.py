"""Forwarding shim (v1299): renamed to minigpt.receipt_chain_review_v1034."""
import sys

from minigpt import receipt_chain_review_v1034 as _target

sys.modules[__name__] = _target
