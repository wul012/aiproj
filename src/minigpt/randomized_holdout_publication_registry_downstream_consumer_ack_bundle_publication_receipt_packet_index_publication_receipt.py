"""Forwarding shim (v1299): renamed to minigpt.ack_bundle_receipt."""
import sys

from minigpt import ack_bundle_receipt as _target

sys.modules[__name__] = _target
