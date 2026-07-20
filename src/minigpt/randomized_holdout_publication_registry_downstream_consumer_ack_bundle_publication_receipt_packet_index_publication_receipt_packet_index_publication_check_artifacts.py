"""Forwarding shim (v1298): renamed to minigpt.registry_ack_pub_check_artifacts."""
import sys

from minigpt import registry_ack_pub_check_artifacts as _target

sys.modules[__name__] = _target
