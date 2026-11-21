import networkx as nx
import numpy as np
import pytest

from src.algorithms.pagerank import pagerank
from tests.helpers import random_connected


@pytest.mark.parametrize("seed", range(3))
def test_pagerank_matches_networkx_undirected(seed):
    g, _ = random_connected(n=300, p=0.02, seed=seed)
    pr, _ = pagerank(g.number_of_nodes(), list(g.edges()))
    expected = nx.pagerank(g, alpha=0.85, tol=1e-12)
    assert np.allclose(pr, [expected[v] for v in range(g.number_of_nodes())], atol=1e-8)
    assert pr.sum() == pytest.approx(1.0)


def test_pagerank_matches_networkx_directed_with_dangling():
    g = nx.gnp_random_graph(200, 0.03, seed=5, directed=True)
    for v in (3, 17, 42):  # força vértices "dangling" (sem arestas de saída)
        g.remove_edges_from(list(g.out_edges(v)))
    n = g.number_of_nodes()
    assert sum(g.out_degree(v) == 0 for v in g) >= 3
    pr, _ = pagerank(n, list(g.edges()), directed=True)
    expected = nx.pagerank(g, alpha=0.85, tol=1e-12)
    assert np.allclose(pr, [expected[v] for v in range(n)], atol=1e-8)


def test_star_center_has_highest_rank():
    pr, _ = pagerank(6, [(0, i) for i in range(1, 6)])
    assert pr.argmax() == 0
