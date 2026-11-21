import math

from src.smallworld import erdos_renyi_gnm


def test_gnm_has_exact_edge_count_and_no_loops():
    edges = erdos_renyi_gnm(500, 1200, seed=1)
    assert len(edges) == 1200
    assert len(set(edges)) == 1200
    assert all(u < v for u, v in edges)


def test_gnm_is_reproducible():
    assert erdos_renyi_gnm(100, 200, seed=7) == erdos_renyi_gnm(100, 200, seed=7)


def test_gnm_degree_is_close_to_expected():
    n, m = 2000, 6000
    deg = [0] * n
    for u, v in erdos_renyi_gnm(n, m, seed=3):
        deg[u] += 1
        deg[v] += 1
    mean = sum(deg) / n
    var = sum((d - mean) ** 2 for d in deg) / n
    assert mean == 2 * m / n
    assert math.isclose(var, mean, rel_tol=0.15)  # ~Poisson: variância ≈ média
