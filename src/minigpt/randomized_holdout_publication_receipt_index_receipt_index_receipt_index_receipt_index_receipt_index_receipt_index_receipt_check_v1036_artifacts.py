"""Forwarding shim (v1299): renamed to minigpt.receipt_chain_check_v1036_artifacts."""
import sys

from minigpt import receipt_chain_check_v1036_artifacts as _target

sys.modules[__name__] = _target
