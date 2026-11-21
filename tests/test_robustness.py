import networkx as nx
import pytest

from src.robustness import metrics_after_removal
from tests.helpers import nx_and_adj, random_connected


@pytest.mark.parametrize("seed", range(3))
def test_metrics_match_networkx(seed):
    g, adj = random_connected(n=300, p=0.012, seed=seed)
    n = g.number_of_nodes()
    removed = set(range(0, n, 7))
    m = metrics_after_removal(adj, removed, k_sources=10**6, seed=0)

    h = g.copy()
    h.remove_nodes_from(removed)
    comps = list(nx.connected_components(h))
    giant = h.subgraph(max(comps, key=len))
    assert m["B_num_componentes"] == len(comps)
    assert m["A_fracao_maior_componente"] == pytest.approx(giant.number_of_nodes() / n)
    assert m["D_fracao_isolados"] == pytest.approx(nx.number_of_isolates(h) / h.number_of_nodes())
    assert m["C_caminho_medio"] == pytest.approx(nx.average_shortest_path_length(giant))


def test_star_center_removal_isolates_everything():
    _, adj = nx_and_adj(nx.star_graph(10))  # centro = 0
    m = metrics_after_removal(adj, {0}, k_sources=5, seed=0)
    assert m["B_num_componentes"] == 10
    assert m["D_fracao_isolados"] == 1.0
