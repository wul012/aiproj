"""Forwarding shim (v1299): renamed to minigpt.receipt_chain_check_v1040."""
import sys

from minigpt import receipt_chain_check_v1040 as _target

sys.modules[__name__] = _target
