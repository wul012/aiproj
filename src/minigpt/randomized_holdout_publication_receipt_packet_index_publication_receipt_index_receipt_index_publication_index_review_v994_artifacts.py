"""Forwarding shim (v1299): renamed to minigpt.packet_chain_review_v994_artifacts."""
import sys

from minigpt import packet_chain_review_v994_artifacts as _target

sys.modules[__name__] = _target
