import networkx as nx
import numpy as np
import pytest

from src.algorithms.floyd_warshall import (
    floyd_warshall,
    floyd_warshall_numpy,
    has_negative_cycle,
)
from tests.helpers import random_weighted


@pytest.mark.parametrize("seed", range(3))
def test_floyd_warshall_matches_networkx(seed):
    g, n, edges, weights = random_weighted(n=80, p=0.06, seed=seed)
    expected = nx.floyd_warshall_numpy(g, nodelist=range(n), weight="weight")
    assert np.array_equal(np.array(floyd_warshall(n, edges, weights)), expected)
    assert np.array_equal(floyd_warshall_numpy(n, edges, weights), expected)


def test_directed_and_negative_weights():
    edges = [(0, 1), (1, 2), (0, 2)]
    d = floyd_warshall(3, edges, [4, -2, 3], directed=True)
    assert d[0] == [0, 4, 2]
    assert d[2][0] == float("inf")
    assert not has_negative_cycle(d)


def test_negative_cycle_detected():
    d = floyd_warshall(3, [(0, 1), (1, 2), (2, 0)], [1, -3, 1], directed=True)
    assert has_negative_cycle(d)
