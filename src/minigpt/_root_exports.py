"""Root package lazy export tables for the compatibility facade."""

from __future__ import annotations

from ._root_lazy_exports_core import ROOT_FACADE_CORE_LAZY_EXPORTS
from ._root_lazy_exports_randomized_holdout import ROOT_FACADE_RANDOMIZED_HOLDOUT_LAZY_EXPORTS
from ._root_lazy_exports_randomized_publication_receipt import (
    ROOT_FACADE_RANDOMIZED_PUBLICATION_RECEIPT_LAZY_EXPORTS,
)
from ._root_lazy_exports_randomized_publication_registry import (
    ROOT_FACADE_RANDOMIZED_PUBLICATION_REGISTRY_LAZY_EXPORTS,
)
from ._root_lazy_exports_route_promotion import ROOT_FACADE_ROUTE_PROMOTION_LAZY_EXPORTS
from ._root_public_exports import ROOT_FACADE_ALL_EXPORTS

ROOT_FACADE_LAZY_EXPORTS = {
    **ROOT_FACADE_CORE_LAZY_EXPORTS,
    **ROOT_FACADE_RANDOMIZED_HOLDOUT_LAZY_EXPORTS,
    **ROOT_FACADE_RANDOMIZED_PUBLICATION_REGISTRY_LAZY_EXPORTS,
    **ROOT_FACADE_RANDOMIZED_PUBLICATION_RECEIPT_LAZY_EXPORTS,
    **ROOT_FACADE_ROUTE_PROMOTION_LAZY_EXPORTS,
}

__all__ = ["ROOT_FACADE_ALL_EXPORTS", "ROOT_FACADE_LAZY_EXPORTS"]
