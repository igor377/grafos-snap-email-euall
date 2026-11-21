"""Busca em Largura (Breadth-First Search).

Fila FIFO (collections.deque). Cada vértice entra na fila uma vez e cada
aresta é examinada duas vezes (uma por extremo) -> O(V + E).
"""

from collections import deque


def bfs(adj, source: int) -> tuple[list[int], list[int], list[int]]:
    """BFS a partir de `source`.

    Retorna (ordem de visita, distâncias em saltos, pai na árvore de BFS);
    vértices inalcançáveis têm distância -1 e pai -1.
    """
    n = len(adj)
    dist = [-1] * n
    parent = [-1] * n
    dist[source] = 0
    order = [source]
    queue = deque([source])
    while queue:
        u = queue.popleft()
        du = dist[u] + 1
        for w in adj[u]:
            if dist[w] < 0:
                dist[w] = du
                parent[w] = u
                order.append(w)
                queue.append(w)
    return order, dist, parent
