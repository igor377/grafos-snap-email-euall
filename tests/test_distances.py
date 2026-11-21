import random

import networkx as nx
import pytest

from src.distances import bfs_distances, bounding_diameters, sampled_paths
from src.treatment import build_adjacency


def connected_random_graph(n, p, seed):
    g = nx.gnp_random_graph(n, p, seed=seed)
    g = g.subgraph(max(nx.connected_components(g), key=len)).copy()
    g = nx.convert_node_labels_to_integers(g)
    return g, build_adjacency(g.number_of_nodes(), g.edges())


def test_bfs_distances_match_networkx():
    g, adj = connected_random_graph(150, 0.03, seed=3)
    expected = nx.single_source_shortest_path_length(g, 0)
    dist = bfs_distances(adj, 0)
    assert all(dist[v] == d for v, d in expected.items())


@pytest.mark.parametrize("seed", [1, 2, 3, 4, 5])
def test_bounding_diameters_exact(seed):
    g, adj = connected_random_graph(200, 0.015, seed=seed)
    r = bounding_diameters(adj)
    assert r["exato"]
    assert r["diametro_lo"] == nx.diameter(g)
    assert r["raio_lo"] == nx.radius(g)


def test_bounding_diameters_path_graph():
    g = nx.path_graph(11)
    r = bounding_diameters(build_adjacency(11, g.edges()))
    assert (r["diametro_lo"], r["raio_lo"]) == (10, 5)


def test_sampled_paths_full_sample_is_exact():
    g, adj = connected_random_graph(120, 0.05, seed=7)
    n = g.number_of_nodes()
    r = sampled_paths(adj, k=n, seed=random.randint(0, 99))
    assert r["L_medio"] == pytest.approx(nx.average_shortest_path_length(g))
