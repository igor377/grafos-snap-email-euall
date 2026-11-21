"""Bellman-Ford.

Aplicabilidade: aceita pesos negativos e detecta ciclos negativos, mas custa
O(V · E). No email-EuAll (não ponderado, pesos sintéticos positivos) não há
vantagem sobre Dijkstra; ele é executado no subgrafo de 300 vértices, já que na
LCC seriam até 224.832 × 679.850 ≈ 1,5 × 10^11 relaxamentos.

Cada aresta não dirigida {u, v} é relaxada nos dois sentidos. Parada antecipada
quando uma rodada não altera nenhuma distância.
"""

INF = float("inf")


def bellman_ford(n: int, edges, weights, source: int, directed: bool = False):
    """Retorna (distâncias, pai, rodadas executadas).

    Lança ValueError se houver ciclo negativo alcançável a partir da fonte.
    """
    arcs = []
    for (u, v), w in zip(edges, weights, strict=True):
        arcs.append((u, v, w))
        if not directed:
            arcs.append((v, u, w))

    dist = [INF] * n
    parent = [-1] * n
    dist[source] = 0
    rounds = 0
    for _ in range(n - 1):
        rounds += 1
        changed = False
        for u, v, w in arcs:
            if dist[u] + w < dist[v]:
                dist[v] = dist[u] + w
                parent[v] = u
                changed = True
        if not changed:
            break
    else:
        for u, v, w in arcs:
            if dist[u] + w < dist[v]:
                raise ValueError("ciclo negativo alcançável a partir da fonte")
    return dist, parent, rounds
