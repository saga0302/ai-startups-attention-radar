"""Rolling-baseline z-score for daily pageview series.

Definition (from the problem statement):
  * Baseline = trailing 30-day mean and standard deviation computed from
    observations strictly BEFORE the evaluation date. The current value is
    never part of its own baseline.
  * Minimum history: at least 14 non-null observations in the window, otherwise
    the z-score is null (no flag).
  * Optional transform: log1p before computing statistics, for skewed counts.
    Default is log1p, documented in docs/decisions.md.
  * Zero-variance windows produce a null z-score rather than an infinite one.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Sequence

DEFAULT_WINDOW_DAYS = 30
DEFAULT_MIN_OBSERVATIONS = 14
DEFAULT_THRESHOLD = 3.0


@dataclass(frozen=True)
class ZScoreResult:
    z: float | None
    baseline_mean: float | None
    baseline_std: float | None
    n_observations: int
    is_anomaly: bool


def _transform(value: float, use_log: bool) -> float:
    return math.log1p(value) if use_log else float(value)


def zscore_at(
    series: Sequence[float | None],
    index: int,
    window_days: int = DEFAULT_WINDOW_DAYS,
    min_observations: int = DEFAULT_MIN_OBSERVATIONS,
    threshold: float = DEFAULT_THRESHOLD,
    use_log: bool = True,
) -> ZScoreResult:
    """Z-score of series[index] against the trailing window that excludes index.

    series holds one value per day in chronological order; None means missing.
    """
    if index < 0 or index >= len(series):
        raise IndexError("index out of range")

    start = max(0, index - window_days)
    history = [
        _transform(v, use_log) for v in series[start:index] if v is not None
    ]
    n = len(history)

    current = series[index]
    if current is None or n < min_observations:
        return ZScoreResult(None, None, None, n, False)

    mean = sum(history) / n
    variance = sum((x - mean) ** 2 for x in history) / (n - 1) if n > 1 else 0.0
    std = math.sqrt(variance)

    if std == 0.0:
        return ZScoreResult(None, mean, 0.0, n, False)

    z = (_transform(current, use_log) - mean) / std
    return ZScoreResult(z, mean, std, n, abs(z) > threshold)


def zscore_series(
    series: Sequence[float | None],
    window_days: int = DEFAULT_WINDOW_DAYS,
    min_observations: int = DEFAULT_MIN_OBSERVATIONS,
    threshold: float = DEFAULT_THRESHOLD,
    use_log: bool = True,
) -> list[ZScoreResult]:
    """Apply zscore_at to every position in a daily series."""
    return [
        zscore_at(series, i, window_days, min_observations, threshold, use_log)
        for i in range(len(series))
    ]
