"""Forwarding shim (v1299): renamed to minigpt.registry_ack_pub."""
import sys

from minigpt import registry_ack_pub as _target

sys.modules[__name__] = _target
