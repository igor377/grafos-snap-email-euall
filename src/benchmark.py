"""Parte II: execução dos algoritmos, tempos e intervalos de confiança.

Para cada algoritmo: n execuções medidas com time.perf_counter (apenas a
chamada do algoritmo; a construção da lista de adjacência fica fora da medição).

IC 95% da média:
  - n >= 30:            Normal:      média ± z_{α/2} · s/√n,       z = 1,96
  - n < 30 (σ desconh.): t-Student:  média ± t_{α/2, n−1} · s/√n

Também é feito um experimento de escala (tempo × tamanho da entrada) em
subgrafos induzidos por BFS de tamanhos crescentes, com ajuste linear em escala
log-log: a inclinação estima o expoente observado da complexidade. Cada tamanho é
medido 30 vezes, com IC 95% por ponto. Ajustamos também o tempo contra a função
teórica f(n) (V+E, (V+E) log V, V³): se f descreve bem o custo, o expoente é ≈ 1.

Uso:
    python -m src.benchmark                 # completo (~9 min)
    python -m src.benchmark --scaling-only  # só o experimento de escala (~4 min)
    python -m src.benchmark --plots-only    # só redesenha as figuras a partir dos CSVs
    python -m src.benchmark --quick         # execução reduzida (teste rápido)
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

    def row(name, kk, m, size, times):
        return {"algoritmo": name, "V": kk, "E": m, "tamanho": size,
                "f_teorica": theoretical_cost(name, kk, m), **confidence_interval(times)}

    rows = []
    for k in (14_000, 28_000, 56_000, 112_000, n):
        kk, sedges, sw = sub(k)
        a = build_adjacency(kk, sedges)
        wa = build_weighted_adjacency(kk, sedges, sw)
        for name, fn in (("BFS", lambda: bfs(a, 0)), ("Dijkstra", lambda: dijkstra(wa, 0))):
            _, times = measure(fn, reps)
            rows.append(row(name, kk, len(sedges), kk + len(sedges), times))
            print(f"  escala {name:15s} V={kk:>7} média {statistics.fmean(times):.4f}s")
    for k in (50, 100, 150, 200, 250, 300):
        kk, sedges, sw = sub(k)
        _, times = measure(lambda: floyd_warshall(kk, sedges, sw), reps)
        rows.append(row("Floyd-Warshall", kk, len(sedges), kk, times))
        print(f"  escala Floyd-Warshall  V={kk:>7} média {statistics.fmean(times):.4f}s")
    return pd.DataFrame(rows)


def theoretical_cost(name: str, v: int, e: int) -> float:
    """Função de custo teórica f(n) de cada algoritmo do experimento de escala."""
    return {"BFS": v + e,
            "Dijkstra": (v + e) * math.log2(v),
            "Floyd-Warshall": float(v) ** 3}[name]


def loglog_fit(x, y) -> tuple[float, float, float]:
    """Reta log10(y) = a·log10(x) + b. Retorna (a, b, R²)."""
    lx, ly = np.log10(np.asarray(x, float)), np.log10(np.asarray(y, float))
    a, b = np.polyfit(lx, ly, 1)
    pred = a * lx + b
    r2 = 1 - np.sum((ly - pred) ** 2) / np.sum((ly - ly.mean()) ** 2)
    return float(a), float(b), float(r2)


def plot_scaling(df: pd.DataFrame) -> pd.DataFrame:
    """Tempo × tamanho com IC 95% por ponto e dois ajustes em log-log:
    (i) contra o tamanho da entrada (expoente teórico 1 ou 3);
    (ii) contra a função teórica f(n) (expoente ideal 1, se f descreve bem o custo)."""
    fig, axes = plt.subplots(1, 3, figsize=(14, 4.2))
    fits = []
    specs = [("BFS", "V + E", 1, "V+E"), ("Dijkstra", "V + E", 1, "(V+E) log V"),
             ("Floyd-Warshall", "V", 3, "V³")]
    for ax, (name, xlabel, theory, fname) in zip(axes, specs):
        d = df[df["algoritmo"] == name]
        slope, intercept, r2 = loglog_fit(d["tamanho"], d["media_s"])
        row = {"algoritmo": name, "expoente_observado": slope, "R2": r2,
               "expoente_teorico": theory}
        if "f_teorica" in d:
            s_f, _, r2_f = loglog_fit(d["f_teorica"], d["media_s"])
            row.update({"funcao_teorica": fname, "expoente_vs_f": s_f, "R2_vs_f": r2_f})
        fits.append(row)
        if "ic95_inf_s" in d:
            err = [d["media_s"] - d["ic95_inf_s"], d["ic95_sup_s"] - d["media_s"]]
            ax.errorbar(d["tamanho"], d["media_s"], yerr=err, fmt="o", capsize=3,
                        label=f"medido (média e IC 95%, n={int(d['n'].iloc[0])})")
        else:
            ax.plot(d["tamanho"], d["media_s"], "o", label="medido")
        ax.set_xscale("log")
        ax.set_yscale("log")
        lx = np.log10(d["tamanho"])
        xs = np.linspace(lx.min(), lx.max(), 50)
        ax.plot(10 ** xs, 10 ** (intercept + slope * xs), "--",
                label=f"ajuste: inclinação {slope:.2f} (R² = {r2:.3f})")
        ax.set_title(f"{name} (teórico: expoente ≈ {theory}"
                     f"{' + fator log' if name == 'Dijkstra' else ''})")
        ax.set_xlabel(f"Tamanho da entrada ({xlabel})")
        ax.set_ylabel("Tempo médio (s)")
        ax.grid(True, which="both", alpha=0.3)
        ax.legend(fontsize=8)
    fig.tight_layout()
    save_figure(fig, "escala_algoritmos")
    plt.close(fig)
    return pd.DataFrame(fits)


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
    parser.add_argument("--scaling-only", action="store_true",
                        help="refaz só o experimento de escala")
    args = parser.parse_args()
    runs, fw_runs, reps = (5, 3, 3) if args.quick else (30, 10, 30)

    if args.plots_only:
        plot_times(pd.read_csv(TABLES_DIR / "parte2_tempos.csv"))
        plot_scaling(pd.read_csv(TABLES_DIR / "parte2_escala.csv"))
        return

    if not args.scaling_only:
        timing, results = run_benchmark(runs, fw_runs)
        timing.to_csv(TABLES_DIR / "parte2_tempos.csv", index=False)
        results.to_csv(TABLES_DIR / "parte2_resultados.csv", index=False)
        plot_times(timing)

    print(f"\nExperimento de escala ({reps} repetições por tamanho)...")
    scaling = scaling_experiment(reps)
    scaling.to_csv(TABLES_DIR / "parte2_escala.csv", index=False)
    slopes = plot_scaling(scaling)
    slopes.to_csv(TABLES_DIR / "parte2_expoentes.csv", index=False)
    print(slopes.to_string(index=False))


if __name__ == "__main__":
    main()
