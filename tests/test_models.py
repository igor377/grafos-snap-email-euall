import networkx as nx
import numpy as np

from src.clustering import clustering_stats
from src.models import barabasi_albert, watts_strogatz
from src.treatment import build_adjacency


def test_barabasi_albert_structure():
    n, m = 3000, 2
    edges = barabasi_albert(n, m, seed=1)
    g = nx.Graph(edges)
    assert g.number_of_nodes() == n
    assert len(edges) == len(set(map(frozenset, edges))) == m * (m + 1) // 2 + (n - m - 1) * m
    assert nx.is_connected(g)
    deg = np.array([d for _, d in g.degree()])
    assert deg.min() >= m
    assert deg.max() > 20 * deg.mean() / 3  # hubs: grau máximo muito acima da média


def test_watts_strogatz_structure():
    n, k = 2000, 4
    lattice = watts_strogatz(n, k, 0.0, seed=1)
    assert len(lattice) == n * k // 2
    c0 = clustering_stats(build_adjacency(n, lattice))["clusterizacao_media"]
    assert abs(c0 - 0.5) < 1e-12  # anel com k=4: C = 3(k-2)/(4(k-1)) = 0,5
    rewired = watts_strogatz(n, k, 0.1, seed=1)
    assert len(rewired) == n * k // 2  # religar não muda o número de arestas
    assert all(u != v for u, v in rewired)
    c1 = clustering_stats(build_adjacency(n, rewired))["clusterizacao_media"]
    assert 0.25 < c1 < 0.5  # cai, mas continua alto com p = 0,1
