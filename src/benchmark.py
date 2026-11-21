"""Parte II: execução dos algoritmos, tempos e intervalos de confiança.

Para cada algoritmo: n execuções medidas com time.perf_counter (apenas a
chamada do algoritmo; a construção da lista de adjacência fica fora da medição).

IC 95% da média:
  - n >= 30:            Normal:      média ± z_{α/2} · s/√n,       z = 1,96
  - n < 30 (σ desconh.): t-Student:  média ± t_{α/2, n−1} · s/√n

Também é feito um experimento de escala (tempo × tamanho da entrada) em
subgrafos induzidos por BFS de tamanhos crescentes, com ajuste linear em escala
log-log: a inclinação estima o expoente observado da complexidade.

Uso:
    python -m src.benchmark            # completo (~5 min)
    python -m src.benchmark --quick    # 5 execuções por algoritmo (teste rápido)
"""

import argparse
import gc
import math
import statistics
import time

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats

from src.algorithms.bellman_ford import bellman_ford
from src.algorithms.bfs import bfs
from src.algorithms.dfs import dfs
from src.algorithms.dijkstra import dijkstra
from src.algorithms.euler import check_directed, check_undirected
from src.algorithms.floyd_warshall import floyd_warshall, floyd_warshall_numpy
from src.algorithms.mst import kruskal, prim
from src.algorithms.tarjan import (
    bridges_and_articulation_points,
    directed_adjacency,
    tarjan_scc,
)
from src.algorithms.weighted import build_weighted_adjacency
from src.load import FIGURES_DIR, save_figure, TABLES_DIR, load_directed, load_lcc, load_subgraph
from src.prepare_data import bfs_sample
from src.treatment import build_adjacency, induced_relabel

Z_95 = 1.96


def confidence_interval(samples: list[float], level: float = 0.95) -> dict:
    n = len(samples)
    mean = statistics.fmean(samples)
    sd = statistics.stdev(samples) if n > 1 else 0.0
    if n >= 30:
        crit, dist = (Z_95 if level == 0.95 else stats.norm.ppf((1 + level) / 2)), "Normal (Z)"
    else:
        crit, dist = stats.t.ppf((1 + level) / 2, n - 1), "t-Student"
    half = crit * sd / math.sqrt(n)
    return {"n": n, "media_s": mean, "desvio_s": sd, "ic95_inf_s": mean - half,
            "ic95_sup_s": mean + half, "distribuicao": dist, "valor_critico": crit}


def measure(fn, runs: int):
    times = []
    result = None
    for _ in range(runs):
        gc.collect()
        t0 = time.perf_counter()
        result = fn()
        times.append(time.perf_counter() - t0)
    return result, times


def run_benchmark(runs: int, fw_runs: int) -> tuple[pd.DataFrame, pd.DataFrame]:
    n, edges, weights = load_lcc()
    adj = build_adjacency(n, edges)
    wadj = build_weighted_adjacency(n, edges, weights)
    nd, dedges = load_directed()
    dadj = directed_adjacency(nd, dedges)
    ns, sedges, sweights = load_subgraph()
    m = len(edges)

    INF = float("inf")
    algos = [
        # nome, grafo, complexidade, função, nº de execuções, resumo do resultado
        ("BFS", "LCC", "O(V+E)", lambda: bfs(adj, 0), runs,
         lambda r: f"visitou {len(r[0])} vértices; profundidade máx. {max(r[1])}"),
        ("DFS (iterativa)", "LCC", "O(V+E)", lambda: dfs(adj, 0), runs,
         lambda r: f"visitou {len(r[0])} vértices"),
        ("Eulerianidade (não dirigido)", "LCC", "O(V+E)", lambda: check_undirected(adj), runs,
         lambda r: f"{r['tipo']}; {r['vertices_grau_impar']} vértices de grau ímpar"),
        ("Eulerianidade (dirigido)", "G_dir", "O(V+E)", lambda: check_directed(nd, dedges), runs,
         lambda r: f"{r['tipo']}; {r['vertices_desbalanceados']} vértices com entrada≠saída; "
                   f"fracamente conexo={r['fracamente_conexo']}"),
        ("Dijkstra (heap)", "LCC ponderada", "O((V+E) log V)", lambda: dijkstra(wadj, 0), runs,
         lambda r: f"alcançou {sum(d < INF for d in r[0])} vértices; dist. máx. {max(r[0]):.0f}"),
        ("Bellman-Ford", "subgrafo 300", "O(V·E)",
         lambda: bellman_ford(ns, sedges, sweights, 0), runs,
         lambda r: f"alcançou {sum(d < INF for d in r[0])} vértices; {r[2]} rodadas"),
        ("Floyd-Warshall (Python puro)", "subgrafo 300", "O(V³)",
         lambda: floyd_warshall(ns, sedges, sweights), fw_runs,
         lambda r: f"matriz {len(r)}×{len(r)}; dist. máx. {max(max(row) for row in r):.0f}"),
        ("Floyd-Warshall (numpy)", "subgrafo 300", "O(V³)",
         lambda: floyd_warshall_numpy(ns, sedges, sweights), runs,
         lambda r: f"matriz {r.shape[0]}×{r.shape[1]}; dist. máx. {r.max():.0f}"),
        ("Tarjan (SCC)", "G_dir", "O(V+E)", lambda: tarjan_scc(dadj), runs,
         lambda r: f"{len(r)} SCCs; maior com {max(map(len, r))} vértices"),
        ("Tarjan (pontes/articulações)", "LCC", "O(V+E)",
         lambda: bridges_and_articulation_points(adj), runs,
         lambda r: f"{len(r[0])} pontes; {len(r[1])} articulações"),
        ("Prim (heap)", "LCC ponderada", "O(E log V)", lambda: prim(wadj), runs,
         lambda r: f"{len(r[0])} arestas; peso total {r[1]}"),
        ("Kruskal (union-find)", "LCC ponderada", "O(E log V)",
         lambda: kruskal(n, edges, weights), runs,
         lambda r: f"{len(r[0])} arestas; peso total {r[1]}"),
    ]

    sizes = {"LCC": (n, m), "LCC ponderada": (n, m), "G_dir": (nd, len(dedges)),
             "subgrafo 300": (ns, len(sedges))}
    timing_rows, result_rows = [], []
    for name, graph, cplx, fn, k, summary in algos:
        result, times = measure(fn, k)
        ci = confidence_interval(times)
        v, e = sizes[graph]
        timing_rows.append({"algoritmo": name, "grafo": graph, "V": v, "E": e,
                            "complexidade": cplx, **ci})
        result_rows.append({"algoritmo": name, "grafo": graph, "resultado": summary(result)})
        print(f"{name:32s} {graph:14s} média {ci['media_s']:.4f}s ± {ci['desvio_s']:.4f} "
              f"IC95% [{ci['ic95_inf_s']:.4f}; {ci['ic95_sup_s']:.4f}] ({ci['distribuicao']}, "
              f"n={ci['n']}) | {summary(result)}")
    return pd.DataFrame(timing_rows), pd.DataFrame(result_rows)


def scaling_experiment(reps: int) -> pd.DataFrame:
    """Tempo × tamanho em subgrafos BFS da LCC; inclinação log-log = expoente observado."""
    n, edges, weights = load_lcc()
    adj = build_adjacency(n, edges)
    order = bfs_sample(adj, n)  # ordem de BFS da LCC inteira (prefixos são conexos)
    weight_of = dict(zip(edges, weights))

    def sub(k):
        mapping, sedges = induced_relabel(order[:k], edges)
        sw = [weight_of[(mapping[u], mapping[v])] for u, v in sedges]
        return k, sedges, sw

    rows = []
    for k in (14_000, 28_000, 56_000, 112_000, n):
        kk, sedges, sw = sub(k)
        a = build_adjacency(kk, sedges)
        wa = build_weighted_adjacency(kk, sedges, sw)
        for name, fn in (("BFS", lambda: bfs(a, 0)), ("Dijkstra", lambda: dijkstra(wa, 0))):
            _, times = measure(fn, reps)
            rows.append({"algoritmo": name, "V": kk, "E": len(sedges),
                         "tamanho": kk + len(sedges), "media_s": statistics.fmean(times)})
    for k in (50, 100, 150, 200, 250, 300):
        kk, sedges, sw = sub(k)
        _, times = measure(lambda: floyd_warshall(kk, sedges, sw), reps)
        rows.append({"algoritmo": "Floyd-Warshall", "V": kk, "E": len(sedges),
                     "tamanho": kk, "media_s": statistics.fmean(times)})
    return pd.DataFrame(rows)


def plot_scaling(df: pd.DataFrame) -> pd.DataFrame:
    fig, axes = plt.subplots(1, 3, figsize=(14, 4))
    slopes = []
    specs = [("BFS", "V + E", 1), ("Dijkstra", "V + E", 1), ("Floyd-Warshall", "V", 3)]
    for ax, (name, xlabel, theory) in zip(axes, specs):
        d = df[df["algoritmo"] == name]
        x, y = np.log10(d["tamanho"]), np.log10(d["media_s"])
        slope, intercept = np.polyfit(x, y, 1)
        slopes.append({"algoritmo": name, "expoente_observado": slope,
                       "expoente_teorico": theory})
        ax.loglog(d["tamanho"], d["media_s"], "o", label="medido")
        xs = np.linspace(x.min(), x.max(), 50)
        ax.loglog(10 ** xs, 10 ** (intercept + slope * xs), "--",
                  label=f"ajuste: inclinação {slope:.2f}")
        ax.set_title(f"{name} (teórico: expoente ≈ {theory}"
                     f"{' + fator log' if name == 'Dijkstra' else ''})")
        ax.set_xlabel(f"Tamanho da entrada ({xlabel})")
        ax.set_ylabel("Tempo médio (s)")
        ax.grid(True, which="both", alpha=0.3)
        ax.legend()
    fig.tight_layout()
    save_figure(fig, "escala_algoritmos")
    plt.close(fig)
    return pd.DataFrame(slopes)


def plot_times(timing: pd.DataFrame) -> None:
    t = timing.sort_values("media_s")
    fig, ax = plt.subplots(figsize=(9, 5))
    err = [t["media_s"] - t["ic95_inf_s"], t["ic95_sup_s"] - t["media_s"]]
    ax.barh(t["algoritmo"] + " [" + t["grafo"] + "]", t["media_s"], xerr=err, capsize=3)
    ax.set_xscale("log")
    ax.set_xlabel("Tempo médio (s), escala log; barras = IC 95%")
    ax.set_title("Tempo de execução observado dos algoritmos")
    ax.grid(True, axis="x", which="both", alpha=0.3)
    fig.tight_layout()
    save_figure(fig, "tempos_algoritmos")
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--quick", action="store_true")
    parser.add_argument("--plots-only", action="store_true",
                        help="apenas redesenha as figuras a partir dos CSVs existentes")
    args = parser.parse_args()
    runs, fw_runs, reps = (5, 3, 2) if args.quick else (30, 10, 5)

    if args.plots_only:
        plot_times(pd.read_csv(TABLES_DIR / "parte2_tempos.csv"))
        plot_scaling(pd.read_csv(TABLES_DIR / "parte2_escala.csv"))
        return

    timing, results = run_benchmark(runs, fw_runs)
    timing.to_csv(TABLES_DIR / "parte2_tempos.csv", index=False)
    results.to_csv(TABLES_DIR / "parte2_resultados.csv", index=False)
    plot_times(timing)

    print("\nExperimento de escala...")
    scaling = scaling_experiment(reps)
    scaling.to_csv(TABLES_DIR / "parte2_escala.csv", index=False)
    slopes = plot_scaling(scaling)
    slopes.to_csv(TABLES_DIR / "parte2_expoentes.csv", index=False)
    print(slopes.to_string(index=False))


if __name__ == "__main__":
    main()
