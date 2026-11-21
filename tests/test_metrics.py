import random

import networkx as nx
import pytest

from src.metrics import basic_metrics, density
from src.treatment import to_undirected_simple


def random_graph(n=200, m=400, seed=1):
    rng = random.Random(seed)
    return to_undirected_simple([(rng.randrange(n), rng.randrange(n)) for _ in range(m)])


def test_basic_metrics_match_networkx():
    n = 200
    edges = random_graph(n)
    g = nx.Graph()
    g.add_nodes_from(range(n))
    g.add_edges_from(edges)
    m = basic_metrics(n, edges)
    deg = [d for _, d in g.degree()]

    assert m["vertices"] == g.number_of_nodes()
    assert m["arestas"] == g.number_of_edges()
    assert m["grau_min"] == min(deg)
    assert m["grau_max"] == max(deg)
    assert m["grau_medio"] == pytest.approx(sum(deg) / n)
    assert m["densidade"] == pytest.approx(nx.density(g))
    assert m["componentes"] == nx.number_connected_components(g)
    assert m["maior_componente"] == len(max(nx.connected_components(g), key=len))


def test_density_complete_graph():
    assert density(5, 10) == 1.0
