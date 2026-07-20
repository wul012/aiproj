"""Forwarding shim (v1296): renamed to minigpt.receipt_chain_review_v1124_artifacts."""
import sys

from minigpt import receipt_chain_review_v1124_artifacts as _target

sys.modules[__name__] = _target
