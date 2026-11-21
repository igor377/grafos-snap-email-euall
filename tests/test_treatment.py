import random

import networkx as nx

from src.treatment import (
    build_adjacency,
    connected_components,
    induced_relabel,
    remove_self_loops,
    to_undirected_simple,
)


def test_remove_self_loops():
    assert remove_self_loops([(0, 0), (0, 1), (2, 2), (1, 2)]) == [(0, 1), (1, 2)]


def test_undirected_simple_merges_reciprocal_edges():
    edges = [(0, 1), (1, 0), (2, 1), (3, 3)]
    assert to_undirected_simple(edges) == [(0, 1), (1, 2)]


def test_components_match_networkx():
    rng = random.Random(42)
    n = 300
    edges = to_undirected_simple([(rng.randrange(n), rng.randrange(n)) for _ in range(250)])
    comps = connected_components(build_adjacency(n, edges))

    g = nx.Graph()
    g.add_nodes_from(range(n))
    g.add_edges_from(edges)
    expected = sorted((sorted(c) for c in nx.connected_components(g)), key=len, reverse=True)

    assert sorted(map(sorted, comps)) == sorted(expected)
    assert len(comps[0]) == len(expected[0])
    assert sum(map(len, comps)) == n


def test_induced_relabel():
    mapping, edges = induced_relabel([5, 2, 9], [(2, 5), (5, 9), (9, 1)])
    assert mapping == [2, 5, 9]
    assert edges == [(0, 1), (1, 2)]
