"""Forwarding shim (v1297): renamed to minigpt.receipt_chain_review_v1090."""
import sys

from minigpt import receipt_chain_review_v1090 as _target

sys.modules[__name__] = _target
