"""Forwarding shim (v1308): implementation moved to minigpt.core.rope."""
import sys

from minigpt.core import rope as _target

sys.modules[__name__] = _target
