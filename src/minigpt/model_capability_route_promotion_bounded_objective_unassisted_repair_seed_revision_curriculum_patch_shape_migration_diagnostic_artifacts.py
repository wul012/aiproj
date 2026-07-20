"""Forwarding shim (v1299): renamed to minigpt.curriculum_patch_shape_diag_artifacts."""
import sys

from minigpt import curriculum_patch_shape_diag_artifacts as _target

sys.modules[__name__] = _target
