"""Parte I: métricas estruturais (implementações próprias).

As métricas são calculadas em dois escopos:
  - grafo completo: não dirigido simples, sem auto-loops (265.214 vértices);
  - LCC: maior componente conexa (224.832 vértices).

Uso:
    python -m src.metrics
"""

import pandas as pd

from src.load import FIGURES_DIR, TABLES_DIR, load_lcc
from src.treatment import build_adjacency, connected_components, treat


def degrees(adj) -> list[int]:
    return [len(nbrs) for nbrs in adj]


def degree_stats(adj) -> dict:
    deg = degrees(adj)
    n = len(deg)
    return {"grau_min": min(deg), "grau_max": max(deg), "grau_medio": sum(deg) / n}


def density(n: int, m: int) -> float:
    """Densidade de grafo não dirigido simples: 2m / (n(n-1))."""
    return 2 * m / (n * (n - 1)) if n > 1 else 0.0


def component_sizes(components) -> list[int]:
    return [len(c) for c in components]


def basic_metrics(n: int, edges, components=None) -> dict:
    adj = build_adjacency(n, edges)
    if components is None:
        components = connected_components(adj)
    sizes = component_sizes(components)
    return {
        "vertices": n,
        "arestas": len(edges),
        **degree_stats(adj),
        "densidade": density(n, len(edges)),
        "componentes": len(sizes),
        "maior_componente": max(sizes),
        "menor_componente": min(sizes),
    }


def main() -> None:
    TABLES_DIR.mkdir(parents=True, exist_ok=True)
    t = treat()
    full = basic_metrics(t["n"], t["undirected_edges"], t["components"])
    n_lcc, lcc_edges, _ = load_lcc()
    lcc = basic_metrics(n_lcc, lcc_edges)

    table = pd.DataFrame({"metrica": list(full), "grafo_completo": list(full.values()),
                          "lcc": [lcc[k] for k in full]})
    table.to_csv(TABLES_DIR / "parte1_basicas.csv", index=False)
    print(table.to_string(index=False))

    # Tamanho de cada componente conexa (grafo completo)
    sizes = component_sizes(t["components"])
    pd.DataFrame({"componente": range(1, len(sizes) + 1), "tamanho": sizes}).to_csv(
        TABLES_DIR / "componentes_tamanhos.csv", index=False)
    freq = pd.Series(sizes).value_counts().sort_index()
    freq_df = pd.DataFrame({"tamanho": freq.index, "quantidade": freq.values})
    freq_df.to_csv(TABLES_DIR / "componentes_frequencia.csv", index=False)
    print("\nFrequência dos tamanhos de componente:")
    print(freq_df.to_string(index=False))
    plot_component_sizes(freq_df, largest=sizes[0])


def plot_component_sizes(freq_df: pd.DataFrame, largest: int) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.scatter(freq_df["tamanho"], freq_df["quantidade"], s=18)
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("Tamanho da componente (vértices)")
    ax.set_ylabel("Quantidade de componentes")
    ax.set_title("Distribuição dos tamanhos das componentes conexas")
    ax.annotate(f"LCC = {largest:,} vértices".replace(",", "."),
                xy=(largest, 1), xytext=(largest / 60, 8),
                arrowprops={"arrowstyle": "->"})
    ax.grid(True, which="both", alpha=0.3)
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "componentes_tamanhos.png", dpi=150)
    plt.close(fig)


if __name__ == "__main__":
    main()
