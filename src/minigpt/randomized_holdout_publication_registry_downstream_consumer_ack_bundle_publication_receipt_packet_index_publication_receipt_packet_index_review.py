"""Forwarding shim (v1299): renamed to minigpt.registry_ack_review."""
import sys

from minigpt import registry_ack_review as _target

sys.modules[__name__] = _target
