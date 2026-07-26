"""Forwarding shim (v1308): implementation moved to minigpt.core.dataset."""
import sys

from minigpt.core import dataset as _target

sys.modules[__name__] = _target
