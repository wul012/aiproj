"""Forwarding shim (v1299): renamed to minigpt.ack_bundle_index."""
import sys

from minigpt import ack_bundle_index as _target

sys.modules[__name__] = _target
