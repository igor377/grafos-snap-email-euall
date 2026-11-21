"""Leitura do grafo bruto (formato edgelist do SNAP)."""

import gzip
import io
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW_FILE = ROOT / "data" / "raw" / "email-EuAll.txt.gz"
PROCESSED_DIR = ROOT / "data" / "processed"
TABLES_DIR = ROOT / "results" / "tables"
FIGURES_DIR = ROOT / "results" / "figures"


def _open(path: Path):
    path = Path(path)
    if path.suffix == ".gz":
        return gzip.open(path, "rt", encoding="utf-8")
    return open(path, "r", encoding="utf-8")


def read_edgelist(path: Path = RAW_FILE) -> tuple[int, list[tuple[int, int]]]:
    """Lê uma edgelist ignorando comentários (`#`).

    Retorna (n, arestas), onde n = maior id + 1. No email-EuAll os ids vão de
    0 a n-1 sem lacunas, então n é também o número de vértices.
    """
    edges: list[tuple[int, int]] = []
    max_id = -1
    with _open(path) as f:
        for line in f:
            if line.startswith("#") or not line.strip():
                continue
            u, v = map(int, line.split())
            edges.append((u, v))
            if u > max_id:
                max_id = u
            if v > max_id:
                max_id = v
    return max_id + 1, edges


def open_write(path: Path):
    """Abre para escrita em texto; se .gz, usa mtime=0 para o arquivo ser determinístico."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.suffix == ".gz":
        raw = gzip.GzipFile(path, "wb", mtime=0)
        return io.TextIOWrapper(raw, encoding="utf-8", newline="\n")
    return open(path, "w", encoding="utf-8", newline="\n")


def write_edgelist(path: Path, edges, header: str = "", weights=None) -> None:
    """Grava uma edgelist (`u v` ou `u v w` por linha), compactada se terminar em .gz."""
    with open_write(path) as f:
        for line in header.splitlines():
            f.write(f"# {line}\n")
        if weights is None:
            for u, v in edges:
                f.write(f"{u}\t{v}\n")
        else:
            for (u, v), w in zip(edges, weights, strict=True):
                f.write(f"{u}\t{v}\t{w}\n")


def read_weighted_edgelist(path: Path) -> tuple[int, list[tuple[int, int]], list[int]]:
    """Lê uma edgelist `u v w`. Retorna (n, arestas, pesos)."""
    edges: list[tuple[int, int]] = []
    weights: list[int] = []
    max_id = -1
    with _open(path) as f:
        for line in f:
            if line.startswith("#") or not line.strip():
                continue
            u, v, w = map(int, line.split())
            edges.append((u, v))
            weights.append(w)
            max_id = max(max_id, u, v)
    return max_id + 1, edges, weights


# Arquivos tratados (gerados por `python -m src.prepare_data`)
LCC_FILE = PROCESSED_DIR / "lcc.edgelist.gz"
LCC_MAP_FILE = PROCESSED_DIR / "lcc_node_map.csv.gz"
DIRECTED_FILE = PROCESSED_DIR / "directed_no_loops.edgelist.gz"
SUBGRAPH_FILE = PROCESSED_DIR / "subgraph_300.edgelist.gz"


def load_lcc() -> tuple[int, list[tuple[int, int]], list[int]]:
    """LCC não dirigida (vértices 0..n-1) com pesos sintéticos 1–10."""
    return read_weighted_edgelist(LCC_FILE)


def load_subgraph() -> tuple[int, list[tuple[int, int]], list[int]]:
    """Subgrafo de 300 vértices (BFS na LCC) com pesos sintéticos 1–10."""
    return read_weighted_edgelist(SUBGRAPH_FILE)


def load_directed() -> tuple[int, list[tuple[int, int]]]:
    """Grafo dirigido original sem auto-loops (ids originais)."""
    return read_edgelist(DIRECTED_FILE)
