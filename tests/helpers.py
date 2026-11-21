"""Geradores de grafos de teste compartilhados entre os testes."""

import random

import networkx as nx

from src.treatment import build_adjacency


def nx_and_adj(g: nx.Graph):
    """Renumera `g` para 0..n-1 e devolve (grafo NetworkX, lista de adjacência)
    com a MESMA ordem de vizinhos, para que ordens de visita sejam comparáveis."""
    g = nx.convert_node_labels_to_integers(g)
    h = nx.Graph()
    h.add_nodes_from(range(g.number_of_nodes()))
    edges = list(g.edges())
    h.add_edges_from(edges)
    return h, build_adjacency(h.number_of_nodes(), edges)


def random_connected(n=200, p=0.02, seed=0):
    g = nx.gnp_random_graph(n, p, seed=seed)
    g = g.subgraph(max(nx.connected_components(g), key=len)).copy()
    return nx_and_adj(g)


def random_weighted(n=150, p=0.04, seed=0, low=1, high=10):
    """Grafo conexo com pesos inteiros; devolve (nx com 'weight', n, arestas, pesos)."""
    g, _ = random_connected(n, p, seed)
    rng = random.Random(seed)
    edges = list(g.edges())
    weights = [rng.randint(low, high) for _ in edges]
    for (u, v), w in zip(edges, weights):
        g[u][v]["weight"] = w
    return g, g.number_of_nodes(), edges, weights
