"""Forwarding shim (v1294): moved to minigpt.packet_index_check_v1012_artifacts.

The historic long name stays importable; the module object IS the
target, so identity-sensitive consumers see no difference.
"""
import sys

import minigpt.packet_index_check_v1012_artifacts as _target

sys.modules[__name__] = _target
