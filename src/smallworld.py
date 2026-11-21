"""Parte III.1: o grafo é small-world? (implementação própria, sem bibliotecas prontas)

Critério (Apêndice A, Watts & Strogatz):
    L ≈ L_rand   e   C ≫ C_rand
    σ = (C / C_rand) / (L / L_rand);  σ > 1 indica small-world.

Referência aleatória: grafo de Erdős–Rényi G(n, m), com o MESMO número de vértices
e de arestas da LCC (logo o mesmo grau médio ⟨k⟩), gerado por código próprio
(sorteio uniforme de m pares distintos). Fazemos R realizações. Como o G(n, m)
com ⟨k⟩ ≈ 3 não é conexo, L_rand é medido na sua maior componente.

Valores analíticos de conferência:  C_rand ≈ ⟨k⟩ / n,   L_rand ≈ ln n / ln ⟨k⟩.

Uso:
    python -m src.smallworld
"""

import math
import random
import statistics

import pandas as pd

from src.clustering import clustering_stats
from src.distances import sampled_paths
from src.load import TABLES_DIR, load_lcc
from src.treatment import build_adjacency, connected_components, induced_relabel

SEED = 42
REALIZATIONS = 5
PATH_SOURCES = 500


def erdos_renyi_gnm(n: int, m: int, seed: int) -> list[tuple[int, int]]:
    """G(n, m): m arestas distintas sorteadas uniformemente, sem auto-loops."""
    rng = random.Random(seed)
    edges: set[tuple[int, int]] = set()
    while len(edges) < m:
        u, v = rng.randrange(n), rng.randrange(n)
        if u == v:
            continue
        edges.add((u, v) if u < v else (v, u))
    return sorted(edges)


def graph_c_and_l(n: int, edges, k_sources: int, seed: int) -> dict:
    """C médio no grafo todo; L estimado na maior componente."""
    adj = build_adjacency(n, edges)
    c = clustering_stats(adj)["clusterizacao_media"]
    comps = connected_components(adj)
    giant_map, giant_edges = induced_relabel(comps[0], edges)
    gadj = build_adjacency(len(giant_map), giant_edges)
    paths = sampled_paths(gadj, min(k_sources, len(giant_map)), seed=seed)
    return {"C": c, "L": paths["L_medio"], "L_ic95_inf": paths["L_ic95_inf"],
            "L_ic95_sup": paths["L_ic95_sup"], "fracao_maior_componente": len(giant_map) / n}


def main() -> None:
    n, edges, _ = load_lcc()
    m = len(edges)
    k_mean = 2 * m / n

    real = graph_c_and_l(n, edges, PATH_SOURCES, SEED)
    print(f"Grafo real (LCC): n={n}, m={m}, <k>={k_mean:.4f}, C={real['C']:.5f}, L={real['L']:.4f}")

    rand_rows = []
    for r in range(REALIZATIONS):
        er = erdos_renyi_gnm(n, m, seed=SEED + r)
        res = graph_c_and_l(n, er, PATH_SOURCES, SEED + r)
        rand_rows.append({"realizacao": r + 1, **res})
        print(f"  ER #{r + 1}: C={res['C']:.6f}, L={res['L']:.4f}, "
              f"maior componente={res['fracao_maior_componente']:.2%}")
    rand = pd.DataFrame(rand_rows)
    rand.to_csv(TABLES_DIR / "parte3_smallworld_er.csv", index=False)

    c_r = statistics.fmean(rand["C"])
    l_r = statistics.fmean(rand["L"])
    c_r_theory = k_mean / n
    l_r_theory = math.log(n) / math.log(k_mean)
    sigma = (real["C"] / c_r) / (real["L"] / l_r)
    sigma_theory = (real["C"] / c_r_theory) / (real["L"] / l_r_theory)

    summary = pd.DataFrame([
        ("Comprimento médio L", real["L"], l_r, l_r_theory, real["L"] / l_r),
        ("Clusterização média C", real["C"], c_r, c_r_theory, real["C"] / c_r),
        ("σ = (C/C_r)/(L/L_r)", sigma, None, sigma_theory, None),
    ], columns=["metrica", "real", "er_medido", "er_analitico", "razao_real_er"])
    summary.to_csv(TABLES_DIR / "parte3_smallworld.csv", index=False)
    print()
    print(summary.to_string(index=False))
    verdict = "SIM" if sigma > 1 and real["L"] / l_r < 2 else "NÃO"
    print(f"\nSmall-world? {verdict}: C/C_r = {real['C'] / c_r:.0f}x, "
          f"L/L_r = {real['L'] / l_r:.2f}, σ = {sigma:.1f}")


if __name__ == "__main__":
    main()
