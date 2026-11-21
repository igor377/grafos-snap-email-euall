"""Baixa o grafo bruto email-EuAll do SNAP para data/raw/.

Uso (a partir da raiz do projeto):
    python scripts/download_data.py           # baixa se ainda não existir
    python scripts/download_data.py --force   # baixa novamente
"""

import argparse
import gzip
import sys
import urllib.request
from pathlib import Path

URL = "https://snap.stanford.edu/data/email-EuAll.txt.gz"
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import src  # noqa: E402,F401  (configura a saída em UTF-8 no Windows)

RAW_DIR = ROOT / "data" / "raw"
DEST = RAW_DIR / "email-EuAll.txt.gz"

# Valores declarados pelo SNAP para o grafo original
EXPECTED_NODES = 265_214
EXPECTED_EDGES = 420_045


def download(force: bool = False) -> Path:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    if DEST.exists() and not force:
        print(f"Arquivo já existe: {DEST} (use --force para baixar de novo)")
        return DEST

    print(f"Baixando {URL} ...")
    tmp = DEST.with_suffix(".part")
    with urllib.request.urlopen(URL, timeout=120) as resp, open(tmp, "wb") as out:
        while chunk := resp.read(1 << 16):
            out.write(chunk)
    tmp.replace(DEST)
    print(f"Salvo em {DEST} ({DEST.stat().st_size / 1e6:.2f} MB)")
    return DEST


def check(path: Path) -> bool:
    """Confere se o arquivo tem o número de vértices e arestas declarado pelo SNAP."""
    nodes = set()
    edges = 0
    with gzip.open(path, "rt", encoding="utf-8") as f:
        for line in f:
            if line.startswith("#") or not line.strip():
                continue
            u, v = line.split()
            nodes.add(u)
            nodes.add(v)
            edges += 1
    ok = len(nodes) == EXPECTED_NODES and edges == EXPECTED_EDGES
    status = "OK" if ok else "DIVERGENTE"
    print(f"Vértices: {len(nodes):,} (esperado {EXPECTED_NODES:,})")
    print(f"Arestas:  {edges:,} (esperado {EXPECTED_EDGES:,})")
    print(f"Conferência: {status}")
    return ok


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--force", action="store_true", help="baixa novamente mesmo se já existir")
    args = parser.parse_args()
    path = download(force=args.force)
    sys.exit(0 if check(path) else 1)
