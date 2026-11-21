"""Parte I: distribuição de graus e visualização reduzida do grafo (LCC).

Visualização: o grafo completo (224.832 vértices) é ilegível. Desenhamos um
subgrafo induzido de ~300 vértices em torno dos hubs: os 5 vértices de maior
grau e, para cada um, os vizinhos de maior grau, até completar 300 vértices.
O NetworkX é usado apenas para o layout e o desenho.

Uso:
    python -m src.visualize
"""

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import networkx as nx
import pandas as pd

from src.load import FIGURES_DIR, TABLES_DIR, load_lcc
from src.metrics import degrees
from src.treatment import build_adjacency

SEED = 42


def degree_distribution(adj) -> pd.DataFrame:
    s = pd.Series(degrees(adj)).value_counts().sort_index()
    n = len(adj)
    return pd.DataFrame({"grau": s.index, "quantidade": s.values, "P_k": s.values / n})


def plot_degree_distribution(dist: pd.DataFrame) -> None:
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4))
    lim = dist[dist["grau"] <= 30]
    ax1.bar(lim["grau"], lim["quantidade"], width=0.8)
    ax1.set_xlabel("Grau k")
    ax1.set_ylabel("Número de vértices")
    ax1.set_title("Distribuição de graus (escala linear, k ≤ 30)")
    ax1.grid(True, axis="y", alpha=0.3)

    ax2.scatter(dist["grau"], dist["P_k"], s=8)
    ax2.set_xscale("log")
    ax2.set_yscale("log")
    ax2.set_xlabel("Grau k")
    ax2.set_ylabel("P(k)")
    ax2.set_title("Distribuição de graus (escala log-log)")
    ax2.grid(True, which="both", alpha=0.3)
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "distribuicao_graus.png", dpi=150)
    plt.close(fig)


def hub_sample(adj, size: int = 300, hubs: int = 5) -> list[int]:
    deg = degrees(adj)
    top = sorted(range(len(adj)), key=lambda v: -deg[v])[:hubs]
    chosen = list(top)
    seen = set(top)
    per_hub = (size - hubs) // hubs
    for h in top:
        nbrs = sorted((w for w in adj[h] if w not in seen), key=lambda w: -deg[w])[:per_hub]
        chosen.extend(nbrs)
        seen.update(nbrs)
    return chosen[:size]


def plot_sample(adj, nodes: list[int]) -> None:
    g = nx.Graph()
    g.add_nodes_from(nodes)
    s = set(nodes)
    g.add_edges_from((u, w) for u in nodes for w in adj[u] if w in s and u < w)
    deg_full = degrees(adj)

    pos = nx.spring_layout(g, seed=SEED, k=0.15, iterations=100)
    sizes = [10 + 300 * (deg_full[v] / max(deg_full)) ** 0.5 for v in g.nodes()]
    colors = [deg_full[v] for v in g.nodes()]
    fig, ax = plt.subplots(figsize=(9, 9))
    nx.draw_networkx_edges(g, pos, ax=ax, alpha=0.25, width=0.5)
    nodes_art = nx.draw_networkx_nodes(g, pos, ax=ax, node_size=sizes, node_color=colors,
                                       cmap="viridis")
    nodes_art.set_norm(matplotlib.colors.LogNorm(vmin=min(colors), vmax=max(colors)))
    fig.colorbar(nodes_art, ax=ax, shrink=0.7, label="Grau no grafo (LCC)")
    ax.set_title(f"Amostra da LCC: {g.number_of_nodes()} vértices e {g.number_of_edges()} "
                 f"arestas em torno dos 5 maiores hubs")
    ax.axis("off")
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "visualizacao_amostra.png", dpi=150)
    plt.close(fig)


def main() -> None:
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    n, edges, _ = load_lcc()
    adj = build_adjacency(n, edges)
    dist = degree_distribution(adj)
    dist.to_csv(TABLES_DIR / "distribuicao_graus.csv", index=False)
    plot_degree_distribution(dist)
    deg1 = dist.loc[dist["grau"] == 1, "P_k"].iloc[0]
    print(f"Graus distintos: {len(dist)}; fração de vértices com grau 1: {deg1:.2%}")
    plot_sample(adj, hub_sample(adj))
    print("Figuras: distribuicao_graus.png, visualizacao_amostra.png")


if __name__ == "__main__":
    main()
