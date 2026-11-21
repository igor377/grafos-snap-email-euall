import networkx as nx
import pytest

from src.clustering import clustering_stats, triangles_per_node
from src.treatment import build_adjacency


def adj_of(g):
    g = nx.convert_node_labels_to_integers(g)
    return g, build_adjacency(g.number_of_nodes(), g.edges())


@pytest.mark.parametrize("seed", [1, 2, 3])
def test_triangles_match_networkx(seed):
    g, adj = adj_of(nx.powerlaw_cluster_graph(300, 3, 0.4, seed=seed))
    expected = nx.triangles(g)
    assert triangles_per_node(adj) == [expected[v] for v in range(g.number_of_nodes())]


@pytest.mark.parametrize("seed", [1, 2, 3])
def test_clustering_matches_networkx(seed):
    g, adj = adj_of(nx.powerlaw_cluster_graph(300, 3, 0.4, seed=seed))
    r = clustering_stats(adj)
    assert r["triangulos"] == sum(nx.triangles(g).values()) // 3
    assert r["clusterizacao_media"] == pytest.approx(nx.average_clustering(g))
    assert r["transitividade"] == pytest.approx(nx.transitivity(g))


def test_complete_graph():
    _, adj = adj_of(nx.complete_graph(5))
    r = clustering_stats(adj)
    assert r["triangulos"] == 10
    assert r["clusterizacao_media"] == 1.0
