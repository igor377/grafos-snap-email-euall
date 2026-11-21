"""Verificação de Eulerianidade (e construção por Hierholzer).

Não dirigido (teorema de Euler):
  - circuito euleriano  <=> arestas numa única componente e todos os graus pares;
  - caminho euleriano   <=> idem, com exatamente 2 vértices de grau ímpar.
Dirigido:
  - circuito <=> arestas numa única componente fracamente conexa e
                 grau_entrada(v) = grau_saida(v) para todo v;
  - caminho  <=> idem, exceto um vértice com saida - entrada = 1 (início) e
                 um com entrada - saida = 1 (fim).
Verificação: O(V + E). Hierholzer (iterativo): O(V + E).
"""

from collections import deque


def _connected_ignoring_isolated(n: int, und_adj) -> bool:
    """True se todos os vértices com grau > 0 estão na mesma componente."""
    start = next((v for v in range(n) if und_adj[v]), None)
    if start is None:
        return True
    seen = [False] * n
    seen[start] = True
    queue = deque([start])
    while queue:
        u = queue.popleft()
        for w in und_adj[u]:
            if not seen[w]:
                seen[w] = True
                queue.append(w)
    return all(seen[v] or not und_adj[v] for v in range(n))


def check_undirected(adj) -> dict:
    n = len(adj)
    odd = [v for v in range(n) if len(adj[v]) % 2 == 1]
    connected = _connected_ignoring_isolated(n, adj)
    if connected and not odd:
        kind = "circuito euleriano"
    elif connected and len(odd) == 2:
        kind = "caminho euleriano"
    else:
        kind = "não euleriano"
    return {"tipo": kind, "conexo": connected, "vertices_grau_impar": len(odd),
            "impares": odd if len(odd) <= 2 else None}


def check_directed(n: int, edges) -> dict:
    out_deg = [0] * n
    in_deg = [0] * n
    und = [[] for _ in range(n)]
    for u, v in edges:
        out_deg[u] += 1
        in_deg[v] += 1
        und[u].append(v)
        und[v].append(u)
    connected = _connected_ignoring_isolated(n, und)
    unbalanced = [v for v in range(n) if out_deg[v] != in_deg[v]]
    plus = [v for v in unbalanced if out_deg[v] - in_deg[v] == 1]
    minus = [v for v in unbalanced if in_deg[v] - out_deg[v] == 1]
    if connected and not unbalanced:
        kind = "circuito euleriano"
    elif connected and len(unbalanced) == 2 and len(plus) == 1 and len(minus) == 1:
        kind = "caminho euleriano"
    else:
        kind = "não euleriano"
    return {"tipo": kind, "fracamente_conexo": connected,
            "vertices_desbalanceados": len(unbalanced),
            "inicio": plus[0] if kind == "caminho euleriano" else None}


def hierholzer_undirected(n: int, edges) -> list[int] | None:
    """Sequência de vértices de um circuito/caminho euleriano, ou None se não existir."""
    adj = [[] for _ in range(n)]
    for i, (u, v) in enumerate(edges):
        adj[u].append((v, i))
        adj[v].append((u, i))
    info = check_undirected([[w for w, _ in a] for a in adj])
    if info["tipo"] == "não euleriano":
        return None
    if not edges:
        return []
    start = info["impares"][0] if info["impares"] else edges[0][0]
    used = [False] * len(edges)
    ptr = [0] * n
    stack, path = [start], []
    while stack:
        u = stack[-1]
        while ptr[u] < len(adj[u]) and used[adj[u][ptr[u]][1]]:
            ptr[u] += 1
        if ptr[u] == len(adj[u]):
            path.append(stack.pop())
        else:
            w, i = adj[u][ptr[u]]
            used[i] = True
            stack.append(w)
    return path[::-1]
