import networkx as nx
import pytest

from src.algorithms.mst import UnionFind, kruskal, prim
from src.algorithms.weighted import build_weighted_adjacency
from tests.helpers import random_weighted


def is_spanning_tree(n, tree):
    t = nx.Graph()
    t.add_nodes_from(range(n))
    t.add_edges_from((u, v) for u, v, _ in tree)
    return nx.is_tree(t)


@pytest.mark.parametrize("seed", range(5))
def test_prim_and_kruskal_match_networkx(seed):
    g, n, edges, weights = random_weighted(seed=seed)
    expected = nx.minimum_spanning_tree(g).size(weight="weight")
    tp, wp = prim(build_weighted_adjacency(n, edges, weights))
    tk, wk = kruskal(n, edges, weights)
    assert wp == wk == expected
    assert len(tp) == len(tk) == n - 1
    assert is_spanning_tree(n, tp) and is_spanning_tree(n, tk)


def test_disconnected_gives_forest():
    edges = [(0, 1), (1, 2), (3, 4)]
    weights = [1, 2, 3]
    tp, wp = prim(build_weighted_adjacency(5, edges, weights))
    tk, wk = kruskal(5, edges, weights)
    assert len(tp) == len(tk) == 3 and wp == wk == 6


def test_union_find():
    uf = UnionFind(4)
    assert uf.union(0, 1) and uf.union(2, 3) and uf.union(1, 3)
    assert not uf.union(0, 2)
    assert len({uf.find(i) for i in range(4)}) == 1
