"""Forwarding shim (v1299): renamed to minigpt.curriculum_patch_train_run_artifacts."""
import sys

from minigpt import curriculum_patch_train_run_artifacts as _target

sys.modules[__name__] = _target
