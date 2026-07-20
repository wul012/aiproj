"""Forwarding shim (v1297): renamed to minigpt.receipt_chain_v1079_artifacts."""
import sys

from minigpt import receipt_chain_v1079_artifacts as _target

sys.modules[__name__] = _target
