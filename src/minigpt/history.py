"""Forwarding shim (v1308): implementation moved to minigpt.core.history."""
import sys

from minigpt.core import history as _target

sys.modules[__name__] = _target
