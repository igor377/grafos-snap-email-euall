"""Centralidade de intermediação (betweenness) pelo algoritmo de Brandes (2001).

    C_B(v) = Σ_{s ≠ v ≠ t} σ_st(v) / σ_st

Para cada fonte s, uma BFS conta os caminhos mínimos σ e, percorrendo os vértices
em ordem decrescente de distância, acumula as dependências
    δ(v) = Σ_{w: v é predecessor de w} σ_v/σ_w · (1 + δ(w)).
Custo exato: O(V·E) em grafos não ponderados, ≈ 7,6·10^10 operações na LCC, o que é
inviável em Python. Por isso usamos a versão AMOSTRADA (Brandes & Pich, 2007): k
fontes sorteadas uniformemente e extrapolação por n/k, um estimador não enviesado
de C_B. O custo cai para O(k·(V+E)).

Os predecessores não são guardados em listas: ao processar w, os predecessores são
os vizinhos v com dist[v] = dist[w] − 1, o que economiza memória.
"""

import random
from collections import deque


def betweenness(adj, k: int | None = None, seed: int = 42) -> list[float]:
    """Betweenness não normalizada de um grafo não dirigido (mesma escala do NetworkX
    com normalized=False). Com k < n, estimativa por amostragem de k fontes."""
    n = len(adj)
    sources = range(n) if k is None or k >= n else random.Random(seed).sample(range(n), k)
    k_eff = n if k is None or k >= n else k
    cb = [0.0] * n
    dist = [-1] * n
    sigma = [0] * n
    delta = [0.0] * n
    for s in sources:
        order = [s]
        dist[s] = 0
        sigma[s] = 1
        queue = deque([s])
        while queue:
            u = queue.popleft()
            du = dist[u] + 1
            su = sigma[u]
            for w in adj[u]:
                if dist[w] < 0:
                    dist[w] = du
                    order.append(w)
                    queue.append(w)
                if dist[w] == du:
                    sigma[w] += su
        for w in reversed(order):
            dw = dist[w] - 1
            coef = (1.0 + delta[w]) / sigma[w]
            for v in adj[w]:
                if dist[v] == dw:
                    delta[v] += sigma[v] * coef
            if w != s:
                cb[w] += delta[w]
        for w in order:  # reinicia só o que foi tocado
            dist[w] = -1
            sigma[w] = 0
            delta[w] = 0.0
    scale = n / k_eff / 2.0  # extrapolação da amostra; /2 porque o grafo é não dirigido
    return [c * scale for c in cb]
