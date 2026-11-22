import random

import networkx as nx
import numpy as np
import pytest

from src.distances import (
    bfs_distance_sum,
    bfs_distances,
    bounding_diameters,
    exact_average_path_length,
    sampled_paths,
    to_csr,
)
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


@pytest.mark.parametrize("seed", range(4))
def test_exact_average_path_length_with_leaves(seed):
    # árvore aleatória + algumas arestas extras: muitas folhas, alguns ciclos
    g = nx.random_labeled_tree(300, seed=seed)
    rng = random.Random(seed)
    for _ in range(40):
        u, v = rng.randrange(300), rng.randrange(300)
        if u != v:
            g.add_edge(u, v)
    _, adj = (g, build_adjacency(300, g.edges()))
    r = exact_average_path_length(adj)
    assert r["L_exato"] == pytest.approx(nx.average_shortest_path_length(g))
    assert r["folhas_deduzidas"] == sum(1 for _, d in g.degree() if d == 1)


def test_bfs_distance_sum_matches_bfs():
    g, adj = connected_random_graph(200, 0.03, seed=11)
    indptr, indices = to_csr(adj)
    dist = np.full(len(adj), -1, dtype=np.int64)
    for s in (0, 5, 17):
        total, reached, ecc = bfs_distance_sum(indptr, indices, s, dist)
        d = bfs_distances(adj, s)
        assert (total, reached, ecc) == (sum(d), len(adj), max(d))
        assert (dist == -1).all()  # vetor de trabalho restaurado


def test_sampled_paths_full_sample_is_exact():
    g, adj = connected_random_graph(120, 0.05, seed=7)
    n = g.number_of_nodes()
    r = sampled_paths(adj, k=n, seed=random.randint(0, 99))
    assert r["L_medio"] == pytest.approx(nx.average_shortest_path_length(g))
