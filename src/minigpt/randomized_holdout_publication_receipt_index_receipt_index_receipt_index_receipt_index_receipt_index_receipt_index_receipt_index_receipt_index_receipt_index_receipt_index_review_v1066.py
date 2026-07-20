"""Forwarding shim (v1297): renamed to minigpt.receipt_chain_review_v1066."""
import sys

from minigpt import receipt_chain_review_v1066 as _target

sys.modules[__name__] = _target
