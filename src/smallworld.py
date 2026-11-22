"""Parte III.1: o grafo é small-world? (implementação própria, sem bibliotecas prontas)

Critério (Apêndice A, Watts & Strogatz):
    L ≈ L_rand   e   C ≫ C_rand
    σ = (C / C_rand) / (L / L_rand);  σ > 1 indica small-world.

Referência aleatória: grafo de Erdős–Rényi G(n, m), com o MESMO número de vértices
e de arestas da LCC (logo o mesmo grau médio ⟨k⟩), gerado por código próprio
(sorteio uniforme de m pares distintos). Fazemos R realizações. Como o G(n, m)
com ⟨k⟩ ≈ 3 não é conexo, L_rand é medido na sua maior componente.

Valores analíticos de conferência:  C_rand ≈ ⟨k⟩ / n,   L_rand ≈ ln n / ln ⟨k⟩.

Segundo modelo nulo, mais exigente: reconexão que PRESERVA A SEQUÊNCIA DE GRAUS
(Maslov & Sneppen, 2002), com 10·m trocas duplas de arestas, em 3 realizações.
Como ele mantém os hubs, separa o agrupamento que é estrutural do que seria mero
efeito da distribuição de graus heterogênea.

O L do grafo real é o EXATO (src.distances), se já calculado.

Uso:
    python -m src.smallworld                # ~15 min
    python -m src.smallworld --config-only  # reaproveita o ER e refaz só o 2º modelo nulo
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
CONFIG_REALIZATIONS = 3
SWAPS_PER_EDGE = 10


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


def degree_preserving_rewire(edges, swaps_per_edge: int = 10, seed: int = SEED):
    """Modelo nulo que PRESERVA A SEQUÊNCIA DE GRAUS (Maslov & Sneppen, 2002).

    Repete trocas duplas de arestas (a, b), (c, d) -> (a, d), (c, b), recusando as que
    criariam laços ou arestas repetidas. Cada vértice mantém exatamente o seu grau,
    mas a estrutura (quem se liga a quem) é aleatorizada. São feitas
    `swaps_per_edge` · m tentativas. Retorna (arestas, trocas aceitas).
    """
    rng = random.Random(seed)
    el = [tuple(e) for e in edges]
    present = {(u, v) if u < v else (v, u) for u, v in el}
    m = len(el)
    accepted = 0
    for _ in range(swaps_per_edge * m):
        i, j = rng.randrange(m), rng.randrange(m)
        if i == j:
            continue
        a, b = el[i]
        c, d = el[j]
        if rng.random() < 0.5:  # escolhe aleatoriamente a orientação da 2ª aresta
            c, d = d, c
        if a == d or c == b or a == c or b == d:
            continue
        e1 = (a, d) if a < d else (d, a)
        e2 = (c, b) if c < b else (b, c)
        if e1 in present or e2 in present:
            continue
        present.discard((a, b) if a < b else (b, a))
        present.discard((c, d) if c < d else (d, c))
        present.add(e1)
        present.add(e2)
        el[i], el[j] = e1, e2
        accepted += 1
    return el, accepted


def exact_real_l(default: float) -> tuple[float, str]:
    """L exato da LCC (src.distances), se já calculado; senão, o estimado."""
    f = TABLES_DIR / "parte1_caminho_exato.csv"
    if f.exists():
        return float(pd.read_csv(f)["L_exato"].iloc[0]), "exato"
    return default, "estimado"


def main() -> None:
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--config-only", action="store_true",
                        help="reaproveita as realizações de Erdős–Rényi do CSV e refaz só "
                             "o modelo nulo que preserva os graus")
    args = parser.parse_args()

    n, edges, _ = load_lcc()
    m = len(edges)
    k_mean = 2 * m / n

    real = graph_c_and_l(n, edges, PATH_SOURCES, SEED)
    real_l, l_kind = exact_real_l(real["L"])
    print(f"Grafo real (LCC): n={n}, m={m}, <k>={k_mean:.4f}, C={real['C']:.5f}, "
          f"L={real_l:.4f} ({l_kind})")

    if args.config_only:
        rand = pd.read_csv(TABLES_DIR / "parte3_smallworld_er.csv")
    else:
        rand_rows = []
        for r in range(REALIZATIONS):
            er = erdos_renyi_gnm(n, m, seed=SEED + r)
            res = graph_c_and_l(n, er, PATH_SOURCES, SEED + r)
            rand_rows.append({"realizacao": r + 1, **res})
            print(f"  ER #{r + 1}: C={res['C']:.6f}, L={res['L']:.4f}, "
                  f"maior componente={res['fracao_maior_componente']:.2%}")
        rand = pd.DataFrame(rand_rows)
        rand.to_csv(TABLES_DIR / "parte3_smallworld_er.csv", index=False)

    conf_rows = []
    for r in range(CONFIG_REALIZATIONS):
        cf, accepted = degree_preserving_rewire(edges, SWAPS_PER_EDGE, seed=SEED + r)
        res = graph_c_and_l(n, cf, PATH_SOURCES, SEED + r)
        conf_rows.append({"realizacao": r + 1, "trocas_aceitas": accepted, **res})
        print(f"  Graus preservados #{r + 1}: {accepted} trocas, C={res['C']:.6f}, "
              f"L={res['L']:.4f}, maior componente={res['fracao_maior_componente']:.2%}")
    conf = pd.DataFrame(conf_rows)
    conf.to_csv(TABLES_DIR / "parte3_smallworld_config.csv", index=False)

    c_r, l_r = statistics.fmean(rand["C"]), statistics.fmean(rand["L"])
    c_c, l_c = statistics.fmean(conf["C"]), statistics.fmean(conf["L"])
    c_r_theory = k_mean / n
    l_r_theory = math.log(n) / math.log(k_mean)
    C, L = real["C"], real_l
    sigma = (C / c_r) / (L / l_r)
    sigma_theory = (C / c_r_theory) / (L / l_r_theory)
    sigma_conf = (C / c_c) / (L / l_c)

    summary = pd.DataFrame([
        ("Comprimento médio L", L, l_r, l_r_theory, L / l_r, l_c, L / l_c),
        ("Clusterização média C", C, c_r, c_r_theory, C / c_r, c_c, C / c_c),
        ("σ = (C/C_r)/(L/L_r)", sigma, None, sigma_theory, None, sigma_conf, None),
    ], columns=["metrica", "real", "er_medido", "er_analitico", "razao_real_er",
                "config_medido", "razao_real_config"])
    summary.to_csv(TABLES_DIR / "parte3_smallworld.csv", index=False)
    print()
    print(summary.to_string(index=False))
    print(f"\nσ (Erdős–Rényi) = {sigma:.1f};  σ (graus preservados) = {sigma_conf:.1f}")


if __name__ == "__main__":
    main()
