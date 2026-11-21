"""Árvore Geradora Mínima: Prim e Kruskal.

Aplicabilidade: com pesos todos iguais (grafo não ponderado) qualquer árvore
geradora seria mínima. Por isso usamos os pesos sintéticos inteiros em [1, 10]
(semente fixa). Executado na LCC (conexa), então a árvore tem V − 1 arestas.

- Prim: heap binário com "lazy deletion" -> O(E log V).
- Kruskal: ordenação das arestas O(E log E) = O(E log V) + union-find com
  compressão de caminho e união por rank (custo quase constante por operação).
Em grafos desconexos ambos devolvem uma floresta geradora mínima.
"""

import heapq


def prim(wadj) -> tuple[list[tuple[int, int, int]], int]:
    """Retorna (arestas (u, v, peso) da floresta geradora mínima, peso total)."""
    n = len(wadj)
    in_tree = [False] * n
    tree: list[tuple[int, int, int]] = []
    total = 0
    for root in range(n):
        if in_tree[root]:
            continue
        in_tree[root] = True
        heap = [(w, root, v) for v, w in wadj[root]]
        heapq.heapify(heap)
        while heap:
            w, u, v = heapq.heappop(heap)
            if in_tree[v]:
                continue
            in_tree[v] = True
            tree.append((u, v, w))
            total += w
            for x, wx in wadj[v]:
                if not in_tree[x]:
                    heapq.heappush(heap, (wx, v, x))
    return tree, total


class UnionFind:
    def __init__(self, n: int):
        self.parent = list(range(n))
        self.rank = [0] * n

    def find(self, x: int) -> int:
        root = x
        while self.parent[root] != root:
            root = self.parent[root]
        while self.parent[x] != root:  # compressão de caminho
            self.parent[x], x = root, self.parent[x]
        return root

    def union(self, a: int, b: int) -> bool:
        ra, rb = self.find(a), self.find(b)
        if ra == rb:
            return False
        if self.rank[ra] < self.rank[rb]:  # união por rank
            ra, rb = rb, ra
        self.parent[rb] = ra
        if self.rank[ra] == self.rank[rb]:
            self.rank[ra] += 1
        return True


def kruskal(n: int, edges, weights) -> tuple[list[tuple[int, int, int]], int]:
    """Retorna (arestas (u, v, peso) da floresta geradora mínima, peso total)."""
    order = sorted(range(len(edges)), key=weights.__getitem__)
    uf = UnionFind(n)
    tree: list[tuple[int, int, int]] = []
    total = 0
    for i in order:
        u, v = edges[i]
        if uf.union(u, v):
            tree.append((u, v, weights[i]))
            total += weights[i]
            if len(tree) == n - 1:
                break
    return tree, total
