"""Centralidades de cada vértice da LCC, calculadas uma vez e salvas em
data/processed/centralidades.csv.gz (usadas na robustez e na tabela de hubs).

Colunas:
  id                  id do vértice na LCC (0..n-1)
  id_original         id no arquivo do SNAP
  grau                grau no grafo não dirigido (LCC)
  grau_entrada/saida  graus no grafo dirigido original (e-mails recebidos/enviados)
  frac_vizinhos_grau1 fração dos vizinhos que têm grau 1 (folhas)
  pagerank            PageRank (d = 0,85), implementação própria
  betweenness         betweenness estimada por Brandes com K fontes amostradas

Uso:
    python -m src.centrality     # ~5 min (betweenness com 500 fontes)
"""

import time

import numpy as np
import pandas as pd

from src.algorithms.betweenness import betweenness
from src.algorithms.pagerank import pagerank
from src.load import LCC_MAP_FILE, PROCESSED_DIR, load_directed, load_lcc, open_write
from src.metrics import degrees
from src.treatment import build_adjacency

CENTRALITY_FILE = PROCESSED_DIR / "centralidades.csv.gz"
BETWEENNESS_SOURCES = 500
SEED = 42


def load_centralities() -> pd.DataFrame:
    return pd.read_csv(CENTRALITY_FILE)


def main() -> None:
    n, edges, _ = load_lcc()
    adj = build_adjacency(n, edges)
    deg = np.asarray(degrees(adj))

    original = pd.read_csv(LCC_MAP_FILE)["id_original"].to_numpy()
    nd, dedges = load_directed()
    d = np.asarray(dedges, dtype=np.int64)
    out_deg = np.bincount(d[:, 0], minlength=nd)[original]
    in_deg = np.bincount(d[:, 1], minlength=nd)[original]

    leaf = deg == 1
    frac_leaf = np.array([leaf[nbrs].mean() if nbrs else 0.0 for nbrs in adj])

    t0 = time.perf_counter()
    pr, iters = pagerank(n, edges)
    print(f"PageRank: {iters} iterações ({time.perf_counter() - t0:.1f}s)")

    t0 = time.perf_counter()
    bc = betweenness(adj, k=BETWEENNESS_SOURCES, seed=SEED)
    print(f"Betweenness ({BETWEENNESS_SOURCES} fontes): {time.perf_counter() - t0:.0f}s")

    df = pd.DataFrame({"id": np.arange(n), "id_original": original, "grau": deg,
                       "grau_entrada": in_deg, "grau_saida": out_deg,
                       "frac_vizinhos_grau1": frac_leaf, "pagerank": pr, "betweenness": bc})
    with open_write(CENTRALITY_FILE) as f:
        df.to_csv(f, index=False, float_format="%.10g", lineterminator="\n")
    print(f"Salvo em {CENTRALITY_FILE}")


if __name__ == "__main__":
    main()
