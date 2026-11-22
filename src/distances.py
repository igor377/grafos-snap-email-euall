"""Parte I: diâmetro, raio e comprimento médio dos caminhos (LCC).

O cálculo exato de todas as excentricidades exige uma BFS por vértice,
O(V·(V+E)) ≈ 224.832 × 564.757 ≈ 1,3 × 10^11 operações: inviável em Python.
Por isso:

* Diâmetro e raio EXATOS: algoritmo BoundingDiameters (Takes & Kosters, 2011),
  que mantém limites inferior/superior de excentricidade para cada vértice
  e para quando os limites do diâmetro e do raio coincidem. Em redes reais
  esparsas costuma convergir com poucas BFS.
* Comprimento médio dos caminhos EXATO: 84% dos vértices são folhas (grau 1), e
  a soma das distâncias de uma folha é deduzida da do seu único vizinho
  (S(ℓ) = n − 2 + S(p)). Bastam BFS a partir dos ~36 mil vértices não folha,
  feitas por níveis com numpy sobre a representação CSR (~40 ms cada, ~25 min).
* Comprimento médio ESTIMADO (para comparação e validação do estimador usado
  nos modelos nulos e na robustez): média das distâncias a partir de k fontes
  uniformes (k = 100 e k = 500, semente fixa), com IC 95%.

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


def to_csr(adj) -> tuple[np.ndarray, np.ndarray]:
    """Lista de adjacência -> (indptr, indices) no formato CSR."""
    deg = np.fromiter((len(a) for a in adj), dtype=np.int64, count=len(adj))
    indptr = np.zeros(len(adj) + 1, dtype=np.int64)
    np.cumsum(deg, out=indptr[1:])
    indices = np.fromiter((w for a in adj for w in a), dtype=np.int64, count=int(indptr[-1]))
    return indptr, indices


def bfs_distance_sum(indptr, indices, source: int, dist: np.ndarray,
                     owner: np.ndarray | None = None) -> tuple[int, int, int]:
    """BFS vetorizada (por níveis) a partir de `source`.

    Retorna (soma das distâncias, nº de vértices alcançados, excentricidade). `dist` é
    um vetor de trabalho preenchido com -1, que é restaurado ao final; `owner` é um
    vetor de trabalho de mesmo tamanho (criado se não for passado).
    """
    if owner is None:
        owner = np.empty_like(dist)
    dist[source] = 0
    frontier = np.array([source], dtype=np.int64)
    visited = [frontier]
    total, reached, level = 0, 1, 0
    while True:
        starts, ends = indptr[frontier], indptr[frontier + 1]
        lens = ends - starts
        size = int(lens.sum())
        if size == 0:
            break
        # posições de todos os vizinhos da fronteira em `indices`
        offsets = np.repeat(starts - np.concatenate(([0], np.cumsum(lens)[:-1])), lens)
        nbrs = indices[offsets + np.arange(size)]
        nbrs = nbrs[dist[nbrs] < 0]
        if nbrs.size == 0:
            break
        level += 1
        # desduplicação sem ordenar: marca todos com o nível e mantém, de cada vértice,
        # só a primeira ocorrência (a posição gravada por último em `owner`)
        dist[nbrs] = level
        pos = np.arange(nbrs.size)
        owner[nbrs] = pos
        nbrs = nbrs[owner[nbrs] == pos]
        total += level * nbrs.size
        reached += nbrs.size
        visited.append(nbrs)
        frontier = nbrs
    for v in visited:
        dist[v] = -1
    return total, reached, level


def exact_average_path_length(adj, verbose: bool = False) -> dict:
    """Comprimento médio EXATO dos caminhos de um grafo conexo, com redução das folhas.

    Se ℓ é folha com vizinho único p, então d(ℓ, t) = 1 + d(p, t) para todo t ≠ ℓ,
    logo S(ℓ) = Σ_t d(ℓ, t) = (n − 2) + S(p). Basta uma BFS por vértice NÃO folha;
    a soma das folhas sai das somas dos seus vizinhos.
    L = Σ_v S(v) / (n (n − 1)).
    """
    n = len(adj)
    indptr, indices = to_csr(adj)
    deg = np.diff(indptr)
    dist = np.full(n, -1, dtype=np.int64)
    owner = np.empty(n, dtype=np.int64)
    sums = np.zeros(n, dtype=np.int64)
    non_leaves = np.flatnonzero(deg != 1)
    t0 = time.perf_counter()
    for i, v in enumerate(non_leaves):
        s, reached, _ = bfs_distance_sum(indptr, indices, int(v), dist, owner)
        if reached != n:
            raise ValueError("o grafo precisa ser conexo")
        sums[v] = s
        if verbose and (i + 1) % 5000 == 0:
            el = time.perf_counter() - t0
            print(f"  {i + 1}/{len(non_leaves)} BFS ({el:.0f}s, faltam ~"
                  f"{el / (i + 1) * (len(non_leaves) - i - 1):.0f}s)")
    leaves = np.flatnonzero(deg == 1)
    parents = indices[indptr[leaves]]
    if np.any(deg[parents] == 1):  # duas folhas adjacentes: só ocorre se n = 2
        raise ValueError("folha ligada a folha")
    sums[leaves] = (n - 2) + sums[parents]
    total = int(sums.sum())
    return {"L_exato": total / (n * (n - 1)), "soma_distancias": total,
            "bfs_executadas": int(len(non_leaves)), "folhas_deduzidas": int(len(leaves)),
            "tempo_s": time.perf_counter() - t0}


def main() -> None:
    n, edges, _ = load_lcc()
    adj = build_adjacency(n, edges)

    print("Comprimento médio exato (BFS só dos vértices não folha)...")
    ex = exact_average_path_length(adj, verbose=True)
    pd.DataFrame([ex]).to_csv(TABLES_DIR / "parte1_caminho_exato.csv", index=False)
    print(f"L exato = {ex['L_exato']:.6f} com {ex['bfs_executadas']} BFS "
          f"({ex['folhas_deduzidas']} folhas deduzidas) em {ex['tempo_s']:.0f}s")

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
