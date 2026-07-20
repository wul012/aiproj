"""Forwarding shim (v1294): moved to minigpt.packet_index_review_v1014.

The historic long name stays importable; the module object IS the
target, so identity-sensitive consumers see no difference.
"""
import sys

import minigpt.packet_index_review_v1014 as _target

sys.modules[__name__] = _target
