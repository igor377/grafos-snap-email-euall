"""Tratamento do grafo email-EuAll.

Etapas (nesta ordem):
  1. Grafo bruto: dirigido, como distribuído pelo SNAP.
  2. Remoção de auto-loops.
  3. Dirigido -> não dirigido simples: u->v e v->u viram uma única aresta {u, v}.
  4. Extração da maior componente conexa (LCC).

Não há etapa temporal nem de multigrafo: o SNAP já distribui o grafo agregado
(out/2003 a mar/2005, sem timestamps) e sem arestas repetidas.

Uso:
    python -m src.treatment     # gera results/tables/tratamento_evolucao.csv
"""

from collections import deque

import pandas as pd

from src.load import RAW_FILE, TABLES_DIR, read_edgelist

Adjacency = list[list[int]]


def remove_self_loops(edges):
    return [(u, v) for u, v in edges if u != v]


def to_undirected_simple(edges) -> list[tuple[int, int]]:
    """Converte arestas dirigidas em não dirigidas sem repetição (u < v)."""
    return sorted({(u, v) if u < v else (v, u) for u, v in edges if u != v})


def build_adjacency(n: int, edges) -> Adjacency:
    """Lista de adjacência não dirigida para vértices 0..n-1."""
    adj: Adjacency = [[] for _ in range(n)]
    for u, v in edges:
        adj[u].append(v)
        adj[v].append(u)
    return adj


def connected_components(adj: Adjacency) -> list[list[int]]:
    """Componentes conexas via BFS iterativa, da maior para a menor."""
    n = len(adj)
    seen = [False] * n
    components = []
    for s in range(n):
        if seen[s]:
            continue
        seen[s] = True
        comp = [s]
        queue = deque([s])
        while queue:
            u = queue.popleft()
            for w in adj[u]:
                if not seen[w]:
                    seen[w] = True
                    comp.append(w)
                    queue.append(w)
        components.append(comp)
    components.sort(key=len, reverse=True)
    return components


def induced_relabel(nodes, edges) -> tuple[list[int], list[tuple[int, int]]]:
    """Restringe as arestas a `nodes` e renumera os vértices para 0..k-1.

    Retorna (mapeamento novo_id -> id_original, arestas renumeradas).
    """
    old_ids = sorted(nodes)
    new_id = {old: i for i, old in enumerate(old_ids)}
    new_edges = [(new_id[u], new_id[v]) for u, v in edges if u in new_id and v in new_id]
    return old_ids, new_edges


def treat(path=RAW_FILE) -> dict:
    """Executa todo o tratamento e devolve os grafos intermediários e a tabela de evolução."""
    n, raw = read_edgelist(path)
    no_loops = remove_self_loops(raw)
    undirected = to_undirected_simple(no_loops)
    adj = build_adjacency(n, undirected)
    components = connected_components(adj)
    lcc_map, lcc_edges = induced_relabel(components[0], undirected)

    evolution = pd.DataFrame(
        [
            ("Grafo bruto (dirigido)", n, len(raw)),
            ("Após remoção de auto-loops (dirigido)", n, len(no_loops)),
            ("Após conversão para não dirigido simples", n, len(undirected)),
            ("Maior componente conexa (LCC)", len(lcc_map), len(lcc_edges)),
        ],
        columns=["etapa", "vertices", "arestas"],
    )
    return {
        "n": n,
        "raw_edges": raw,
        "directed_edges": no_loops,  # G_dir: usado no Tarjan (SCC)
        "undirected_edges": undirected,
        "components": components,
        "lcc_map": lcc_map,
        "lcc_edges": lcc_edges,
        "evolution": evolution,
    }


def main() -> None:
    result = treat()
    evo = result["evolution"]
    comps = result["components"]
    print(evo.to_string(index=False))
    print(f"\nAuto-loops removidos: {len(result['raw_edges']) - len(result['directed_edges'])}")
    print(f"Componentes conexas (não dirigido): {len(comps)}")
    print(f"LCC: {len(comps[0])} vértices ({len(comps[0]) / result['n']:.2%} do total), "
          f"{len(result['lcc_edges'])} arestas "
          f"({len(result['lcc_edges']) / len(result['undirected_edges']):.2%} do total)")
    TABLES_DIR.mkdir(parents=True, exist_ok=True)
    out = TABLES_DIR / "tratamento_evolucao.csv"
    evo.to_csv(out, index=False)
    print(f"\nTabela salva em {out}")


if __name__ == "__main__":
    main()
