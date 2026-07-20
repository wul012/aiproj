"""Forwarding shim (v1298): renamed to minigpt.registry_ack_packet_review."""
import sys

from minigpt import registry_ack_packet_review as _target

sys.modules[__name__] = _target
