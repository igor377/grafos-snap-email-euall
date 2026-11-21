"""Algoritmos de Tarjan (versões iterativas).

1. tarjan_scc: componentes fortemente conexas de um grafo DIRIGIDO.
   Executado no grafo dirigido original sem auto-loops (G_dir). Rodá-lo sobre a
   versão não dirigida seria trivial: cada componente conexa viraria uma única SCC.
2. bridges_and_articulation_points: pontes e vértices de articulação de um grafo
   NÃO dirigido, pelo mesmo esquema de índices/low-link. Executado na LCC.

Ambos fazem uma única DFS: O(V + E). São iterativos (pilha explícita), porque a
recursão estouraria o limite de pilha do Python em grafos com ~10^5 vértices.
"""


def tarjan_scc(adj) -> list[list[int]]:
    """SCCs de um grafo dirigido dado por adj[u] = [sucessores]."""
    n = len(adj)
    index = [-1] * n
    low = [0] * n
    on_stack = [False] * n
    stack: list[int] = []
    sccs: list[list[int]] = []
    counter = 0

    for s in range(n):
        if index[s] != -1:
            continue
        index[s] = low[s] = counter
        counter += 1
        stack.append(s)
        on_stack[s] = True
        call = [(s, 0)]
        while call:
            v, i = call[-1]
            succ = adj[v]
            if i < len(succ):
                call[-1] = (v, i + 1)
                w = succ[i]
                if index[w] == -1:
                    index[w] = low[w] = counter
                    counter += 1
                    stack.append(w)
                    on_stack[w] = True
                    call.append((w, 0))
                elif on_stack[w] and index[w] < low[v]:
                    low[v] = index[w]
            else:
                call.pop()
                if call:
                    p = call[-1][0]
                    if low[v] < low[p]:
                        low[p] = low[v]
                if low[v] == index[v]:
                    comp = []
                    while True:
                        w = stack.pop()
                        on_stack[w] = False
                        comp.append(w)
                        if w == v:
                            break
                    sccs.append(comp)
    return sccs


def bridges_and_articulation_points(adj) -> tuple[list[tuple[int, int]], list[int]]:
    """Pontes (u < v) e vértices de articulação de um grafo não dirigido simples."""
    n = len(adj)
    disc = [-1] * n
    low = [0] * n
    is_art = [False] * n
    bridges: list[tuple[int, int]] = []
    counter = 0

    for s in range(n):
        if disc[s] != -1:
            continue
        disc[s] = low[s] = counter
        counter += 1
        root_children = 0
        call = [(s, -1, 0)]  # (vértice, pai, próximo índice de vizinho)
        while call:
            v, parent, i = call[-1]
            nbrs = adj[v]
            if i < len(nbrs):
                call[-1] = (v, parent, i + 1)
                w = nbrs[i]
                if disc[w] == -1:
                    disc[w] = low[w] = counter
                    counter += 1
                    if v == s:
                        root_children += 1
                    call.append((w, v, 0))
                elif w != parent and disc[w] < low[v]:
                    low[v] = disc[w]
            else:
                call.pop()
                if parent != -1:
                    if low[v] < low[parent]:
                        low[parent] = low[v]
                    if low[v] > disc[parent]:
                        bridges.append((min(parent, v), max(parent, v)))
                    if parent != s and low[v] >= disc[parent]:
                        is_art[parent] = True
        if root_children > 1:
            is_art[s] = True
    return bridges, [v for v in range(n) if is_art[v]]


def directed_adjacency(n: int, edges) -> list[list[int]]:
    adj: list[list[int]] = [[] for _ in range(n)]
    for u, v in edges:
        adj[u].append(v)
    return adj
