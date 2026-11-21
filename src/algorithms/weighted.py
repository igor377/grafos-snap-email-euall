"""Estruturas auxiliares para grafos ponderados."""


def build_weighted_adjacency(n: int, edges, weights) -> list[list[tuple[int, int]]]:
    """Lista de adjacência não dirigida: adj[u] = [(v, peso), ...]."""
    adj: list[list[tuple[int, int]]] = [[] for _ in range(n)]
    for (u, v), w in zip(edges, weights, strict=True):
        adj[u].append((v, w))
        adj[v].append((u, w))
    return adj
