"""Forwarding shim (v1299): renamed to minigpt.receipt_chain_v1035_artifacts."""
import sys

from minigpt import receipt_chain_v1035_artifacts as _target

sys.modules[__name__] = _target
