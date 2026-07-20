"""Forwarding shim (v1298): renamed to minigpt.registry_ack_packet_review_artifacts."""
import sys

from minigpt import registry_ack_packet_review_artifacts as _target

sys.modules[__name__] = _target
