"""Forwarding shim (v1308): implementation moved to minigpt.core.model."""
import sys

from minigpt.core import model as _target

sys.modules[__name__] = _target
