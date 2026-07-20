"""Forwarding shim (v1298): renamed to minigpt.packet_chain_review_v1002_artifacts."""
import sys

from minigpt import packet_chain_review_v1002_artifacts as _target

sys.modules[__name__] = _target
