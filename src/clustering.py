"""Parte I: número de triângulos e coeficiente de clusterização (implementação própria).

Triângulos: algoritmo "forward" (Schank & Wagner, 2005). Cada aresta é
orientada do vértice de menor posto para o de maior posto, com posto dado por
(grau, id). Cada triângulo é encontrado exatamente uma vez, intersectando os
conjuntos de saída dos extremos de cada aresta. Custo O(m^{3/2}).

Clusterização local:  C(v) = 2·T(v) / (k_v (k_v − 1)), e C(v) = 0 se k_v < 2
(mesma convenção do NetworkX). Coeficiente médio = média de C(v) sobre todos os
vértices. Também reportamos a transitividade global = 3·T / (nº de triplas conexas).

Uso:
    python -m src.clustering
"""

import time

import pandas as pd

from src.load import TABLES_DIR, load_lcc
from src.treatment import build_adjacency, treat


def triangles_per_node(adj) -> list[int]:
    n = len(adj)
    rank = sorted(range(n), key=lambda v: (len(adj[v]), v))
    pos = [0] * n
    for i, v in enumerate(rank):
        pos[v] = i
    out = [set() for _ in range(n)]
    for u in range(n):
        pu = pos[u]
        out[u] = {w for w in adj[u] if pos[w] > pu}

    tri = [0] * n
    for u in range(n):
        ou = out[u]
        for v in ou:
            for w in ou & out[v]:
                tri[u] += 1
                tri[v] += 1
                tri[w] += 1
    return tri


def clustering_stats(adj) -> dict:
    tri = triangles_per_node(adj)
    n = len(adj)
    local_sum = 0.0
    triples = 0
    for v in range(n):
        k = len(adj[v])
        if k >= 2:
            pairs = k * (k - 1) // 2
            local_sum += tri[v] / pairs
            triples += pairs
    total_tri = sum(tri) // 3
    return {
        "triangulos": total_tri,
        "clusterizacao_media": local_sum / n,
        "transitividade": 3 * total_tri / triples if triples else 0.0,
        "vertices_em_triangulos": sum(1 for t in tri if t > 0),
    }


def main() -> None:
    rows = []
    t = treat()
    n_lcc, lcc_edges, _ = load_lcc()
    for scope, n, edges in [("grafo_completo", t["n"], t["undirected_edges"]),
                            ("lcc", n_lcc, lcc_edges)]:
        t0 = time.perf_counter()
        r = clustering_stats(build_adjacency(n, edges))
        r = {"escopo": scope, **r, "tempo_s": time.perf_counter() - t0}
        rows.append(r)
        print(f"{scope}: {r['triangulos']:,} triângulos, C médio = {r['clusterizacao_media']:.4f}, "
              f"transitividade = {r['transitividade']:.4f}, "
              f"vértices em triângulos = {r['vertices_em_triangulos']:,} ({r['tempo_s']:.1f}s)")
    pd.DataFrame(rows).to_csv(TABLES_DIR / "parte1_clusterizacao.csv", index=False)


if __name__ == "__main__":
    main()
