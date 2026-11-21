"""PageRank por iteração de potência (implementação própria).

    PR(v) = (1 − d)/n + d · ( Σ_{u ∈ N(v)} PR(u)/k_u  +  Σ_{u: k_u = 0} PR(u)/n )

com fator de amortecimento d = 0,85. Em grafo não dirigido cada aresta vale nos
dois sentidos; vértices sem arestas ("dangling") redistribuem sua massa
uniformemente. Cada iteração custa O(V + E), vetorizada com numpy.bincount; para
quando a variação L1 entre iterações fica abaixo de `tol`.
"""

import numpy as np


def pagerank(n: int, edges, d: float = 0.85, tol: float = 1e-10,
             max_iter: int = 200, directed: bool = False) -> tuple[np.ndarray, int]:
    """Retorna (vetor de PageRank que soma 1, número de iterações)."""
    e = np.asarray(edges, dtype=np.int64).reshape(-1, 2)
    src, dst = e[:, 0], e[:, 1]
    if not directed:
        src, dst = np.concatenate([src, dst]), np.concatenate([dst, src])
    out_deg = np.bincount(src, minlength=n).astype(float)
    dangling = out_deg == 0
    inv = np.zeros(n)
    inv[~dangling] = 1.0 / out_deg[~dangling]

    x = np.full(n, 1.0 / n)
    for it in range(1, max_iter + 1):
        spread = np.bincount(dst, weights=x[src] * inv[src], minlength=n)
        new = (1 - d) / n + d * (spread + x[dangling].sum() / n)
        if np.abs(new - x).sum() < tol:
            return new, it
        x = new
    return x, max_iter
