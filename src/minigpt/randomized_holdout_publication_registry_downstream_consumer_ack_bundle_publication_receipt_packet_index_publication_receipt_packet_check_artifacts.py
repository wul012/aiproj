"""Forwarding shim (v1299): renamed to minigpt.ack_bundle_packet_check_artifacts."""
import sys

from minigpt import ack_bundle_packet_check_artifacts as _target

sys.modules[__name__] = _target
