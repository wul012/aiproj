from __future__ import annotations

import itertools
import math


def _rank(xs: list[float]) -> list[float]:
    order = sorted(range(len(xs)), key=lambda i: xs[i])
    ranks = [0.0] * len(xs)
    i = 0
    while i < len(xs):
        j = i
        while j + 1 < len(xs) and xs[order[j + 1]] == xs[order[i]]:
            j += 1
        avg = (i + j) / 2.0 + 1.0
        for k in range(i, j + 1):
            ranks[order[k]] = avg
        i = j + 1
    return ranks


def _pearson(xs: list[float], ys: list[float]) -> float:
    n = len(xs)
    mx, my = sum(xs) / n, sum(ys) / n
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    sxx = sum((x - mx) ** 2 for x in xs)
    syy = sum((y - my) ** 2 for y in ys)
    if sxx == 0 or syy == 0:
        return 0.0
    return sxy / math.sqrt(sxx * syy)


def spearman(xs: list[float], ys: list[float]) -> float:
    return _pearson(_rank(xs), _rank(ys))


def spearman_perm_p(xs: list[float], ys: list[float]) -> float:
    """Exact two-sided permutation p-value for |Spearman| (N is tiny -> enumerate)."""
    obs = abs(spearman(xs, ys))
    n = len(xs)
    if n > 8:  # 8! = 40320, safe cap
        return float("nan")
    rx = _rank(xs)
    cnt = tot = 0
    for perm in itertools.permutations(range(n)):
        tot += 1
        ry = [_rank(ys)[i] for i in perm]
        if abs(_pearson(rx, ry)) >= obs - 1e-12:
            cnt += 1
    return cnt / tot


def _ols2(y: list[float], x1: list[float], x2: list[float]) -> tuple[float, float, float]:
    """Standardized 2-variable OLS y ~ x1 + x2; returns (beta1*, beta2*, R^2)."""

    def z(v: list[float]) -> list[float]:
        m = sum(v) / len(v)
        sd = math.sqrt(sum((t - m) ** 2 for t in v) / len(v)) or 1.0
        return [(t - m) / sd for t in v]

    y_std, x1_std, x2_std = z(y), z(x1), z(x2)
    r12 = _pearson(x1_std, x2_std)
    r_y1 = _pearson(y_std, x1_std)
    r_y2 = _pearson(y_std, x2_std)
    denom = 1 - r12**2
    if abs(denom) < 1e-9:
        return float("nan"), float("nan"), float("nan")
    b1 = (r_y1 - r_y2 * r12) / denom
    b2 = (r_y2 - r_y1 * r12) / denom
    r2 = b1 * r_y1 + b2 * r_y2
    return b1, b2, r2


def _isotonic_decreasing(xs: list[float], ys: list[float]) -> list[tuple[float, float]]:
    """PAVA fit of y non-increasing in x; returns sorted (x, y_fit) for interpolation."""
    pts = sorted(zip(xs, ys))
    xv = [x for x, _ in pts]
    yv = [y for _, y in pts]
    weights = [1.0] * len(yv)
    merged: list[list[float]] = []
    for val, wt in zip(yv, weights):
        merged.append([val, wt])
        while len(merged) > 1 and merged[-2][0] < merged[-1][0]:
            v2, w2 = merged.pop()
            v1, w1 = merged.pop()
            merged.append([(v1 * w1 + v2 * w2) / (w1 + w2), w1 + w2])
    fit = []
    for val, wt in merged:
        for _ in range(int(round(wt))):
            fit.append(val)
    return list(zip(xv, fit))


def _interp(curve: list[tuple[float, float]], x: float) -> float:
    """Linear interpolation on a sorted (x,y) curve; clamps to the endpoints."""
    if x <= curve[0][0]:
        return curve[0][1]
    if x >= curve[-1][0]:
        return curve[-1][1]
    for (x0, y0), (x1, y1) in zip(curve, curve[1:]):
        if x0 <= x <= x1:
            t = 0.0 if x1 == x0 else (x - x0) / (x1 - x0)
            return y0 + t * (y1 - y0)
    return curve[-1][1]


__all__ = [
    "_interp",
    "_isotonic_decreasing",
    "_ols2",
    "spearman",
    "spearman_perm_p",
]
