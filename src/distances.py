"""Parte I: diâmetro, raio e comprimento médio dos caminhos (LCC).

O cálculo exato de todas as excentricidades exige uma BFS por vértice,
O(V·(V+E)) ≈ 224.832 × 564.757 ≈ 1,3 × 10^11 operações: inviável em Python.
Por isso:

* Diâmetro e raio EXATOS: algoritmo BoundingDiameters (Takes & Kosters, 2011),
  que mantém limites inferior/superior de excentricidade para cada vértice
  e para quando os limites do diâmetro e do raio coincidem. Em redes reais
  esparsas costuma convergir com poucas BFS.
* Comprimento médio dos caminhos ESTIMADO: média das distâncias a partir de
  k fontes uniformes (k = 100 e k = 500, semente fixa), com IC 95% sobre as
  médias por fonte. Também reportamos as excentricidades das fontes amostradas
  (estimativa ingênua de diâmetro/raio), para comparação.

Uso:
    python -m src.distances
"""

import math
import random
import time
from collections import deque

import numpy as np
import pandas as pd

from src.load import TABLES_DIR, load_lcc
from src.treatment import build_adjacency

SEED = 42


def bfs_distances(adj, source: int) -> list[int]:
    """Distâncias (em saltos) de `source` a todos os vértices; -1 se inalcançável."""
    dist = [-1] * len(adj)
    dist[source] = 0
    queue = deque([source])
    while queue:
        u = queue.popleft()
        du = dist[u] + 1
        for w in adj[u]:
            if dist[w] < 0:
                dist[w] = du
                queue.append(w)
    return dist


def eccentricity(adj, v: int) -> int:
    return max(bfs_distances(adj, v))


def bounding_diameters(adj, max_bfs: int = 3000, verbose: bool = False) -> dict:
    """Diâmetro e raio exatos de um grafo conexo (Takes & Kosters, 2011)."""
    n = len(adj)
    deg = np.fromiter((len(a) for a in adj), dtype=np.int64, count=n)
    ecc_lo = np.zeros(n, dtype=np.int64)
    ecc_up = np.full(n, np.iinfo(np.int64).max // 4, dtype=np.int64)
    candidate = np.ones(n, dtype=bool)
    d_lo, d_up = 0, int(ecc_up[0])
    r_lo, r_up = 0, int(ecc_up[0])
    bfs_count = 0
    pick_high = True

    while (d_lo != d_up or r_lo != r_up) and candidate.any() and bfs_count < max_bfs:
        idx = np.flatnonzero(candidate)
        if pick_high:  # maior limite superior (desempate: maior grau)
            key = ecc_up[idx] * (n + 1) + deg[idx]
            v = int(idx[np.argmax(key)])
        else:          # menor limite inferior (desempate: maior grau)
            key = ecc_lo[idx] * (n + 1) - deg[idx]
            v = int(idx[np.argmin(key)])
        pick_high = not pick_high

        dist = np.asarray(bfs_distances(adj, v), dtype=np.int64)
        e = int(dist.max())
        bfs_count += 1
        ecc_lo[v] = ecc_up[v] = e

        np.maximum(ecc_lo, np.maximum(e - dist, dist), out=ecc_lo)
        np.minimum(ecc_up, e + dist, out=ecc_up)

        d_lo = max(d_lo, e)
        r_up = min(r_up, e)
        d_up = int(ecc_up.max())
        r_lo = int(ecc_lo.min())

        # Vértice deixa de ser candidato se não pode mais alterar D nem R
        candidate &= ~(((ecc_up <= d_lo) & (ecc_lo >= r_up)) | (ecc_lo == ecc_up))
        if verbose and bfs_count % 10 == 0:
            print(f"  BFS {bfs_count}: D in [{d_lo}, {d_up}], R in [{r_lo}, {r_up}], "
                  f"candidatos={int(candidate.sum())}")

    return {"diametro_lo": d_lo, "diametro_up": d_up, "raio_lo": r_lo, "raio_up": r_up,
            "bfs": bfs_count, "exato": d_lo == d_up and r_lo == r_up}


def sampled_paths(adj, k: int, seed: int = SEED) -> dict:
    """Comprimento médio dos caminhos e excentricidades a partir de k fontes aleatórias."""
    n = len(adj)
    rng = random.Random(seed)
    sources = rng.sample(range(n), k)
    means, eccs = [], []
    for s in sources:
        dist = np.asarray(bfs_distances(adj, s), dtype=np.int64)
        means.append(dist.sum() / (n - 1))  # LCC: todos alcançáveis
        eccs.append(int(dist.max()))
    means = np.asarray(means)
    sd = float(means.std(ddof=1))
    half = 1.96 * sd / math.sqrt(k)  # k >= 30 -> Normal (Z)
    return {"k": k, "L_medio": float(means.mean()), "L_desvio": sd,
            "L_ic95_inf": float(means.mean() - half), "L_ic95_sup": float(means.mean() + half),
            "ecc_max_amostra": max(eccs), "ecc_min_amostra": min(eccs)}


def main() -> None:
    n, edges, _ = load_lcc()
    adj = build_adjacency(n, edges)

    rows = []
    for k in (100, 500):
        t0 = time.perf_counter()
        r = sampled_paths(adj, k)
        r["tempo_s"] = time.perf_counter() - t0
        rows.append(r)
        print(f"Amostra k={k}: L = {r['L_medio']:.4f} "
              f"(IC95% [{r['L_ic95_inf']:.4f}; {r['L_ic95_sup']:.4f}]), "
              f"ecc. máx/mín na amostra = {r['ecc_max_amostra']}/{r['ecc_min_amostra']} "
              f"({r['tempo_s']:.1f}s)")
    pd.DataFrame(rows).to_csv(TABLES_DIR / "parte1_caminhos_amostragem.csv", index=False)

    t0 = time.perf_counter()
    bd = bounding_diameters(adj, verbose=True)
    bd["tempo_s"] = time.perf_counter() - t0
    pd.DataFrame([bd]).to_csv(TABLES_DIR / "parte1_diametro_raio.csv", index=False)
    status = "exatos" if bd["exato"] else "limites (não convergiu)"
    print(f"BoundingDiameters ({status}): diâmetro em [{bd['diametro_lo']}, {bd['diametro_up']}], "
          f"raio em [{bd['raio_lo']}, {bd['raio_up']}] com {bd['bfs']} BFS "
          f"({bd['tempo_s']:.1f}s)")


if __name__ == "__main__":
    main()
