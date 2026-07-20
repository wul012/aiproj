"""v1290 grok-arc common helpers: identity guards + behavior checks.

The extraction is only safe while every arc module's private name still IS
the shared function — these guards make any silent re-fork or drift a test
failure. Pytest-style but pytest-import-free (the CI unit-test runner is
plain unittest without pytest installed).
"""
from __future__ import annotations

import math
import statistics

from minigpt.grok_arc_common import agg_pyplot, median, median_or_nan, save_figure

PLAIN_MEDIAN_MODULES = (
    "grok_init_rescue_v1280",
    "grok_norm_vs_step_v1281",
    "grok_width_lr_v1282",
    "grok_circuit_timing_v1284",
    "grok_deep_plateau_v1285",
    "grok_lr_compression_v1286",
    "grok_purification_v1287",
    "grok_spike_anatomy_v1288",
    "grok_spike_microscopy_v1289",
)
GUARDED_MEDIAN_MODULES = ("capacity_squeeze_v1277", "grok_speed_v1279")


def _import(name):
    module = __import__(f"minigpt.{name}", fromlist=["_median"])
    return module


def test_median_identity_across_arc_modules():
    for name in PLAIN_MEDIAN_MODULES:
        assert _import(name)._median is median, name
    for name in GUARDED_MEDIAN_MODULES:
        assert _import(name)._median is median_or_nan, name


def test_median_matches_statistics_median():
    cases = [[3.0], [2.0, 4.0], [5.0, 1.0, 3.0], [4.0, 1.0, 3.0, 2.0],
             [0.1, 0.9, 0.5, 0.7, 0.3]]
    for xs in cases:
        assert abs(median(xs) - statistics.median(xs)) < 1e-12, xs
        assert abs(median_or_nan(xs) - statistics.median(xs)) < 1e-12, xs
    assert math.isnan(median_or_nan([]))
    assert isinstance(median_or_nan([1]), float)


def test_agg_pyplot_and_save_figure(tmp_path):
    plt = agg_pyplot()
    assert plt.get_backend().lower() == "agg"
    fig, ax = plt.subplots(figsize=(2, 2))
    ax.plot([0, 1], [0, 1])
    out = tmp_path / "nested" / "fig.png"
    save_figure(fig, out)
    assert out.exists() and out.stat().st_size > 0
