import numpy as np
import pytest

from src.powerlaw import ccdf, fit_line, fit_mle, mle_gamma


def zeta_sample(gamma, size, seed):
    rng = np.random.default_rng(seed)
    return rng.zipf(gamma, size)


def test_ccdf_starts_at_one_and_decreases():
    ks, tail = ccdf(np.array([1, 1, 2, 3, 3, 3]))
    assert list(ks) == [1, 2, 3]
    assert tail[0] == 1.0 and np.all(np.diff(tail) < 0)
    assert tail[-1] == pytest.approx(0.5)


@pytest.mark.parametrize("gamma", [1.8, 2.2, 2.5, 3.0])
def test_mle_recovers_exponent(gamma):
    deg = zeta_sample(gamma, 200_000, seed=1)

    def tol(kmin):  # 3 erros padrão da MLE: 3 (γ − 1) / √n_cauda
        return 3 * (gamma - 1) / np.sqrt(np.sum(deg >= kmin))

    assert mle_gamma(deg, kmin=1) == pytest.approx(gamma, abs=tol(1))
    assert mle_gamma(deg, kmin=5) == pytest.approx(gamma, abs=tol(5))
    fit = fit_mle(deg)
    assert fit["gamma"] == pytest.approx(gamma, abs=tol(fit["kmin"]))


def test_fit_line_exact_power():
    x = np.array([1, 10, 100, 1000])
    slope, _, r2 = fit_line(x, 3 * x ** -2.0)
    assert slope == pytest.approx(-2.0) and r2 == pytest.approx(1.0)
