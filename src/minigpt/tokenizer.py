"""Forwarding shim (v1308): implementation moved to minigpt.core.tokenizer."""
import sys

from minigpt.core import tokenizer as _target

sys.modules[__name__] = _target
