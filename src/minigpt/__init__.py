"""MiniGPT learning project."""

from __future__ import annotations

from importlib import import_module
from typing import Any

from ._root_exports import ROOT_FACADE_ALL_EXPORTS, ROOT_FACADE_LAZY_EXPORTS

__all__ = list(ROOT_FACADE_ALL_EXPORTS)
_EXPORTS = ROOT_FACADE_LAZY_EXPORTS


def __getattr__(name: str) -> Any:
    if name not in _EXPORTS:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    module_name, attr_name = _EXPORTS[name]
    value = getattr(import_module(f"{__name__}.{module_name}"), attr_name)
    globals()[name] = value
    return value