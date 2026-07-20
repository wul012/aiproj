"""Forwarding shim (v1299): renamed to minigpt.ack_bundle_review."""
import sys

from minigpt import ack_bundle_review as _target

sys.modules[__name__] = _target
