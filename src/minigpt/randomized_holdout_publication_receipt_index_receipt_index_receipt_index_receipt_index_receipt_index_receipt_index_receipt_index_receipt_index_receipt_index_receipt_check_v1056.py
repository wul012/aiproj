"""Forwarding shim (v1297): renamed to minigpt.receipt_chain_check_v1056."""
import sys

from minigpt import receipt_chain_check_v1056 as _target

sys.modules[__name__] = _target
