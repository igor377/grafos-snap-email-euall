import networkx as nx
import pytest

from src.algorithms.bfs import bfs
from src.algorithms.dfs import dfs
from tests.helpers import nx_and_adj, random_connected


@pytest.mark.parametrize("seed", range(5))
def test_bfs_matches_networkx(seed):
    g, adj = random_connected(seed=seed)
    order, dist, parent = bfs(adj, 0)
    assert order == [0] + [v for _, v in nx.bfs_edges(g, 0)]
    expected = nx.single_source_shortest_path_length(g, 0)
    assert all(dist[v] == d for v, d in expected.items())
    for v in order[1:]:
        assert dist[v] == dist[parent[v]] + 1


@pytest.mark.parametrize("seed", range(5))
def test_dfs_matches_networkx(seed):
    g, adj = random_connected(seed=seed)
    order, parent = dfs(adj, 0)
    assert order == list(nx.dfs_preorder_nodes(g, 0))
    assert {(parent[v], v) for v in order[1:]} == set(nx.dfs_edges(g, 0))


def test_unreachable_vertices():
    g = nx.Graph([(0, 1), (2, 3)])
    _, adj = nx_and_adj(g)
    order, dist, _ = bfs(adj, 0)
    assert sorted(order) == [0, 1] and dist[2] == -1
    assert sorted(dfs(adj, 0)[0]) == [0, 1]


def test_dfs_deep_path_no_recursion_error():
    n = 50_000
    g = nx.path_graph(n)
    _, adj = nx_and_adj(g)
    order, _ = dfs(adj, 0)
    assert order == list(range(n))
