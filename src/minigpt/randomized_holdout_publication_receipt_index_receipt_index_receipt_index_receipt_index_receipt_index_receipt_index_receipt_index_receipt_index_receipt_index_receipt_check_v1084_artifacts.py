"""Forwarding shim (v1296): renamed to minigpt.receipt_chain_check_v1084_artifacts."""
import sys

from minigpt import receipt_chain_check_v1084_artifacts as _target

sys.modules[__name__] = _target
