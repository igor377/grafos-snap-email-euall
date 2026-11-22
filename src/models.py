"""Parte III (extra): o grafo se aproxima de algum modelo clássico?

Geramos, com código próprio, três modelos com o mesmo número de vértices da LCC e
comparamos grau máximo, clusterização média C, comprimento médio L e a cauda da
distribuição de graus (MLE discreta de γ, com o KS de bondade do ajuste):

  * Erdős–Rényi G(n, m): mesmos n e m da LCC (src.smallworld.erdos_renyi_gnm);
  * Barabási–Albert (1999): crescimento com ligação preferencial, m = 2 arestas por
    vértice novo (m = 1 geraria uma árvore, sem triângulos);
  * Watts–Strogatz (1998): anel com k = 4 vizinhos e religação com p = 0,1
    (k precisa ser par; k = 2 seria um anel simples).
BA e WS ficam com ≈ 2n arestas, um pouco acima das ≈ 1,5n da LCC, porque m e k são
inteiros. L é estimado por BFS a partir de 100 fontes na maior componente de cada grafo.

Uso:
    python -m src.models    # ~3 min
"""

import random

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from src.clustering import clustering_stats
from src.distances import sampled_paths
from src.load import TABLES_DIR, load_lcc, save_figure
from src.metrics import degrees
from src.powerlaw import ccdf, fit_mle
from src.smallworld import erdos_renyi_gnm
from src.treatment import build_adjacency, connected_components, induced_relabel

SEED = 42
PATH_SOURCES = 100
BA_M = 2
WS_K, WS_P = 4, 0.1


def barabasi_albert(n: int, m: int, seed: int = SEED) -> list[tuple[int, int]]:
    """Ligação preferencial: cada vértice novo liga-se a m vértices distintos, sorteados
    com probabilidade proporcional ao grau. `pool` contém cada vértice uma vez por
    unidade de grau, então um sorteio uniforme em `pool` é proporcional ao grau."""
    rng = random.Random(seed)
    edges = [(u, v) for u in range(m + 1) for v in range(u + 1, m + 1)]  # clique inicial
    pool = [x for e in edges for x in e]
    for new in range(m + 1, n):
        targets = set()
        while len(targets) < m:
            targets.add(rng.choice(pool))
        for t in targets:
            edges.append((t, new))
            pool += (t, new)
    return edges


def watts_strogatz(n: int, k: int, p: float, seed: int = SEED) -> list[tuple[int, int]]:
    """Anel regular (cada vértice ligado aos k/2 vizinhos de cada lado) em que cada
    aresta (u, u+j) é religada, com probabilidade p, para (u, w) com w uniforme,
    evitando laços e arestas repetidas."""
    rng = random.Random(seed)
    edges = {(u, (u + j) % n) if u < (u + j) % n else ((u + j) % n, u)
             for u in range(n) for j in range(1, k // 2 + 1)}
    for u in range(n):
        for j in range(1, k // 2 + 1):
            v = (u + j) % n
            e = (u, v) if u < v else (v, u)
            if rng.random() < p and e in edges:
                w = rng.randrange(n)
                f = (u, w) if u < w else (w, u)
                if w != u and f not in edges:
                    edges.remove(e)
                    edges.add(f)
    return sorted(edges)


def describe(name: str, n: int, edges, seed: int) -> tuple[dict, np.ndarray]:
    adj = build_adjacency(n, edges)
    deg = np.asarray(degrees(adj))
    c = clustering_stats(adj)["clusterizacao_media"]
    comps = connected_components(adj)
    gmap, gedges = induced_relabel(comps[0], edges)
    L = sampled_paths(build_adjacency(len(gmap), gedges), min(PATH_SOURCES, len(gmap)),
                      seed=seed)["L_medio"]
    tail = fit_mle(deg, min_kmin=2) if deg.max() >= 10 else None
    row = {"modelo": name, "n": n, "m": len(edges), "grau_medio": deg.mean(),
           "grau_max": int(deg.max()), "fracao_grau1": float((deg == 1).mean()),
           "C": c, "L": L, "fracao_maior_componente": len(gmap) / n,
           "gamma_mle": tail["gamma"] if tail else np.nan,
           "kmin_mle": tail["kmin"] if tail else np.nan,
           "ks_mle": tail["ks"] if tail else np.nan}
    print(f"{name:22s} m={len(edges):>7} kmax={row['grau_max']:>5} C={c:.4f} L={L:.3f} "
          f"γ={row['gamma_mle']:.2f} KS={row['ks_mle']:.3f}")
    return row, deg


def main() -> None:
    n, lcc_edges, _ = load_lcc()
    graphs = [
        ("email-EuAll (LCC)", lcc_edges),
        ("Erdős–Rényi G(n,m)", erdos_renyi_gnm(n, len(lcc_edges), seed=SEED)),
        (f"Barabási–Albert (m={BA_M})", barabasi_albert(n, BA_M)),
        (f"Watts–Strogatz (k={WS_K}, p={WS_P})", watts_strogatz(n, WS_K, WS_P)),
    ]
    rows, degs = [], {}
    for name, edges in graphs:
        row, deg = describe(name, n, edges, SEED)
        rows.append(row)
        degs[name] = deg
    pd.DataFrame(rows).to_csv(TABLES_DIR / "parte3_modelos.csv", index=False)

    fig, ax = plt.subplots(figsize=(7, 4.5))
    for (name, deg), style in zip(degs.items(), ("o", "s", "^", "v")):
        ks, tail = ccdf(deg)
        ax.loglog(ks, tail, style, ms=3, label=name)
    ax.set_xlabel("Grau k")
    ax.set_ylabel("P(K ≥ k)")
    ax.set_title("CCDF dos graus: grafo real × modelos clássicos")
    ax.grid(True, which="both", alpha=0.3)
    ax.legend(fontsize=8)
    fig.tight_layout()
    save_figure(fig, "modelos_ccdf")
    plt.close(fig)


if __name__ == "__main__":
    main()
