"""v1290: shared micro-helpers for the grokking-arc experiment modules.

Contract-preserving extraction in the v1187 `report_check_common` precedent:
each function here is the byte-identical private helper that was previously
copy-pasted across the arc modules (`_median` nine times, the guarded float
median twice, the Agg figure scaffolding twelve times). The experiment
modules re-import them under their old private names, so every published
cache, report, and figure re-derives unchanged — decide() bodies are not
touched. Identity guards live in tests/test_grok_arc_common_v1290.py, and
the v1290 close re-derived the committed v1277-v1289 artifacts byte-for-byte
through these helpers.
"""
from __future__ import annotations

from pathlib import Path


def median(values: list[float]) -> float:
    """The arc's plain median (the v1280-v1289 copy): no empty-input guard,
    result type follows the inputs."""
    ordered = sorted(values)
    n = len(ordered)
    mid = n // 2
    return ordered[mid] if n % 2 else (ordered[mid - 1] + ordered[mid]) / 2


def median_or_nan(values: list[float]) -> float:
    """The guarded float median (the v1277/v1279 copy): empty input -> NaN,
    result always a float."""
    ordered = sorted(values)
    n = len(ordered)
    if n == 0:
        return float("nan")
    mid = n // 2
    return float(ordered[mid]) if n % 2 \
        else float((ordered[mid - 1] + ordered[mid]) / 2)


def agg_pyplot():
    """Headless pyplot: the lazy Agg-backend import block every arc
    plot_result carried. Lazy so importing an experiment module never pays
    for matplotlib."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    return plt


def save_figure(fig, path, dpi: int = 160) -> None:
    """The uniform figure tail: ensure the parent directory, save at the
    arc's dpi, close the figure."""
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=dpi)
    import matplotlib.pyplot as plt
    plt.close(fig)
