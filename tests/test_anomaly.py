import math
import pytest
from pageviews_anomaly.anomaly import zscore_at


def test_current_value_is_excluded_from_its_own_baseline():
    # Flat history of 100s, then a spike. If the spike leaked into its own
    # baseline the std would grow and the z-score would shrink.
    series = [100.0] * 20 + [100_000.0]
    result = zscore_at(series, 20, use_log=False)
    assert result.baseline_mean == pytest.approx(100.0)
    assert result.baseline_std == 0.0
    # Zero variance -> null z, not inf
    assert result.z is None
    assert result.is_anomaly is False


def test_spike_flagged_against_noisy_baseline():
    base = [100.0 + ((-1) ** i) * 5 for i in range(30)]  # mean 100, std ~5.1
    series = base + [200.0]
    result = zscore_at(series, 30, use_log=False)
    assert result.n_observations == 30
    assert result.z is not None and result.z > 3
    assert result.is_anomaly is True


def test_minimum_history_enforced():
    series = [10.0, 12.0, 11.0, 13.0] * 2 + [500.0]  # only 8 prior values
    result = zscore_at(series, 8, use_log=False)
    assert result.z is None
    assert result.is_anomaly is False
    assert result.n_observations == 8


def test_missing_history_values_are_skipped_not_zero_filled():
    noisy = [100.0 + ((-1) ** i) * 5 for i in range(30)]
    series: list[float | None] = list(noisy)
    series[3] = None
    series[7] = None
    series.append(200.0)
    result = zscore_at(series, 30, use_log=False)
    assert result.n_observations == 28


def test_null_current_value_gives_null_result():
    series = [100.0 + ((-1) ** i) * 5 for i in range(30)] + [None]
    result = zscore_at(series, 30)
    assert result.z is None and result.is_anomaly is False


def test_window_limits_history_to_thirty_days():
    # 40 days at 1000, then 30 days at 10, then a 10 today.
    # The trailing 30-day window contains only the 10s, so the current 10
    # is unremarkable. Using the full history would flag it.
    noisy_low = [10.0 + ((-1) ** i) * 1 for i in range(30)]
    series = [1000.0] * 40 + noisy_low + [10.0]
    result = zscore_at(series, len(series) - 1, use_log=False)
    assert result.baseline_mean == pytest.approx(10.0, abs=0.5)
    assert result.is_anomaly is False


def test_log_transform_reduces_skew_effect():
    # Skewed counts: a big spike against a log baseline should still be finite.
    base = [1.0, 2.0, 1.0, 3.0, 2.0, 1.0, 2.0, 3.0, 1.0, 2.0, 2.0, 1.0, 3.0, 2.0]
    series = [float(x) for x in base] + [5000.0]
    result = zscore_at(series, len(series) - 1, use_log=True)
    assert result.z is not None and math.isfinite(result.z)
    assert result.is_anomaly is True



