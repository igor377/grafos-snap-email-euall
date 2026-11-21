"""Floyd-Warshall: caminhos mínimos entre todos os pares.

Programação dinâmica: d_k[i][j] = min(d_{k-1}[i][j], d_{k-1}[i][k] + d_{k-1}[k][j]).
Tempo O(V^3), memória O(V^2).

Na LCC (V = 224.832) seriam ~1,1 × 10^16 operações e uma matriz de ~5 × 10^10
células (~400 GB em float64), o que é inviável. Por isso o algoritmo roda no
subgrafo de 300 vértices.

Duas implementações do MESMO algoritmo:
  - floyd_warshall:        três laços em Python puro (referência didática);
  - floyd_warshall_numpy:  laço em k em Python; a atualização O(V^2) de cada k
                           é vetorizada com numpy (np.minimum + broadcasting).
"""

import numpy as np

INF = float("inf")


def _initial_matrix(n: int, edges, weights, directed: bool):
    d = [[INF] * n for _ in range(n)]
    for i in range(n):
        d[i][i] = 0
    for (u, v), w in zip(edges, weights, strict=True):
        if w < d[u][v]:
            d[u][v] = w
        if not directed and w < d[v][u]:
            d[v][u] = w
    return d


def floyd_warshall(n: int, edges, weights, directed: bool = False) -> list[list[float]]:
    d = _initial_matrix(n, edges, weights, directed)
    for k in range(n):
        dk = d[k]
        for i in range(n):
            di = d[i]
            dik = di[k]
            if dik == INF:
                continue
            for j in range(n):
                nd = dik + dk[j]
                if nd < di[j]:
                    di[j] = nd
    return d


def floyd_warshall_numpy(n: int, edges, weights, directed: bool = False) -> np.ndarray:
    d = np.array(_initial_matrix(n, edges, weights, directed), dtype=np.float64)
    for k in range(n):
        np.minimum(d, d[:, k, None] + d[None, k, :], out=d)
    return d


def has_negative_cycle(d) -> bool:
    """Após o Floyd-Warshall, há ciclo negativo se algum d[i][i] < 0."""
    return any(d[i][i] < 0 for i in range(len(d)))
