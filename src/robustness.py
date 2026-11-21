"""Parte III.3: robustez à remoção de 5% dos vértices (Apêndice C).

Política para grafo desconexo: trabalhamos na LCC (N = 224.832 vértices).
r = ⌊0,05 · N⌋ vértices são removidos, junto com as arestas incidentes.

Métricas após a remoção:
  A: S/N, fração de vértices (em relação ao N original) na maior componente;
  B: número de componentes conexas do grafo restante;
  C: comprimento médio dos caminhos na maior componente restante (BFS a partir
     de K fontes aleatórias);
  D: fração de vértices isolados (grau 0) entre os N − r restantes.

Cenários:
  (a) aleatório: R = 30 repetições, r vértices sorteados uniformemente;
  (b) direcionado: ranking FIXO por centralidade de grau (calculada uma vez no
      grafo original), removendo os r primeiros. O grau foi escolhido (uma das
      centralidades recomendadas) porque a betweenness exata custa O(V·E),
      ≈ 7,6 × 10^10 operações aqui.

Uso:
    python -m src.robustness            # completo (~6 min)
    python -m src.robustness --quick    # 3 repetições
"""

import argparse
import random
import statistics
from collections import deque

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from src.distances import sampled_paths
from src.load import FIGURES_DIR, save_figure, TABLES_DIR, load_lcc
from src.metrics import degrees
from src.treatment import build_adjacency

SEED = 42
FRACTION = 0.05
PATH_SOURCES = 50


def metrics_after_removal(adj, removed: set[int], k_sources: int, seed: int) -> dict:
    n = len(adj)
    alive = [v not in removed for v in range(n)]
    comp_id = [-1] * n
    sizes: list[int] = []
    isolated = 0
    for s in range(n):
        if not alive[s] or comp_id[s] != -1:
            continue
        cid = len(sizes)
        comp_id[s] = cid
        size = 1
        queue = deque([s])
        has_edge = False
        while queue:
            u = queue.popleft()
            for w in adj[u]:
                if alive[w]:
                    has_edge = True
                    if comp_id[w] == -1:
                        comp_id[w] = cid
                        size += 1
                        queue.append(w)
        if not has_edge:
            isolated += 1
        sizes.append(size)

    giant = max(range(len(sizes)), key=sizes.__getitem__)
    # subgrafo da maior componente, renumerado, para estimar distâncias
    nodes = [v for v in range(n) if comp_id[v] == giant]
    new_id = {v: i for i, v in enumerate(nodes)}
    gadj = [[new_id[w] for w in adj[v] if comp_id[w] == giant] for v in nodes]
    paths = sampled_paths(gadj, min(k_sources, len(nodes)), seed=seed) if len(nodes) > 1 \
        else {"L_medio": 0.0}
    return {
        "A_fracao_maior_componente": sizes[giant] / n,
        "B_num_componentes": len(sizes),
        "C_caminho_medio": paths["L_medio"],
        "D_fracao_isolados": isolated / (n - len(removed)),
        "tamanho_maior_componente": sizes[giant],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--quick", action="store_true")
    parser.add_argument("--plots-only", action="store_true",
                        help="apenas redesenha a figura a partir dos CSVs existentes")
    args = parser.parse_args()
    reps = 3 if args.quick else 30

    n, edges, _ = load_lcc()
    r = int(FRACTION * n)
    if args.plots_only:
        plot_robustness(pd.read_csv(TABLES_DIR / "parte3_robustez_aleatoria.csv"),
                        pd.read_csv(TABLES_DIR / "parte3_robustez.csv"), r)
        return
    adj = build_adjacency(n, edges)
    print(f"N = {n}, r = ⌊0,05·N⌋ = {r}")

    base = metrics_after_removal(adj, set(), PATH_SOURCES, SEED)
    print(f"Original: {base}")

    rng = random.Random(SEED)
    random_rows = []
    for i in range(reps):
        removed = set(rng.sample(range(n), r))
        m = metrics_after_removal(adj, removed, PATH_SOURCES, SEED + i)
        random_rows.append({"repeticao": i + 1, **m})
        print(f"  aleatória #{i + 1}: A={m['A_fracao_maior_componente']:.4f} "
              f"B={m['B_num_componentes']} C={m['C_caminho_medio']:.3f} "
              f"D={m['D_fracao_isolados']:.4f}")
    rand = pd.DataFrame(random_rows)
    rand.to_csv(TABLES_DIR / "parte3_robustez_aleatoria.csv", index=False)

    deg = degrees(adj)
    ranking = sorted(range(n), key=lambda v: (-deg[v], v))
    target = metrics_after_removal(adj, set(ranking[:r]), PATH_SOURCES, SEED)
    print(f"Direcionada (grau): {target}")

    metrics = ["A_fracao_maior_componente", "B_num_componentes", "C_caminho_medio",
               "D_fracao_isolados"]
    rows = []
    for mname in metrics:
        mean = statistics.fmean(rand[mname])
        sd = statistics.stdev(rand[mname]) if reps > 1 else 0.0
        rows.append({"metrica": mname, "original": base[mname], "aleatoria_media": mean,
                     "aleatoria_desvio": sd, "direcionada_grau": target[mname]})
    summary = pd.DataFrame(rows)
    a = summary.set_index("metrica").loc["A_fracao_maior_componente"]
    summary.attrs["razoes"] = (a["aleatoria_media"] / a["original"],
                               a["direcionada_grau"] / a["original"])
    summary.to_csv(TABLES_DIR / "parte3_robustez.csv", index=False)
    print()
    print(summary.to_string(index=False))
    print(f"\nS_rand/S0 = {summary.attrs['razoes'][0]:.4f}   "
          f"S_target/S0 = {summary.attrs['razoes'][1]:.4f}")

    plot_robustness(rand, summary, r)


METRICS = ["A_fracao_maior_componente", "B_num_componentes", "C_caminho_medio",
           "D_fracao_isolados"]
TITLES = {"A_fracao_maior_componente": "A: S/N (maior componente)",
          "B_num_componentes": "B: nº de componentes",
          "C_caminho_medio": "C: caminho médio na maior comp.",
          "D_fracao_isolados": "D: fração de isolados"}
TARGET_STYLE = {"direcionada_grau": ("D", "red", "grau"),
                "direcionada_pagerank": ("^", "darkorange", "PageRank")}


def plot_robustness(rand: pd.DataFrame, summary: pd.DataFrame, r: int) -> None:
    """Boxplots das remoções aleatórias + original + cada ataque direcionado do resumo."""
    s = summary.set_index("metrica")
    targets = [c for c in summary.columns if c.startswith("direcionada_")]
    reps = len(rand)
    fig, axes = plt.subplots(1, 4, figsize=(16, 4.5))
    for ax, mname in zip(axes, METRICS):
        vals = rand[mname]
        mean, sd = vals.mean(), vals.std(ddof=1) if reps > 1 else 0.0
        ax.boxplot(vals, widths=0.5)
        ax.errorbar([1.35], [mean], yerr=[sd], fmt="o", color="C0", capsize=4,
                    label=f"aleatória: {mean:.4g} ± {sd:.2g}")
        ax.scatter([1], [s.loc[mname, "original"]], marker="s", color="gray", zorder=3,
                   label=f"original: {s.loc[mname, 'original']:.4g}")
        for i, col in enumerate(targets):
            marker, color, label = TARGET_STYLE.get(col, ("x", "black", col))
            ax.scatter([0.85 + 0.3 * i], [s.loc[mname, col]], marker=marker, color=color,
                       s=45, zorder=3, label=f"ataque ({label}): {s.loc[mname, col]:.4g}")
        ax.set_title(TITLES[mname])
        ax.set_xticks([])
        ax.grid(True, axis="y", alpha=0.3)
        ax.legend(fontsize=7, loc="best")
    names = ", ".join(TARGET_STYLE.get(c, ("", "", c))[2] for c in targets)
    fig.suptitle(f"Robustez: remoção de 5% dos vértices (r = {r}); boxplot = {reps} "
                 f"remoções aleatórias; marcadores = ataque direcionado ({names})")
    fig.tight_layout()
    save_figure(fig, "robustez")
    plt.close(fig)


if __name__ == "__main__":
    main()
