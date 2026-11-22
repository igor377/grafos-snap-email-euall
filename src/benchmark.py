"""Parte II: execução dos algoritmos, tempos e intervalos de confiança.

Para cada algoritmo: n execuções medidas com time.perf_counter (apenas a
chamada do algoritmo; a construção da lista de adjacência fica fora da medição).

IC 95% da média:
  - n >= 30:            Normal:      média ± z_{α/2} · s/√n,       z = 1,96
  - n < 30 (σ desconh.): t-Student:  média ± t_{α/2, n−1} · s/√n

Também é feito um experimento de escala (tempo × tamanho da entrada) em
subgrafos induzidos por BFS de tamanhos crescentes, com ajuste linear em escala
log-log, para TODOS os algoritmos: o tempo médio é ajustado contra a própria
função teórica f(n) (V+E, (V+E) log V, E log V, V·E, V³); se f descreve bem o
custo, a inclinação é ≈ 1. Cada tamanho é medido 30 vezes, com IC 95% por ponto.
Os lineares e quase lineares usam subgrafos de 14 mil vértices até a LCC inteira;
Bellman-Ford, de 1 mil a 16 mil; Floyd-Warshall, de 50 a 300 (Python puro) e de
250 a 1.000 (versão vetorizada com numpy, mesmo algoritmo O(V³)).

Uso:
    python -m src.benchmark                 # completo (~20 min)
    python -m src.benchmark --scaling-only  # só o experimento de escala (~15 min)
    python -m src.benchmark --scaling-only --only "Floyd-Warshall (numpy)"
                                            # refaz só um algoritmo da escala
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


LINEAR_SIZES = (14_000, 28_000, 56_000, 112_000)  # + a LCC inteira
BF_SIZES = (1_000, 2_000, 4_000, 8_000, 16_000)
FW_SIZES = (50, 100, 150, 200, 250, 300)
FW_NUMPY_SIZES = (250, 500, 750, 1_000)

# nome -> (f(n) como texto, função teórica de (V, E))
THEORY = {
    "BFS": ("V+E", lambda v, e: v + e),
    "DFS": ("V+E", lambda v, e: v + e),
    "Eulerianidade": ("V+E", lambda v, e: v + e),
    "Tarjan (pontes/articulações)": ("V+E", lambda v, e: v + e),
    "Dijkstra": ("(V+E) log V", lambda v, e: (v + e) * math.log2(v)),
    "Prim": ("E log V", lambda v, e: e * math.log2(v)),
    "Kruskal": ("E log V", lambda v, e: e * math.log2(v)),
    "Bellman-Ford": ("V·E", lambda v, e: float(v) * e),
    "Floyd-Warshall": ("V³", lambda v, e: float(v) ** 3),
    "Floyd-Warshall (numpy)": ("V³", lambda v, e: float(v) ** 3),
}


def theoretical_cost(name: str, v: int, e: int) -> float:
    """Função de custo teórica f(n) do algoritmo, no pior caso."""
    return THEORY[name][1](v, e)


def scaling_experiment(reps: int, only: set[str] | None = None) -> pd.DataFrame:
    """Tempo × tamanho para os 9 algoritmos (e a versão numpy do Floyd-Warshall) em
    subgrafos induzidos por prefixos da ordem de BFS da LCC (todo prefixo é conexo).
    Cada tamanho é medido `reps` vezes. `only` restringe a alguns algoritmos."""
    n, edges, weights = load_lcc()
    adj = build_adjacency(n, edges)
    order = bfs_sample(adj, n)
    weight_of = dict(zip(edges, weights))

    def sub(k):
        mapping, sedges = induced_relabel(order[:k], edges)
        sw = [weight_of[(mapping[u], mapping[v])] for u, v in sedges]
        return k, sedges, sw

    rows = []

    def record(name, kk, m, fn, extra=None):
        if only and name not in only:
            return
        result, times = measure(fn, reps)
        rows.append({"algoritmo": name, "V": kk, "E": m,
                     "f_teorica": theoretical_cost(name, kk, m),
                     **(extra(result) if extra else {}), **confidence_interval(times)})
        print(f"  escala {name:30s} V={kk:>7} E={m:>7} média {statistics.fmean(times):.4f}s")

    linear = {"BFS", "DFS", "Eulerianidade", "Tarjan (pontes/articulações)", "Dijkstra",
              "Prim", "Kruskal"}
    for k in (*LINEAR_SIZES, n) if not only or only & linear else ():
        kk, se, sw = sub(k)
        a = build_adjacency(kk, se)
        wa = build_weighted_adjacency(kk, se, sw)
        m = len(se)
        record("BFS", kk, m, lambda: bfs(a, 0))
        record("DFS", kk, m, lambda: dfs(a, 0))
        record("Eulerianidade", kk, m, lambda: check_undirected(a))
        record("Tarjan (pontes/articulações)", kk, m, lambda: bridges_and_articulation_points(a))
        record("Dijkstra", kk, m, lambda: dijkstra(wa, 0))
        record("Prim", kk, m, lambda: prim(wa))
        record("Kruskal", kk, m, lambda: kruskal(kk, se, sw))
    for k in BF_SIZES:
        kk, se, sw = sub(k)
        record("Bellman-Ford", kk, len(se), lambda: bellman_ford(kk, se, sw, 0),
               extra=lambda r: {"rodadas": r[2]})
    for k in FW_SIZES:
        kk, se, sw = sub(k)
        record("Floyd-Warshall", kk, len(se), lambda: floyd_warshall(kk, se, sw))
    for k in FW_NUMPY_SIZES:
        kk, se, sw = sub(k)
        record("Floyd-Warshall (numpy)", kk, len(se),
               lambda: floyd_warshall_numpy(kk, se, sw))
    return pd.DataFrame(rows)


def loglog_fit(x, y) -> tuple[float, float, float]:
    """Reta log10(y) = a·log10(x) + b. Retorna (a, b, R²)."""
    lx, ly = np.log10(np.asarray(x, float)), np.log10(np.asarray(y, float))
    a, b = np.polyfit(lx, ly, 1)
    pred = a * lx + b
    r2 = 1 - np.sum((ly - pred) ** 2) / np.sum((ly - ly.mean()) ** 2)
    return float(a), float(b), float(r2)


def plot_scaling(df: pd.DataFrame) -> pd.DataFrame:
    """Um painel por algoritmo: tempo médio (IC 95%) contra a função teórica f(n), em
    log-log. Se f descreve o custo, a inclinação é ≈ 1."""
    names = [a for a in THEORY if a in set(df["algoritmo"])]
    cols = 3
    rows_n = math.ceil(len(names) / cols)
    fig, axes = plt.subplots(rows_n, cols, figsize=(14, 3.6 * rows_n), squeeze=False)
    fits = []
    for ax, name in zip(axes.flat, names):
        d = df[df["algoritmo"] == name].sort_values("f_teorica")
        fname = THEORY[name][0]
        slope, intercept, r2 = loglog_fit(d["f_teorica"], d["media_s"])
        fit = {"algoritmo": name, "funcao_teorica": fname, "expoente_vs_f": slope,
               "R2_vs_f": r2, "V_min": int(d["V"].min()), "V_max": int(d["V"].max()),
               "pontos": len(d)}
        if "rodadas" in d and d["rodadas"].notna().any():
            fit["rodadas_min"] = int(d["rodadas"].min())
            fit["rodadas_max"] = int(d["rodadas"].max())
        fits.append(fit)
        err = [d["media_s"] - d["ic95_inf_s"], d["ic95_sup_s"] - d["media_s"]]
        ax.errorbar(d["f_teorica"], d["media_s"], yerr=err, fmt="o", capsize=3,
                    label=f"média e IC 95% (n={int(d['n'].iloc[0])})")
        lx = np.log10(d["f_teorica"])
        xs = np.linspace(lx.min(), lx.max(), 50)
        ax.plot(10 ** xs, 10 ** (intercept + slope * xs), "--",
                label=f"inclinação {slope:.2f} (R² = {r2:.3f})")
        ax.set_xscale("log")
        ax.set_yscale("log")
        ax.set_title(f"{name}: f(n) = {fname}", fontsize=10)
        ax.set_xlabel("f(n)")
        ax.set_ylabel("Tempo médio (s)")
        ax.grid(True, which="both", alpha=0.3)
        ax.legend(fontsize=7)
    for ax in list(axes.flat)[len(names):]:
        ax.axis("off")
    fig.suptitle("Complexidade observada: tempo × função teórica f(n) (ideal: inclinação 1)")
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
    parser.add_argument("--only", nargs="+", metavar="ALGORITMO",
                        help="(com --scaling-only) mede só estes algoritmos e substitui "
                             "apenas as linhas deles no CSV de escala existente")
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

    only = set(args.only) if args.only else None
    if only and not only <= set(THEORY):
        parser.error(f"algoritmos desconhecidos: {sorted(only - set(THEORY))}")
    print(f"\nExperimento de escala ({reps} repetições por tamanho)...")
    scaling = scaling_experiment(reps, only)
    if only:
        old = pd.read_csv(TABLES_DIR / "parte2_escala.csv")
        scaling = pd.concat([old[~old["algoritmo"].isin(only)], scaling], ignore_index=True)
    scaling.to_csv(TABLES_DIR / "parte2_escala.csv", index=False)
    slopes = plot_scaling(scaling)
    slopes.to_csv(TABLES_DIR / "parte2_expoentes.csv", index=False)
    print(slopes.to_string(index=False))


if __name__ == "__main__":
    main()
