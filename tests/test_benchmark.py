import math

import pytest
from scipy import stats

from src.benchmark import confidence_interval


def test_large_sample_uses_normal():
    samples = [1.0 + (i % 5) * 0.1 for i in range(30)]
    ci = confidence_interval(samples)
    assert ci["distribuicao"] == "Normal (Z)"
    assert ci["valor_critico"] == 1.96
    half = 1.96 * ci["desvio_s"] / math.sqrt(30)
    assert ci["ic95_sup_s"] - ci["media_s"] == pytest.approx(half)


def test_small_sample_uses_t_student():
    samples = [2.0, 2.2, 1.9, 2.1, 2.05, 1.95, 2.15, 2.0, 1.98, 2.02]
    ci = confidence_interval(samples)
    assert ci["distribuicao"] == "t-Student"
    assert ci["valor_critico"] == pytest.approx(stats.t.ppf(0.975, 9))
    lo, hi = stats.t.interval(0.95, 9, loc=ci["media_s"], scale=stats.sem(samples))
    assert (ci["ic95_inf_s"], ci["ic95_sup_s"]) == pytest.approx((lo, hi))
