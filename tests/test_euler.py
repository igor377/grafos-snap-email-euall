import networkx as nx
import pytest

from src.algorithms.euler import check_directed, check_undirected, hierholzer_undirected
from tests.helpers import nx_and_adj, random_connected


def kind_nx(g):
    if nx.is_eulerian(g):
        return "circuito euleriano"
    if nx.has_eulerian_path(g):
        return "caminho euleriano"
    return "não euleriano"


@pytest.mark.parametrize("g", [
    nx.cycle_graph(7),                       # circuito
    nx.path_graph(6),                        # caminho
    nx.complete_graph(5),                    # todos os graus = 4 -> circuito
    nx.complete_graph(4),                    # graus 3 -> não euleriano
    nx.star_graph(4),                        # não euleriano
    nx.Graph([(0, 1), (1, 2), (2, 0), (3, 4), (4, 5), (5, 3)]),  # desconexo
])
def test_undirected_classification(g):
    h, adj = nx_and_adj(g)
    assert check_undirected(adj)["tipo"] == kind_nx(h)


@pytest.mark.parametrize("seed", range(5))
def test_undirected_random(seed):
    g, adj = random_connected(seed=seed)
    assert check_undirected(adj)["tipo"] == kind_nx(g)


@pytest.mark.parametrize("edges", [
    [(0, 1), (1, 2), (2, 0)],                  # circuito
    [(0, 1), (1, 2)],                          # caminho
    [(0, 1), (0, 2)],                          # não euleriano
    [(0, 1), (1, 0), (1, 2), (2, 1)],          # circuito
])
def test_directed_classification(edges):
    g = nx.DiGraph(edges)
    n = g.number_of_nodes()
    assert check_directed(n, edges)["tipo"] == kind_nx(g)


@pytest.mark.parametrize("g", [nx.cycle_graph(8), nx.path_graph(5), nx.complete_graph(5)])
def test_hierholzer_uses_every_edge_once(g):
    h, _ = nx_and_adj(g)
    edges = list(h.edges())
    walk = hierholzer_undirected(h.number_of_nodes(), edges)
    assert len(walk) == len(edges) + 1
    walked = sorted(tuple(sorted(p)) for p in zip(walk, walk[1:]))
    assert walked == sorted(tuple(sorted(e)) for e in edges)


def test_hierholzer_none_when_not_eulerian():
    assert hierholzer_undirected(5, list(nx.star_graph(4).edges())) is None
