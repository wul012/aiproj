"""Forwarding shim (v1299): renamed to minigpt.surface_partial_hit_diag_artifacts."""
import sys

from minigpt import surface_partial_hit_diag_artifacts as _target

sys.modules[__name__] = _target
