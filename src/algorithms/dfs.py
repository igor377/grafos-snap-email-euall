"""Busca em Profundidade (Depth-First Search), versão iterativa.

Uma versão recursiva estouraria a pilha do Python (limite padrão ~1000
chamadas) em caminhos longos da LCC. Usamos uma pilha explícita de
(vértice, índice do próximo vizinho), o que reproduz exatamente a ordem da DFS
recursiva. Cada vértice é empilhado uma vez e cada aresta examinada duas
vezes -> O(V + E).
"""


def dfs(adj, source: int) -> tuple[list[int], list[int]]:
    """DFS a partir de `source`. Retorna (ordem de descoberta / pré-ordem, pai)."""
    n = len(adj)
    visited = [False] * n
    parent = [-1] * n
    visited[source] = True
    order = [source]
    stack = [(source, 0)]
    while stack:
        u, i = stack[-1]
        nbrs = adj[u]
        # avança até o próximo vizinho não visitado
        while i < len(nbrs) and visited[nbrs[i]]:
            i += 1
        if i == len(nbrs):
            stack.pop()
            continue
        w = nbrs[i]
        stack[-1] = (u, i + 1)
        visited[w] = True
        parent[w] = u
        order.append(w)
        stack.append((w, 0))
    return order, parent
