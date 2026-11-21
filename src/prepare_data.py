"""Gera o conjunto de dados tratado em data/processed/.

Arquivos gerados:
  lcc.edgelist.gz                  LCC não dirigida, vértices renumerados 0..n-1, `u v w`
  lcc_node_map.csv.gz              novo_id -> id original do SNAP
  directed_no_loops.edgelist.gz    grafo dirigido sem auto-loops (G_dir, para o Tarjan)
  subgraph_300.edgelist.gz         subgrafo induzido de 300 vértices obtido por BFS na LCC, `u v w`

Pesos: o grafo é não ponderado. Para os algoritmos ponderados (Dijkstra,
Bellman-Ford, Floyd-Warshall, Prim, Kruskal) atribuímos pesos inteiros
uniformes em [1, 10] com semente fixa, garantindo reprodutibilidade.

Uso:
    python -m src.prepare_data
"""

import random
from collections import deque

from src.load import (
    DIRECTED_FILE,
    LCC_FILE,
    LCC_MAP_FILE,
    SUBGRAPH_FILE,
    open_write,
    write_edgelist,
)
from src.treatment import build_adjacency, induced_relabel, treat

SEED = 42
SUBGRAPH_SIZE = 300
WEIGHT_MIN, WEIGHT_MAX = 1, 10


def synthetic_weights(m: int, seed: int = SEED) -> list[int]:
    rng = random.Random(seed)
    return [rng.randint(WEIGHT_MIN, WEIGHT_MAX) for _ in range(m)]


def bfs_sample(adj, size: int, seed: int = SEED) -> list[int]:
    """Primeiros `size` vértices visitados por uma BFS a partir de um vértice aleatório.

    O subgrafo induzido por esses vértices é conexo (contém a árvore da BFS).
    """
    rng = random.Random(seed)
    start = rng.randrange(len(adj))
    seen = {start}
    order = [start]
    queue = deque([start])
    while queue and len(order) < size:
        u = queue.popleft()
        for w in adj[u]:
            if w not in seen:
                seen.add(w)
                order.append(w)
                queue.append(w)
                if len(order) == size:
                    break
    return order


def main() -> None:
    t = treat()

    # LCC renumerada + pesos
    n_lcc = len(t["lcc_map"])
    lcc_edges = t["lcc_edges"]
    lcc_weights = synthetic_weights(len(lcc_edges))
    write_edgelist(
        LCC_FILE, lcc_edges, weights=lcc_weights,
        header=(f"email-EuAll - LCC nao dirigida simples, sem auto-loops\n"
                f"Vertices: {n_lcc} Arestas: {len(lcc_edges)}\n"
                f"Pesos sinteticos uniformes em [{WEIGHT_MIN},{WEIGHT_MAX}], seed={SEED}\n"
                f"u\tv\tw"),
    )
    with open_write(LCC_MAP_FILE) as f:
        f.write("novo_id,id_original\n")
        for new, old in enumerate(t["lcc_map"]):
            f.write(f"{new},{old}\n")

    # Grafo dirigido sem auto-loops
    write_edgelist(
        DIRECTED_FILE, t["directed_edges"],
        header=(f"email-EuAll - dirigido, sem auto-loops (ids originais)\n"
                f"Vertices: {t['n']} Arestas: {len(t['directed_edges'])}\nu\tv"),
    )

    # Subgrafo de 300 vértices via BFS na LCC
    adj = build_adjacency(n_lcc, lcc_edges)
    sample = bfs_sample(adj, SUBGRAPH_SIZE)
    weight_of = {e: w for e, w in zip(lcc_edges, lcc_weights)}
    sub_map, sub_edges = induced_relabel(sample, lcc_edges)
    sub_weights = [weight_of[(sub_map[u], sub_map[v])] for u, v in sub_edges]
    write_edgelist(
        SUBGRAPH_FILE, sub_edges, weights=sub_weights,
        header=(f"email-EuAll - subgrafo induzido por BFS na LCC (seed={SEED}, "
                f"inicio no id {sample[0]} da LCC)\n"
                f"Vertices: {len(sub_map)} Arestas: {len(sub_edges)}\n"
                f"Pesos herdados da LCC\nu\tv\tw"),
    )

    for path, desc in [
        (LCC_FILE, f"LCC: {n_lcc} vértices, {len(lcc_edges)} arestas"),
        (LCC_MAP_FILE, "mapa de ids da LCC"),
        (DIRECTED_FILE, f"dirigido: {t['n']} vértices, {len(t['directed_edges'])} arestas"),
        (SUBGRAPH_FILE, f"subgrafo: {len(sub_map)} vértices, {len(sub_edges)} arestas"),
    ]:
        print(f"{path.name:32s} {path.stat().st_size / 1e6:6.2f} MB  {desc}")


if __name__ == "__main__":
    main()
