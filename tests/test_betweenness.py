import networkx as nx
import numpy as np
import pytest
from scipy.stats import spearmanr

from src.algorithms.betweenness import betweenness
from tests.helpers import nx_and_adj, random_connected


@pytest.mark.parametrize("seed", range(3))
def test_exact_matches_networkx(seed):
    g, adj = random_connected(n=200, p=0.025, seed=seed)
    ours = betweenness(adj)  # k = None -> exato
    expected = nx.betweenness_centrality(g, normalized=False)
    assert np.allclose(ours, [expected[v] for v in range(g.number_of_nodes())])


def test_path_and_star():
    _, adj = nx_and_adj(nx.path_graph(5))
    assert betweenness(adj) == pytest.approx([0, 3, 4, 3, 0])
    _, adj = nx_and_adj(nx.star_graph(4))  # centro 0 intermedia todos os C(4,2)=6 pares
    assert betweenness(adj) == pytest.approx([6, 0, 0, 0, 0])


def test_sampled_estimate_preserves_ranking():
    g, adj = nx_and_adj(nx.barabasi_albert_graph(1500, 2, seed=7))
    exact = betweenness(adj)
    approx = betweenness(adj, k=300, seed=1)
    rho = spearmanr(exact, approx).statistic
    assert rho > 0.9
    top_exact = set(np.argsort(exact)[::-1][:30])
    top_approx = set(np.argsort(approx)[::-1][:30])
    assert len(top_exact & top_approx) >= 24
