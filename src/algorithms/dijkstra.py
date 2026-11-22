"""Dijkstra com heap binário (heapq) e "lazy deletion".

Aplicabilidade: exige pesos não negativos. O SNAP não informa quantos e-mails cada
par trocou; com peso 1 Dijkstra equivaleria à BFS. Usamos pesos derivados da
reciprocidade (1 = laço recíproco, 2 = mão única): o caminho de menor custo prefere
cadeias de comunicação nos dois sentidos.

Cada aresta pode inserir uma entrada no heap -> O((V + E) log V).
"""

import heapq

INF = float("inf")


def dijkstra(wadj, source: int) -> tuple[list[float], list[int]]:
    """Retorna (distâncias, pai na árvore de caminhos mínimos); INF se inalcançável."""
    n = len(wadj)
    dist = [INF] * n
    parent = [-1] * n
    dist[source] = 0
    heap = [(0, source)]
    done = [False] * n
    while heap:
        d, u = heapq.heappop(heap)
        if done[u]:
            continue
        done[u] = True
        for v, w in wadj[u]:
            nd = d + w
            if nd < dist[v]:
                dist[v] = nd
                parent[v] = u
                heapq.heappush(heap, (nd, v))
    return dist, parent
