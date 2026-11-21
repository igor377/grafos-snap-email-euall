"""Leitura do grafo bruto (formato edgelist do SNAP)."""

import gzip
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


def write_edgelist(path: Path, edges, header: str = "") -> None:
    """Grava uma edgelist (u v por linha), compactada se o nome terminar em .gz."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "wt", encoding="utf-8", newline="\n") as f:
        for line in header.splitlines():
            f.write(f"# {line}\n")
        for u, v in edges:
            f.write(f"{u}\t{v}\n")
