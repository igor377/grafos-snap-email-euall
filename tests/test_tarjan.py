import networkx as nx
import pytest

from src.algorithms.tarjan import (
    bridges_and_articulation_points,
    directed_adjacency,
    tarjan_scc,
)
from tests.helpers import nx_and_adj, random_connected


def as_sets(components):
    return sorted(sorted(c) for c in components)


@pytest.mark.parametrize("seed", range(5))
def test_scc_matches_networkx(seed):
    g = nx.gnp_random_graph(300, 0.008, seed=seed, directed=True)
    n = g.number_of_nodes()
    sccs = tarjan_scc(directed_adjacency(n, g.edges()))
    assert as_sets(sccs) == as_sets(nx.strongly_connected_components(g))


def test_scc_deep_cycle_no_recursion_error():
    n = 50_000
    edges = [(i, (i + 1) % n) for i in range(n)]
    sccs = tarjan_scc(directed_adjacency(n, edges))
    assert len(sccs) == 1 and len(sccs[0]) == n


@pytest.mark.parametrize("seed", range(5))
def test_bridges_and_articulation_match_networkx(seed):
    g, adj = random_connected(n=250, p=0.012, seed=seed)
    bridges, arts = bridges_and_articulation_points(adj)
    assert sorted(bridges) == sorted(tuple(sorted(e)) for e in nx.bridges(g))
    assert sorted(arts) == sorted(nx.articulation_points(g))


def test_bridges_path_and_cycle():
    _, adj = nx_and_adj(nx.path_graph(5))
    bridges, arts = bridges_and_articulation_points(adj)
    assert len(bridges) == 4 and sorted(arts) == [1, 2, 3]
    _, adj = nx_and_adj(nx.cycle_graph(5))
    assert bridges_and_articulation_points(adj) == ([], [])
