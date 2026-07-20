"""Forwarding shim (v1299): renamed to minigpt.curriculum_patch_shape_diag."""
import sys

from minigpt import curriculum_patch_shape_diag as _target

sys.modules[__name__] = _target
