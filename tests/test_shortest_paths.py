import networkx as nx
import pytest

from src.algorithms.bellman_ford import bellman_ford
from src.algorithms.dijkstra import dijkstra
from src.algorithms.weighted import build_weighted_adjacency
from tests.helpers import random_weighted


@pytest.mark.parametrize("seed", range(5))
def test_dijkstra_matches_networkx(seed):
    g, n, edges, weights = random_weighted(seed=seed)
    dist, parent = dijkstra(build_weighted_adjacency(n, edges, weights), 0)
    expected = nx.single_source_dijkstra_path_length(g, 0)
    assert all(dist[v] == d for v, d in expected.items())
    for v in range(1, n):  # árvore de caminhos mínimos consistente
        assert dist[v] == dist[parent[v]] + g[parent[v]][v]["weight"]


@pytest.mark.parametrize("seed", range(5))
def test_bellman_ford_matches_networkx(seed):
    g, n, edges, weights = random_weighted(seed=seed)
    dist, _, rounds = bellman_ford(n, edges, weights, 0)
    expected = nx.single_source_bellman_ford_path_length(g, 0)
    assert all(dist[v] == d for v, d in expected.items())
    assert rounds <= n - 1


def test_bellman_ford_negative_weights_directed():
    edges = [(0, 1), (1, 2), (0, 2)]
    dist, _, _ = bellman_ford(3, edges, [4, -2, 3], 0, directed=True)
    assert dist == [0, 4, 2]


def test_bellman_ford_detects_negative_cycle():
    with pytest.raises(ValueError):
        bellman_ford(3, [(0, 1), (1, 2), (2, 0)], [1, -3, 1], 0, directed=True)
